#!/usr/bin/env python3
"""Run bounded, read-only help probes against the installed SMARTS ``scl`` CLI.

The checker never imports the repository checkout, installs packages, starts a
server, or executes a scenario. It is safe to call from any current working
directory. Use ``--scl PATH`` when the console script is not on ``PATH``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_COMMANDS: tuple[tuple[str, ...], ...] = (
    (),
    ("scenario",),
    ("run",),
    ("scenario", "build"),
    ("scenario", "build-all"),
    ("scenario", "clean"),
    ("scenario", "replay"),
    ("envision", "start"),
    ("diagnostic", "run"),
    ("benchmark", "list"),
    ("benchmark", "run"),
    ("zoo", "build"),
    ("zoo", "install"),
    ("zoo", "manager"),
    ("waymo", "overview"),
    ("waymo", "preview"),
    ("waymo", "export"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scl",
        default=os.environ.get("SCL", "scl"),
        help="installed scl executable or path (default: SCL environment or scl)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="per-help timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--top-level-only",
        action="store_true",
        help="probe only scl, scl scenario, and scl run",
    )
    return parser.parse_args(argv)


def resolve_executable(value: str) -> str | None:
    candidate = Path(value).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        return str(candidate) if candidate.is_file() else None
    found = shutil.which(value)
    if found:
        return found
    sibling = Path(sys.executable).with_name(value + (".exe" if sys.platform == "win32" else ""))
    return str(sibling) if sibling.is_file() else None


def run_help(executable: str, command: tuple[str, ...], timeout: float) -> tuple[bool, str]:
    label = "scl" if not command else "scl " + " ".join(command)
    try:
        result = subprocess.run(
            [executable, *command, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"{label}: {error}"
    output = (result.stdout + result.stderr).strip()
    if result.returncode:
        return False, f"{label}: exit={result.returncode}\n{output}"
    if not output or "Usage:" not in output:
        return False, f"{label}: help returned no Click usage text"
    return True, f"{label}: ok"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    executable = resolve_executable(args.scl)
    if executable is None:
        print(f"FAIL: installed scl executable not found: {args.scl}", file=sys.stderr)
        return 2

    commands = DEFAULT_COMMANDS[:3] if args.top_level_only else DEFAULT_COMMANDS
    failures = 0
    print(f"scl executable: {executable}")
    for command in commands:
        ok, message = run_help(executable, command, args.timeout)
        print(("PASS: " if ok else "FAIL: ") + message)
        failures += not ok
    if failures:
        print(f"{failures} help probe(s) failed", file=sys.stderr)
        return 1
    print(f"PASS: {len(commands)} bounded help probes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
