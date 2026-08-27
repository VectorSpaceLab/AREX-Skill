#!/usr/bin/env python3
"""Print safe help output for smolagents console commands without running an agent."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence


ENTRY_POINTS = {
    "smolagent": "smolagents.cli",
    "webagent": "smolagents.vision_web_browser",
}


def _run(command: Sequence[str]) -> int:
    completed = subprocess.run(command, text=True, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Print --help for smolagents CLI entry points.")
    parser.add_argument(
        "--command",
        choices=sorted(ENTRY_POINTS),
        default="smolagent",
        help="Command to inspect without running a model-backed task.",
    )
    parser.add_argument(
        "--prefer-module",
        action="store_true",
        help="Use python -m module --help before trying the console script.",
    )
    args = parser.parse_args()

    module_command = [sys.executable, "-m", ENTRY_POINTS[args.command], "--help"]
    script_path = shutil.which(args.command)
    script_command = [script_path, "--help"] if script_path else None

    commands: list[Sequence[str]] = []
    if args.prefer_module:
        commands.append(module_command)
        if script_command:
            commands.append(script_command)
    else:
        if script_command:
            commands.append(script_command)
        commands.append(module_command)

    last_code = 127
    for command in commands:
        last_code = _run(command)
        if last_code == 0:
            return 0

    if script_command is None:
        print(
            f"Could not find console script {args.command!r}; module fallback also failed.",
            file=sys.stderr,
        )
    return last_code


if __name__ == "__main__":
    raise SystemExit(main())
