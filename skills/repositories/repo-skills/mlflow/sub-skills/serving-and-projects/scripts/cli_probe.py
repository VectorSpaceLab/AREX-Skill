#!/usr/bin/env python3
"""Safely probe installed MLflow CLI help/version surfaces.

This script only runs allowlisted `mlflow ... --help` and version commands. It
never starts servers, launches project runs, builds Docker images, mutates
databases, or contacts deployment targets except for local CLI help text.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass

DEFAULT_COMMANDS = [
    "mlflow",
    "mlflow server",
    "mlflow run",
    "mlflow models",
    "mlflow models serve",
    "mlflow models predict",
    "mlflow deployments",
    "mlflow deployments help",
    "mlflow db",
    "mlflow artifacts",
    "mlflow experiments",
    "mlflow runs",
    "mlflow traces",
    "mlflow datasets",
    "mlflow scorers",
    "mlflow mcp",
    "mlflow agent",
    "mlflow assistant",
    "mlflow doctor",
]

ALLOWLIST_PREFIXES = {
    ("mlflow",),
    ("mlflow", "server"),
    ("mlflow", "ui"),
    ("mlflow", "run"),
    ("mlflow", "models"),
    ("mlflow", "models", "serve"),
    ("mlflow", "models", "predict"),
    ("mlflow", "models", "prepare-env"),
    ("mlflow", "models", "generate-dockerfile"),
    ("mlflow", "models", "build-docker"),
    ("mlflow", "models", "update-pip-requirements"),
    ("mlflow", "deployments"),
    ("mlflow", "deployments", "help"),
    ("mlflow", "db"),
    ("mlflow", "artifacts"),
    ("mlflow", "experiments"),
    ("mlflow", "runs"),
    ("mlflow", "traces"),
    ("mlflow", "datasets"),
    ("mlflow", "scorers"),
    ("mlflow", "mcp"),
    ("mlflow", "agent"),
    ("mlflow", "agent", "setup"),
    ("mlflow", "assistant"),
    ("mlflow", "doctor"),
    ("mlflow", "gateway"),
    ("mlflow", "sagemaker"),
    ("mlflow", "migrate-filestore"),
}


@dataclass
class ProbeResult:
    command: str
    argv: list[str]
    returncode: int | None
    ok: bool
    stdout: str
    stderr: str
    error: str | None = None


def normalize_command(command: str) -> list[str]:
    argv = shlex.split(command)
    if not argv or argv[0] != "mlflow":
        raise ValueError("commands must start with 'mlflow'")
    if any(token.startswith("-") for token in argv[1:]):
        raise ValueError("provide command words only; probe adds --help or --version")
    if tuple(argv) not in ALLOWLIST_PREFIXES:
        allowed = "\n  ".join(" ".join(parts) for parts in sorted(ALLOWLIST_PREFIXES))
        raise ValueError(f"command is not allowlisted: {command!r}\nAllowed commands:\n  {allowed}")
    return argv


def build_probe_argv(argv: list[str], mlflow_executable: str, python_module: str | None) -> list[str]:
    suffix = ["--version"] if argv == ["mlflow"] else [*argv[1:], "--help"]
    if python_module:
        return [python_module, "-m", "mlflow", *suffix]
    return [mlflow_executable, *suffix]


def probe(command: str, timeout: float, mlflow_executable: str, python_module: str | None) -> ProbeResult:
    try:
        argv = normalize_command(command)
    except ValueError as exc:
        return ProbeResult(command, [], None, False, "", "", str(exc))

    probe_argv = build_probe_argv(argv, mlflow_executable, python_module)
    try:
        completed = subprocess.run(
            probe_argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        missing = python_module or mlflow_executable
        return ProbeResult(command, probe_argv, None, False, "", "", f"executable not found: {missing}")
    except subprocess.TimeoutExpired as exc:
        return ProbeResult(
            command,
            probe_argv,
            None,
            False,
            exc.stdout or "",
            exc.stderr or "",
            f"timed out after {timeout:g}s",
        )

    return ProbeResult(
        command=command,
        argv=probe_argv,
        returncode=completed.returncode,
        ok=completed.returncode == 0,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def render_text(results: list[ProbeResult]) -> str:
    blocks = []
    for result in results:
        status = "OK" if result.ok else "FAIL"
        argv = " ".join(shlex.quote(part) for part in result.argv) if result.argv else result.command
        block = [f"## {status}: {result.command}", f"$ {argv}"]
        if result.returncode is not None:
            block.append(f"returncode: {result.returncode}")
        if result.error:
            block.append(f"error: {result.error}")
        if result.stderr.strip():
            block.extend(["stderr:", result.stderr.rstrip()])
        if result.stdout.strip():
            block.extend(["stdout:", result.stdout.rstrip()])
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commands",
        nargs="+",
        default=DEFAULT_COMMANDS,
        help="Allowlisted mlflow command prefixes to probe. Defaults to common serving/project groups.",
    )
    parser.add_argument(
        "--mlflow-executable",
        default="mlflow",
        help="MLflow console executable to probe when --python-module is not set.",
    )
    parser.add_argument(
        "--python-module",
        metavar="PYTHON",
        help="Run probes as PYTHON -m mlflow instead of through a console script.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds per probe command.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    results = [
        probe(command, args.timeout, args.mlflow_executable, args.python_module)
        for command in args.commands
    ]
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        print(render_text(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
