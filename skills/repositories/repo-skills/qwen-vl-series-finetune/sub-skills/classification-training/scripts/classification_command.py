#!/usr/bin/env python3
"""Build a safe Qwen-VL classification command without running training by default."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _run_env() -> dict[str, str]:
    env = os.environ.copy()
    source_root = str(_skill_root() / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = source_root if not existing else f"{source_root}{os.pathsep}{existing}"
    return env


def _format_shell_command(cmd: list[str]) -> str:
    body = " ".join(shlex.quote(part) for part in cmd)
    return f"cd {shlex.quote(str(_skill_root()))} && PYTHONPATH=src${{PYTHONPATH:+:$PYTHONPATH}} {body}"


def _execution_command(cmd: list[str], env: dict[str, str]) -> list[str]:
    if cmd and cmd[0] == "deepspeed" and shutil.which("deepspeed", path=env.get("PATH")) is None:
        return [sys.executable, "-m", "deepspeed", *cmd[1:]]
    if cmd and cmd[0] == "python":
        return [sys.executable, *cmd[1:]]
    return cmd


def _deepspeed_config(name: str) -> str:
    return str(Path("scripts") / "deepspeed" / name)


def build_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        "deepspeed",
        "src/train/train_cls.py",
        "--deepspeed",
        _deepspeed_config(args.deepspeed_config),
        "--model_id",
        args.model_id,
        "--data_path",
        args.data_path,
        "--image_folder",
        args.image_folder,
        "--output_dir",
        args.output_dir,
        "--loss_type",
        args.loss_type,
        "--num_labels",
        str(args.num_labels),
        "--per_device_train_batch_size",
        str(args.per_device_train_batch_size),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--num_train_epochs",
        str(args.num_train_epochs),
        "--learning_rate",
        str(args.learning_rate),
        "--head_lr",
        str(args.head_lr),
        "--vision_lr",
        str(args.vision_lr),
        "--merger_lr",
        str(args.merger_lr),
        "--weight_decay",
        str(args.weight_decay),
        "--warmup_ratio",
        str(args.warmup_ratio),
        "--max_grad_norm",
        str(args.max_grad_norm),
        "--lr_scheduler_type",
        args.lr_scheduler_type,
        "--logging_steps",
        str(args.logging_steps),
        "--bf16",
        str(args.bf16),
        "--fp16",
        str(args.fp16),
        "--disable_flash_attn2",
        str(args.disable_flash_attn2),
        "--tf32",
        str(args.tf32),
        "--use_liger_kernel",
        str(args.use_liger_kernel),
        "--bits",
        str(args.bits),
        "--double_quant",
        str(args.double_quant),
        "--quant_type",
        args.quant_type,
        "--remove_unused_columns",
        str(args.remove_unused_columns),
        "--freeze_llm",
        str(args.freeze_llm),
        "--freeze_vision_tower",
        str(args.freeze_vision_tower),
        "--freeze_merger",
        str(args.freeze_merger),
        "--lazy_preprocess",
        str(args.lazy_preprocess),
        "--gradient_checkpointing",
        str(args.gradient_checkpointing),
        "--report_to",
        args.report_to,
        "--save_strategy",
        args.save_strategy,
        "--dataloader_num_workers",
        str(args.dataloader_num_workers),
        "--eval_strategy",
        args.eval_strategy,
        "--load_best_model_at_end",
        str(args.load_best_model_at_end),
        "--metric_for_best_model",
        args.metric_for_best_model,
        "--greater_is_better",
        str(args.greater_is_better),
    ]
    if args.eval_path is not None:
        cmd.extend(["--eval_path", args.eval_path])
    if args.eval_image_folder is not None:
        cmd.extend(["--eval_image_folder", args.eval_image_folder])
    if args.lora_enable:
        cmd.extend([
            "--lora_enable",
            "True",
            "--lora_rank",
            str(args.lora_rank),
            "--lora_alpha",
            str(args.lora_alpha),
            "--lora_dropout",
            str(args.lora_dropout),
            "--num_lora_modules",
            str(args.num_lora_modules),
            "--lora_bias",
            args.lora_bias,
        ])
        if args.lora_namespan_exclude is not None:
            cmd.extend(["--lora_namespan_exclude", args.lora_namespan_exclude])
    if args.vision_lora:
        cmd.extend(["--vision_lora", "True"])
    if args.use_dora:
        cmd.extend(["--use_dora", "True"])
    if args.enable_reasoning:
        cmd.extend(["--enable_reasoning", "True"])
    if args.mlp_head_dim is not None:
        cmd.extend(["--mlp_head_dim", str(args.mlp_head_dim)])
    if args.mlp_head_dropout is not None:
        cmd.extend(["--mlp_head_dropout", str(args.mlp_head_dropout)])
    if args.class_balanced_beta is not None:
        cmd.extend(["--class_balanced_beta", str(args.class_balanced_beta)])
    if args.focal_alpha is not None:
        cmd.extend(["--focal_alpha", args.focal_alpha])
    if args.focal_gamma is not None:
        cmd.extend(["--focal_gamma", str(args.focal_gamma)])
    if args.early_stopping_patience is not None:
        cmd.extend(["--early_stopping_patience", str(args.early_stopping_patience)])
    if args.early_stopping_threshold is not None:
        cmd.extend(["--early_stopping_threshold", str(args.early_stopping_threshold)])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--image-folder", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--eval-path", default=None)
    parser.add_argument("--eval-image-folder", default=None)
    parser.add_argument("--deepspeed-config", default="zero3.json")
    parser.add_argument("--loss-type", default="cross_entropy", choices=["cross_entropy", "focal_loss", "class_balanced_cross_entropy", "class_balanced_focal_loss"])
    parser.add_argument("--num-labels", type=int, default=2)
    parser.add_argument("--per-device-train-batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--num-train-epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--head-lr", type=float, default=4e-5)
    parser.add_argument("--vision-lr", type=float, default=6e-6)
    parser.add_argument("--merger-lr", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.02)
    parser.add_argument("--warmup-ratio", type=float, default=0.05)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--report-to", default="tensorboard")
    parser.add_argument("--save-strategy", default="epoch")
    parser.add_argument("--dataloader-num-workers", type=int, default=4)
    parser.add_argument("--eval-strategy", default="epoch")
    parser.add_argument("--load-best-model-at-end", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--metric-for-best-model", default="eval_f1")
    parser.add_argument("--greater-is-better", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--disable-flash-attn2", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--tf32", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-liger-kernel", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--remove-unused-columns", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--freeze-llm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--freeze-vision-tower", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--freeze-merger", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--lazy-preprocess", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--gradient-checkpointing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--lora-enable", action="store_true")
    parser.add_argument("--vision-lora", action="store_true")
    parser.add_argument("--use-dora", action="store_true")
    parser.add_argument("--bits", type=int, default=16, choices=[4, 8, 16])
    parser.add_argument("--double-quant", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--quant-type", default="nf4", choices=["nf4", "fp4"])
    parser.add_argument("--lora-rank", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-bias", default="none")
    parser.add_argument("--lora-namespan-exclude", default=None)
    parser.add_argument("--num-lora-modules", type=int, default=-1)
    parser.add_argument("--enable-reasoning", action="store_true")
    parser.add_argument("--mlp-head-dim", type=int, default=0)
    parser.add_argument("--mlp-head-dropout", type=float, default=0.0)
    parser.add_argument("--class-balanced-beta", type=float, default=0.999)
    parser.add_argument("--focal-alpha", default=None)
    parser.add_argument("--focal-gamma", type=float, default=0.0)
    parser.add_argument("--early-stopping-patience", type=int, default=0)
    parser.add_argument("--early-stopping-threshold", type=float, default=0.0)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.vision_lora:
        args.lora_enable = True
        args.freeze_vision_tower = True
        args.freeze_merger = True
    if args.lora_enable:
        args.freeze_llm = True

    cmd = build_command(args)
    print(_format_shell_command(cmd))
    if args.run:
        env = _run_env()
        return subprocess.call(_execution_command(cmd, env), cwd=str(_skill_root()), env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
