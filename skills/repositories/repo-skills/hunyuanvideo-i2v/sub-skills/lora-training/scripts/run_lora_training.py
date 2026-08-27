#!/usr/bin/env python3
"""Build or execute the canonical HunyuanVideo-I2V LoRA training command.

Safe by default: prints the command unless --execute is passed.

Example:
  python scripts/run_lora_training.py --repo-root . --data-jsons-path ./assets/demo/i2v_lora/train_dataset/processed_data/json_path
"""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


def _shell_quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _maybe_add(cmd: list[str], flag: str, value) -> None:
    if value is not None:
        cmd.extend([flag, str(value)])


def build_command(args: argparse.Namespace, extra_args: list[str]) -> tuple[list[str], dict[str, str], Path]:
    repo_root = Path(args.repo_root).resolve()
    train_script = repo_root / "train_image2video_lora.py"
    if not train_script.exists():
        raise FileNotFoundError(f"training script not found: {train_script}")

    # Prefer the CLI when it exists; otherwise fall back to the module form.
    if shutil.which("deepspeed"):
        cmd = ["deepspeed"]
    else:
        cmd = [sys.executable, "-m", "deepspeed"]

    output_dir = args.output_dir or str(Path(args.save_base) / "log_EXP")
    task_flag = args.task_flag or f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{args.exp_name}"

    cmd.extend(["--include", args.include, "--master_addr", args.chief_ip, str(train_script)])

    canonical = [
        ("--lr", 1e-4),
        ("--warmup-num-steps", 500),
        ("--global-seed", 1024),
        ("--tensorboard", None),
        ("--zero-stage", 2),
        ("--vae", "884-16c-hy"),
        ("--vae-precision", "fp16"),
        ("--vae-tiling", None),
        ("--denoise-type", "flow"),
        ("--flow-reverse", None),
        ("--flow-shift", 7.0),
        ("--i2v-mode", None),
        ("--model", "HYVideo-T/2"),
        ("--video-micro-batch-size", 1),
        ("--gradient-checkpoint", None),
        ("--ckpt-every", 500),
        ("--embedded-cfg-scale", 6.0),
        ("--data-type", "video"),
        ("--data-jsons-path", args.data_jsons_path),
        ("--sample-n-frames", 129),
        ("--sample-stride", 1),
        ("--num-workers", 8),
        ("--uncond-p", 0.1),
        ("--sematic-cond-drop-p", 0.1),
        ("--text-encoder", "llm-i2v"),
        ("--text-encoder-precision", "fp16"),
        ("--text-states-dim", 4096),
        ("--text-len", 256),
        ("--tokenizer", "llm-i2v"),
        ("--prompt-template", "dit-llm-encode-i2v"),
        ("--prompt-template-video", "dit-llm-encode-video-i2v"),
        ("--hidden-state-skip-layer", 2),
        ("--text-encoder-2", "clipL"),
        ("--text-encoder-precision-2", "fp16"),
        ("--text-states-dim-2", 768),
        ("--tokenizer-2", "clipL"),
        ("--text-len-2", 77),
        ("--use-lora", None),
        ("--lora-rank", 64),
        ("--task-flag", task_flag),
        ("--output-dir", output_dir),
    ]

    for flag, value in canonical:
        if value is None:
            cmd.append(flag)
        else:
            cmd.extend([flag, str(value)])

    cmd.extend(extra_args)
    return cmd, os.environ.copy(), repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute the canonical HunyuanVideo-I2V LoRA training command")
    parser.add_argument("--repo-root", default=".", help="Path to the HunyuanVideo-I2V checkout")
    parser.add_argument("--data-jsons-path", default="./assets/demo/i2v_lora/train_dataset/processed_data/json_path", help="Processed latent JSON directory")
    parser.add_argument("--save-base", default=".", help="Root path for saving experimental results")
    parser.add_argument("--exp-name", default="i2v_lora", help="Experiment suffix used when task-flag is not supplied")
    parser.add_argument("--chief-ip", default="127.0.0.1", help="Master node IP")
    parser.add_argument("--include", default="localhost:0", help="DeepSpeed include string")
    parser.add_argument("--output-dir", default=None, help="Override the output directory instead of using save-base/log_EXP")
    parser.add_argument("--task-flag", default=None, help="Override the generated task flag")
    parser.add_argument("--execute", action="store_true", help="Actually run the command instead of printing it")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it (default behavior)")
    args, extra_args = parser.parse_known_args()

    cmd, env, repo_root = build_command(args, extra_args)
    if args.chief_ip:
        env["CHIEF_IP"] = args.chief_ip
    env["TOKENIZERS_PARALLELISM"] = "false"

    print(_shell_quote(cmd))
    print(f"cwd={repo_root}")
    if not args.execute:
        return 0

    subprocess.run(cmd, cwd=str(repo_root), env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
