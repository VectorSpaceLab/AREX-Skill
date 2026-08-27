#!/usr/bin/env python3
"""Safe Dagster CLI smoke checks for local development environments.

This script checks imports and selected `--help` commands only. It does not start
services, load user code, execute jobs, materialize assets, or mutate an instance.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from typing import NamedTuple, Sequence


DEFAULT_COMMANDS: tuple[str, ...] = (
    "dagster",
    "project",
    "definitions",
    "asset",
    "job",
    "schedule",
    "sensor",
    "instance",
    "debug",
)

COMMAND_ARGS: dict[str, tuple[str, ...]] = {
    "dagster": ("--help",),
    "project": ("project", "--help"),
    "dev": ("dev", "--help"),
    "definitions": ("definitions", "validate", "--help"),
    "asset": ("asset", "materialize", "--help"),
    "job": ("job", "execute", "--help"),
    "job-launch": ("job", "launch", "--help"),
    "schedule": ("schedule", "--help"),
    "sensor": ("sensor", "--help"),
    "instance": ("instance", "--help"),
    "debug": ("debug", "--help"),
}


class CheckResult(NamedTuple):
    name: str
    ok: bool
    detail: str


def import_check(module_name: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return CheckResult(f"import {module_name}", False, f"{type(exc).__name__}: {exc}")

    version = getattr(module, "__version__", None)
    detail = f"version {version}" if version else "imported"
    return CheckResult(f"import {module_name}", True, detail)


def run_help(command: Sequence[str], timeout: float) -> CheckResult:
    display = " ".join(command)
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return CheckResult(display, False, "executable not found")
    except subprocess.TimeoutExpired:
        return CheckResult(display, False, f"timed out after {timeout:g}s")

    if completed.returncode == 0:
        first_line = (completed.stdout or completed.stderr).strip().splitlines()
        detail = first_line[0] if first_line else "help returned no text"
        return CheckResult(display, True, detail)

    message = (completed.stderr or completed.stdout).strip().splitlines()
    detail = message[0] if message else f"exit code {completed.returncode}"
    return CheckResult(display, False, detail)


def parse_commands(raw: str) -> list[str]:
    commands = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = [item for item in commands if item not in COMMAND_ARGS]
    if unknown:
        known = ", ".join(sorted(COMMAND_ARGS))
        raise SystemExit(f"Unknown command key(s): {', '.join(unknown)}. Known keys: {known}")
    return commands


def print_result(result: CheckResult, verbose: bool) -> None:
    status = "OK" if result.ok else "FAIL"
    print(f"[{status}] {result.name}: {result.detail}")
    if verbose and not result.ok:
        print(f"       hint: run the equivalent command manually with the active Python environment")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Dagster import/version and selected safe CLI --help commands."
    )
    parser.add_argument(
        "--commands",
        default=",".join(DEFAULT_COMMANDS),
        help=(
            "Comma-separated command keys to check. "
            f"Known keys: {', '.join(sorted(COMMAND_ARGS))}."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for each --help command.",
    )
    parser.add_argument(
        "--skip-console-script",
        action="store_true",
        help="Skip checking the dagster console script on PATH.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra hints for failures.",
    )
    args = parser.parse_args(argv)

    command_keys = parse_commands(args.commands)
    results: list[CheckResult] = []

    results.append(import_check("dagster"))

    if "dev" in command_keys:
        results.append(import_check("dagster_webserver"))

    module_prefix = [sys.executable, "-m", "dagster"]
    for key in command_keys:
        results.append(run_help([*module_prefix, *COMMAND_ARGS[key]], args.timeout))

    if not args.skip_console_script:
        dagster_executable = shutil.which("dagster")
        if dagster_executable:
            results.append(run_help([dagster_executable, "--help"], args.timeout))
        else:
            results.append(
                CheckResult(
                    "dagster console script",
                    False,
                    "not found on PATH; python -m dagster may still work",
                )
            )

    for result in results:
        print_result(result, args.verbose)

    if all(result.ok for result in results):
        return 0

    print("One or more checks failed. Fix the active environment before running local Dagster CLI workflows.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
