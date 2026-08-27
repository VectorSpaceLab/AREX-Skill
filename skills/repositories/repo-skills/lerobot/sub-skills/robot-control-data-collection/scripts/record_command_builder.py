#!/usr/bin/env python3
"""Build a LeRobot recording command without opening or controlling hardware."""

from __future__ import annotations

import argparse
import shlex
from collections.abc import Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a dry-run lerobot-record command and live-safety checklist."
    )
    parser.add_argument("--robot-type", required=True, help="Registered value for --robot.type")
    parser.add_argument("--robot-port", help="Serial path, CAN channel, or other port; omit for network-only configs")
    parser.add_argument("--robot-id", default="robot", help="Calibration identity for --robot.id")
    parser.add_argument("--teleop-type", required=True, help="Registered value for --teleop.type")
    parser.add_argument("--teleop-port", help="Teleoperator port; omit for phone/gamepad/network modes")
    parser.add_argument("--teleop-id", default="teleop", help="Calibration identity for --teleop.id")
    parser.add_argument("--repo-id", required=True, help="Local/HF-style dataset identifier")
    parser.add_argument("--task", required=True, help="One-sentence task label")
    parser.add_argument("--fps", type=int, default=30, help="Control and dataset FPS (default: 30)")
    parser.add_argument("--episodes", type=int, default=1, help="Number of episodes (default: 1)")
    parser.add_argument("--episode-time-s", type=float, default=10.0, help="Episode duration (default: 10)")
    parser.add_argument("--reset-time-s", type=float, default=5.0, help="Reset duration (default: 5)")
    parser.add_argument(
        "--cameras",
        help="Raw draccus value for --robot.cameras, for example '{front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}',",
    )
    parser.add_argument(
        "--robot-arg",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Additional nested robot field, repeated; emits --robot.FIELD=VALUE",
    )
    parser.add_argument(
        "--teleop-arg",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Additional nested teleoperator field, repeated; emits --teleop.FIELD=VALUE",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Plan --resume=true; inspect the existing dataset before confirmation",
    )
    return parser


def _nested_args(prefix: str, values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if "=" not in value or value.startswith("="):
            raise ValueError(f"{prefix} extra must be FIELD=VALUE, got {value!r}")
        field, raw = value.split("=", 1)
        if not field or field.startswith("-"):
            raise ValueError(f"invalid {prefix} field in {value!r}")
        result.append(f"--{prefix}.{field}={raw}")
    return result


def build_command(args: argparse.Namespace) -> list[str]:
    if args.fps <= 0:
        raise ValueError("--fps must be positive")
    if args.episodes <= 0:
        raise ValueError("--episodes must be positive")
    if args.episode_time_s <= 0 or args.reset_time_s < 0:
        raise ValueError("episode time must be positive and reset time cannot be negative")

    command = [
        "lerobot-record",
        f"--robot.type={args.robot_type}",
        f"--robot.id={args.robot_id}",
        f"--teleop.type={args.teleop_type}",
        f"--teleop.id={args.teleop_id}",
        f"--dataset.repo_id={args.repo_id}",
        f"--dataset.single_task={args.task}",
        f"--dataset.fps={args.fps}",
        f"--dataset.num_episodes={args.episodes}",
        f"--dataset.episode_time_s={args.episode_time_s:g}",
        f"--dataset.reset_time_s={args.reset_time_s:g}",
        "--dataset.push_to_hub=false",
        "--display_data=false",
    ]
    if args.robot_port:
        command.append(f"--robot.port={args.robot_port}")
    if args.teleop_port:
        command.append(f"--teleop.port={args.teleop_port}")
    if args.cameras:
        command.append(f"--robot.cameras={args.cameras}")
    command.extend(_nested_args("robot", args.robot_arg))
    command.extend(_nested_args("teleop", args.teleop_arg))
    if args.resume:
        command.append("--resume=true")
    return command


def main() -> int:
    args = _parser().parse_args()
    try:
        command = build_command(args)
    except ValueError as exc:
        _parser().error(str(exc))
    print("DRY RUN ONLY: this script does not invoke LeRobot and does not open devices.")
    print("Review the selected type, ports, calibration ids, camera profiles, workspace, and emergency stop.")
    print("Keep --dataset.push_to_hub=false until the local dataset is inspected.")
    print("\nCommand to run only after a separate live-action confirmation:\n")
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
