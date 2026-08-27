#!/usr/bin/env python3
"""Build, but do not run, D-FINE train.py commands.

The helper prints a shell-quoted command string for training, evaluation,
resume, and tuning workflows. It does not execute the command.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Sequence

RESERVED_UPDATE_KEYS = {
    "checkpoint",
    "config",
    "device",
    "devices",
    "local_rank",
    "master_port",
    "mode",
    "nproc",
    "output_dir",
    "print_method",
    "print_rank",
    "seed",
    "single_process",
    "summary_dir",
    "test_only",
    "resume",
    "tuning",
    "use_amp",
}

EXAMPLE_TEXT = """Examples:
  python scripts/dfine_train_command.py --config configs/dfine/dfine_hgnetv2_l_coco.yml --mode train --devices 0,1,2,3 --use-amp --seed 0
  python scripts/dfine_train_command.py --config configs/dfine/dfine_hgnetv2_l_coco.yml --mode test --checkpoint output/dfine_l_coco/best_stg2.pth --devices 0,1,2,3
  python scripts/dfine_train_command.py --config configs/dfine/objects365/dfine_hgnetv2_l_obj2coco.yml --mode tune --checkpoint output/dfine_l_obj365/best_stg2.pth --devices 0,1,2,3 --output-dir output/dfine_l_obj2coco
"""


def split_devices(text: str | None) -> List[str]:
    if text is None:
        return []
    devices = [item.strip() for item in text.split(",") if item.strip()]
    if not devices:
        raise ValueError("--devices must contain at least one CUDA device id")
    return devices


def flatten_update_groups(groups: Sequence[Sequence[str]] | None) -> List[str]:
    flattened: List[str] = []
    if not groups:
        return flattened
    for group in groups:
        flattened.extend(group)
    return flattened


def validate_update_tokens(tokens: Sequence[str]) -> List[str]:
    validated: List[str] = []
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"invalid override token '{token}'; expected KEY=VALUE")
        key, _ = token.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"invalid override token '{token}'; empty key")
        if key in RESERVED_UPDATE_KEYS:
            raise ValueError(
                f"--update cannot set reserved key '{key}'. Use the dedicated script flag instead."
            )
        validated.append(token)
    return validated


def build_command(args: argparse.Namespace) -> str:
    devices = split_devices(args.devices)

    nproc = args.nproc
    if args.single_process:
        if nproc is not None and nproc > 1:
            raise ValueError("--single-process cannot be combined with --nproc > 1")
        nproc = 1
    if nproc is None:
        nproc = len(devices) if len(devices) > 1 else 1
    if nproc < 1:
        raise ValueError("--nproc must be at least 1")
    if devices and nproc > len(devices):
        raise ValueError("--nproc cannot exceed the number of visible devices")

    distributed = not args.single_process and nproc > 1
    if args.device and distributed:
        raise ValueError("--device is only supported for single-process commands")

    if args.mode == "train" and args.checkpoint:
        raise ValueError("--checkpoint is only valid for test, resume, or tune")
    if args.mode in {"test", "resume", "tune"} and not args.checkpoint:
        raise ValueError(f"--checkpoint is required for mode={args.mode}")

    updates = validate_update_tokens(flatten_update_groups(args.update))

    cmd: List[str] = []
    if devices:
        cmd.append(f"CUDA_VISIBLE_DEVICES={','.join(devices)}")

    if distributed:
        cmd.extend(
            [
                "torchrun",
                f"--master_port={args.master_port}",
                f"--nproc_per_node={nproc}",
            ]
        )
    else:
        cmd.append("python")

    cmd.extend(["train.py", "-c", args.config])

    if args.device:
        cmd.extend(["--device", args.device])
    if args.print_method:
        cmd.extend(["--print-method", args.print_method])
    if args.print_rank is not None:
        cmd.extend(["--print-rank", str(args.print_rank)])

    if args.mode == "test":
        cmd.append("--test-only")
        cmd.extend(["-r", args.checkpoint])
    elif args.mode == "resume":
        cmd.extend(["-r", args.checkpoint])
    elif args.mode == "tune":
        cmd.extend(["-t", args.checkpoint])

    if args.use_amp:
        cmd.append("--use-amp")
    if args.seed is not None:
        cmd.extend(["--seed", str(args.seed)])
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    if args.summary_dir:
        cmd.extend(["--summary-dir", args.summary_dir])
    if updates:
        cmd.extend(["-u", *updates])

    return shlex.join(cmd)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a D-FINE train.py command without executing it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLE_TEXT,
    )
    parser.add_argument("--config", required=True, help="train.py config path")
    parser.add_argument(
        "--mode",
        choices=("train", "test", "resume", "tune"),
        default="train",
        help="command mode to build",
    )
    parser.add_argument("--checkpoint", help="checkpoint path for test, resume, or tune")
    parser.add_argument(
        "--devices",
        help="comma-separated CUDA device ids used for CUDA_VISIBLE_DEVICES",
    )
    parser.add_argument(
        "--nproc",
        type=int,
        help="number of torchrun processes per node; inferred from --devices when omitted",
    )
    parser.add_argument("--master-port", type=int, default=7777, help="torchrun master port")
    parser.add_argument("--device", help="train.py --device value for single-process commands")
    parser.add_argument("--print-method", help="train.py --print-method value")
    parser.add_argument(
        "--print-rank",
        type=int,
        help="train.py --print-rank value",
    )
    parser.add_argument("--use-amp", action="store_true", help="add train.py --use-amp")
    parser.add_argument("--seed", type=int, help="add train.py --seed")
    parser.add_argument("--output-dir", help="add train.py --output-dir")
    parser.add_argument("--summary-dir", help="add train.py --summary-dir")
    parser.add_argument(
        "--single-process",
        action="store_true",
        help="force python instead of torchrun",
    )
    parser.add_argument(
        "--update",
        action="append",
        nargs="+",
        metavar="KEY=VALUE",
        help="repeatable YAML override tokens passed to train.py -u",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        command = build_command(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
