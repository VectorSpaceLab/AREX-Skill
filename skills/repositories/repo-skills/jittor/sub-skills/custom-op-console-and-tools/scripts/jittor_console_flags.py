#!/usr/bin/env python3
"""Safe wrapper for `python -m jittor_utils.config`.

The wrapper prints command templates, generated C++ console source, or build
flags. It never compiles, runs the generated binary, starts services, or depends
on a source checkout.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from typing import List

CONFIG_FLAGS = ["--include-flags", "--libs-flags", "--cxx-flags"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print Jittor C++ console flags, example source, or a compile command template."
    )
    parser.add_argument(
        "--mode",
        choices=["command", "flags", "example", "help"],
        default="command",
        help="What to print: compile command template, combined flags, C++ example, or config help.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run jittor_utils.config (default: this Python).",
    )
    parser.add_argument(
        "--compiler",
        default="g++",
        help="Compiler name/path to show in command mode (default: g++).",
    )
    parser.add_argument(
        "--source",
        default="example.cc",
        help="C++ source file name to show in command mode (default: example.cc).",
    )
    parser.add_argument(
        "--output",
        default="example",
        help="Output binary name to show in command mode (default: example).",
    )
    parser.add_argument(
        "--verbose-jittor-logs",
        action="store_true",
        help="Allow logs from jittor_utils.config. Default suppresses logs when supported.",
    )
    return parser.parse_args()


def quote(value: str) -> str:
    return shlex.quote(value)


def config_command(python: str, extra_args: List[str]) -> List[str]:
    return [python, "-m", "jittor_utils.config", *extra_args]


def run_config(python: str, extra_args: List[str], verbose_logs: bool) -> int:
    env = os.environ.copy()
    if not verbose_logs:
        env.setdefault("log_silent", "1")
    proc = subprocess.run(
        config_command(python, extra_args),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        print(
            "jittor_utils.config failed. If the message mentions the Python dynamic library, "
            "use a Python environment that exposes a shared libpython and regenerate flags there.",
            file=sys.stderr,
        )
    return proc.returncode


def print_command_template(args: argparse.Namespace) -> None:
    py = quote(args.python)
    cfg = f"$({py} -m jittor_utils.config {' '.join(CONFIG_FLAGS)})"
    cmd = " ".join(
        [
            quote(args.compiler),
            quote(args.source),
            cfg,
            "-o",
            quote(args.output),
        ]
    )
    print(cmd)
    print("# Generate example source with:")
    print(f"{py} -m jittor_utils.config --cxx-example > {quote(args.source)}")
    print("# Run the binary from the same Python environment that generated the flags.")
    print("# If launch fails with libpython not found, expose that environment's Python library directory to the dynamic linker.")


def main() -> int:
    args = parse_args()
    if args.mode == "command":
        print_command_template(args)
        return 0
    if args.mode == "flags":
        return run_config(args.python, CONFIG_FLAGS, args.verbose_jittor_logs)
    if args.mode == "example":
        return run_config(args.python, ["--cxx-example"], args.verbose_jittor_logs)
    if args.mode == "help":
        return run_config(args.python, ["--help"], args.verbose_jittor_logs)
    raise AssertionError(args.mode)


if __name__ == "__main__":
    sys.exit(main())
