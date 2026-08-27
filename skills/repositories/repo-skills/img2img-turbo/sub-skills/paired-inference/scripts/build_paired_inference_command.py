#!/usr/bin/env python3
"""Validate Pix2Pix-Turbo paired inference args and print a source-checkout command.

This helper intentionally does not import the model, download checkpoints, or run
inference. It mirrors the safe argument contract for src/inference_paired.py.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

PRETRAINED_NAMES = ("edge_to_image", "sketch_to_image_stochastic")
DEFAULT_LOW_THRESHOLD = 100
DEFAULT_HIGH_THRESHOLD = 200
DEFAULT_GAMMA = 0.4
DEFAULT_SEED = 42
MAX_GRADIO_SEED = 2_147_483_647


def _nonempty(value: str) -> str:
    if value is None or not str(value).strip():
        raise argparse.ArgumentTypeError("value must be non-empty")
    return value


def _threshold(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("threshold must be an integer") from exc
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("threshold must be in the range 0..255")
    return parsed


def _gamma(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("gamma must be a float") from exc
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("gamma must be in the range 0..1")
    return parsed


def _seed(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seed must be an integer") from exc
    if not 0 <= parsed <= MAX_GRADIO_SEED:
        raise argparse.ArgumentTypeError(
            f"seed must be in the range 0..{MAX_GRADIO_SEED}"
        )
    return parsed


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate paired Pix2Pix-Turbo inference options and print the "
            "source-checkout command. The helper does not run the model."
        )
    )
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument(
        "--model_name",
        choices=PRETRAINED_NAMES,
        help="pretrained paired model selector",
    )
    selector.add_argument(
        "--model_path",
        type=_nonempty,
        help="custom Pix2Pix-Turbo checkpoint path for --model_path inference",
    )
    parser.add_argument(
        "--input_image",
        required=True,
        type=_nonempty,
        help="input image path as it will be seen from the source checkout",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        type=_nonempty,
        help="non-empty text prompt passed to Pix2Pix_Turbo.forward",
    )
    parser.add_argument(
        "--output_dir",
        default="output",
        type=_nonempty,
        help="source CLI output directory (default: output)",
    )
    parser.add_argument(
        "--low_threshold",
        "--low-threshold",
        dest="low_threshold",
        type=_threshold,
        default=None,
        help="Canny low threshold for edge_to_image (source default: 100)",
    )
    parser.add_argument(
        "--high_threshold",
        "--high-threshold",
        dest="high_threshold",
        type=_threshold,
        default=None,
        help="Canny high threshold for edge_to_image (source default: 200)",
    )
    parser.add_argument(
        "--gamma",
        type=_gamma,
        default=None,
        help="sketch stochastic guidance r/gamma in [0, 1] (source default: 0.4)",
    )
    parser.add_argument(
        "--seed",
        type=_seed,
        default=None,
        help="non-negative sketch stochastic seed (source default: 42)",
    )
    parser.add_argument(
        "--use_fp16",
        action="store_true",
        help="include source --use_fp16 flag",
    )
    parser.add_argument(
        "--source_root",
        default=".",
        type=_nonempty,
        help="source checkout directory to put after 'cd' in the printed command",
    )
    parser.add_argument(
        "--python",
        default="python",
        type=_nonempty,
        help="Python executable name for the printed command (default: python)",
    )
    parser.add_argument(
        "--strict_paths",
        action="store_true",
        help="treat missing input/model paths as errors instead of warnings",
    )
    parser.add_argument(
        "--command_only",
        action="store_true",
        help="print only the shell command, without explanatory comments",
    )
    return parser


def _path_for_check(source_root: str, user_path: str) -> Path:
    path = Path(user_path)
    if path.is_absolute():
        return path
    return Path(source_root) / path


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    low_was_set = args.low_threshold is not None
    high_was_set = args.high_threshold is not None
    gamma_was_set = args.gamma is not None
    seed_was_set = args.seed is not None

    if (low_was_set or high_was_set):
        low = args.low_threshold if low_was_set else DEFAULT_LOW_THRESHOLD
        high = args.high_threshold if high_was_set else DEFAULT_HIGH_THRESHOLD
        if low >= high:
            parser.error("Canny low threshold must be lower than high threshold")

    check_input = _path_for_check(args.source_root, args.input_image)
    if check_input.exists():
        try:
            from PIL import Image
        except Exception as exc:  # pragma: no cover - depends on caller env
            _warn(f"could not import Pillow to inspect image size: {exc}")
        else:
            try:
                with Image.open(check_input) as image:
                    width, height = image.size
            except Exception as exc:
                if args.strict_paths:
                    parser.error(f"could not open input image for inspection: {exc}")
                _warn(f"could not inspect input image dimensions: {exc}")
            else:
                new_width = width - (width % 8)
                new_height = height - (height % 8)
                if new_width <= 0 or new_height <= 0:
                    parser.error(
                        "input image would round down to a zero dimension; "
                        "use at least 8 pixels in width and height"
                    )
                if new_width != width or new_height != height:
                    _warn(
                        "source script will resize input from "
                        f"{width}x{height} to {new_width}x{new_height} "
                        "to make dimensions divisible by 8"
                    )
    else:
        message = (
            f"input image not found for inspection at {check_input}; "
            "printed command may still be valid in the target source checkout"
        )
        if args.strict_paths:
            parser.error(message)
        _warn(message)

    if args.model_path:
        check_model = _path_for_check(args.source_root, args.model_path)
        if not check_model.exists():
            message = (
                f"model checkpoint not found at {check_model}; "
                "printed command may still be valid after training/download"
            )
            if args.strict_paths:
                parser.error(message)
            _warn(message)

    if args.model_name == "edge_to_image":
        if gamma_was_set or seed_was_set:
            _warn("--gamma/--seed are ignored by the source edge_to_image branch")
    elif args.model_name == "sketch_to_image_stochastic":
        if low_was_set or high_was_set:
            _warn("Canny thresholds are ignored by the source sketch branch")
    elif args.model_path:
        if low_was_set or high_was_set or gamma_was_set or seed_was_set:
            _warn(
                "Canny thresholds and stochastic gamma/seed are ignored by the "
                "source custom-checkpoint branch"
            )


def shell_join(parts: list[str]) -> str:
    return " ".join(part if part == "&&" else shlex.quote(str(part)) for part in parts)


def build_command(args: argparse.Namespace) -> str:
    parts = [
        "cd",
        args.source_root,
        "&&",
        args.python,
        "src/inference_paired.py",
        "--input_image",
        args.input_image,
        "--prompt",
        args.prompt,
        "--output_dir",
        args.output_dir,
    ]

    if args.model_name:
        parts.extend(["--model_name", args.model_name])
    else:
        parts.extend(["--model_path", args.model_path])

    if args.model_name == "edge_to_image":
        parts.extend(
            [
                "--low_threshold",
                str(args.low_threshold if args.low_threshold is not None else DEFAULT_LOW_THRESHOLD),
                "--high_threshold",
                str(args.high_threshold if args.high_threshold is not None else DEFAULT_HIGH_THRESHOLD),
            ]
        )
    elif args.model_name == "sketch_to_image_stochastic":
        parts.extend(
            [
                "--gamma",
                str(args.gamma if args.gamma is not None else DEFAULT_GAMMA),
                "--seed",
                str(args.seed if args.seed is not None else DEFAULT_SEED),
            ]
        )

    if args.use_fp16:
        parts.append("--use_fp16")

    return shell_join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    command = build_command(args)
    if not args.command_only:
        print("# Planned Pix2Pix-Turbo paired inference command; model is not run by this helper.")
        print("# Run only from a prepared source checkout with CUDA and approved model downloads.")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
