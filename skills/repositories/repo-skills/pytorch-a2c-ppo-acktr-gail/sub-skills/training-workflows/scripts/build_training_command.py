#!/usr/bin/env python3
"""Build safe pytorch-a2c-ppo-acktr-gail training/playback commands.

This helper prints commands only; it never imports Gym, creates environments,
or starts training. Use it to generate current parser flags from common presets.

Examples:
  python build_training_command.py --preset atari-ppo --env-name PongNoFrameskip-v4
  python build_training_command.py --preset mujoco-ppo --env-name Reacher-v2 --no-cuda
  python build_training_command.py --mode enjoy --algo ppo --env-name Reacher-v2
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePosixPath


def _add(cmd, *parts):
    cmd.extend(str(p) for p in parts if p is not None and str(p) != "")


def build_train(args):
    cmd = [args.python, args.train_entrypoint]
    algo = args.algo
    preset = args.preset

    if preset == "atari-ppo":
        algo = "ppo"
        num_env_steps = 10_000_000
        defaults = [
            ("--use-gae", None),
            ("--lr", "2.5e-4"),
            ("--clip-param", "0.1"),
            ("--value-loss-coef", "0.5"),
            ("--num-processes", "8"),
            ("--num-steps", "128"),
            ("--num-mini-batch", "4"),
            ("--log-interval", "1"),
            ("--use-linear-lr-decay", None),
            ("--entropy-coef", "0.01"),
        ]
    elif preset == "mujoco-ppo":
        algo = "ppo"
        num_env_steps = 1_000_000
        defaults = [
            ("--use-gae", None),
            ("--log-interval", "1"),
            ("--num-steps", "2048"),
            ("--num-processes", "1"),
            ("--lr", "3e-4"),
            ("--entropy-coef", "0"),
            ("--value-loss-coef", "0.5"),
            ("--ppo-epoch", "10"),
            ("--num-mini-batch", "32"),
            ("--gamma", "0.99"),
            ("--gae-lambda", str(args.gae_lambda)),
            ("--use-linear-lr-decay", None),
            ("--use-proper-time-limits", None),
        ]
    elif preset == "acktr-atari":
        algo = "acktr"
        num_env_steps = 10_000_000
        defaults = [("--num-processes", "32"), ("--num-steps", "20")]
    elif preset == "a2c-basic":
        num_env_steps = 10_000_000
        defaults = []
    else:
        num_env_steps = None
        defaults = []

    _add(cmd, "--env-name", args.env_name)
    if algo != "a2c":
        _add(cmd, "--algo", algo)
    for flag, value in defaults:
        _add(cmd, flag, value)

    if args.num_env_steps is not None:
        _add(cmd, "--num-env-steps", args.num_env_steps)
    elif num_env_steps is not None:
        _add(cmd, "--num-env-steps", num_env_steps)
    if args.log_dir:
        _add(cmd, "--log-dir", args.log_dir)
    save_dir = args.save_dir or "./trained_models/"
    _add(cmd, "--save-dir", save_dir)
    seed = args.seed if args.seed is not None else 1
    _add(cmd, "--seed", seed)
    if args.no_cuda:
        _add(cmd, "--no-cuda")
    if args.use_proper_time_limits and "--use-proper-time-limits" not in cmd:
        _add(cmd, "--use-proper-time-limits")
    if args.gail:
        _add(cmd, "--gail")
        if args.gail_experts_dir:
            _add(cmd, "--gail-experts-dir", args.gail_experts_dir)

    return cmd


def build_enjoy(args):
    cmd = [args.python, args.enjoy_entrypoint, "--env-name", args.env_name]
    load_dir = args.load_dir
    save_root = args.save_dir or "./trained_models/"
    if load_dir is None:
        load_dir = str(PurePosixPath(save_root) / args.algo)
    if load_dir:
        _add(cmd, "--load-dir", load_dir)
    if args.seed is not None:
        _add(cmd, "--seed", args.seed)
    if args.non_det:
        _add(cmd, "--non-det")
    return cmd


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print safe training/playback commands without executing them.")
    parser.add_argument("--mode", choices=["train", "enjoy"], default="train")
    parser.add_argument("--python", default="python", help="Python executable to show in the command")
    parser.add_argument("--train-entrypoint", default="main.py", help="Training entrypoint path in the working checkout/copy")
    parser.add_argument("--enjoy-entrypoint", default="enjoy.py", help="Playback entrypoint path in the working checkout/copy")
    parser.add_argument("--algo", choices=["a2c", "ppo", "acktr"], default="a2c")
    parser.add_argument("--env-name", default="PongNoFrameskip-v4")
    parser.add_argument("--preset", choices=["a2c-basic", "atari-ppo", "mujoco-ppo", "acktr-atari"], default="a2c-basic")
    parser.add_argument("--num-env-steps", type=int, default=None)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--save-dir", default="./trained_models/")
    parser.add_argument("--load-dir", default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--no-cuda", action="store_true")
    parser.add_argument("--use-proper-time-limits", action="store_true")
    parser.add_argument("--gae-lambda", type=float, default=0.95, help="Current parser flag; replaces stale --tau")
    parser.add_argument("--gail", action="store_true")
    parser.add_argument("--gail-experts-dir", default=None)
    parser.add_argument("--non-det", action="store_true", help="Use non-deterministic playback action selection in enjoy mode")
    args = parser.parse_args(argv)

    cmd = build_enjoy(args) if args.mode == "enjoy" else build_train(args)
    print(shlex.join(cmd))


if __name__ == "__main__":
    main()
