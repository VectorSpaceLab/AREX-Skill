#!/usr/bin/env python3
"""Check Ray imports, optional workflow modules, and CLI availability.

This helper is intentionally read-only: it does not start Ray, submit jobs,
connect to a cluster, or deploy Serve applications.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Iterable


WORKFLOWS = {
    "core": ["ray"],
    "data": ["ray", "ray.data"],
    "train": ["ray", "ray.train"],
    "tune": ["ray", "ray.tune"],
    "serve": ["ray", "ray.serve"],
    "rllib": ["ray", "ray.rllib"],
}

CLI_COMMANDS = {
    "ray": ["ray", "--help"],
    "serve": ["serve", "--help"],
    "tune": ["tune", "--help"],
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_distribution() -> CheckResult:
    try:
        version = importlib.metadata.version("ray")
    except importlib.metadata.PackageNotFoundError:
        return CheckResult("distribution:ray", False, "Python distribution 'ray' is not installed")
    return CheckResult("distribution:ray", True, version)


def check_import(module_name: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report any import failure.
        return CheckResult(f"import:{module_name}", False, f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", "imported")
    return CheckResult(f"import:{module_name}", True, str(version))


def check_cli(command_name: str) -> CheckResult:
    command = CLI_COMMANDS[command_name]
    executable = shutil.which(command[0])
    if not executable:
        return CheckResult(f"cli:{command_name}", False, f"'{command[0]}' executable not found on PATH")
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(f"cli:{command_name}", False, f"{type(exc).__name__}: {exc}")
    output = (completed.stdout or completed.stderr).strip().splitlines()
    detail = output[0] if output else f"exit code {completed.returncode}"
    return CheckResult(f"cli:{command_name}", completed.returncode == 0, detail)


def unique_modules(required: Iterable[str]) -> list[str]:
    modules: list[str] = []
    for workflow in required:
        for module_name in WORKFLOWS[workflow]:
            if module_name not in modules:
                modules.append(module_name)
    return modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Ray package imports and optional CLI help safely.")
    parser.add_argument(
        "--require",
        action="append",
        choices=sorted(WORKFLOWS),
        default=[],
        help="Workflow import surface to require. May be repeated. Defaults to core.",
    )
    parser.add_argument(
        "--check-cli",
        action="append",
        choices=sorted(CLI_COMMANDS),
        default=[],
        help="CLI help command to check without connecting to a cluster. May be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required = args.require or ["core"]
    results = [check_distribution()]
    results.extend(check_import(module_name) for module_name in unique_modules(required))
    results.extend(check_cli(command_name) for command_name in args.check_cli)

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
