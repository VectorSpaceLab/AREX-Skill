#!/usr/bin/env python3
"""Check that the installed CellTypist CLI exposes expected options."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Sequence

EXPECTED_OPTIONS = [
    "--indata",
    "--model",
    "--transpose-input",
    "--gene-file",
    "--cell-file",
    "--mode",
    "--p-thres",
    "--majority-voting",
    "--over-clustering",
    "--use-GPU",
    "--min-prop",
    "--outdir",
    "--prefix",
    "--xlsx",
    "--plot-results",
    "--update-models",
    "--show-models",
    "--quiet",
]


def run_help(command: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [command, "--help"],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", default="celltypist", help="CellTypist CLI command name or path.")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds before the help command times out.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    command_path = shutil.which(args.command) if "/" not in args.command else args.command
    result = {
        "command": args.command,
        "command_found": bool(command_path),
        "returncode": None,
        "missing_options": list(EXPECTED_OPTIONS),
        "stderr": "",
        "ok": False,
    }
    if not command_path:
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"CellTypist command not found: {args.command}", file=sys.stderr)
        return 2

    try:
        completed = run_help(command_path, args.timeout)
    except subprocess.TimeoutExpired:
        result["stderr"] = f"Timed out after {args.timeout} seconds"
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result["stderr"], file=sys.stderr)
        return 3

    help_text = completed.stdout + completed.stderr
    missing = [option for option in EXPECTED_OPTIONS if option not in help_text]
    result.update(
        {
            "returncode": completed.returncode,
            "missing_options": missing,
            "stderr": completed.stderr.strip(),
            "ok": completed.returncode == 0 and not missing,
        }
    )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Command: {command_path}")
        print(f"Return code: {completed.returncode}")
        if missing:
            print("Missing expected options: " + ", ".join(missing), file=sys.stderr)
        else:
            print("All expected CellTypist CLI options are present.")
        if completed.stderr.strip():
            print("stderr:")
            print(completed.stderr.strip())

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
