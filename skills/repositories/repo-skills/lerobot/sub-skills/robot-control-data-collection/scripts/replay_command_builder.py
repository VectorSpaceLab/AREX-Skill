#!/usr/bin/env python3
"""Build a LeRobot replay command without opening or controlling hardware."""

from __future__ import annotations

import argparse
import shlex
from collections.abc import Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a dry-run lerobot-replay command and actuation checklist."
    )
    parser.add_argument("--robot-type", required=True, help="Registered value for --robot.type")
    parser.add_argument("--robot-port", help="Serial path, CAN channel, or other port")
    parser.add_argument("--robot-id", default="robot", help="Calibration identity for --robot.id")
    parser.add_argument("--repo-id", required=True, help="Dataset identifier")
    parser.add_argument("--episode", type=int, required=True, help="Dataset episode index")
    parser.add_argument("--root", help="Optional local dataset root")
    parser.add_argument(
        "--robot-arg",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Additional nested robot field, repeated; emits --robot.FIELD=VALUE",
    )
    return parser


def _nested_args(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if "=" not in value or value.startswith("="):
            raise ValueError(f"robot extra must be FIELD=VALUE, got {value!r}")
        field, raw = value.split("=", 1)
        if not field or field.startswith("-"):
            raise ValueError(f"invalid robot field in {value!r}")
        result.append(f"--robot.{field}={raw}")
    return result


def build_command(args: argparse.Namespace) -> list[str]:
    if args.episode < 0:
        raise ValueError("--episode must be zero or greater")
    command = [
        "lerobot-replay",
        f"--robot.type={args.robot_type}",
        f"--robot.id={args.robot_id}",
        f"--dataset.repo_id={args.repo_id}",
        f"--dataset.episode={args.episode}",
    ]
    if args.robot_port:
        command.append(f"--robot.port={args.robot_port}")
    if args.root:
        command.append(f"--dataset.root={args.root}")
    command.extend(_nested_args(args.robot_arg))
    return command


def main() -> int:
    args = _parser().parse_args()
    try:
        command = build_command(args)
    except ValueError as exc:
        _parser().error(str(exc))
    print("DRY RUN ONLY: this script does not invoke LeRobot and does not open devices.")
    print("ACTUATES ROBOT if the printed command is later executed.")
    print("Before running it, validate the episode, action keys/units, dataset FPS, calibration, start pose,")
    print("workspace, emergency-stop access, and an immediate power-isolation plan.")
    print("The replay implementation paces from the dataset's stored FPS; do not treat this as a speed test.")
    print("\nCommand to run only after a separate live-action confirmation:\n")
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
