#!/usr/bin/env python3
"""Safe Unsloth Studio preflight checker.

This script inspects local environment variables, launch flags, expected Studio
paths, port availability, and CLI help. It does not start Studio, install
packages, fetch network resources, load models, or modify user files.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable

THREAD_ENV_VARS = (
    "UNSLOTH_CPU_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

STUDIO_ENV_VARS = (
    "UNSLOTH_STUDIO_HOME",
    "STUDIO_HOME",
    "UNSLOTH_LLAMA_CPP_PATH",
    "UNSLOTH_STUDIO_URL",
    "UNSLOTH_API_KEY",
    "UNSLOTH_STUDIO_ALLOW_STDIO_MCP",
    "UNSLOTH_STUDIO_TRUST_FORWARDED",
    "UNSLOTH_STUDIO_DOCUMENTS_HOME",
    "UNSLOTH_STUDIO_PROJECTS_HOME",
    "UNSLOTH_NO_TORCH",
    "UNSLOTH_PYTHON",
)


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    return repr(value)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_studio_root() -> tuple[Path, str]:
    override = (os.environ.get("UNSLOTH_STUDIO_HOME") or "").strip()
    if override:
        return Path(override).expanduser(), "UNSLOTH_STUDIO_HOME"
    alias = (os.environ.get("STUDIO_HOME") or "").strip()
    if alias:
        return Path(alias).expanduser(), "STUDIO_HOME"
    return Path.home() / ".unsloth" / "studio", "default"


def _is_loopback(host: str) -> bool:
    lowered = (host or "").strip().lower()
    if lowered in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return bool(socket.getaddrinfo(lowered, None, socket.AF_UNSPEC)) and all(
            _addr_is_loopback(item[4][0]) for item in socket.getaddrinfo(lowered, None, socket.AF_UNSPEC)
        )
    except Exception:
        return False


def _addr_is_loopback(value: str) -> bool:
    try:
        import ipaddress

        return ipaddress.ip_address(value).is_loopback
    except Exception:
        return False


def _port_state(host: str, port: int, timeout: float = 0.3) -> dict:
    result = {"host": host, "port": port, "connects": False, "bind_available": None, "error": None}
    try:
        with socket.create_connection((host, port), timeout=timeout):
            result["connects"] = True
    except OSError as exc:
        result["connect_error"] = exc.__class__.__name__
    try:
        family = socket.AF_INET6 if ":" in host and host != "0.0.0.0" else socket.AF_INET
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            result["bind_available"] = True
    except OSError as exc:
        result["bind_available"] = False
        result["error"] = str(exc)
    return result


def _path_info(path: Path) -> dict:
    info = {"path": str(path), "exists": False, "is_dir": False, "is_file": False}
    try:
        info["exists"] = path.exists()
        info["is_dir"] = path.is_dir()
        info["is_file"] = path.is_file()
        if info["exists"]:
            info["resolved"] = str(path.resolve())
    except OSError as exc:
        info["error"] = str(exc)
    return info


def _run_help(command: list[str], timeout: float) -> dict:
    executable = shutil.which(command[0])
    if executable is None:
        return {"command": command, "found": False}
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return {
            "command": [executable, *command[1:]],
            "found": True,
            "returncode": completed.returncode,
            "first_lines": output.splitlines()[:18],
        }
    except subprocess.TimeoutExpired:
        return {"command": [executable, *command[1:]], "found": True, "timeout": True}
    except Exception as exc:
        return {"command": [executable, *command[1:]], "found": True, "error": str(exc)}


def _validate_cpu_threads(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw.strip())
    except ValueError:
        return "UNSLOTH_CPU_THREADS must be a positive integer"
    if value <= 0:
        return "UNSLOTH_CPU_THREADS must be a positive integer"
    return None


def _flag_warnings(args: argparse.Namespace, extras: Iterable[str]) -> list[str]:
    warnings: list[str] = []
    extras = list(extras)
    if args.secure and args.no_cloudflare:
        warnings.append("--secure requires Cloudflare; do not combine with --no-cloudflare")
    if args.secure and args.host not in {"127.0.0.1", "localhost", "::1"}:
        warnings.append("--secure will force the raw server bind back to loopback")
    if args.host in {"0.0.0.0", "::"}:
        warnings.append("raw wildcard bind is network-reachable; keep API keys private")
        if not args.disable_tools:
            warnings.append("consider --disable-tools for network-exposed Studio")
    if args.enable_tools and args.disable_tools:
        warnings.append("do not pass both --enable-tools and --disable-tools")
    if args.parallel < 1 or args.parallel > 64:
        warnings.append("--parallel must be between 1 and 64")
    if "--mmproj" in extras or "--mmproj-url" in extras:
        warnings.append("--mmproj/--mmproj-url are Studio-managed llama-server flags")
    if "--api-key" in extras or "--ssl-key-file" in extras or "--ssl-cert-file" in extras:
        warnings.append("llama-server auth/TLS flags are Studio-managed and should not be pass-through extras")
    return warnings


def build_report(args: argparse.Namespace, extras: list[str]) -> dict:
    root, root_source = _resolve_studio_root()
    venv = root / "unsloth_studio"
    python_bin = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    shim = root / "bin" / ("unsloth.exe" if os.name == "nt" else "unsloth")
    frontend = venv / ("Lib/site-packages/studio/frontend/dist/index.html" if os.name == "nt" else "lib")
    if os.name != "nt":
        frontend_candidates = list(venv.glob("lib/python*/site-packages/studio/frontend/dist/index.html"))
    else:
        frontend_candidates = [frontend]

    env_snapshot = {name: os.environ.get(name) for name in STUDIO_ENV_VARS if os.environ.get(name) is not None}
    redacted_env = dict(env_snapshot)
    if "UNSLOTH_API_KEY" in redacted_env:
        value = redacted_env["UNSLOTH_API_KEY"] or ""
        redacted_env["UNSLOTH_API_KEY"] = value[:6] + "..." if value else ""

    thread_snapshot = {name: os.environ.get(name) for name in THREAD_ENV_VARS if os.environ.get(name) is not None}
    warnings = _flag_warnings(args, extras)
    cpu_warning = _validate_cpu_threads(os.environ.get("UNSLOTH_CPU_THREADS"))
    if cpu_warning:
        warnings.append(cpu_warning)
    if os.environ.get("UNSLOTH_STUDIO_HOME") and os.environ.get("STUDIO_HOME"):
        warnings.append("UNSLOTH_STUDIO_HOME overrides STUDIO_HOME")
    if _truthy(os.environ.get("UNSLOTH_STUDIO_ALLOW_STDIO_MCP")) and (args.host in {"0.0.0.0", "::"}):
        warnings.append("stdio MCP explicitly enabled while using a network bind")

    report = {
        "ok": not warnings,
        "platform": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "requested_launch": {
            "host": args.host,
            "port": args.port,
            "secure": args.secure,
            "cloudflare": not args.no_cloudflare,
            "api_only": args.api_only,
            "parallel": args.parallel,
            "enable_tools": args.enable_tools,
            "disable_tools": args.disable_tools,
            "extras": extras,
            "loopback_host": _is_loopback(args.host),
        },
        "environment": redacted_env,
        "thread_environment": thread_snapshot,
        "studio_root": {
            "source": root_source,
            **_path_info(root),
            "venv_python": _path_info(python_bin),
            "launcher_shim": _path_info(shim),
            "auth_dir": _path_info(root / "auth"),
            "studio_db": _path_info(root / "studio.db"),
            "rag_dir": _path_info(root / "rag"),
            "cache_dir": _path_info(root / "cache"),
            "llama_cpp_dir": _path_info(root / "llama.cpp"),
            "frontend_index_candidates": [_path_info(candidate) for candidate in frontend_candidates[:5]],
        },
        "port": _port_state(args.host, args.port) if args.check_port else {"skipped": True},
        "cli_help": {},
        "warnings": warnings,
    }
    if args.check_cli_help:
        timeout = args.help_timeout
        report["cli_help"] = {
            "unsloth": _run_help(["unsloth", "--help"], timeout),
            "unsloth_studio": _run_help(["unsloth", "studio", "--help"], timeout),
            "unsloth_studio_run": _run_help(["unsloth", "studio", "run", "--help"], timeout),
            "unsloth_connect": _run_help(["unsloth", "connect", "--help"], timeout),
        }
    return report


def print_text(report: dict) -> None:
    print("Unsloth Studio safe preflight")
    print(f"ok: {report['ok']}")
    print(f"platform: {report['platform']['system']} {report['platform']['release']} {report['platform']['machine']}")
    root = report["studio_root"]
    print(f"studio root ({root['source']}): {root['path']} exists={root['exists']}")
    print(f"requested: host={report['requested_launch']['host']} port={report['requested_launch']['port']} secure={report['requested_launch']['secure']} cloudflare={report['requested_launch']['cloudflare']}")
    port = report["port"]
    if not port.get("skipped"):
        print(f"port: connects={port.get('connects')} bind_available={port.get('bind_available')}")
    if report["environment"]:
        print("environment:")
        for key, value in sorted(report["environment"].items()):
            print(f"  {key}={value}")
    if report["thread_environment"]:
        print("thread env:")
        for key, value in sorted(report["thread_environment"].items()):
            print(f"  {key}={value}")
    if report["warnings"]:
        print("warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    if report["cli_help"]:
        print("cli help:")
        for name, result in report["cli_help"].items():
            status = "found" if result.get("found") else "missing"
            if result.get("timeout"):
                status = "timeout"
            elif result.get("returncode") not in (None, 0):
                status = f"rc={result.get('returncode')}"
            print(f"  {name}: {status}")


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Safely inspect Unsloth Studio launch prerequisites without starting Studio."
    )
    parser.add_argument("--host", "-H", default="127.0.0.1", help="Intended Studio host bind")
    parser.add_argument("--port", "-p", type=int, default=8888, help="Intended Studio port")
    parser.add_argument("--secure", action="store_true", help="Check secure tunnel launch implications")
    parser.add_argument("--no-cloudflare", action="store_true", help="Check Cloudflare-disabled implications")
    parser.add_argument("--api-only", action="store_true", help="Check API-only launch implications")
    parser.add_argument("--parallel", type=int, default=1, help="Intended llama-server parallel slots")
    parser.add_argument("--enable-tools", action="store_true", help="Check forced enabled tool policy")
    parser.add_argument("--disable-tools", action="store_true", help="Check forced disabled tool policy")
    parser.add_argument("--no-port-check", dest="check_port", action="store_false", help="Skip local socket checks")
    parser.add_argument("--no-cli-help", dest="check_cli_help", action="store_false", help="Skip CLI --help probes")
    parser.add_argument("--help-timeout", type=float, default=8.0, help="Seconds per CLI help probe")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.set_defaults(check_port=True, check_cli_help=True)
    return parser.parse_known_args(argv)


def main(argv: list[str]) -> int:
    args, extras = parse_args(argv)
    report = build_report(args, extras)
    if args.json:
        print(json.dumps(report, indent=2, default=_json_default))
    else:
        print_text(report)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
