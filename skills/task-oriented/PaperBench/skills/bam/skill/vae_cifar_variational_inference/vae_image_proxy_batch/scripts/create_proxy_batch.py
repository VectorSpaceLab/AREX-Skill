#!/usr/bin/env python3
"""Create deterministic synthetic binary images for VAE recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _empty(height: int, width: int) -> list[list[float]]:
    return [[0.0 for _ in range(width)] for _ in range(height)]


def _pattern(index: int, height: int, width: int) -> list[list[float]]:
    image = _empty(height, width)
    mode = index % 6
    if mode == 0:
        row = index % height
        for col in range(width):
            image[row][col] = 1.0
    elif mode == 1:
        col = index % width
        for row in range(height):
            image[row][col] = 1.0
    elif mode == 2:
        for row in range(height):
            image[row][row % width] = 1.0
    elif mode == 3:
        for row in range(height):
            image[row][width - 1 - (row % width)] = 1.0
    elif mode == 4:
        for row in range(height):
            for col in range(width):
                image[row][col] = float((row + col + index) % 2 == 0)
    else:
        top = max(0, height // 4)
        bottom = min(height, height - top)
        left = max(0, width // 4)
        right = min(width, width - left)
        for row in range(top, bottom):
            for col in range(left, right):
                image[row][col] = 1.0
    return image


def create_batch(batch_size: int = 8, height: int = 8, width: int = 8, seed: int = 0) -> dict:
    if batch_size <= 0 or height <= 0 or width <= 0:
        raise ValueError("batch_size, height, and width must be positive")
    offset = seed % 6
    images = [[_pattern(offset + idx, height, width)] for idx in range(batch_size)]
    return {
        "dataset": "synthetic_binary_images",
        "split": "deterministic_tiny_batch_8x8" if (height, width) == (8, 8) else "deterministic_tiny_batch",
        "seed": seed,
        "shape": [batch_size, 1, height, width],
        "value_range": [0.0, 1.0],
        "synthetic_proxy": True,
        "images": images,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = create_batch(args.batch_size, args.height, args.width, args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "shape": payload["shape"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
