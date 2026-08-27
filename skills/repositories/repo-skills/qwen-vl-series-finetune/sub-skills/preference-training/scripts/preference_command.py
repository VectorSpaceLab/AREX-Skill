#!/usr/bin/env python3
"""Build a safe Qwen-VL DPO or GRPO command without running training by default."""

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


def build_dpo(args: argparse.Namespace) -> list[str]:
    cmd = [
        "deepspeed",
        "src/train/train_dpo.py",
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
        "--image_min_pixels",
        str(args.image_min_pixels),
        "--image_max_pixels",
        str(args.image_max_pixels),
        "--video_min_pixels",
        str(args.video_min_pixels),
        "--video_max_pixels",
        str(args.video_max_pixels),
        "--dpo_loss",
        args.dpo_loss,
        "--precompute_ref_log_probs",
        str(args.precompute_ref_log_probs),
        "--beta",
        str(args.beta),
        "--use_liger_loss",
        str(args.use_liger_loss),
        "--bits",
        str(args.bits),
        "--double_quant",
        str(args.double_quant),
        "--quant_type",
        args.quant_type,
        "--per_device_train_batch_size",
        str(args.per_device_train_batch_size),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--num_train_epochs",
        str(args.num_train_epochs),
        "--learning_rate",
        str(args.learning_rate),
        "--bf16",
        str(args.bf16),
        "--fp16",
        str(args.fp16),
        "--disable_flash_attn2",
        str(args.disable_flash_attn2),
        "--tf32",
        str(args.tf32),
        "--remove_unused_columns",
        str(args.remove_unused_columns),
        "--freeze_vision_tower",
        str(args.freeze_vision_tower),
        "--freeze_llm",
        str(args.freeze_llm),
        "--freeze_merger",
        str(args.freeze_merger),
        "--report_to",
        args.report_to,
        "--lazy_preprocess",
        str(args.lazy_preprocess),
        "--save_strategy",
        args.save_strategy,
        "--save_steps",
        str(args.save_steps),
        "--save_total_limit",
        str(args.save_total_limit),
        "--dataloader_num_workers",
        str(args.dataloader_num_workers),
        "--weight_decay",
        str(args.weight_decay),
        "--warmup_ratio",
        str(args.warmup_ratio),
        "--lr_scheduler_type",
        args.lr_scheduler_type,
        "--logging_steps",
        str(args.logging_steps),
        "--gradient_checkpointing",
        str(args.gradient_checkpointing),
    ]
    if args.enable_reasoning:
        cmd.extend(["--enable_reasoning", "True"])
    if args.vision_lora:
        cmd.extend(["--vision_lora", "True"])
    if args.image_resized_width is not None:
        cmd.extend(["--image_resized_width", str(args.image_resized_width)])
    if args.image_resized_height is not None:
        cmd.extend(["--image_resized_height", str(args.image_resized_height)])
    if args.video_resized_width is not None:
        cmd.extend(["--video_resized_width", str(args.video_resized_width)])
    if args.video_resized_height is not None:
        cmd.extend(["--video_resized_height", str(args.video_resized_height)])
    if args.fps is not None:
        cmd.extend(["--fps", str(args.fps)])
    if args.nframes is not None:
        cmd.extend(["--nframes", str(args.nframes)])
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
    return cmd


