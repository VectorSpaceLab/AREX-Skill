#!/usr/bin/env python3
"""Safe Dagster skill environment probe.

This helper checks importability and command availability without starting
Dagster services, executing user code, or mutating instance state.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from importlib import metadata


MODULES = [
    ("dagster", "dagster"),
    ("dagster-webserver", "dagster_webserver"),
    ("dagster-graphql", "dagster_graphql"),
    ("dagster-pipes", "dagster_pipes"),
]

COMMANDS = ["dagster", "dagster-webserver", "dagster-graphql"]


def check_import(distribution: str, module_name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all import failures.
        return False, f"{module_name}: import failed: {type(exc).__name__}: {exc}"

    try:
        version = metadata.version(distribution)
    except Exception:
        version = getattr(module, "__version__", "unknown")
    return True, f"{module_name}: ok ({distribution} {version})"


def check_command(command: str, timeout: int) -> tuple[bool, str]:
    executable = shutil.which(command)
    if executable is None:
        return False, f"{command}: missing from PATH"
    try:
        result = subprocess.run(
            [executable, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all command failures.
        return False, f"{command}: --help failed: {type(exc).__name__}: {exc}"
    if result.returncode != 0:
        stderr = result.stderr.strip().splitlines()[0] if result.stderr.strip() else "no stderr"
        return False, f"{command}: --help exited {result.returncode}: {stderr}"
    first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "help returned no output"
    return True, f"{command}: ok ({first_line})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Dagster package imports and safe CLI help availability.")
    parser.add_argument("--skip-cli", action="store_true", help="Only check Python imports.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for each --help command.")
    args = parser.parse_args()

    failures = 0
    print(f"Python: {sys.executable}")
    for distribution, module_name in MODULES:
        ok, message = check_import(distribution, module_name)
        print(message)
        failures += 0 if ok else 1

    if not args.skip_cli:
        for command in COMMANDS:
            ok, message = check_command(command, args.timeout)
            print(message)
            failures += 0 if ok else 1

    if failures:
        print("Result: one or more Dagster packages or commands are unavailable.")
        return 1
    print("Result: Dagster core package checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
