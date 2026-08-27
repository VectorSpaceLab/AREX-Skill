#!/usr/bin/env python3
"""Validate and print a zi2zi training command.

This helper does not launch TensorFlow. It checks that the experiment layout is
plausible and prints the intended legacy zi2zi invocation so a user can review
flags before starting a long run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a zi2zi training command")
    parser.add_argument("--experiment-dir", required=True)
    parser.add_argument("--experiment-id", type=int, default=0)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--L1-penalty", type=int, default=100)
    parser.add_argument("--Lconst-penalty", type=int, default=15)
    parser.add_argument("--Ltv-penalty", type=float, default=0.0)
    parser.add_argument("--Lcategory-penalty", type=float, default=1.0)
    parser.add_argument("--embedding-num", type=int, default=40)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument("--epoch", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--schedule", type=int, default=10)
    parser.add_argument("--resume", type=int, default=1)
    parser.add_argument("--freeze-encoder", type=int, default=0)
    parser.add_argument("--fine-tune", default=None)
    parser.add_argument("--inst-norm", type=int, default=0)
    parser.add_argument("--sample-steps", type=int, default=10)
    parser.add_argument("--checkpoint-steps", type=int, default=500)
    parser.add_argument("--flip-labels", type=int, default=0)
    parser.add_argument("--python-bin", default="python")
    parser.add_argument("--check-data", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    experiment_dir = Path(args.experiment_dir)
    data_dir = experiment_dir / "data"
    train_obj = data_dir / "train.obj"
    val_obj = data_dir / "val.obj"

    problems: List[str] = []
    warnings: List[str] = []
    if args.embedding_num <= 0:
        problems.append("--embedding-num must be positive")
    if args.batch_size <= 0:
        problems.append("--batch-size must be positive")
    if args.image_size <= 0:
        problems.append("--image-size must be positive")
    if args.check_data:
        if not train_obj.exists():
            problems.append(f"missing file: {train_obj}")
        if not val_obj.exists():
            problems.append(f"missing file: {val_obj}")
    if args.flip_labels and not args.fine_tune:
        warnings.append("flip_labels is most useful during later fine-tuning, not from a blank start")

    cmd = [
        args.python_bin,
        "train.py",
        f"--experiment_dir={args.experiment_dir}",
        f"--experiment_id={args.experiment_id}",
        f"--image_size={args.image_size}",
        f"--L1_penalty={args.L1_penalty}",
        f"--Lconst_penalty={args.Lconst_penalty}",
        f"--Ltv_penalty={args.Ltv_penalty}",
        f"--Lcategory_penalty={args.Lcategory_penalty}",
        f"--embedding_num={args.embedding_num}",
        f"--embedding_dim={args.embedding_dim}",
        f"--epoch={args.epoch}",
        f"--batch_size={args.batch_size}",
        f"--lr={args.lr}",
        f"--schedule={args.schedule}",
        f"--resume={args.resume}",
        f"--freeze_encoder={args.freeze_encoder}",
        f"--inst_norm={args.inst_norm}",
        f"--sample_steps={args.sample_steps}",
        f"--checkpoint_steps={args.checkpoint_steps}",
    ]
    if args.fine_tune:
        cmd.append(f"--fine_tune={args.fine_tune}")
    if args.flip_labels:
        cmd.append(f"--flip_labels={args.flip_labels}")

    report: Dict[str, object] = {
        "experiment_dir": str(experiment_dir),
        "data_dir": str(data_dir),
        "train_obj_exists": train_obj.exists(),
        "val_obj_exists": val_obj.exists(),
        "minimum_embedding_num": args.embedding_num,
        "command": " ".join(map(str, cmd)),
        "warnings": warnings,
        "problems": problems,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("# zi2zi training plan\n")
        if problems:
            print("## Problems to fix before training")
            for problem in problems:
                print(f"- {problem}")
            print()
        if warnings:
            print("## Warnings")
            for warning in warnings:
                print(f"- {warning}")
            print()
        print("## Expected data layout")
        print(f"- {train_obj}")
        print(f"- {val_obj}")
        print()
        print("## Command")
        print(report["command"])
    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
