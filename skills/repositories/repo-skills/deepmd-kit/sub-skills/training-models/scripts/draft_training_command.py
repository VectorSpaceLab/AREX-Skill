#!/usr/bin/env python3
"""Draft safe DeePMD-kit training commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


BACKEND_FLAGS = {
    "tf": "--tf",
    "tensorflow": "--tf",
    "pt": "--pt",
    "pytorch": "--pt",
    "jax": "--jax",
    "pd": "--pd",
    "paddle": "--pd",
}

BACKEND_NAMES = {
    "--tf": "TensorFlow",
    "--pt": "PyTorch",
    "--jax": "JAX",
    "--pd": "Paddle",
}


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage()
        raise SystemExit(f"error: {message}")


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def normalize_backend(value: str) -> str:
    try:
        return BACKEND_FLAGS[value.lower()]
    except KeyError as exc:
        choices = ", ".join(sorted(BACKEND_FLAGS))
        raise argparse.ArgumentTypeError(
            f"unsupported backend {value!r}; choose one of: {choices}"
        ) from exc


def build_train_parts(args: argparse.Namespace) -> list[str]:
    parts = ["dp", args.backend_flag, "train", args.input]
    if args.restart:
        parts.extend(["--restart", args.restart])
    if args.init_model:
        parts.extend(["--init-model", args.init_model])
    if args.finetune:
        parts.extend(["--finetune", args.finetune])
    if args.use_pretrain_script:
        parts.append("--use-pretrain-script")
    if args.model_branch:
        parts.extend(["--model-branch", args.model_branch])
    if args.force_load:
        parts.append("--force-load")
    if args.skip_neighbor_stat:
        parts.append("--skip-neighbor-stat")
    return parts


def with_distributed_launcher(args: argparse.Namespace, train_parts: list[str]) -> list[str]:
    if not args.distributed_nproc:
        return train_parts

    nproc = str(args.distributed_nproc)
    if args.backend_flag == "--pt":
        return ["torchrun", f"--nproc_per_node={nproc}", "--no-python", *train_parts]
    if args.backend_flag == "--tf":
        return ["horovodrun", "-np", nproc, *train_parts]
    if args.backend_flag == "--pd":
        gpu_list = ",".join(str(index) for index in range(args.distributed_nproc))
        return [
            "python",
            "-m",
            "paddle.distributed.launch",
            f"--gpus={gpu_list}",
            *train_parts,
        ]
    return train_parts


def freeze_hint(args: argparse.Namespace) -> str:
    if args.backend_flag == "--tf":
        return "dp --tf freeze -o model.pb"
    if args.backend_flag == "--pt":
        if args.freeze_head:
            return shell_join(["dp", "--pt", "freeze", "-o", "model_branch.pth", "--head", args.freeze_head])
        return "dp --pt freeze -o model.pth"
    if args.backend_flag == "--pd":
        if args.freeze_head:
            return shell_join(["dp", "--pd", "freeze", "-o", "model_branch", "--head", args.freeze_head])
        return "dp --pd freeze -o model"
    return "Confirm freeze support and output format for the selected JAX model/backend."


def add_notes(args: argparse.Namespace) -> list[str]:
    notes = [
        "This script only drafts commands; it never starts DeePMD-kit training.",
        f"Backend: {BACKEND_NAMES[args.backend_flag]} ({args.backend_flag}).",
    ]

    input_path = Path(args.input)
    if not input_path.exists():
        notes.append(
            "Input path was not found from the current directory; keep it as a placeholder or run from the training directory."
        )

    if args.skip_neighbor_stat:
        notes.append(
            "--skip-neighbor-stat disables neighbor-stat checks, automatic sel, and compression preparation; use mainly for bounded smoke checks or prevalidated sel."
        )
    else:
        notes.append(
            "Keep neighbor-stat enabled when using sel: auto/auto:factor or when sel has not been validated."
        )

    if args.finetune:
        notes.append(
            "Fine-tuning requires compatible model architecture/type_map; use --model-branch for multi-task pretrained models."
        )
    if args.use_pretrain_script:
        notes.append(
            "--use-pretrain-script requires the pretrained model to embed a usable model definition."
        )
    if args.model_branch:
        if args.model_branch.upper() == "RANDOM":
            notes.append("Model branch RANDOM intentionally uses a randomly initialized fitting head.")
        else:
            notes.append("Verify the branch name with `dp --pt show MODEL model-branch` when using a local multi-task model.")
    if args.distributed_nproc:
        if args.backend_flag == "--jax":
            notes.append("No generic JAX distributed launcher was added; confirm installation-specific launch support.")
        elif args.backend_flag == "--pt":
            notes.append("PyTorch distributed launch uses torchrun; validate single-process training first.")
        elif args.backend_flag == "--tf":
            notes.append("TensorFlow distributed launch uses Horovod/MPI; site MPI wrappers may need adjustment.")
        elif args.backend_flag == "--pd":
            notes.append("Paddle launch assumes GPUs numbered from 0; adjust --gpus for scheduler-visible devices.")
    if args.backend_flag != "--pt" and args.model_branch:
        notes.append("Model-branch training selection is primarily documented for PyTorch/Paddle fine-tuning; confirm support for this backend.")

    notes.append("For quick validation, reduce numb_steps/disp_freq/save_freq in the input rather than interrupting a production config.")
    notes.append("Example water data should be treated as workflow smoke data, not production training data.")
    return notes


def parse_args() -> argparse.Namespace:
    parser = Parser(
        description="Emit a safe DeePMD-kit training command and notes without running training.",
    )
    parser.add_argument(
        "--backend",
        required=True,
        type=normalize_backend,
        dest="backend_flag",
        help="Training backend: tf/tensorflow, pt/pytorch, jax, or pd/paddle.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Training input JSON/YAML path to pass to `dp train`.",
    )

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--restart", help="Checkpoint prefix/path for continuing the same run.")
    source_group.add_argument("--init-model", help="Checkpoint prefix/path for initializing a new run.")
    source_group.add_argument("--finetune", help="Frozen/checkpoint/pretrained model to fine-tune from.")

    parser.add_argument(
        "--use-pretrain-script",
        action="store_true",
        help="Add DeePMD-kit flag to inherit model definition from the pretrained model when supported.",
    )
    parser.add_argument(
        "--model-branch",
        help="Multi-task branch/head for fine-tuning; use RANDOM only intentionally.",
    )
    parser.add_argument(
        "--force-load",
        action="store_true",
        help="Add PyTorch force-load flag for partial checkpoint compatibility.",
    )
    parser.add_argument(
        "--skip-neighbor-stat",
        action="store_true",
        help="Skip neighbor-stat calculation during training startup.",
    )
    parser.add_argument(
        "--distributed-nproc",
        type=int,
        help="Draft a distributed launcher for this many local processes/GPUs.",
    )
    parser.add_argument(
        "--freeze-head",
        help="Optional multi-task head/branch to show in the freeze hint.",
    )
    args = parser.parse_args()

    if args.distributed_nproc is not None and args.distributed_nproc < 1:
        parser.error("--distributed-nproc must be a positive integer")
    if args.use_pretrain_script and not (args.finetune or args.init_model):
        parser.error("--use-pretrain-script is meaningful only with --finetune or --init-model")
    if args.model_branch and not args.finetune:
        parser.error("--model-branch is intended for fine-tuning command drafts; use --freeze-head for freeze hints")
    if args.force_load and args.backend_flag != "--pt":
        parser.error("--force-load is a PyTorch training option")
    return args


def main() -> int:
    args = parse_args()
    train_parts = build_train_parts(args)
    command_parts = with_distributed_launcher(args, train_parts)

    print("Training command (not executed):")
    print(shell_join(command_parts))
    print()
    print("Freeze hint after a successful checkpoint:")
    print(freeze_hint(args))
    print()
    print("Notes:")
    for note in add_notes(args):
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
