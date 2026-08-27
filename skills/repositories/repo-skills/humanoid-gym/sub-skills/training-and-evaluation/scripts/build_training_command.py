#!/usr/bin/env python3
"""Build a safe Humanoid-Gym PPO training command without launching Isaac Gym."""

import argparse
import shlex
import sys
from typing import Any, List, Tuple

DEFAULT_SCRIPT = "humanoid/scripts/train.py"
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

    if args.num_envs is not None:
        parts.append(f"--num_envs={args.num_envs}")
    if args.max_iterations is not None:
        parts.append(f"--max_iterations={args.max_iterations}")
    if args.headless:
        parts.append("--headless")
    if args.sim_device:
        parts.append(f"--sim_device={args.sim_device}")
    if args.rl_device:
        parts.append(f"--rl_device={args.rl_device}")

    warnings: List[str] = []
    resume = bool(args.resume or args.load_run or args.checkpoint is not None)
    if resume and not args.resume:
        warnings.append("resume was inferred because load-run/checkpoint were supplied")
        parts.append("--resume")
    elif args.resume:
        parts.append("--resume")

    if args.load_run:
        parts.append(f"--load_run={args.load_run}")
    if args.checkpoint is not None:
        parts.append(f"--checkpoint={args.checkpoint}")

    if args.sim_device and args.rl_device and args.sim_device != args.rl_device:
        warnings.append("README guidance says sim_device and rl_device should match")

    return shlex.join(str(part) for part in parts), warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a Humanoid-Gym PPO training command without launching Isaac Gym.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--task", default=DEFAULT_TASK, help="Registered task name to train.")
    parser.add_argument("--run-name", "--run_name", dest="run_name", default="", help="Run name used in the log directory.")
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=None, help="Override the number of parallel environments.")
    parser.add_argument("--max-iterations", "--max_iterations", dest="max_iterations", type=int, default=None, help="Override the PPO iteration count.")
    parser.add_argument("--headless", action="store_true", help="Add the headless launch flag.")
    parser.add_argument("--sim-device", "--sim_device", dest="sim_device", default="", help="Isaac Gym simulation device, e.g. cpu or cuda:0.")
    parser.add_argument("--rl-device", "--rl_device", dest="rl_device", default="", help="RL device passed to the runner, e.g. cpu or cuda:0.")
    parser.add_argument("--resume", action="store_true", help="Resume from an existing run.")
    parser.add_argument("--load-run", "--load_run", dest="load_run", default="", help="Existing run directory name to resume from.")
    parser.add_argument("--checkpoint", type=int, default=None, help="Checkpoint iteration to resume from.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command, warnings = build_command(args)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
