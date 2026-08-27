#!/usr/bin/env python3
"""Inspect a Pillow-readable image and optionally write a thumbnail.

Examples:
    python inspect_image.py input.png
    python inspect_image.py input.png --thumbnail thumb.jpg --max-size 256 256 --format JPEG
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report basic Pillow image facts and optionally write an "
            "aspect-preserving thumbnail. Uses installed Pillow only."
        ),
        epilog=(
            "Tiny fixture idea: create a 2x2 PNG with Pillow, then run this "
            "script against it to confirm mode, size, and thumbnail behavior."
        ),
    )
    parser.add_argument("image", help="Path to the input image to inspect.")
    parser.add_argument(
        "--thumbnail",
        metavar="PATH",
        help="Optional output path for an aspect-preserving thumbnail.",
    )
    parser.add_argument(
        "--max-size",
        nargs=2,
        type=int,
        default=(128, 128),
        metavar=("WIDTH", "HEIGHT"),
        help="Maximum thumbnail size. Default: 128 128.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        help="Optional explicit thumbnail format, useful for extensionless paths.",
    )
    parser.add_argument(
        "--strict-bombs",
        action="store_true",
        help="Treat Pillow DecompressionBombWarning as an error.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text summary.",
    )
    return parser.parse_args()


def validate_size(size: tuple[int, int]) -> tuple[int, int]:
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("--max-size values must be positive integers")
    return width, height


def load_pillow() -> tuple[Any, type[Exception]]:
    try:
        from PIL import Image, UnidentifiedImageError
    except ModuleNotFoundError as exc:
        if exc.name == "PIL":
            raise RuntimeError("Pillow is required for image inspection") from exc
        raise
    return Image, UnidentifiedImageError


def inspect_image(args: argparse.Namespace) -> dict[str, object]:
    Image, _ = load_pillow()
    max_size = validate_size(tuple(args.max_size))
    input_path = Path(args.image)

    if args.strict_bombs:
        warnings.simplefilter("error", Image.DecompressionBombWarning)

    with Image.open(input_path) as im:
        facts: dict[str, object] = {
            "path": str(input_path),
            "format": im.format,
            "mode": im.mode,
            "size": list(im.size),
            "width": im.width,
            "height": im.height,
            "bands": list(im.getbands()),
            "animated": bool(getattr(im, "is_animated", False)),
            "frames": getattr(im, "n_frames", 1),
        }

        if args.thumbnail:
            thumb = im.copy()
            thumb.thumbnail(max_size, Image.Resampling.LANCZOS)
            output_path = Path(args.thumbnail)
            save_kwargs = {}
            if args.output_format:
                save_kwargs["format"] = args.output_format
            thumb.save(output_path, **save_kwargs)
            facts["thumbnail"] = {
                "path": str(output_path),
                "size": list(thumb.size),
                "format": args.output_format or output_path.suffix.lstrip(".").upper() or None,
            }

    return facts


def print_text(facts: dict[str, object]) -> None:
    print(f"path: {facts['path']}")
    print(f"format: {facts['format']}")
    print(f"mode: {facts['mode']}")
    print(f"size: {facts['width']}x{facts['height']}")
    print(f"bands: {', '.join(facts['bands'])}")
    print(f"animated: {facts['animated']}")
    print(f"frames: {facts['frames']}")
    thumbnail = facts.get("thumbnail")
    if isinstance(thumbnail, dict):
        width, height = thumbnail["size"]
        print(f"thumbnail: {thumbnail['path']} ({width}x{height})")


def main() -> int:
    args = parse_args()
    try:
        Image, UnidentifiedImageError = load_pillow()
        facts = inspect_image(args)
    except RuntimeError as exc:
        print(f"inspect_image.py: error: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, OSError, ValueError, Image.DecompressionBombWarning, UnidentifiedImageError) as exc:
        print(f"inspect_image.py: error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(facts, indent=2, sort_keys=True))
    else:
        print_text(facts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
