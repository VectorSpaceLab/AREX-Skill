#!/usr/bin/env python3
"""Build a safe Humanoid-Gym play/evaluation command without launching Isaac Gym."""

import argparse
import shlex
import sys
from typing import Any, List, Tuple

DEFAULT_SCRIPT = "humanoid/scripts/play.py"
DEFAULT_TASK = "humanoid_ppo"


def _add_flag(parts: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str) and value == "":
        return
    parts.append(f"{flag}={value}")


def build_command(args: argparse.Namespace) -> Tuple[str, List[str]]:
    parts: List[str] = ["python", DEFAULT_SCRIPT]
    _add_flag(parts, "--task", args.task)
    _add_flag(parts, "--run_name", args.run_name)

    if args.load_run:
        parts.append(f"--load_run={args.load_run}")
    if args.checkpoint is not None:
        parts.append(f"--checkpoint={args.checkpoint}")
    if args.headless:
        parts.append("--headless")

    warnings: List[str] = [
        "source play.py hard-codes EXPORT_POLICY=True, RENDER=True, and FIX_COMMAND=True unless the source file is edited",
        "the requested export/no-render/fix-command intent is advisory only for this builder",
    ]
    if args.no_render:
        warnings.append("--no-render was requested, but play.py still renders until edited")
    if args.notes:
        warnings.append(f"notes: {args.notes}")
    if args.export:
        warnings.append("export intent recorded; play.py already exports policy_1.pt by default")
    if args.fix_command:
        warnings.append("fix-command intent recorded; play.py already fixes the command vector by default")

    return shlex.join(str(part) for part in parts), warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a Humanoid-Gym play command without launching Isaac Gym.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--task", default=DEFAULT_TASK, help="Registered task name to evaluate.")
    parser.add_argument("--run-name", "--run_name", dest="run_name", default="", help="Run name used in the exported video filename.")
    parser.add_argument("--load-run", "--load_run", dest="load_run", default="", help="Existing run directory name to load from.")
    parser.add_argument("--checkpoint", type=int, default=None, help="Checkpoint iteration to load.")
    parser.add_argument("--headless", action="store_true", help="Add the headless launch flag.")
    parser.add_argument("--export", action="store_true", help="Record that exported-policy output is desired.")
    parser.add_argument("--no-render", "--no_render", dest="no_render", action="store_true", help="Record that rendering should be disabled if the source is edited.")
    parser.add_argument("--fix-command", "--fix_command", dest="fix_command", action="store_true", help="Record that fixed command inputs are desired.")
    parser.add_argument("--notes", default="", help="Free-form notes to print with the warnings.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command, warnings = build_command(args)
    print(
        "WARNING: requested intent -> "
        f"export={args.export}, no_render={args.no_render}, fix_command={args.fix_command}",
        file=sys.stderr,
    )
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