def build_grpo(args: argparse.Namespace) -> list[str]:
    cmd = [
        "deepspeed",
        "src/train/train_grpo.py",
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
        "--image_min_pixels",
        str(args.image_min_pixels),
        "--image_max_pixels",
        str(args.image_max_pixels),
        "--video_min_pixels",
        str(args.video_min_pixels),
        "--video_max_pixels",
        str(args.video_max_pixels),
        "--use_liger_loss",
        str(args.use_liger_loss),
        "--bits",
        str(args.bits),
        "--double_quant",
        str(args.double_quant),
        "--quant_type",
        args.quant_type,
        "--beta",
        str(args.beta),
        "--temperature",
        str(args.temperature),
        "--top_p",
        str(args.top_p),
        "--top_k",
        str(args.top_k),
        "--repetition_penalty",
        str(args.repetition_penalty),
        "--max_completion_length",
        str(args.max_completion_length),
        "--max_prompt_length",
        str(args.max_prompt_length),
        "--num_generations",
        str(args.num_generations),
        "--per_device_train_batch_size",
        str(args.per_device_train_batch_size),
        "--gradient_accumulation_steps",
        str(args.gradient_accumulation_steps),
        "--num_train_epochs",
        str(args.num_train_epochs),
        "--learning_rate",
        str(args.learning_rate),
        "--bf16",
        str(args.bf16),
        "--fp16",
        str(args.fp16),
        "--disable_flash_attn2",
        str(args.disable_flash_attn2),
        "--tf32",
        str(args.tf32),
        "--remove_unused_columns",
        str(args.remove_unused_columns),
        "--freeze_vision_tower",
        str(args.freeze_vision_tower),
        "--freeze_llm",
        str(args.freeze_llm),
        "--freeze_merger",
        str(args.freeze_merger),
        "--report_to",
        args.report_to,
        "--lazy_preprocess",
        str(args.lazy_preprocess),
        "--save_strategy",
        args.save_strategy,
        "--save_total_limit",
        str(args.save_total_limit),
        "--dataloader_num_workers",
        str(args.dataloader_num_workers),
        "--weight_decay",
        str(args.weight_decay),
        "--warmup_ratio",
        str(args.warmup_ratio),
        "--lr_scheduler_type",
        args.lr_scheduler_type,
        "--logging_steps",
        str(args.logging_steps),
        "--gradient_checkpointing",
        str(args.gradient_checkpointing),
    ]
    if args.enable_reasoning:
        cmd.extend(["--enable_reasoning", "True"])
    if args.vision_lora:
        cmd.extend(["--vision_lora", "True"])
    if args.image_resized_width is not None:
        cmd.extend(["--image_resized_width", str(args.image_resized_width)])
    if args.image_resized_height is not None:
        cmd.extend(["--image_resized_height", str(args.image_resized_height)])
    if args.video_resized_width is not None:
        cmd.extend(["--video_resized_width", str(args.video_resized_width)])
    if args.video_resized_height is not None:
        cmd.extend(["--video_resized_height", str(args.video_resized_height)])
    if args.fps is not None:
        cmd.extend(["--fps", str(args.fps)])
    if args.nframes is not None:
        cmd.extend(["--nframes", str(args.nframes)])
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
    if args.min_p is not None:
        cmd.extend(["--min_p", str(args.min_p)])
    if args.liger_grpo_loss_type:
        cmd.extend(["--liger_grpo_loss_type", args.liger_grpo_loss_type])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dpo", "grpo"], required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--image-folder", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--image-min-pixels", type=int, default=512 * 28 * 28)
    parser.add_argument("--image-max-pixels", type=int, default=1280 * 28 * 28)
    parser.add_argument("--video-min-pixels", type=int, default=128 * 28 * 28)
    parser.add_argument("--video-max-pixels", type=int, default=256 * 28 * 28)
    parser.add_argument("--image-resized-width", type=int, default=None)
    parser.add_argument("--image-resized-height", type=int, default=None)
    parser.add_argument("--video-resized-width", type=int, default=None)
    parser.add_argument("--video-resized-height", type=int, default=None)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--nframes", type=int, default=None)
    parser.add_argument("--deepspeed-config", default="zero3_offload.json")
    parser.add_argument("--per-device-train-batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", "--gradient-accumulation_steps", dest="gradient_accumulation_steps", type=int, default=4)
    parser.add_argument("--num-train-epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--report-to", default="tensorboard")
    parser.add_argument("--save-strategy", default="steps")
    parser.add_argument("--save-steps", type=int, default=200)
    parser.add_argument("--save-total-limit", type=int, default=10)
    parser.add_argument("--dataloader-num-workers", type=int, default=4)
    parser.add_argument("--bf16", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--disable-flash-attn2", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--remove-unused-columns", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--freeze-vision-tower", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--freeze-llm", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--freeze-merger", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--use-liger-loss", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--lazy-preprocess", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tf32", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--gradient-checkpointing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-reasoning", action="store_true")
    parser.add_argument("--vision-lora", action="store_true")
    parser.add_argument("--lora-enable", action="store_true")
    parser.add_argument("--bits", type=int, default=16, choices=[4, 8, 16])
    parser.add_argument("--double-quant", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--quant-type", default="nf4", choices=["nf4", "fp4"])
    parser.add_argument("--lora-rank", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-bias", default="none")
    parser.add_argument("--lora-namespan-exclude", default=None)
    parser.add_argument("--num-lora-modules", type=int, default=-1)
    parser.add_argument("--run", action="store_true")

    # DPO-only
    parser.add_argument("--dpo-loss", default="sigmoid")
    parser.add_argument("--precompute-ref-log-probs", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--beta", type=float, default=0.1)

    # GRPO-only
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--min-p", type=float, default=None)
    parser.add_argument("--repetition-penalty", type=float, default=1.0)
    parser.add_argument("--max-completion-length", type=int, default=256)
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--num-generations", type=int, default=2)
    parser.add_argument("--liger-grpo-loss-type", default=None)

    args = parser.parse_args()
    if args.vision_lora:
        args.lora_enable = True
        args.freeze_vision_tower = True
        args.freeze_merger = True
        args.gradient_checkpointing = False
    if args.lora_enable:
        args.freeze_llm = True
    if args.bits in {4, 8}:
        args.use_liger_loss = False
    if args.fps is not None and args.nframes is not None:
        parser.error("--fps and --nframes are mutually exclusive")
    if args.mode == "grpo" and not args.freeze_llm:
        args.freeze_llm = True
    if args.mode == "dpo":
        cmd = build_dpo(args)
    else:
        cmd = build_grpo(args)

    print(_format_shell_command(cmd))
    if args.run:
        env = _run_env()
        return subprocess.call(_execution_command(cmd, env), cwd=str(_skill_root()), env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
