#!/usr/bin/env python3
"""Print nnU-Net v2 training command matrices without running training."""

from __future__ import annotations

import argparse
import shlex
from itertools import product
from typing import Iterable


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate nnUNetv2_train commands for datasets, configurations, and folds. "
            "This script only prints commands; it never launches training."
        )
    )
    parser.add_argument("datasets", nargs="+", help="Dataset IDs or names, for example 1 or Dataset001_Example.")
    parser.add_argument(
        "--configs",
        nargs="+",
        required=True,
        help="Configurations to train, for example 2d 3d_fullres 3d_lowres 3d_cascade_fullres.",
    )
    parser.add_argument(
        "--folds",
        nargs="+",
        default=["0", "1", "2", "3", "4"],
        help="Folds to train. Use integers or all. Default: 0 1 2 3 4.",
    )
    parser.add_argument("-tr", "--trainer", default="nnUNetTrainer", help="Trainer class name.")
    parser.add_argument("-p", "--plans", default="nnUNetPlans", help="Plans identifier.")
    parser.add_argument("--npz", action="store_true", help="Add --npz to export validation probabilities.")
    parser.add_argument("--continue-training", action="store_true", help="Add --c to continue training.")
    parser.add_argument("--validation-only", action="store_true", help="Add --val to only run validation.")
    parser.add_argument("--val-best", action="store_true", help="Add --val_best to validate checkpoint_best.pth.")
    parser.add_argument(
        "--disable-checkpointing",
        action="store_true",
        help="Add --disable_checkpointing for non-resumable experiments.",
    )
    parser.add_argument("--pretrained-weights", help="Checkpoint path for -pretrained_weights.")
    parser.add_argument("--device", choices=["cuda", "cpu", "mps"], default="cuda", help="Device type.")
    parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs for DDP training.")
    parser.add_argument(
        "--gpu-ids",
        nargs="+",
        help="Optional CUDA_VISIBLE_DEVICES assignments cycled across generated commands.",
    )
    parser.add_argument(
        "--cascade-order",
        action="store_true",
        help="Print 3d_lowres before 3d_cascade_fullres when both are requested.",
    )
    parser.add_argument(
        "--dry-run-comment",
        action="store_true",
        help="Prefix output with comments describing matrix size and selected strategy.",
    )
    args = parser.parse_args()

    if args.continue_training and args.validation_only:
        parser.error("--continue-training and --validation-only map to mutually exclusive nnUNet flags --c and --val")
    if args.continue_training and args.pretrained_weights:
        parser.error("--continue-training cannot be combined with --pretrained-weights")
    if args.val_best and args.disable_checkpointing:
        parser.error("--val-best cannot be combined with --disable-checkpointing")
    if args.num_gpus < 1:
        parser.error("--num-gpus must be at least 1")
    if args.num_gpus > 1 and args.device != "cuda":
        parser.error("--num-gpus greater than 1 requires --device cuda")
    return args


def ordered_configs(configs: list[str], cascade_order: bool) -> list[str]:
    if not cascade_order:
        return configs
    order = {"3d_lowres": 0, "3d_cascade_fullres": 1}
    return sorted(configs, key=lambda config: (order.get(config, -1), configs.index(config)))


def build_command(args: argparse.Namespace, dataset: str, config: str, fold: str) -> list[str]:
    command = ["nnUNetv2_train", dataset, config, fold]
    if args.trainer != "nnUNetTrainer":
        command.extend(["-tr", args.trainer])
    if args.plans != "nnUNetPlans":
        command.extend(["-p", args.plans])
    if args.pretrained_weights:
        command.extend(["-pretrained_weights", args.pretrained_weights])
    if args.num_gpus != 1:
        command.extend(["-num_gpus", str(args.num_gpus)])
    if args.npz:
        command.append("--npz")
    if args.continue_training:
        command.append("--c")
    if args.validation_only:
        command.append("--val")
    if args.val_best:
        command.append("--val_best")
    if args.disable_checkpointing:
        command.append("--disable_checkpointing")
    if args.device != "cuda":
        command.extend(["-device", args.device])
    return command


def main() -> int:
    args = parse_args()
    configs = ordered_configs(args.configs, args.cascade_order)
    rows = list(product(args.datasets, configs, args.folds))

    if args.dry_run_comment:
        print(f"# commands: {len(rows)}")
        print(f"# trainer: {args.trainer}")
        print(f"# plans: {args.plans}")
        print(f"# device: {args.device}")
        if args.num_gpus > 1:
            print(f"# ddp GPUs per command: {args.num_gpus}")
        elif args.gpu_ids:
            print(f"# cycling CUDA_VISIBLE_DEVICES over: {', '.join(args.gpu_ids)}")

    for index, (dataset, config, fold) in enumerate(rows):
        command = shell_join(build_command(args, dataset, config, fold))
        if args.gpu_ids:
            gpu_id = args.gpu_ids[index % len(args.gpu_ids)]
            command = f"CUDA_VISIBLE_DEVICES={shlex.quote(gpu_id)} {command}"
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
