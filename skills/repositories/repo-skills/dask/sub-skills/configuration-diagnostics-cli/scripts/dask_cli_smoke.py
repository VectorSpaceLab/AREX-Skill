#!/usr/bin/env python3
"""Run safe smoke checks for the installed Dask CLI.

The default checks avoid persistent config writes and avoid `dask docs`, which may
open a browser. Use --help to inspect this wrapper's options.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence


def _run(command: Sequence[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    print(f"exit={completed.returncode}\n")
    return completed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dask-executable",
        default=os.environ.get("DASK_CLI", "dask"),
        help="Dask CLI executable to run; defaults to DASK_CLI or 'dask'.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for each CLI command.",
    )
    parser.add_argument(
        "--skip-info-versions",
        action="store_true",
        help="Skip 'dask info versions' if importing optional dependencies is too slow/noisy.",
    )
    args = parser.parse_args(argv)

    executable = shutil.which(args.dask_executable)
    if executable is None:
        print(f"Could not find Dask CLI executable: {args.dask_executable}", file=sys.stderr)
        return 127

    checks: list[list[str]] = [
        [executable, "--help"],
        [executable, "config", "get", "temporary-directory"],
        [executable, "config", "list"],
    ]
    if not args.skip_info_versions:
        checks.append([executable, "info", "versions"])

    failures = 0
    for command in checks:
        try:
            completed = _run(command, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print(f"Timed out: {' '.join(command)}", file=sys.stderr)
            failures += 1
            continue
        if completed.returncode != 0:
            failures += 1

    if failures:
        print(f"Dask CLI smoke checks failed: {failures}/{len(checks)}", file=sys.stderr)
        return 1

    print("Dask CLI smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
