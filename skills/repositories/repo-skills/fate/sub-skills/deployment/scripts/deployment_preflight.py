#!/usr/bin/env python3
"""Safe, read-only preflight checks for the deployment sub-skill.

The script inspects:
- package presence and versions
- command availability for fate_flow, pipeline, Docker, and compose
- local port occupancy
- optional SSH reachability checks when targets are supplied

It is intentionally non-destructive. By default, mismatches are reported as
warnings. Pass --strict to turn warnings into a non-zero exit code.
"""

from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
from importlib import metadata
from typing import Iterable

EXPECTED_VERSIONS = {
    "pyfate": "2.2.0",
    "fate_client": "2.2.0",
    "fate_flow": "2.2.0",
    "fate_utils": "0.1.0",
}

DEFAULT_PORTS = [8080, 9360, 9380, 9370, 4670, 4671]


def run_command(argv: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return 127, f"command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(argv)}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def package_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive for unknown envs
        return f"error: {exc}"


def import_fate_version() -> str | None:
    try:
        import fate  # type: ignore

        return getattr(fate, "__version__", None)
    except Exception as exc:  # pragma: no cover - defensive for unknown envs
        return f"error: {exc}"


def port_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def classify_version(current: str | None, expected: str) -> tuple[str, str]:
    if current is None:
        return "warn", "not installed"
    if isinstance(current, str) and current.startswith("error:"):
        return "warn", current
    if current != expected:
        return "warn", f"installed {current}, expected {expected}"
    return "ok", f"version {current}"


def add_result(results: list[dict], level: str, name: str, detail: str, strict: bool) -> None:
    effective = "error" if strict and level != "ok" else level
    results.append({"level": effective, "name": name, "detail": detail})
    print(f"[{effective.upper():5}] {name}: {detail}")


def check_package(results: list[dict], dist_name: str, strict: bool) -> None:
    level, detail = classify_version(package_version(dist_name), EXPECTED_VERSIONS[dist_name])
    add_result(results, level, f"package {dist_name}", detail, strict)


def check_import(results: list[dict], strict: bool) -> None:
    current = import_fate_version()
    expected = EXPECTED_VERSIONS["pyfate"]
    level, detail = classify_version(current, expected)
    add_result(results, level, "import fate", detail, strict)


def check_help_command(results: list[dict], label: str, argv: list[str], strict: bool) -> None:
    rc, output = run_command(argv)
    if rc == 0:
        first_line = output.splitlines()[0] if output else "help available"
        add_result(results, "ok", label, first_line, strict)
    else:
        msg = output or f"exit code {rc}"
        add_result(results, "warn", label, msg, strict)


def check_command_presence(results: list[dict], command: str, strict: bool) -> None:
    path = shutil.which(command)
    if path:
        add_result(results, "ok", f"command {command}", path, strict)
    else:
        add_result(results, "warn", f"command {command}", "not found on PATH", strict)


def check_compose(results: list[dict], strict: bool) -> None:
    if shutil.which("docker-compose"):
        check_help_command(results, "command docker-compose", ["docker-compose", "--version"], strict)
        return
    if shutil.which("docker"):
        rc, output = run_command(["docker", "compose", "version"])
        if rc == 0:
            first_line = output.splitlines()[0] if output else "compose available via docker"
            add_result(results, "ok", "command docker compose", first_line, strict)
        else:
            add_result(results, "warn", "command docker compose", output or f"exit code {rc}", strict)
        return
    add_result(results, "warn", "compose support", "docker and docker-compose are both missing", strict)


def check_ports(results: list[dict], ports: Iterable[int], strict: bool) -> None:
    for port in ports:
        if port_listening(port):
            add_result(results, "warn", f"port {port}", "listening on 127.0.0.1", strict)
        else:
            add_result(results, "ok", f"port {port}", "free on 127.0.0.1", strict)


def check_ssh_targets(results: list[dict], targets: list[str], strict: bool) -> None:
    if not targets:
        return
    check_command_presence(results, "ssh", strict)
    for target in targets:
        rc, output = run_command(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", target, "echo ok"],
            timeout=8,
        )
        if rc == 0:
            add_result(results, "ok", f"ssh {target}", "keyless login works", strict)
        else:
            add_result(results, "warn", f"ssh {target}", output or f"exit code {rc}", strict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe deployment preflight for FATE")
    parser.add_argument(
        "--mode",
        choices=["all", "pypi", "service", "docker", "compose"],
        default="all",
        help="Focus the check on one deployment path.",
    )
    parser.add_argument(
        "--ports",
        nargs="*",
        type=int,
        default=DEFAULT_PORTS,
        help="Ports to probe locally for occupancy.",
    )
    parser.add_argument(
        "--ssh-target",
        action="append",
        default=[],
        help="Optional SSH target in user@host form for a read-only keyless-login probe.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when any warning is found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[dict] = []

    print(f"Mode: {args.mode}")
    print("Checks are read-only. Warnings do not fail the script unless --strict is set.\n")

    check_import(results, args.strict)
    check_package(results, "pyfate", args.strict)
    check_package(results, "fate_utils", args.strict)

    if args.mode in {"all", "service", "compose"}:
        check_package(results, "fate_client", args.strict)
        check_package(results, "fate_flow", args.strict)
        check_command_presence(results, "fate_flow", args.strict)
        check_help_command(results, "fate_flow --help", ["fate_flow", "--help"], args.strict)
        check_command_presence(results, "pipeline", args.strict)
        check_help_command(results, "pipeline --help", ["pipeline", "--help"], args.strict)
        check_help_command(
            results,
            "python -m fate.components --help",
            [sys.executable, "-m", "fate.components", "--help"],
            args.strict,
        )

    if args.mode in {"all", "docker", "compose"}:
        check_command_presence(results, "docker", args.strict)
        check_help_command(results, "docker --version", ["docker", "--version"], args.strict)
        check_compose(results, args.strict)

    if args.mode in {"all", "service", "docker", "compose"}:
        check_ports(results, args.ports, args.strict)

    if args.mode == "pypi":
        check_help_command(
            results,
            "python -m fate.components --help",
            [sys.executable, "-m", "fate.components", "--help"],
            args.strict,
        )

    if args.mode == "compose":
        check_ssh_targets(results, args.ssh_target, args.strict)
    elif args.ssh_target:
        # Allow SSH probes in other modes when the caller supplies targets.
        check_ssh_targets(results, args.ssh_target, args.strict)

    warnings = sum(1 for item in results if item["level"] == "warn")
    errors = sum(1 for item in results if item["level"] == "error")
    oks = sum(1 for item in results if item["level"] == "ok")

    print(
        f"\nSummary: {oks} ok, {warnings} warn, {errors} error"
        + (" (strict mode)" if args.strict else "")
    )

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
