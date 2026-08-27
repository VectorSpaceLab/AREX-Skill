#!/usr/bin/env python3
"""Build MMDetection training/testing launch commands without running them."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


DEFAULT_PORT = 29500


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def parse_cfg_options(values: list[str] | None) -> list[str]:
    if not values:
        return []
    bad_values = [value for value in values if "=" not in value]
    if bad_values:
        raise SystemExit(
            "Every --cfg-options entry must be key=value; invalid: "
            + ", ".join(bad_values)
        )
    return values


def add_common_options(
    command: list[str], args: argparse.Namespace, *, include_work_dir: bool = True
) -> None:
    if include_work_dir and args.work_dir:
        command.extend(["--work-dir", args.work_dir])
    if getattr(args, "cfg_options", None):
        command.append("--cfg-options")
        command.extend(args.cfg_options)


def validate_common(args: argparse.Namespace, warnings: list[str]) -> None:
    if args.cpu and args.gpus != 1:
        raise SystemExit("--cpu can only be combined with --gpus 1.")
    if args.launcher == "slurm" and args.cpu:
        raise SystemExit("Slurm wrappers are GPU-oriented; omit --cpu or use launcher=single.")
    if args.launcher == "single" and args.gpus != 1:
        raise SystemExit("launcher=single requires --gpus 1; use launcher=dist or launcher=slurm.")
    if args.launcher in {"dist", "slurm"} and args.gpus < 1:
        raise SystemExit("Distributed and Slurm launchers require --gpus >= 1.")
    if args.port < 1 or args.port > 65535:
        raise SystemExit("--port must be between 1 and 65535.")
    if args.port == DEFAULT_PORT and args.launcher in {"dist", "slurm"}:
        warnings.append(
            "Default port 29500 is used; choose a unique --port for concurrent jobs."
        )
    if args.work_dir is None and getattr(args, "mode", "") == "train":
        warnings.append(
            "No --work-dir supplied; MMDetection will use config work_dir or ./work_dirs/<config-stem>."
        )


def build_train(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    validate_common(args, warnings)

    if args.resume and args.load_from:
        raise SystemExit(
            "Do not combine --resume with --load-from intent. Use --resume for interrupted runs; put load_from in the config for fine-tuning."
        )
    if args.load_from:
        warnings.append(
            "This script cannot edit configs; add load_from to the config before launching fine-tuning."
        )
    if args.auto_scale_lr:
        warnings.append(
            "Confirm the config defines auto_scale_lr.enable and auto_scale_lr.base_batch_size before launching."
        )
    if any(option.startswith("train_dataloader.batch_size=") for option in args.cfg_options or []):
        if not args.auto_scale_lr:
            warnings.append(
                "train_dataloader.batch_size is overridden without --auto-scale-lr; manually verify optimizer LR."
            )

    command: list[str]
    if args.launcher == "single":
        command = ["python", "tools/train.py", args.config]
    elif args.launcher == "dist":
        command = ["bash", "tools/dist_train.sh", args.config, str(args.gpus)]
    else:
        command = [
            "bash",
            "tools/slurm_train.sh",
            args.partition,
            args.job_name,
            args.config,
            args.work_dir or f"work_dirs/{Path(args.config).stem}",
        ]

    add_common_options(command, args, include_work_dir=args.launcher != "slurm")
    if args.amp:
        command.append("--amp")
    if args.auto_scale_lr:
        command.append("--auto-scale-lr")
    if args.resume is not None:
        command.append("--resume")
        if args.resume != "auto":
            command.append(args.resume)

    env: list[str] = []
    if args.cpu:
        env.append("CUDA_VISIBLE_DEVICES=-1")
    elif args.cuda_visible_devices:
        env.append(f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")
    if args.launcher == "dist":
        env.extend(
            [
                f"PORT={args.port}",
                f"NNODES={args.nnodes}",
                f"NODE_RANK={args.node_rank}",
                f"MASTER_ADDR={args.master_addr}",
            ]
        )
    elif args.launcher == "slurm":
        env.extend(
            [
                f"GPUS={args.gpus}",
                f"GPUS_PER_NODE={args.gpus_per_node}",
                f"CPUS_PER_TASK={args.cpus_per_task}",
            ]
        )
        if args.port != DEFAULT_PORT:
            if "--cfg-options" not in command:
                command.append("--cfg-options")
            command.append(f"env_cfg.dist_cfg.port={args.port}")

    return env + command, warnings


def build_test(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    validate_common(args, warnings)

    if args.out and not args.out.endswith((".pkl", ".pickle")):
        raise SystemExit("--out must end with .pkl or .pickle for tools/test.py.")
    if args.show and args.show_dir:
        warnings.append("Both --show and --show-dir are set; prefer --show-dir on headless servers.")
    elif args.show:
        warnings.append("--show requires a GUI/display server; use --show-dir on remote servers.")

    command: list[str]
    if args.launcher == "single":
        command = ["python", "tools/test.py", args.config, args.checkpoint]
    elif args.launcher == "dist":
        command = ["bash", "tools/dist_test.sh", args.config, args.checkpoint, str(args.gpus)]
    else:
        command = [
            "bash",
            "tools/slurm_test.sh",
            args.partition,
            args.job_name,
            args.config,
            args.checkpoint,
        ]

    add_common_options(command, args)
    if args.out:
        command.extend(["--out", args.out])
    if args.show:
        command.append("--show")
    if args.show_dir:
        command.extend(["--show-dir", args.show_dir])
    if args.wait_time is not None:
        command.extend(["--wait-time", str(args.wait_time)])
    if args.tta:
        command.append("--tta")

    env: list[str] = []
    if args.cpu:
        env.append("CUDA_VISIBLE_DEVICES=-1")
    elif args.cuda_visible_devices:
        env.append(f"CUDA_VISIBLE_DEVICES={args.cuda_visible_devices}")
    if args.launcher == "dist":
        env.extend(
            [
                f"PORT={args.port}",
                f"NNODES={args.nnodes}",
                f"NODE_RANK={args.node_rank}",
                f"MASTER_ADDR={args.master_addr}",
            ]
        )
    elif args.launcher == "slurm":
        env.extend(
            [
                f"GPUS={args.gpus}",
                f"GPUS_PER_NODE={args.gpus_per_node}",
                f"CPUS_PER_TASK={args.cpus_per_task}",
            ]
        )

    return env + command, warnings


def add_shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--launcher", choices=["single", "dist", "slurm"], default="single")
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--cpu", action="store_true", help="Prefix command with CUDA_VISIBLE_DEVICES=-1")
    parser.add_argument("--cuda-visible-devices", help="Comma-separated GPU ids for CUDA_VISIBLE_DEVICES")
    parser.add_argument("--work-dir")
    parser.add_argument("--cfg-options", nargs="+", type=str)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--nnodes", type=int, default=1)
    parser.add_argument("--node-rank", type=int, default=0)
    parser.add_argument("--master-addr", default="127.0.0.1")
    parser.add_argument("--partition", default="PARTITION")
    parser.add_argument("--job-name", default="mmdet_job")
    parser.add_argument("--gpus-per-node", type=int, default=8)
    parser.add_argument("--cpus-per-task", type=int, default=5)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print MMDetection train/test commands and validate common flag combinations."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    train = subparsers.add_parser("train", help="Build a tools/train.py command")
    train.add_argument("config")
    add_shared(train)
    train.add_argument("--amp", action="store_true")
    train.add_argument("--auto-scale-lr", action="store_true")
    train.add_argument(
        "--resume",
        nargs="?",
        const="auto",
        help="Resume from latest checkpoint, or from the provided checkpoint path.",
    )
    train.add_argument(
        "--load-from",
        help="Intent marker for fine-tuning; warns because load_from belongs in the config.",
    )

    test = subparsers.add_parser("test", help="Build a tools/test.py command")
    test.add_argument("config")
    test.add_argument("checkpoint")
    add_shared(test)
    test.add_argument("--out")
    test.add_argument("--show", action="store_true")
    test.add_argument("--show-dir")
    test.add_argument("--wait-time", type=float)
    test.add_argument("--tta", action="store_true")

    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()
    args.cfg_options = parse_cfg_options(args.cfg_options)

    if args.mode == "train":
        command, warnings = build_train(args)
    else:
        command, warnings = build_test(args)

    print(shell_join(command))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
