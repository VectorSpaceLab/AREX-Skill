#!/usr/bin/env python3
"""Render a ProtoMotions train-agent command from explicit arguments."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot-name", required=True)
    parser.add_argument("--simulator", required=True)
    parser.add_argument("--experiment-path", required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--motion-file", required=True)
    parser.add_argument("--num-envs", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--ngpu", type=int, default=1)
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--headless", default="True")
    parser.add_argument("--use-wandb", action="store_true")
    parser.add_argument("--use-slurm", action="store_true")
    parser.add_argument("--create-config-only", action="store_true")
    parser.add_argument("--override", action="append", default=[], help="Scalar override key=value; may repeat")
    args = parser.parse_args()

    cmd = [
        "protomotions",
        "train-agent",
        "--robot-name", args.robot_name,
        "--simulator", args.simulator,
        "--experiment-path", args.experiment_path,
        "--experiment-name", args.experiment_name,
        "--motion-file", args.motion_file,
        "--num-envs", str(args.num_envs),
        "--batch-size", str(args.batch_size),
        "--ngpu", str(args.ngpu),
        "--nodes", str(args.nodes),
        "--headless", str(args.headless),
    ]
    if args.use_wandb:
        cmd.append("--use-wandb")
    if args.use_slurm:
        cmd.append("--use-slurm")
    if args.create_config_only:
        cmd.append("--create-config-only")
    if args.override:
        cmd.append("--overrides")
        cmd.extend(args.override)

    print(" ".join(shlex.quote(part) for part in cmd))
    total_gpus = args.ngpu * args.nodes
    print(f"# total_gpus={total_gpus} effective_num_envs={args.num_envs * total_gpus} effective_batch_size={args.batch_size * total_gpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
