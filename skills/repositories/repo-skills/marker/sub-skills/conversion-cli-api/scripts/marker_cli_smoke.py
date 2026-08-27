#!/usr/bin/env python3
"""Help-only smoke checks for installed Marker conversion CLIs.

This script does not run document conversion and does not initialize Marker models.
It only locates console scripts and executes each with --help.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_COMMANDS = ("marker_single", "marker", "marker_chunk_convert")


@dataclass
class CheckResult:
    command: str
    found: bool
    returncode: int | None
    first_line: str


def find_executable(command: str) -> str | None:
    executable = shutil.which(command)
    if executable:
        return executable
    sibling = Path(sys.executable).resolve().parent / command
    if sibling.exists() and sibling.is_file():
        return str(sibling)
    return None


def run_help(command: str, timeout: float) -> CheckResult:
    executable = find_executable(command)
    if executable is None:
        return CheckResult(command=command, found=False, returncode=None, first_line="not found on PATH or next to the active Python")

    completed = subprocess.run(
        [executable, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    first_line = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), "no output")
    return CheckResult(
        command=command,
        found=True,
        returncode=completed.returncode,
        first_line=first_line,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run help-only smoke checks for installed Marker conversion console scripts."
    )
    parser.add_argument(
        "commands",
        nargs="*",
        default=list(DEFAULT_COMMANDS),
        help="Console scripts to check. Defaults to marker_single, marker, and marker_chunk_convert.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to allow for each --help invocation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    failures = 0

    for command in args.commands:
        try:
            result = run_help(command, args.timeout)
        except subprocess.TimeoutExpired:
            failures += 1
            print(f"FAIL {command}: --help timed out after {args.timeout:g}s")
            continue
        except OSError as exc:
            failures += 1
            print(f"FAIL {command}: {exc}")
            continue

        if not result.found:
            failures += 1
            print(f"FAIL {result.command}: {result.first_line}")
        elif result.returncode != 0:
            failures += 1
            print(f"FAIL {result.command}: exit {result.returncode}; {result.first_line}")
        else:
            print(f"OK   {result.command}: {result.first_line}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
