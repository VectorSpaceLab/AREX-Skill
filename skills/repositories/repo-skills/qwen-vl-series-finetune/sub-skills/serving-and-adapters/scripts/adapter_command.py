#!/usr/bin/env python3
"""Build safe Qwen-VL merge and Gradio commands without running them by default."""

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


def build_merge(args: argparse.Namespace) -> list[str]:
    cmd = [
        "python",
        "src/merge_lora_weights.py",
        "--model-path",
        args.model_path,
        "--model-base",
        args.model_base,
        "--save-model-path",
        args.save_model_path,
    ]
    if args.safe_serialization:
        cmd.append("--safe-serialization")
    return cmd


def build_gradio(args: argparse.Namespace) -> list[str]:
    cmd = [
        "python",
        "-m",
        "src.serve.app",
        "--model-path",
        args.model_path,
        "--device",
        args.device,
        "--temperature",
        str(args.temperature),
        "--repetition-penalty",
        str(args.repetition_penalty),
        "--max-new-tokens",
        str(args.max_new_tokens),
    ]
    if args.model_base is not None:
        cmd.extend(["--model-base", args.model_base])
    if args.load_8bit:
        cmd.append("--load-8bit")
    if args.load_4bit:
        cmd.append("--load-4bit")
    if args.disable_flash_attention:
        cmd.append("--disable_flash_attention")
    if args.debug:
        cmd.append("--debug")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    merge = subparsers.add_parser("merge", help="Build a merge command")
    merge.add_argument("--model-path", required=True)
    merge.add_argument("--model-base", required=True)
    merge.add_argument("--save-model-path", required=True)
    merge.add_argument("--safe-serialization", action="store_true")
    merge.add_argument("--run", action="store_true")

    gradio = subparsers.add_parser("gradio", help="Build a Gradio launch command")
    gradio.add_argument("--model-path", required=True)
    gradio.add_argument("--model-base", default=None)
    gradio.add_argument("--device", default="cuda")
    gradio.add_argument("--load-8bit", action="store_true")
    gradio.add_argument("--load-4bit", action="store_true")
    gradio.add_argument("--disable-flash-attention", action="store_true")
    gradio.add_argument("--temperature", type=float, default=0.0)
    gradio.add_argument("--repetition-penalty", type=float, default=1.0)
    gradio.add_argument("--max-new-tokens", type=int, default=1024)
    gradio.add_argument("--debug", action="store_true")
    gradio.add_argument("--run", action="store_true")

    args = parser.parse_args()
    if args.mode == "merge":
        cmd = build_merge(args)
    else:
        cmd = build_gradio(args)

    print(_format_shell_command(cmd))
    if getattr(args, "run", False):
        env = _run_env()
        return subprocess.call(_execution_command(cmd, env), cwd=str(_skill_root()), env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
