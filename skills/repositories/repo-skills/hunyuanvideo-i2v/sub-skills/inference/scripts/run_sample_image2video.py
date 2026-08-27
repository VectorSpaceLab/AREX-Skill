#!/usr/bin/env python3
"""Build or execute the canonical HunyuanVideo-I2V sampling command.

Safe by default: prints the command unless --execute is passed.

Examples (run from the real checkout root; this helper is under the generated skill):
  python "$SKILL_ROOT/sub-skills/inference/scripts/run_sample_image2video.py" --repo-root "$CHECKOUT_ROOT" --mode stable --prompt "..." --image-path "$CHECKOUT_ROOT/assets/demo/i2v/imgs/0.jpg" --dry-run
  python "$SKILL_ROOT/sub-skills/inference/scripts/run_sample_image2video.py" --repo-root "$CHECKOUT_ROOT" --mode lora --prompt "..." --image-path "$CHECKOUT_ROOT/assets/demo/i2v_lora/imgs/embrace.png" --lora-path "$CHECKOUT_ROOT/ckpts/.../adapter.safetensors" --execute
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _shell_quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _maybe_add(cmd: list[str], flag: str, value: str | int | float | None) -> None:
    if value is not None:
        cmd.extend([flag, str(value)])


def build_command(args: argparse.Namespace) -> tuple[list[str], dict[str, str]]:
    repo_root = Path(args.repo_root).resolve()
    sample_script = repo_root / "sample_image2video.py"
    if not sample_script.exists():
        raise FileNotFoundError(f"sample script not found: {sample_script}")

    cmd = [sys.executable, str(sample_script)]

    # Canonical inference inputs.
    cmd.extend(["--model", args.model, "--i2v-mode", "--i2v-image-path", args.image_path, "--save-path", args.save_path])
    _maybe_add(cmd, "--prompt", args.prompt)
    _maybe_add(cmd, "--i2v-resolution", args.resolution)
    _maybe_add(cmd, "--video-length", args.video_length)
    _maybe_add(cmd, "--infer-steps", args.infer_steps)
    _maybe_add(cmd, "--seed", args.seed)
    _maybe_add(cmd, "--embedded-cfg-scale", args.embedded_cfg_scale)
    _maybe_add(cmd, "--cfg-scale", args.cfg_scale)

    # Mode-specific defaults.
    if args.mode == "stable":
        cmd.extend(["--i2v-stability", "--flow-reverse"])
        _maybe_add(cmd, "--flow-shift", args.flow_shift if args.flow_shift is not None else 7.0)
    elif args.mode == "dynamic":
        cmd.append("--flow-reverse")
        _maybe_add(cmd, "--flow-shift", args.flow_shift if args.flow_shift is not None else 17.0)
    elif args.mode == "lora":
        cmd.extend(["--i2v-stability", "--flow-reverse", "--use-lora"])
        _maybe_add(cmd, "--flow-shift", args.flow_shift if args.flow_shift is not None else 5.0)
        _maybe_add(cmd, "--lora-path", args.lora_path)
        _maybe_add(cmd, "--lora-scale", args.lora_scale)
    elif args.mode == "xdit":
        cmd.extend(["--i2v-stability", "--flow-reverse"])
        _maybe_add(cmd, "--flow-shift", args.flow_shift if args.flow_shift is not None else 7.0)
        _maybe_add(cmd, "--ulysses-degree", args.ulysses_degree)
        _maybe_add(cmd, "--ring-degree", args.ring_degree)
    else:  # pragma: no cover - argparse guards this
        raise ValueError(f"Unknown mode: {args.mode}")

    if args.use_cpu_offload:
        cmd.append("--use-cpu-offload")

    if args.allow_resize_for_sp:
        env = {"ALLOW_RESIZE_FOR_SP": "1"}
    else:
        env = {}

    return cmd, env


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute the canonical HunyuanVideo-I2V inference command")
    parser.add_argument("--repo-root", default=".", help="Path to the HunyuanVideo-I2V checkout")
    parser.add_argument("--mode", choices=["stable", "dynamic", "lora", "xdit"], default="stable")
    parser.add_argument("--prompt", required=True, help="Text prompt for generation")
    parser.add_argument("--image-path", required=True, help="Reference image path")
    parser.add_argument("--save-path", default="./results", help="Directory for generated mp4 files")
    parser.add_argument("--model", default="HYVideo-T/2", help="Backbone model name")
    parser.add_argument("--resolution", choices=["360p", "540p", "720p"], default="720p")
    parser.add_argument("--video-length", type=int, default=129)
    parser.add_argument("--infer-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cfg-scale", type=float, default=1.0)
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--flow-shift", type=float, default=None, help="Override the mode default flow shift")
    parser.add_argument("--use-cpu-offload", action="store_true")
    parser.add_argument("--lora-path", default=None, help="LoRA weight path for mode=lora")
    parser.add_argument("--lora-scale", type=float, default=1.0)
    parser.add_argument("--ulysses-degree", type=int, default=1)
    parser.add_argument("--ring-degree", type=int, default=1)
    parser.add_argument("--allow-resize-for-sp", action="store_true", help="Set ALLOW_RESIZE_FOR_SP=1 for xDiT runs")
    parser.add_argument("--execute", action="store_true", help="Actually run the command instead of printing it")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it (default behavior)")
    args = parser.parse_args()

    if args.mode == "lora" and not args.lora_path:
        parser.error("--lora-path is required when --mode lora")
    if args.mode != "lora" and args.lora_path:
        # Allow the user to pass it, but only keep it for lora mode.
        pass

    cmd, env = build_command(args)
    repo_root = Path(args.repo_root).resolve()

    print(_shell_quote(cmd))
    if env:
        for key, value in env.items():
            print(f"{key}={value}")

    if not args.execute:
        return 0

    merged_env = os.environ.copy()
    merged_env.update(env)
    subprocess.run(cmd, cwd=str(repo_root), env=merged_env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
