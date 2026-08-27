#!/usr/bin/env python3
"""Build a safe MuZero command without running training.

This helper mirrors the inspected AI-Optimizer MuZero CLI surface, validates
lightweight argument combinations, and prints one shell-quoted command beginning
with ``python main.py``. It intentionally does not import Ray, Torch, Gym, or
any source package modules, and it never creates directories or starts training.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import List, Sequence


CASES = ("classic_control", "atari", "box2d")
OPERATIONS = ("train", "test")
MAX_NUMPY_SEED = 2**32 - 1


def non_empty_string(value: str) -> str:
    """Return a stripped string or raise an argparse error for empty values."""
    stripped = value.strip()
    if not stripped:
        raise argparse.ArgumentTypeError("value must not be empty")
    return stripped


def seed_value(value: str) -> int:
    """Parse a NumPy-compatible seed used by the source script."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seed must be an integer") from exc
    if parsed < 0 or parsed > MAX_NUMPY_SEED:
        raise argparse.ArgumentTypeError(f"seed must be in [0, {MAX_NUMPY_SEED}]")
    return parsed


def positive_int(value: str) -> int:
    """Parse a positive integer for evaluation episode count."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def bounded_probability(value: str) -> float:
    """Parse a float in [0, 1] for revisit-policy search rate."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be a float") from exc
    if parsed < 0.0 or parsed > 1.0:
        raise argparse.ArgumentTypeError("revisit policy search rate must be in [0, 1]")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a shell-quoted AI-Optimizer MuZero command recipe. The command is not executed."
    )
    parser.add_argument("--env", required=True, type=non_empty_string, help="Gym environment name, for example CartPole-v1")
    parser.add_argument("--case", required=True, choices=CASES, help="MuZero domain selector")
    parser.add_argument("--opr", required=True, choices=OPERATIONS, help="operation to construct: train or test")
    parser.add_argument("--result-dir", type=non_empty_string, help="optional result root emitted as --result_dir")
    parser.add_argument("--no-cuda", action="store_true", help="emit --no_cuda to force CPU selection")
    parser.add_argument("--debug", action="store_true", help="emit --debug for additional source logging")
    parser.add_argument("--render", action="store_true", help="emit --render, generally for test-time visualization")
    parser.add_argument("--force", action="store_true", help="emit --force to allow source result overwrite behavior")
    parser.add_argument("--seed", type=seed_value, default=0, help="NumPy-compatible seed (default: 0)")
    parser.add_argument("--test-episodes", type=positive_int, default=10, help="test episode count emitted for --opr test (default: 10)")
    parser.add_argument("--value-loss-coeff", type=float, help="optional value-loss coefficient override")
    parser.add_argument(
        "--revisit-policy-search-rate",
        type=bounded_probability,
        help="optional target policy re-estimation rate in [0, 1]",
    )
    parser.add_argument("--use-priority", action="store_true", help="emit --use_priority for prioritized replay sampling")
    parser.add_argument(
        "--use-max-priority",
        action="store_true",
        help="emit --use_max_priority; requires --use-priority because source only honors it with priority enabled",
    )
    parser.add_argument("--use-target-model", action="store_true", help="emit --use_target_model for bootstrap value estimation")
    return parser


def build_command(args: argparse.Namespace) -> List[str]:
    if args.use_max_priority and not args.use_priority:
        raise ValueError("--use-max-priority requires --use-priority")

    command: List[str] = ["python", "main.py", "--env", args.env, "--case", args.case, "--opr", args.opr]
    command.extend(["--seed", str(args.seed)])

    if args.result_dir:
        command.extend(["--result_dir", args.result_dir])
    if args.no_cuda:
        command.append("--no_cuda")
    if args.debug:
        command.append("--debug")
    if args.render:
        command.append("--render")
    if args.force:
        command.append("--force")
    if args.opr == "test":
        command.extend(["--test_episodes", str(args.test_episodes)])
    if args.value_loss_coeff is not None:
        command.extend(["--value_loss_coeff", str(args.value_loss_coeff)])
    if args.revisit_policy_search_rate is not None:
        command.extend(["--revisit_policy_search_rate", str(args.revisit_policy_search_rate)])
    if args.use_priority:
        command.append("--use_priority")
    if args.use_max_priority:
        command.append("--use_max_priority")
    if args.use_target_model:
        command.append("--use_target_model")

    return command


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        command = build_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
