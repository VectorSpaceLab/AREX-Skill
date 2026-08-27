#!/usr/bin/env python3
"""Validate Towhee CLI help without downloads, template writes, or servers."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from typing import Iterable, Sequence


HELP_CHECKS = [
    {
        "label": "towhee --help",
        "args": ["--help"],
        "expected": ["init", "server"],
    },
    {
        "label": "towhee init --help",
        "args": ["init", "--help"],
        "expected": ["uri", "--dir", "--type", "pyop", "nnop"],
    },
    {
        "label": "towhee server --help",
        "args": ["server", "--help"],
        "expected": ["source", "--host", "--http-port", "--grpc-port", "--uri", "--params"],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe Towhee CLI help checks only. The script never runs "
            "`towhee init` without --help and never starts `towhee server`."
        )
    )
    parser.add_argument(
        "--python-module",
        action="store_true",
        help="Use `python -m towhee` instead of the `towhee` console script.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-command timeout in seconds. Default: 20.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print captured help output for each successful command.",
    )
    return parser.parse_args()


def base_command(force_python_module: bool) -> list[str]:
    if force_python_module:
        return [sys.executable, "-m", "towhee"]
    if shutil.which("towhee") is None:
        print("towhee console script not found; falling back to python -m towhee", file=sys.stderr)
        return [sys.executable, "-m", "towhee"]
    return ["towhee"]


def run_help(cmd: Sequence[str], timeout: float) -> str:
    completed = subprocess.run(
        list(cmd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise AssertionError(
            f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}\n{output}"
        )
    return output


def assert_contains(output: str, expected: Iterable[str], label: str) -> None:
    missing = [token for token in expected if token not in output]
    if missing:
        raise AssertionError(
            f"{label} help output is missing expected token(s): {', '.join(missing)}\n{output}"
        )


def main() -> int:
    args = parse_args()
    base = base_command(args.python_module)
    for check in HELP_CHECKS:
        cmd = base + check["args"]
        output = run_help(cmd, args.timeout)
        assert_contains(output, check["expected"], check["label"])
        print(f"OK: {check['label']} via {' '.join(base)}")
        if args.verbose:
            print(output.rstrip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"Timed out while running: {' '.join(exc.cmd)}") from exc
    except AssertionError as exc:
        raise SystemExit(str(exc)) from exc
