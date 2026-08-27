#!/usr/bin/env python3
"""Convert one local image to PNG without accidental replacement."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a local image to PNG with Pillow. The input is never a "
            "URL; an existing output is protected unless --overwrite is used."
        )
    )
    parser.add_argument("input", type=Path, help="local image path")
    parser.add_argument("--output", required=True, type=Path, help="explicit PNG output path")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output explicitly")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser()
    destination = args.output.expanduser()
    try:
        if not source.is_file():
            raise FileNotFoundError(f"input is not a regular file: {source}")
        if destination.suffix.lower() != ".png":
            raise ValueError("--output must have a .png suffix")
        if source.resolve() == destination.resolve():
            raise ValueError("input and output must be different paths")
        if destination.exists() and not args.overwrite:
            raise FileExistsError(
                f"output exists: {destination}; choose another path or pass --overwrite"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image.save(destination, format="PNG")
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        print(f"error: conversion failed: {exc}", file=sys.stderr)
        return 1

    print(f"saved={destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
