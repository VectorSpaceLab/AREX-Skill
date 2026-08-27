#!/usr/bin/env python3
"""Safe OpenCompass CLI smoke checks for the evaluation-workflows skill.

This script never runs model inference. It can verify that `opencompass --help`
works and can render a shell-quoted command for review.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from shlex import quote

REQUIRED_HELP_FLAGS = (
    "--models",
    "--datasets",
    "--debug",
    "--dry-run",
    "--accelerator",
    "--mode",
    "--reuse",
    "--work-dir",
    "--config-dir",
    "--slurm",
    "--dlc",
    "--hf-num-gpus",
)


def run_help_check(executable: str) -> None:
    if shutil.which(executable) is None:
        raise SystemExit(f"Could not find `{executable}` on PATH.")

    completed = subprocess.run(
        [executable, "--help"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"`{executable} --help` failed with exit code {completed.returncode}:\n"
            f"{completed.stdout}"
        )

    missing = [flag for flag in REQUIRED_HELP_FLAGS if flag not in completed.stdout]
    if missing:
        raise SystemExit(
            "`opencompass --help` did not include expected flags: "
            + ", ".join(missing)
        )

    print(f"OK: `{executable} --help` exposes expected evaluation workflow flags.")


def render_command(executable: str, opencompass_args: list[str]) -> None:
    command = [executable, *opencompass_args]
    print(" ".join(quote(part) for part in command))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OpenCompass CLI help and render safe command examples."
    )
    parser.add_argument(
        "--executable",
        default="opencompass",
        help="OpenCompass executable name or path to check/render.",
    )
    parser.add_argument(
        "--check-help",
        action="store_true",
        help="Run `opencompass --help` and assert expected workflow flags appear.",
    )
    parser.add_argument(
        "--show-command",
        nargs=argparse.REMAINDER,
        help=(
            "Render a shell-quoted OpenCompass command from the remaining arguments "
            "without executing it. Example: --show-command config.py --mode eval "
            "--reuse latest -w outputs/run"
        ),
    )
    args = parser.parse_args(argv)
    if not args.check_help and args.show_command is None:
        parser.error("choose --check-help and/or --show-command ...")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.check_help:
        run_help_check(args.executable)
    if args.show_command is not None:
        render_command(args.executable, args.show_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
