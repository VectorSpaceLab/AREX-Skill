#!/usr/bin/env python3
"""Print a safe LLaVA training command template.

The script only builds commands; it never launches training. It is intended for
pretrain, fine-tune, LoRA, QLoRA, and task-specific variants.
"""

from __future__ import annotations

import argparse
import shlex
import sys


MODE_HELP = """Available modes: pretrain, finetune, finetune-lora, finetune-qlora, task-finetune, task-lora, scienceqa"""


def build_command(args: argparse.Namespace) -> list[str]:
    if args.mode in {"pretrain", "finetune", "finetune-lora", "finetune-qlora", "task-finetune", "task-lora", "scienceqa"}:
        cmd = [
            "deepspeed",
            "llava/train/train_mem.py",
            "--deepspeed",
            args.deepspeed,
            "--model_name_or_path",
            args.model_name_or_path,
            "--version",
            args.version,
            "--data_path",
            args.data_path,
            "--image_folder",
            args.image_folder,
            "--vision_tower",
            args.vision_tower,
            "--output_dir",
            args.output_dir,
            "--num_train_epochs",
            str(args.num_train_epochs),
            "--per_device_train_batch_size",
            str(args.per_device_train_batch_size),
            "--per_device_eval_batch_size",
            str(args.per_device_eval_batch_size),
            "--gradient_accumulation_steps",
            str(args.gradient_accumulation_steps),
            "--learning_rate",
            str(args.learning_rate),
            "--weight_decay",
            str(args.weight_decay),
            "--warmup_ratio",
            str(args.warmup_ratio),
            "--lr_scheduler_type",
            args.lr_scheduler_type,
            "--logging_steps",
            str(args.logging_steps),
            "--model_max_length",
            str(args.model_max_length),
            "--dataloader_num_workers",
            str(args.dataloader_num_workers),
        ]
    else:
        raise ValueError(f"unknown mode: {args.mode}")

    if args.mode == "pretrain":
        cmd += ["--tune_mm_mlp_adapter", "True"]
    elif args.mode in {"finetune", "task-finetune", "scienceqa"}:
        if args.pretrain_mm_mlp_adapter:
            cmd += ["--pretrain_mm_mlp_adapter", args.pretrain_mm_mlp_adapter]
    elif args.mode in {"finetune-lora", "task-lora"}:
        cmd += ["--lora_enable", "True", "--lora_r", str(args.lora_r), "--lora_alpha", str(args.lora_alpha)]
        if args.mm_projector_lr is not None:
            cmd += ["--mm_projector_lr", str(args.mm_projector_lr)]
        if args.bits is not None:
            cmd += ["--bits", str(args.bits)]
    elif args.mode == "finetune-qlora":
        cmd += ["--lora_enable", "True", "--bits", "4", "--lora_r", str(args.lora_r), "--lora_alpha", str(args.lora_alpha)]
        if args.mm_projector_lr is not None:
            cmd += ["--mm_projector_lr", str(args.mm_projector_lr)]
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe LLaVA training command.", epilog=MODE_HELP)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--deepspeed", default="scripts/deepspeed/zero3.json")
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--image_folder", required=True)
    parser.add_argument("--vision_tower", default="openai/clip-vit-large-patch14-336")
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_train_epochs", type=float, default=1.0)
    parser.add_argument("--per_device_train_batch_size", type=int, default=16)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=4)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--weight_decay", type=float, default=0.0)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--lr_scheduler_type", default="cosine")
    parser.add_argument("--logging_steps", type=int, default=1)
    parser.add_argument("--model_max_length", type=int, default=2048)
    parser.add_argument("--dataloader_num_workers", type=int, default=4)
    parser.add_argument("--pretrain_mm_mlp_adapter")
    parser.add_argument("--lora_r", type=int, default=128)
    parser.add_argument("--lora_alpha", type=int, default=256)
    parser.add_argument("--mm_projector_lr", type=float)
    parser.add_argument("--bits", type=int)
    args = parser.parse_args()

    cmd = build_command(args)
    print(shlex.join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
