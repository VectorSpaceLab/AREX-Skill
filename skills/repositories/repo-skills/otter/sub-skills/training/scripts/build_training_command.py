#!/usr/bin/env python3
"""Build Otter training commands without launching training.

This helper validates required arguments for the selected workflow and prints a
shell command that a user may run later. It never imports Otter or starts a
training process.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Iterable, List

CONFIGS = {
    "ddp": "pipeline/accelerate_configs/accelerate_config_ddp.yaml",
    "fsdp": "pipeline/accelerate_configs/accelerate_config_fsdp.yaml",
    "zero1": "pipeline/accelerate_configs/accelerate_config_zero1.yaml",
    "zero2": "pipeline/accelerate_configs/accelerate_config_zero2.yaml",
    "zero2-slurm": "pipeline/accelerate_configs/accelerate_config_zero2_slurm.yaml",
    "zero3": "pipeline/accelerate_configs/accelerate_config_zero3.yaml",
    "zero3-offload": "pipeline/accelerate_configs/accelerate_config_zero3_offload.yaml",
    "zero3-slurm": "pipeline/accelerate_configs/accelerate_config_zero3_slurm.yaml",
}

SFT_MODEL_CHOICES = ["otter", "flamingo", "idefics", "llama2", "debug_model", "fuyu"]
SFT_FORMAT_CHOICES = ["simple", "llama2", "idefics", "fuyu"]
SCHEDULERS = ["constant", "linear", "cosine"]
PRECISIONS = ["amp_bf16", "amp_bfloat16", "bf16", "amp", "fp16", "fp32"]


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a float, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def add_bool(cmd: List[str], enabled: bool, flag: str) -> None:
    if enabled:
        cmd.append(flag)


def add_opt(cmd: List[str], flag: str, value) -> None:
    if value is not None:
        cmd.append(f"{flag}={value}")


def require(parser: argparse.ArgumentParser, args: argparse.Namespace, attr: str, flag: str) -> None:
    if getattr(args, attr) in (None, ""):
        parser.error(f"{flag} is required for --mode {args.mode}")


def validate_image_resolution(parser: argparse.ArgumentParser, value: str | None) -> None:
    if not value:
        return
    parts = value.split(",")
    if len(parts) != 2:
        parser.error("--image-resolution must use the train_args.py tuple format x,y with no spaces")
    try:
        width, height = (int(part) for part in parts)
    except ValueError:
        parser.error("--image-resolution must contain two integers, for example 224,224")
    if width <= 0 or height <= 0:
        parser.error("--image-resolution dimensions must be > 0")


def config_path(config_name: str, custom_config: str | None) -> str:
    if custom_config:
        return custom_config
    return CONFIGS[config_name]


def base_launch(args: argparse.Namespace) -> List[str]:
    cmd = [
        "accelerate",
        "launch",
        f"--config_file={config_path(args.accelerate_config, args.custom_accelerate_config)}",
        f"--num_processes={args.num_processes}",
    ]
    add_opt(cmd, "--num_machines", args.num_machines)
    add_opt(cmd, "--machine_rank", args.machine_rank)
    add_opt(cmd, "--main_process_ip", args.main_process_ip)
    add_opt(cmd, "--main_process_port", args.main_process_port)
    return cmd


def append_common_training_flags(cmd: List[str], args: argparse.Namespace) -> None:
    add_opt(cmd, "--external_save_dir", args.external_save_dir)
    add_opt(cmd, "--run_name", args.run_name)
    add_bool(cmd, args.offline, "--offline")
    add_opt(cmd, "--num_epochs", args.num_epochs)
    add_opt(cmd, "--logging_steps", args.logging_steps)
    add_opt(cmd, "--gradient_accumulation_steps", args.gradient_accumulation_steps)
    add_opt(cmd, "--pretrained_model_name_or_path", args.pretrained_model)
    add_opt(cmd, "--seed", args.seed)
    add_opt(cmd, "--learning_rate", args.learning_rate)
    add_opt(cmd, "--lr_scheduler", args.lr_scheduler)
    add_opt(cmd, "--warmup_steps", args.warmup_steps)
    add_opt(cmd, "--warmup_steps_ratio", args.warmup_steps_ratio)
    add_opt(cmd, "--weight_decay", args.weight_decay)
    add_opt(cmd, "--workers", args.workers)
    add_bool(cmd, args.mask_lm_head, "--mask_lm_head")
    add_bool(cmd, args.save_hf_model, "--save_hf_model")
    add_bool(cmd, args.report_to_wandb, "--report_to_wandb")
    add_opt(cmd, "--wandb_project", args.wandb_project)
    add_opt(cmd, "--wandb_entity", args.wandb_entity)
    add_bool(cmd, args.save_checkpoints_to_wandb, "--save_checkpoints_to_wandb")
    add_bool(cmd, args.resume_from_checkpoint, "--resume_from_checkpoint")
    add_bool(cmd, args.delete_previous_checkpoint, "--delete_previous_checkpoint")


def build_sft_command(args: argparse.Namespace) -> List[str]:
    cmd = base_launch(args)
    cmd.append("pipeline/train/instruction_following.py")
    append_common_training_flags(cmd, args)
    add_opt(cmd, "--model_name", args.model_name)
    add_opt(cmd, "--instruction_format", args.instruction_format)
    add_opt(cmd, "--training_data_yaml", args.training_data_yaml)
    add_bool(cmd, args.gradient_checkpointing, "--gradient_checkpointing")
    add_bool(cmd, args.save_ckpt_each_epoch, "--save_ckpt_each_epoch")
    add_opt(cmd, "--batch_size", args.batch_size)
    add_opt(cmd, "--save_steps_interval", args.save_steps_interval)
    add_opt(cmd, "--peft_model_name_or_path", args.peft_model)
    add_opt(cmd, "--trained_ckpt", args.trained_ckpt)
    add_opt(cmd, "--max_seq_len", args.max_seq_len)
    add_opt(cmd, "--patch-image-size", args.patch_image_size)
    add_opt(cmd, "--resample_frames", args.resample_frames)
    add_opt(cmd, "--customized_config", args.customized_config)
    add_bool(cmd, args.keep_symbols, "--keep_symbols")
    add_bool(cmd, args.remove_answer_token, "--remove_answer_token")
    add_bool(cmd, args.remove_eos_token, "--remove_eos_token")
    add_bool(cmd, args.populate_rel_ins, "--populate_rel_ins")
    add_bool(cmd, args.resize_embedding, "--resize_embedding")
    add_opt(cmd, "--image_resolution", args.image_resolution)
    add_bool(cmd, args.with_task_description, "--with_task_description")
    add_bool(cmd, args.enable_lora, "--enable_lora")
    add_bool(cmd, args.dynamic_resolution, "--dynamic_resolution")
    return cmd


def build_pretraining_command(args: argparse.Namespace) -> List[str]:
    cmd = base_launch(args)
    cmd.append("pipeline/train/pretraining.py")
    append_common_training_flags(cmd, args)
    add_opt(cmd, "--mmc4_shards", args.mmc4_shards)
    add_opt(cmd, "--laion_shards", args.laion_shards)
    add_opt(cmd, "--train_num_samples_mmc4", args.train_num_samples_mmc4)
    add_opt(cmd, "--train_num_samples_laion", args.train_num_samples_laion)
    add_opt(cmd, "--batch_size_mmc4", args.batch_size_mmc4)
    add_opt(cmd, "--batch_size_laion", args.batch_size_laion)
    add_bool(cmd, args.dataset_resampled, "--dataset_resampled")
    add_opt(cmd, "--mmc4_textsim_threshold", args.mmc4_textsim_threshold)
    add_opt(cmd, "--checkpointing_steps", args.checkpointing_steps)
    add_opt(cmd, "--loss_multiplier_mmc4", args.loss_multiplier_mmc4)
    add_opt(cmd, "--loss_multiplier_laion", args.loss_multiplier_laion)
    add_opt(cmd, "--precision", args.precision)
    add_opt(cmd, "--max-src-length", args.max_src_length)
    add_opt(cmd, "--max-tgt-length", args.max_tgt_length)
    add_opt(cmd, "--patch-image-size", args.patch_image_size)
    return cmd


def build_pretraining_cc3m_command(args: argparse.Namespace) -> List[str]:
    cmd = base_launch(args)
    cmd.append("pipeline/train/pretraining_cc3m.py")
    append_common_training_flags(cmd, args)
    add_opt(cmd, "--cc3m_shards", args.cc3m_shards)
    add_opt(cmd, "--train_num_samples_cc3m", args.train_num_samples_cc3m)
    add_opt(cmd, "--batch_size_cc3m", args.batch_size_cc3m)
    add_bool(cmd, args.dataset_resampled, "--dataset_resampled")
    add_opt(cmd, "--checkpointing_steps", args.checkpointing_steps)
    add_opt(cmd, "--loss_multiplier_cc3m", args.loss_multiplier_cc3m)
    add_opt(cmd, "--max-src-length", args.max_src_length)
    add_opt(cmd, "--max-tgt-length", args.max_tgt_length)
    add_opt(cmd, "--patch-image-size", args.patch_image_size)
    return cmd


def shell_text(cmd: Iterable[str], include_pythonpath: bool) -> str:
    rendered = shlex.join(list(cmd))
    if include_pythonpath:
        return "export PYTHONPATH=.\n" + rendered
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit validated Otter training commands without launching training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=["sft", "otterhd", "pretraining", "pretraining-cc3m"], required=True)
    parser.add_argument("--format", choices=["shell", "json"], default="shell", help="Output format")
    parser.add_argument("--no-pythonpath", action="store_true", help="Do not prepend 'export PYTHONPATH=.' in shell output")

    launch = parser.add_argument_group("Accelerate launch")
    launch.add_argument("--accelerate-config", choices=sorted(CONFIGS), default=None, help="Named repository Accelerate config")
    launch.add_argument("--custom-accelerate-config", help="Custom config path to place after --config_file")
    launch.add_argument("--num-processes", type=positive_int, default=8)
    launch.add_argument("--num-machines", type=positive_int)
    launch.add_argument("--machine-rank", type=nonnegative_int)
    launch.add_argument("--main-process-ip")
    launch.add_argument("--main-process-port", type=positive_int)

    common = parser.add_argument_group("Common training flags")
    common.add_argument("--pretrained-model", help="Value for --pretrained_model_name_or_path")
    common.add_argument("--external-save-dir", default="checkpoints")
    common.add_argument("--run-name")
    common.add_argument("--offline", action="store_true")
    common.add_argument("--num-epochs", type=positive_int, default=3)
    common.add_argument("--logging-steps", type=positive_int, default=100)
    common.add_argument("--gradient-accumulation-steps", type=positive_int, default=1)
    common.add_argument("--seed", type=int, default=42)
    common.add_argument("--learning-rate", type=positive_float)
    common.add_argument("--lr-scheduler", choices=SCHEDULERS)
    common.add_argument("--warmup-steps", type=nonnegative_int, default=1000)
    common.add_argument("--warmup-steps-ratio", type=positive_float)
    common.add_argument("--weight-decay", type=float, default=0.1)
    common.add_argument("--workers", type=nonnegative_int)
    common.add_argument("--mask-lm-head", action="store_true")
    common.add_argument("--save-hf-model", action="store_true")
    common.add_argument("--report-to-wandb", action="store_true")
    common.add_argument("--wandb-project")
    common.add_argument("--wandb-entity")
    common.add_argument("--save-checkpoints-to-wandb", action="store_true")
    common.add_argument("--resume-from-checkpoint", action="store_true")
    common.add_argument("--delete-previous-checkpoint", action="store_true")

    sft = parser.add_argument_group("SFT / instruction-following flags")
    sft.add_argument("--training-data-yaml")
    sft.add_argument("--model-name", choices=SFT_MODEL_CHOICES)
    sft.add_argument("--instruction-format", choices=SFT_FORMAT_CHOICES)
    sft.add_argument("--gradient-checkpointing", action="store_true")
    sft.add_argument("--save-ckpt-each-epoch", action="store_true")
    sft.add_argument("--batch-size", type=positive_int)
    sft.add_argument("--save-steps-interval", type=int)
    sft.add_argument("--peft-model")
    sft.add_argument("--trained-ckpt")
    sft.add_argument("--max-seq-len", type=positive_int)
    sft.add_argument("--patch-image-size", type=positive_int, default=224)
    sft.add_argument("--resample-frames", type=positive_int)
    sft.add_argument("--customized-config")
    sft.add_argument("--keep-symbols", action="store_true")
    sft.add_argument("--remove-answer-token", action="store_true")
    sft.add_argument("--remove-eos-token", action="store_true")
    sft.add_argument("--populate-rel-ins", action="store_true")
    sft.add_argument("--resize-embedding", action="store_true")
    sft.add_argument("--image-resolution", default="224,224")
    sft.add_argument("--with-task-description", action="store_true")
    sft.add_argument("--enable-lora", action="store_true")
    sft.add_argument("--dynamic-resolution", action="store_true")

    pre = parser.add_argument_group("MMC4 + LAION pretraining flags")
    pre.add_argument("--mmc4-shards")
    pre.add_argument("--laion-shards")
    pre.add_argument("--train-num-samples-mmc4", type=positive_int, default=100)
    pre.add_argument("--train-num-samples-laion", type=positive_int, default=100)
    pre.add_argument("--batch-size-mmc4", type=positive_int, default=8)
    pre.add_argument("--batch-size-laion", type=positive_int, default=8)
    pre.add_argument("--dataset-resampled", action="store_true")
    pre.add_argument("--mmc4-textsim-threshold", type=float, default=0.32)
    pre.add_argument("--checkpointing-steps", type=positive_int, default=10000)
    pre.add_argument("--loss-multiplier-mmc4", type=float, default=1.0)
    pre.add_argument("--loss-multiplier-laion", type=float, default=0.2)
    pre.add_argument("--precision", choices=PRECISIONS, default="amp")
    pre.add_argument("--max-src-length", type=positive_int, default=1024)
    pre.add_argument("--max-tgt-length", type=positive_int, default=1024)

    cc3m = parser.add_argument_group("CC3M pretraining flags")
    cc3m.add_argument("--cc3m-shards")
    cc3m.add_argument("--train-num-samples-cc3m", type=positive_int, default=100)
    cc3m.add_argument("--batch-size-cc3m", type=positive_int, default=8)
    cc3m.add_argument("--loss-multiplier-cc3m", type=float, default=1.0)
    return parser


def apply_mode_defaults(args: argparse.Namespace) -> None:
    if args.accelerate_config is None:
        args.accelerate_config = "zero2" if args.mode == "otterhd" else "zero3"
    if args.run_name is None:
        args.run_name = {
            "sft": "Otter_SFT",
            "otterhd": "OtterHD_Fuyu_Finetune",
            "pretraining": "Otter_Pretraining_MMC4_LAION",
            "pretraining-cc3m": "Otter_Pretraining_CC3M",
        }[args.mode]
    if args.learning_rate is None:
        args.learning_rate = 1e-5 if args.mode == "otterhd" else 2e-5 if args.mode == "sft" else 1e-4
    if args.lr_scheduler is None:
        args.lr_scheduler = "linear" if args.mode == "otterhd" else "cosine" if args.mode == "sft" else "constant"
    if args.batch_size is None:
        args.batch_size = 8
    if args.max_seq_len is None:
        args.max_seq_len = 1024 if args.mode in {"sft", "otterhd"} else None
    if args.workers is None:
        args.workers = 1 if args.mode == "otterhd" else max(1, args.num_processes * 2)
    if args.resample_frames is None:
        args.resample_frames = 32
    if args.save_steps_interval is None:
        args.save_steps_interval = -1
    if args.mode == "otterhd":
        args.model_name = args.model_name or "fuyu"
        args.instruction_format = args.instruction_format or "fuyu"
        args.pretrained_model = args.pretrained_model or "adept/fuyu-8b"
        args.dynamic_resolution = True if not args.dynamic_resolution else args.dynamic_resolution
        if args.gradient_accumulation_steps == 1:
            args.gradient_accumulation_steps = 2
    elif args.mode == "sft":
        args.model_name = args.model_name or "otter"
        args.instruction_format = args.instruction_format or "simple"


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.save_checkpoints_to_wandb and not args.report_to_wandb:
        parser.error("--save-checkpoints-to-wandb requires --report-to-wandb")
    if args.report_to_wandb and (not args.wandb_project or not args.wandb_entity):
        parser.error("--report-to-wandb requires --wandb-project and --wandb-entity")
    if args.mode in {"sft", "otterhd"}:
        require(parser, args, "training_data_yaml", "--training-data-yaml")
        require(parser, args, "pretrained_model", "--pretrained-model")
        validate_image_resolution(parser, args.image_resolution)
        if args.model_name == "fuyu" and args.instruction_format != "fuyu":
            parser.error("Fuyu/OtterHD training should use --instruction-format fuyu")
        if args.instruction_format == "fuyu" and args.model_name != "fuyu":
            parser.error("--instruction-format fuyu should be paired with --model-name fuyu")
    elif args.mode == "pretraining":
        require(parser, args, "pretrained_model", "--pretrained-model")
        require(parser, args, "mmc4_shards", "--mmc4-shards")
        require(parser, args, "laion_shards", "--laion-shards")
    elif args.mode == "pretraining-cc3m":
        require(parser, args, "pretrained_model", "--pretrained-model")
        require(parser, args, "cc3m_shards", "--cc3m-shards")
    if args.num_machines and args.num_machines > 1:
        for attr, flag in [
            ("machine_rank", "--machine-rank"),
            ("main_process_ip", "--main-process-ip"),
            ("main_process_port", "--main-process-port"),
        ]:
            if getattr(args, attr) in (None, ""):
                parser.error(f"multi-machine launch requires {flag}")


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    apply_mode_defaults(args)
    validate_args(parser, args)

    if args.mode in {"sft", "otterhd"}:
        cmd = build_sft_command(args)
    elif args.mode == "pretraining":
        cmd = build_pretraining_command(args)
    else:
        cmd = build_pretraining_cc3m_command(args)

    if args.format == "json":
        payload = {
            "mode": args.mode,
            "command": cmd,
            "shell": shell_text(cmd, include_pythonpath=not args.no_pythonpath),
            "launches_training": False,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(shell_text(cmd, include_pythonpath=not args.no_pythonpath))
    return 0


if __name__ == "__main__":
    sys.exit(main())
