#!/usr/bin/env python3
"""Reshape one MNIST CSV row into a 28x28x1 Python list literal.

Input format: label,pixel0,pixel1,...,pixel783
Output format: nested list suitable for saved-model style input expressions.
"""

import argparse
import sys


def _parse_csv_row(line):
    try:
        values = [int(part.strip()) for part in line.strip().split(",") if part.strip() != ""]
    except ValueError as exc:
        raise ValueError("MNIST row must contain only integer label/pixel values") from exc

    if len(values) < 2:
        raise ValueError("MNIST row must contain one label followed by pixel values")
    return values[0], values[1:]


def _reshape_pixels(pixels, shape):
    height, width, channels = shape
    expected = height * width * channels
    if len(pixels) != expected:
        raise ValueError(f"expected {expected} pixels for shape {shape}, got {len(pixels)}")

    result = []
    index = 0
    for _ in range(height):
        row = []
        for _ in range(width):
            cell = pixels[index:index + channels]
            index += channels
            row.append(cell)
        result.append(row)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert one MNIST CSV row into a 28x28x1 list literal."
    )
    parser.add_argument(
        "--line",
        help="CSV row to reshape. If omitted, one line is read from stdin.",
    )
    parser.add_argument(
        "--shape",
        nargs=3,
        type=int,
        default=(28, 28, 1),
        metavar=("HEIGHT", "WIDTH", "CHANNELS"),
        help="Image shape after removing the label. Default: 28 28 1.",
    )
    args = parser.parse_args(argv)

    line = args.line if args.line is not None else sys.stdin.readline()
    if not line:
        print("mnist_reshape: expected a CSV row on stdin or via --line", file=sys.stderr)
        return 2

    try:
        _, pixels = _parse_csv_row(line)
        image = _reshape_pixels(pixels, tuple(args.shape))
    except Exception as exc:
        print(f"mnist_reshape: {exc}", file=sys.stderr)
        return 1

    print(repr(image))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
