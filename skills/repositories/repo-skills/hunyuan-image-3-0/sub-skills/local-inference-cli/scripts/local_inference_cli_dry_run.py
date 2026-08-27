#!/usr/bin/env python3
"""Render and validate safe HunyuanImage-3 local CLI commands.

This helper never imports the model package and never launches generation.
It renders a command for the bundled `run_hunyuan_image_generation.py` runner
and reports warnings or errors for common local-inference issues.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shlex
import sys
from pathlib import Path


PROFILE_DEFAULTS = {
    "base": {
        "bot_task": "image",
        "image_size": "1024x1024",
        "verbose": 1,
        "attn_impl": "sdpa",
        "moe_impl": "eager",
        "diff_infer_steps": 50,
    },
    "instruct": {
        "bot_task": "think_recaption",
        "image_size": "auto",
        "use_system_prompt": "en_unified",
        "infer_align_image_size": True,
        "verbose": 2,
        "attn_impl": "sdpa",
        "moe_impl": "eager",
        "diff_infer_steps": 50,
    },
    "distil": {
        "bot_task": "think_recaption",
        "image_size": "auto",
        "use_system_prompt": "en_unified",
        "infer_align_image_size": True,
        "verbose": 2,
        "attn_impl": "sdpa",
        "moe_impl": "eager",
        "diff_infer_steps": 8,
    },
    "custom": {},
}


EDIT_TASKS = {"recaption", "think_recaption"}
ALLOWED_IMAGE_SIZE = re.compile(r"^(auto|\d+x\d+|\d+:\d+)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render or validate a safe HunyuanImage-3 local inference command "
            "without importing the model stack or launching generation."
        )
    )
    parser.add_argument("--profile", choices=tuple(PROFILE_DEFAULTS), default="custom")
    parser.add_argument("--model-id", required=True, help="Local checkpoint path used by the bundled generation runner")
    parser.add_argument("--prompt", required=True, help="Prompt to embed in the rendered command")
    parser.add_argument("--image", help="Optional comma-separated image list")
    parser.add_argument("--save", default="image.png", help="Output image path")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--image-size", dest="image_size")
    parser.add_argument("--bot-task", dest="bot_task")
    parser.add_argument("--use-system-prompt", dest="use_system_prompt")
    parser.add_argument("--system-prompt", dest="system_prompt")
    parser.add_argument("--max_new_tokens", type=int)
    parser.add_argument("--diff-infer-steps", dest="diff_infer_steps", type=int)
    parser.add_argument("--verbose", type=int)
    parser.add_argument("--attn-impl", dest="attn_impl", choices=("sdpa", "flash_attention_2"))
    parser.add_argument("--moe-impl", dest="moe_impl", choices=("eager", "flashinfer"))
    parser.add_argument("--reproduce", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--infer-align-image-size",
        dest="infer_align_image_size",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument("--use-taylor-cache", dest="use_taylor_cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument(
        "--taylor-cache-interval",
        dest="taylor_cache_interval",
        type=int,
    )
    parser.add_argument(
        "--taylor-cache-order",
        dest="taylor_cache_order",
        type=int,
    )
    parser.add_argument(
        "--taylor-cache-enable-first-enhance",
        dest="taylor_cache_enable_first_enhance",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--taylor-cache-first-enhance-steps",
        dest="taylor_cache_first_enhance_steps",
        type=int,
    )
    parser.add_argument(
        "--taylor-cache-enable-tailing-enhance",
        dest="taylor_cache_enable_tailing_enhance",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--taylor-cache-tailing-enhance-steps",
        dest="taylor_cache_tailing_enhance_steps",
        type=int,
    )
    parser.add_argument(
        "--taylor-cache-low-freqs-order",
        dest="taylor_cache_low_freqs_order",
        type=int,
    )
    parser.add_argument(
        "--taylor-cache-high-freqs-order",
        dest="taylor_cache_high_freqs_order",
        type=int,
    )
    parser.add_argument("--rewrite", action=argparse.BooleanOptionalAction, default=None)
    return parser


def apply_profile_defaults(args: argparse.Namespace) -> argparse.Namespace:
    defaults = PROFILE_DEFAULTS[args.profile]
    for key, value in defaults.items():
        if getattr(args, key) is None:
            setattr(args, key, value)
    return args


def split_images(image_arg: str | None) -> list[str]:
    if not image_arg:
        return []
    return [part.strip() for part in image_arg.split(",") if part.strip()]


def render_command(args: argparse.Namespace) -> list[str]:
    cmd: list[str] = ["python", "scripts/run_hunyuan_image_generation.py"]

    def add(flag: str, value: object | None) -> None:
        if value is None:
            return
        cmd.extend([flag, str(value)])

    add("--model-id", args.model_id)
    add("--prompt", args.prompt)
    add("--image", args.image)
    add("--save", args.save)
    add("--seed", args.seed)
    add("--image-size", args.image_size)
    add("--bot-task", args.bot_task)
    add("--use-system-prompt", args.use_system_prompt)
    add("--system-prompt", args.system_prompt)
    add("--max_new_tokens", args.max_new_tokens)
    add("--diff-infer-steps", args.diff_infer_steps)
    add("--verbose", args.verbose)
    add("--attn-impl", args.attn_impl)
    add("--moe-impl", args.moe_impl)
    if args.reproduce:
        cmd.append("--reproduce")
    if args.infer_align_image_size:
        cmd.append("--infer-align-image-size")
    if args.use_taylor_cache:
        cmd.append("--use-taylor-cache")
    add("--taylor-cache-interval", args.taylor_cache_interval)
    add("--taylor-cache-order", args.taylor_cache_order)
    if args.taylor_cache_enable_first_enhance:
        cmd.append("--taylor-cache-enable-first-enhance")
    add("--taylor-cache-first-enhance-steps", args.taylor_cache_first_enhance_steps)
    if args.taylor_cache_enable_tailing_enhance:
        cmd.append("--taylor-cache-enable-tailing-enhance")
    add("--taylor-cache-tailing-enhance-steps", args.taylor_cache_tailing_enhance_steps)
    add("--taylor-cache-low-freqs-order", args.taylor_cache_low_freqs_order)
    add("--taylor-cache-high-freqs-order", args.taylor_cache_high_freqs_order)
    if args.rewrite:
        cmd.extend(["--rewrite", "1"])
    return cmd


def warn(message: str, warnings: list[str]) -> None:
    warnings.append(message)


def validate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    if args.image_size is not None and not ALLOWED_IMAGE_SIZE.match(args.image_size):
        errors.append(
            "--image-size must be auto, a size like 1024x1024, or a ratio like 16:9"
        )

    if args.use_system_prompt == "custom" and not args.system_prompt:
        errors.append("--use-system-prompt custom requires --system-prompt")

    if args.bot_task in EDIT_TASKS and not args.image:
        errors.append(
            f"--bot-task {args.bot_task} expects one or more --image inputs"
        )

    if args.image and args.bot_task == "image":
        warn(
            "The documented editing flows use recaption or think_recaption; "
            "double-check that image conditioning is what you want.",
            warnings,
        )

    model_path = Path(args.model_id).expanduser()
    if not model_path.exists():
        warn(
            f"Checkpoint path '{args.model_id}' does not exist yet; the real CLI will fail until it does.",
            warnings,
        )
    if "." in model_path.name:
        warn(
            "Local checkpoint folder names with dots are risky; rename the directory to a dot-free local path.",
            warnings,
        )

    image_paths = split_images(args.image)
    for image_path in image_paths:
        if not Path(image_path).expanduser().exists():
            warn(
                f"Reference image '{image_path}' does not exist yet; the real CLI will fail until it does.",
                warnings,
            )
    if len(image_paths) > 3:
        warn(
            "The repo demos show up to three image inputs; larger sets are untested in this sub-skill.",
            warnings,
        )

    if args.infer_align_image_size is True and not image_paths:
        warn(
            "--infer-align-image-size has no effect without image inputs.",
            warnings,
        )

    if args.reproduce and args.seed is None:
        warn(
            "Reproduction is more useful with an explicit --seed.",
            warnings,
        )

    if args.rewrite:
        if not os.getenv("DEEPSEEK_KEY_ID") or not os.getenv("DEEPSEEK_KEY_SECRET"):
            errors.append(
                "--rewrite requires DEEPSEEK_KEY_ID and DEEPSEEK_KEY_SECRET"
            )
        warn(
            "DeepSeek rewrite is credential and network bound. The bundled runner includes --sys-deepseek-prompt, while the original source snapshot has a parser mismatch in this branch.",
            warnings,
        )

    if args.attn_impl == "flash_attention_2" and importlib.util.find_spec("flash_attn") is None:
        warn(
            "flash_attention_2 was requested but flash_attn is not importable in this environment.",
            warnings,
        )
    if args.moe_impl == "flashinfer" and importlib.util.find_spec("flashinfer") is None:
        warn(
            "flashinfer was requested but flashinfer is not importable in this environment.",
            warnings,
        )

    return warnings, errors


def format_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args = apply_profile_defaults(args)

    warnings, errors = validate(args)
    command = format_command(render_command(args))

    print("COMMAND:")
    print(command)

    if warnings:
        print("\nWARNINGS:")
        for message in warnings:
            print(f"- {message}")

    if errors:
        print("\nERRORS:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
