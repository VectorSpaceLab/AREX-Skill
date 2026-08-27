#!/usr/bin/env python3
"""Validate and print an img2img-turbo CycleGAN-Turbo inference command.

This helper is intentionally safe: it does not import torch, instantiate the
model, download checkpoints, read images, or run inference. It mirrors the
source CLI's user-facing arguments and adds preflight validation for common
assertion-prone combinations.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List

PRETRAINED_NAMES = (
    "day_to_night",
    "night_to_day",
    "clear_to_rainy",
    "rainy_to_clear",
)

IMAGE_PREP_CHOICES = (
    "resize_512x512",
    "resize_512",
    "resized_crop_512",
    "resize_256x256",
    "resize_256",
    "resize_286_randomcrop_256x256_hflip",
    "no_resize",
)

DIRECTIONS = ("a2b", "b2a")


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate CycleGAN-Turbo unpaired inference arguments and print "
            "the source-checkout command without running the model."
        )
    )
    parser.add_argument(
        "--source_root",
        default=".",
        help="Source checkout directory to cd into in the printed command (default: current directory).",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python command name to print before src/inference_unpaired.py (default: python).",
    )
    parser.add_argument("--input_image", required=True, help="Path to the input image to translate.")
    parser.add_argument(
        "--model_name",
        choices=PRETRAINED_NAMES,
        default=None,
        help="Known pretrained CycleGAN-Turbo model name.",
    )
    parser.add_argument(
        "--model_path",
        default=None,
        help="Path to a custom CycleGAN-Turbo checkpoint state dict.",
    )
    parser.add_argument(
        "--output_dir",
        default="output",
        help="Directory where the source script will save the output (default: output).",
    )
    parser.add_argument(
        "--image_prep",
        default="resize_512x512",
        choices=IMAGE_PREP_CHOICES,
        help="Image preparation method accepted by build_transform.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Target-domain prompt. Required for --model_path and forbidden for --model_name.",
    )
    parser.add_argument(
        "--direction",
        choices=DIRECTIONS,
        default=None,
        help="Custom checkpoint direction. Required for --model_path and forbidden for --model_name.",
    )
    parser.add_argument(
        "--use_fp16",
        action="store_true",
        help="Include --use_fp16 in the printed source command.",
    )
    parser.add_argument(
        "--command_only",
        action="store_true",
        help="print only the shell command, without explanatory comments",
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    selectors = [args.model_name is not None, args.model_path is not None]
    if sum(selectors) != 1:
        parser.error("provide exactly one of --model_name or --model_path")

    if args.model_name is not None:
        if args.prompt is not None:
            parser.error("do not pass --prompt with a pretrained --model_name; the model supplies its caption")
        if args.direction is not None:
            parser.error("do not pass --direction with a pretrained --model_name; the model supplies its direction")

    if args.model_path is not None:
        if args.prompt is None or not args.prompt.strip():
            parser.error("--prompt is required when using --model_path")
        if args.direction is None:
            parser.error("--direction a2b|b2a is required when using --model_path")


def build_source_command(args: argparse.Namespace) -> List[str]:
    command = [
        args.python,
        "src/inference_unpaired.py",
        "--input_image",
        args.input_image,
        "--output_dir",
        args.output_dir,
        "--image_prep",
        args.image_prep,
    ]

    if args.model_name is not None:
        command.extend(["--model_name", args.model_name])
    else:
        command.extend(["--model_path", args.model_path])
        command.extend(["--prompt", args.prompt])
        command.extend(["--direction", args.direction])

    if args.use_fp16:
        command.append("--use_fp16")

    return command


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    cd_prefix = ["cd", args.source_root]
    command = build_source_command(args)
    if not args.command_only:
        print("# Planned CycleGAN-Turbo unpaired inference command; model is not run by this helper.")
        print("# Run only from a prepared source checkout with CUDA and any approved checkpoint downloads.")
    print(f"{quote_command(cd_prefix)} && {quote_command(command)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
