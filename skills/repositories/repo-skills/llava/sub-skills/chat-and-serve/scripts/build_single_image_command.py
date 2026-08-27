#!/usr/bin/env python3
"""Print a safe LLaVA single-image command template.

The script only builds commands; it never downloads models or runs inference.
It accepts either the one-shot `llava.eval.run_llava` path or the interactive
`llava.serve.cli` path.
"""

from __future__ import annotations

import argparse
import shlex
import sys


def build_run_llava(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "llava.eval.run_llava",
        "--model-path",
        args.model_path,
        "--image-file",
        args.image_file,
        "--query",
        args.query,
        "--temperature",
        str(args.temperature),
        "--num_beams",
        str(args.num_beams),
        "--max_new_tokens",
        str(args.max_new_tokens),
    ]
    if args.model_base:
        cmd += ["--model-base", args.model_base]
    if args.conv_mode:
        cmd += ["--conv-mode", args.conv_mode]
    if args.top_p is not None:
        cmd += ["--top_p", str(args.top_p)]
    return cmd


def build_cli(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "llava.serve.cli",
        "--model-path",
        args.model_path,
        "--image-file",
        args.image_file,
        "--device",
        args.device,
        "--temperature",
        str(args.temperature),
        "--max-new-tokens",
        str(args.max_new_tokens),
    ]
    if args.model_base:
        cmd += ["--model-base", args.model_base]
    if args.conv_mode:
        cmd += ["--conv-mode", args.conv_mode]
    if args.load_8bit:
        cmd.append("--load-8bit")
    if args.load_4bit:
        cmd.append("--load-4bit")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe LLaVA single-image command.")
    parser.add_argument("--mode", choices=["run-llava", "cli"], default="run-llava")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--image-file", required=True)
    parser.add_argument("--query", default="What is in this image?")
    parser.add_argument("--model-base")
    parser.add_argument("--conv-mode")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, dest="top_p")
    parser.add_argument("--num-beams", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--load-8bit", action="store_true")
    parser.add_argument("--load-4bit", action="store_true")
    args = parser.parse_args()

    if args.load_8bit and args.load_4bit:
        parser.error("--load-8bit and --load-4bit are mutually exclusive")

    if args.mode == "run-llava":
        cmd = build_run_llava(args)
    else:
        cmd = build_cli(args)

    print(shlex.join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
