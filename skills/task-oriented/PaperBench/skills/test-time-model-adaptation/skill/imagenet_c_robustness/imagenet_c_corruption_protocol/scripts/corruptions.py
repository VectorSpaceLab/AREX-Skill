#!/usr/bin/env python3
"""Deterministic ImageNet-C-style corruption helpers for reduced recovery."""
from __future__ import annotations

import argparse
import json
import math
import random
from typing import Iterable, List

CORRUPTIONS = {
    "gaussian_noise",
    "shot_noise",
    "defocus_blur",
    "brightness",
    "contrast",
    "pixelate",
    "jpeg_compression_proxy",
}


def _validate_image(image: List[List[List[float]]]) -> None:
    if not image or not image[0] or not image[0][0]:
        raise ValueError("image must be a non-empty HxWxC array")
    channels = len(image[0][0])
    for row in image:
        if len(row) != len(image[0]):
            raise ValueError("all rows must have the same width")
        for pixel in row:
            if len(pixel) != channels:
                raise ValueError("all pixels must have the same channel count")
            for value in pixel:
                if value < 0.0 or value > 1.0:
                    raise ValueError("image values must be in [0, 1]")


def _clip(value: float) -> float:
    return min(1.0, max(0.0, value))


def _map_pixels(image: List[List[List[float]]], fn) -> List[List[List[float]]]:
    return [[[ _clip(fn(value, y, x, c)) for c, value in enumerate(pixel)] for x, pixel in enumerate(row)] for y, row in enumerate(image)]


def _box_blur(image: List[List[List[float]]], radius: int) -> List[List[List[float]]]:
    height = len(image)
    width = len(image[0])
    channels = len(image[0][0])
    out = []
    for y in range(height):
        row = []
        for x in range(width):
            pixel = []
            for c in range(channels):
                values = []
                for yy in range(max(0, y - radius), min(height, y + radius + 1)):
                    for xx in range(max(0, x - radius), min(width, x + radius + 1)):
                        values.append(image[yy][xx][c])
                pixel.append(sum(values) / len(values))
            row.append(pixel)
        out.append(row)
    return out


def _down_up_sample(image: List[List[List[float]]], block: int) -> List[List[List[float]]]:
    height = len(image)
    width = len(image[0])
    channels = len(image[0][0])
    out = [[[0.0 for _ in range(channels)] for _ in range(width)] for _ in range(height)]
    for y0 in range(0, height, block):
        for x0 in range(0, width, block):
            coords = [(y, x) for y in range(y0, min(height, y0 + block)) for x in range(x0, min(width, x0 + block))]
            means = [sum(image[y][x][c] for y, x in coords) / len(coords) for c in range(channels)]
            for y, x in coords:
                out[y][x] = list(means)
    return out


def mean_abs_difference(a: List[List[List[float]]], b: List[List[List[float]]]) -> float:
    total = 0.0
    count = 0
    for row_a, row_b in zip(a, b):
        for pixel_a, pixel_b in zip(row_a, row_b):
            for value_a, value_b in zip(pixel_a, pixel_b):
                total += abs(value_a - value_b)
                count += 1
    return total / count if count else 0.0


def apply_corruption(image: List[List[List[float]]], corruption: str, severity: int, seed: int = 0) -> dict:
    _validate_image(image)
    if corruption not in CORRUPTIONS:
        raise ValueError(f"unknown corruption: {corruption}")
    if severity not in {1, 2, 3, 4, 5}:
        raise ValueError("severity must be an integer from 1 to 5")
    rng = random.Random(seed + severity * 1009 + sum(ord(ch) for ch in corruption))

    if corruption == "gaussian_noise":
        sigma = 0.04 * severity
        corrupted = _map_pixels(image, lambda value, *_: value + rng.gauss(0.0, sigma))
    elif corruption == "shot_noise":
        scale = 35.0 / severity
        corrupted = _map_pixels(image, lambda value, *_: rng.gauss(value, math.sqrt(max(value, 0.001) / scale)))
    elif corruption == "defocus_blur":
        corrupted = _box_blur(image, radius=max(1, severity // 2))
    elif corruption == "brightness":
        delta = 0.08 * severity
        corrupted = _map_pixels(image, lambda value, *_: value + delta)
    elif corruption == "contrast":
        factor = max(0.05, 1.0 - 0.15 * severity)
        corrupted = _map_pixels(image, lambda value, *_: 0.5 + factor * (value - 0.5))
    elif corruption == "pixelate":
        corrupted = _down_up_sample(image, block=severity + 1)
    else:
        levels = max(2, 18 - 3 * severity)
        corrupted = _map_pixels(image, lambda value, *_: round(value * (levels - 1)) / (levels - 1))

    metadata = {
        "corruption": corruption,
        "severity": severity,
        "seed": seed,
        "mean_abs_difference": mean_abs_difference(image, corrupted),
        "shape": [len(image), len(image[0]), len(image[0][0])],
    }
    return {"image": corrupted, "metadata": metadata}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file containing an HxWxC image array")
    parser.add_argument("--output", required=True)
    parser.add_argument("--corruption", required=True, choices=sorted(CORRUPTIONS))
    parser.add_argument("--severity", required=True, type=int)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        image = json.load(handle)
    result = apply_corruption(image, args.corruption, args.severity, args.seed)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
