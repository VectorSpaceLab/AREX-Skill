#!/usr/bin/env python3
"""Write a local Canny preview image without downloading or running a model."""

from __future__ import annotations

import argparse
from pathlib import Path


def _threshold(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("threshold must be an integer") from exc
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("threshold must be in the range 0..255")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read an image, optionally resize it down to a multiple of 8, and "
            "write a three-channel Canny preview/control image."
        )
    )
    parser.add_argument("--input_image", required=True, help="input image path")
    parser.add_argument("--output_image", required=True, help="output preview path")
    parser.add_argument(
        "--low_threshold",
        "--low-threshold",
        dest="low_threshold",
        type=_threshold,
        default=100,
        help="Canny low threshold (default: 100)",
    )
    parser.add_argument(
        "--high_threshold",
        "--high-threshold",
        dest="high_threshold",
        type=_threshold,
        default=200,
        help="Canny high threshold (default: 200)",
    )
    parser.add_argument(
        "--invert-preview",
        action="store_true",
        help="invert the preview so edges appear dark on a light background",
    )
    parser.add_argument(
        "--resize-multiple-of-8",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="resize the input down to dimensions divisible by 8 before Canny",
    )
    return parser


def _check_thresholds(low: int, high: int, parser: argparse.ArgumentParser) -> None:
    if low >= high:
        parser.error("Canny low threshold must be lower than high threshold")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _check_thresholds(args.low_threshold, args.high_threshold, parser)

    input_path = Path(args.input_image)
    output_path = Path(args.output_image)
    if not input_path.exists():
        parser.error(f"input image not found: {input_path}")

    try:
        import cv2
    except Exception as exc:  # pragma: no cover - import depends on environment
        parser.error(f"opencv import failed: {exc}")

    try:
        from PIL import Image
        import numpy as np
    except Exception as exc:  # pragma: no cover - import depends on environment
        parser.error(f"image-processing import failed: {exc}")

    with Image.open(input_path) as image:
        image = image.convert("RGB")
        if args.resize_multiple_of_8:
            new_width = image.width - image.width % 8
            new_height = image.height - image.height % 8
            if new_width <= 0 or new_height <= 0:
                parser.error(
                    "input image would round down to a zero dimension; use at "
                    "least 8 pixels in width and height"
                )
            if new_width != image.width or new_height != image.height:
                image = image.resize((new_width, new_height), Image.LANCZOS)
        image_np = np.array(image)

    canny = cv2.Canny(image_np, args.low_threshold, args.high_threshold)
    canny_rgb = np.repeat(canny[:, :, None], 3, axis=2)
    if args.invert_preview:
        canny_rgb = 255 - canny_rgb

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canny_rgb).save(output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
