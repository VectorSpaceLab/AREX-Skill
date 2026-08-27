#!/usr/bin/env python3
"""Dry-run composer for BEVFormer training commands."""

from __future__ import annotations

import argparse
import shlex

DEFAULT_TRAIN_PORT = 28509
DEFAULT_FP16_PORT = 28508


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formats the error
        raise argparse.ArgumentTypeError("expected an integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a BEVFormer distributed training command"
    )
    parser.add_argument("--config", required=True, help="training config path")
    parser.add_argument(
        "--gpus",
        type=positive_int,
        default=1,
        help="number of GPUs for the distributed launcher",
    )
    parser.add_argument(
        "--work-dir", help="directory for logs and checkpoints"
    )
    parser.add_argument(
        "--port",
        type=positive_int,
        help="master port for torch.distributed.launch",
    )
    parser.add_argument(
        "--fp16",
        action="store_true",
        help="switch to the fp16 training entrypoint",
    )
    parser.add_argument(
        "--resume-from",
        help="checkpoint to resume from",
    )
    parser.add_argument(
        "--seed", type=int, help="random seed forwarded to the trainer"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="skip validation during training",
    )
    parser.add_argument(
        "--autoscale-lr",
        action="store_true",
        help="scale learning rate by GPU count",
    )
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        metavar="KEY=VALUE",
        help="OpenMMLab config overrides",
    )
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    script = "tools/fp16/train.py" if args.fp16 else "tools/train.py"
    port = args.port if args.port is not None else (
        DEFAULT_FP16_PORT if args.fp16 else DEFAULT_TRAIN_PORT
    )

    command = [
        "python",
        "-m",
        "torch.distributed.launch",
        f"--nproc_per_node={args.gpus}",
        f"--master_port={port}",
        script,
        args.config,
        "--launcher",
        "pytorch",
    ]

    if args.work_dir:
        command.extend(["--work-dir", args.work_dir])
    if args.resume_from:
        command.extend(["--resume-from", args.resume_from])
    if args.seed is not None:
        command.extend(["--seed", str(args.seed)])
    if args.no_validate:
        command.append("--no-validate")
    if args.autoscale_lr:
        command.append("--autoscale-lr")
    if args.cfg_options:
        command.append("--cfg-options")
        command.extend(args.cfg_options)

    command.append("--deterministic")
    return command


def main() -> None:
    args = parse_args()
    print(shlex.join(build_command(args)))


if __name__ == "__main__":
    main()
