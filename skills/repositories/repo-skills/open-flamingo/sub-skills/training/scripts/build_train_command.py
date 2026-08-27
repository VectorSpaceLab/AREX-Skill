#!/usr/bin/env python3
"""Render a safe torchrun command for OpenFlamingo training.

This script only prints a command. It never launches training.

Examples:
    python scripts/build_train_command.py \
      --lm-path anas-awadalla/mpt-1b-redpajama-200b \
      --tokenizer-path anas-awadalla/mpt-1b-redpajama-200b \
      --laion-shards "/path/to/laion/shard-{0000..0999}.tar" \
      --mmc4-shards "/path/to/mmc4/shard-{0000..0999}.tar" \
      --run-name openflamingo-3b-vitl-mpt1b
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import List, Optional


PRECISION_CHOICES = ["amp_bf16", "amp_bfloat16", "bf16", "fp16", "fp32"]
LR_SCHEDULER_CHOICES = ["constant", "linear", "cosine"]
FSDP_SHARDING_CHOICES = ["full", "hybrid"]


def nonempty_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("value must be non-empty")
    return value


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse handles message
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def add_option(parts: List[str], flag: str, value: Optional[object]) -> None:
    if value is None:
        return
    parts.extend([flag, str(value)])


def add_flag(parts: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        parts.append(flag)


def build_command(args: argparse.Namespace) -> str:
    parts: List[str] = [
        "torchrun",
        "--standalone",
        "--nproc_per_node",
        str(args.nproc_per_node),
        args.train_script,
        "--vision_encoder_path",
        args.vision_encoder_path,
        "--vision_encoder_pretrained",
        args.vision_encoder_pretrained,
        "--lm_path",
        args.lm_path,
        "--tokenizer_path",
        args.tokenizer_path,
        "--cross_attn_every_n_layers",
        str(args.cross_attn_every_n_layers),
        "--run_name",
        args.run_name,
        "--batch_size_mmc4",
        str(args.batch_size_mmc4),
        "--batch_size_laion",
        str(args.batch_size_laion),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--seed",
        str(args.seed),
        "--learning_rate",
        str(args.learning_rate),
        "--lr_scheduler",
        args.lr_scheduler,
        "--loss_multiplier_mmc4",
        str(args.loss_multiplier_mmc4),
        "--loss_multiplier_laion",
        str(args.loss_multiplier_laion),
        "--warmup_steps",
        str(args.warmup_steps),
        "--weight_decay",
        str(args.weight_decay),
        "--precision",
        args.precision,
        "--num_epochs",
        str(args.num_epochs),
        "--logging_steps",
        str(args.logging_steps),
        "--laion_shards",
        args.laion_shards,
        "--mmc4_shards",
        args.mmc4_shards,
        "--workers",
        str(args.workers),
        "--mmc4_textsim_threshold",
        str(args.mmc4_textsim_threshold),
        "--mmc4_max_num_images",
        str(args.mmc4_max_num_images),
        "--mmc4_min_num_images",
        str(args.mmc4_min_num_images),
        "--dist-url",
        args.dist_url,
        "--dist-backend",
        args.dist_backend,
    ]

    add_flag(parts, "--dataset_resampled", args.dataset_resampled)
    add_flag(parts, "--gradient_checkpointing", args.gradient_checkpointing)
    add_flag(parts, "--freeze_lm_embeddings", args.freeze_lm_embeddings)
    add_flag(parts, "--report_to_wandb", args.report_to_wandb)
    add_flag(parts, "--save_checkpoints_to_wandb", args.save_checkpoints_to_wandb)
    add_flag(parts, "--offline", args.offline)
    add_flag(parts, "--delete_previous_checkpoint", args.delete_previous_checkpoint)
    add_flag(parts, "--fsdp", args.fsdp)
    add_flag(parts, "--fsdp_use_orig_params", args.fsdp_use_orig_params)
    add_flag(parts, "--no-set-device-rank", args.no_set_device_rank)

    add_option(parts, "--train_num_samples_mmc4", args.train_num_samples_mmc4)
    add_option(parts, "--train_num_samples_laion", args.train_num_samples_laion)
    if args.fsdp:
        add_option(parts, "--fsdp_sharding_strategy", args.fsdp_sharding_strategy)
    add_option(parts, "--resume_from_checkpoint", args.resume_from_checkpoint)
    add_option(parts, "--wandb_project", args.wandb_project)
    add_option(parts, "--wandb_entity", args.wandb_entity)

    return shlex.join(parts)


def validate(args: argparse.Namespace) -> None:
    required_pairs = {
        "lm-path": args.lm_path,
        "tokenizer-path": args.tokenizer_path,
        "laion-shards": args.laion_shards,
        "mmc4-shards": args.mmc4_shards,
        "run-name": args.run_name,
    }
    for label, value in required_pairs.items():
        if not value:
            raise SystemExit(f"--{label} must be provided")

    if args.save_checkpoints_to_wandb and not args.report_to_wandb:
        raise SystemExit(
            "--save-checkpoints-to-wandb requires --report-to-wandb"
        )

    if args.train_num_samples_mmc4 is not None and args.train_num_samples_laion is not None:
        mmc4_batches = args.train_num_samples_mmc4 // args.batch_size_mmc4
        laion_batches = args.train_num_samples_laion // args.batch_size_laion
        if mmc4_batches != laion_batches:
            raise SystemExit(
                "MMC4 and LAION must yield the same number of batches per epoch "
                f"(got {mmc4_batches} vs {laion_batches})"
            )
    elif args.train_num_samples_mmc4 is None or args.train_num_samples_laion is None:
        print(
            "warning: one or both sample budgets were omitted; make sure shard metadata "
            "or explicit train_num_samples_* values will be available at runtime",
            file=sys.stderr,
        )

    if args.fsdp and not args.fsdp_use_orig_params:
        print(
            "warning: FSDP without --fsdp_use_orig_params will train more embeddings than "
            "the recommended setup",
            file=sys.stderr,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a safe torchrun command for OpenFlamingo training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    default_wrapper = str(Path(__file__).resolve().with_name("run_training_entrypoint.py"))
    parser.add_argument(
        "--train-script",
        default=default_wrapper,
        help="Training entrypoint to call in the rendered command. Defaults to this skill's bundled wrapper that locates the installed OpenFlamingo package.",
    )
    parser.add_argument("--nproc-per-node", type=positive_int, default=1, help="torchrun process count per node.")

    parser.add_argument("--vision-encoder-path", default="ViT-L-14", help="OpenCLIP vision encoder path.")
    parser.add_argument("--vision-encoder-pretrained", default="openai", help="OpenCLIP vision encoder weights tag.")
    parser.add_argument("--lm-path", required=True, type=nonempty_text, help="Language model checkpoint path or hub id.")
    parser.add_argument("--tokenizer-path", required=True, type=nonempty_text, help="Tokenizer checkpoint path or hub id.")
    parser.add_argument("--cross-attn-every-n-layers", type=positive_int, default=1, help="Cross-attention insertion interval.")

    parser.add_argument("--run-name", required=True, type=nonempty_text, help="Run name and checkpoint directory.")
    parser.add_argument("--resume-from-checkpoint", type=nonempty_text, help="Explicit checkpoint file to resume from.")
    parser.add_argument("--delete-previous-checkpoint", action="store_true", help="Delete the previous checkpoint after each save.")

    parser.add_argument("--batch-size-mmc4", type=positive_int, default=128, help="MMC4 batch size per process.")
    parser.add_argument("--batch-size-laion", type=positive_int, default=128, help="LAION batch size per process.")
    parser.add_argument("--gradient-accumulation-steps", type=positive_int, default=1, help="Gradient accumulation steps.")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed.")
    parser.add_argument("--learning-rate", type=float, default=1e-4, help="AdamW learning rate.")
    parser.add_argument("--lr-scheduler", choices=LR_SCHEDULER_CHOICES, default="constant", help="Learning rate scheduler.")
    parser.add_argument("--loss-multiplier-mmc4", type=float, default=1.0, help="MMC4 loss multiplier.")
    parser.add_argument("--loss-multiplier-laion", type=float, default=1.0, help="LAION loss multiplier.")
    parser.add_argument("--warmup-steps", type=positive_int, default=5000, help="Scheduler warmup steps.")
    parser.add_argument("--weight-decay", type=float, default=0.1, help="AdamW weight decay.")
    parser.add_argument("--precision", choices=PRECISION_CHOICES, default="fp32", help="Precision mode to pass through to train.py.")
    parser.add_argument("--num-epochs", type=positive_int, default=1, help="Epoch budget.")
    parser.add_argument("--logging-steps", type=positive_int, default=100, help="Console logging interval.")
    parser.add_argument("--workers", type=positive_int, default=1, help="DataLoader workers per process.")
    parser.add_argument("--mmc4-textsim-threshold", type=float, default=30.0, help="MMC4 similarity threshold.")
    parser.add_argument("--mmc4-max-num-images", type=positive_int, default=6, help="Maximum MMC4 images per sample.")
    parser.add_argument("--mmc4-min-num-images", type=positive_int, default=1, help="Minimum MMC4 images per sample.")

    parser.add_argument("--laion-shards", required=True, type=nonempty_text, help="LAION shard pattern.")
    parser.add_argument("--mmc4-shards", required=True, type=nonempty_text, help="MMC4 shard pattern.")
    parser.add_argument("--train-num-samples-mmc4", type=positive_int, help="Explicit MMC4 sample budget.")
    parser.add_argument("--train-num-samples-laion", type=positive_int, help="Explicit LAION sample budget.")
    parser.add_argument("--dataset-resampled", action="store_true", help="Sample shards with replacement.")

    parser.add_argument("--dist-url", default="env://", help="Distributed init URL.")
    parser.add_argument("--dist-backend", default="nccl", help="Distributed backend.")
    parser.add_argument("--no-set-device-rank", action="store_true", help="Do not map device from local rank.")
    parser.add_argument("--fsdp", action="store_true", help="Enable FSDP flags in the rendered command.")
    parser.add_argument("--fsdp-use-orig-params", action="store_true", help="Pass --fsdp_use_orig_params.")
    parser.add_argument("--fsdp-sharding-strategy", choices=FSDP_SHARDING_CHOICES, default="full", help="FSDP sharding strategy.")

    parser.add_argument("--gradient-checkpointing", action="store_true", help="Enable gradient checkpointing.")
    parser.add_argument("--freeze-lm-embeddings", action="store_true", help="Keep LM embeddings frozen.")
    parser.add_argument("--offline", action="store_true", help="Enable offline mode.")

    parser.add_argument("--report-to-wandb", action="store_true", help="Enable W&B logging.")
    parser.add_argument("--wandb-project", type=nonempty_text, help="W&B project name.")
    parser.add_argument("--wandb-entity", type=nonempty_text, help="W&B entity name.")
    parser.add_argument("--save-checkpoints-to-wandb", action="store_true", help="Upload checkpoints to W&B after each save.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate(args)
    print(build_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
