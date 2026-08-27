#!/usr/bin/env python3
"""Estimate Skywork-R1V image tile grids without loading ML libraries."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, Iterable, Optional, Tuple


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def target_ratios(min_num: int, max_num: int) -> Iterable[Tuple[int, int]]:
    ratios = {
        (i, j)
        for n in range(min_num, max_num + 1)
        for i in range(1, n + 1)
        for j in range(1, n + 1)
        if min_num <= i * j <= max_num
    }
    return sorted(ratios, key=lambda pair: (pair[0] * pair[1], pair[0], pair[1]))


def find_closest_aspect_ratio(
    aspect_ratio: float,
    ratios: Iterable[Tuple[int, int]],
    width: int,
    height: int,
    image_size: int,
) -> Tuple[int, int]:
    best_ratio_diff = float("inf")
    best_ratio = (1, 1)
    area = width * height
    for ratio in ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def estimate_grid(
    width: int,
    height: int,
    min_num: int,
    max_num: int,
    image_size: int,
    thumbnail: bool,
) -> Dict[str, object]:
    aspect_ratio = width / height
    columns, rows = find_closest_aspect_ratio(
        aspect_ratio,
        target_ratios(min_num, max_num),
        width,
        height,
        image_size,
    )
    blocks = columns * rows
    thumbnail_added = bool(thumbnail and blocks != 1)
    total_patches = blocks + (1 if thumbnail_added else 0)
    return {
        "algorithm": "skywork-r1v-dynamic-preprocess-estimate",
        "aspect_ratio": aspect_ratio,
        "grid": {
            "blocks": blocks,
            "columns": columns,
            "rows": rows,
            "target_aspect_ratio": columns / rows,
        },
        "image_size": image_size,
        "input": {
            "height": height,
            "width": width,
        },
        "max_num": max_num,
        "min_num": min_num,
        "thumbnail_added": thumbnail_added,
        "thumbnail_requested": bool(thumbnail),
        "total_patches": total_patches,
    }


def read_image_size(path: str) -> Tuple[int, int]:
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional Pillow
        raise RuntimeError("Pillow is required for --image; use --width/--height instead") from exc

    try:
        with Image.open(path) as image:
            return image.size
    except Exception as exc:
        raise RuntimeError(f"Could not read image size for {path!r}: {exc}") from exc


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate Skywork-R1V dynamic image tile grid and patch count without torch/model downloads.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--image", help="Optional image file to inspect with Pillow.")
    parser.add_argument("--width", type=positive_int, help="Image width in pixels when --image is not used.")
    parser.add_argument("--height", type=positive_int, help="Image height in pixels when --image is not used.")
    parser.add_argument("--min-num", type=positive_int, default=1, help="Minimum number of tiles to consider.")
    parser.add_argument("--max-num", type=positive_int, default=12, help="Maximum number of tiles to consider.")
    parser.add_argument("--image-size", type=positive_int, default=448, help="Native square tile size.")
    parser.add_argument("--thumbnail", action="store_true", help="Add the native thumbnail patch when grid has more than one tile.")
    args = parser.parse_args(argv)

    if args.image and (args.width is not None or args.height is not None):
        parser.error("Use either --image or --width/--height, not both")
    if not args.image and (args.width is None or args.height is None):
        parser.error("Provide --image or both --width and --height")
    if args.min_num > args.max_num:
        parser.error("--min-num must be <= --max-num")
    return args


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if args.image:
        try:
            width, height = read_image_size(args.image)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        width, height = args.width, args.height

    result = estimate_grid(width, height, args.min_num, args.max_num, args.image_size, args.thumbnail)
    if args.image:
        result["input"]["source"] = "image"
        result["input"]["path"] = args.image
    else:
        result["input"]["source"] = "dimensions"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
