#!/usr/bin/env python3
"""Create a deterministic tiny LR/HR/SR PNG fixture.

The script writes matching lr_<L>, hr_<R>, and sr_<L>_<R> directories with a
few RGB PNGs. It is safe by default: it refuses to overwrite a non-empty output
directory unless --overwrite is passed.

Example:
    python scripts/prepare_tiny_dataset.py \
        --out ./tiny_fixture \
        --l-resolution 16 \
        --r-resolution 128 \
        --count 3
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Sequence, Tuple

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - exercised only when Pillow is missing.
    raise SystemExit(
        "Pillow is required for this helper. Install the package that provides PIL, then rerun."
    ) from exc

try:
    RESAMPLE_BICUBIC = Image.Resampling.BICUBIC
except AttributeError:  # pragma: no cover - older Pillow fallback.
    RESAMPLE_BICUBIC = Image.BICUBIC


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def prepare_output_root(root: Path, overwrite: bool) -> None:
    if root.exists():
        if root.is_file():
            if not overwrite:
                raise SystemExit(f"{root} already exists as a file; pass --overwrite to replace it.")
            root.unlink()
        elif any(root.iterdir()):
            if not overwrite:
                raise SystemExit(
                    f"{root} already exists and is not empty; pass --overwrite to replace it."
                )
            shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)


def make_pattern_image(size: int, index: int) -> Image.Image:
    image = Image.new("RGB", (size, size))
    pixels = image.load()
    denom = max(1, size - 1)
    for y in range(size):
        y_ratio = (y * 255) // denom
        for x in range(size):
            x_ratio = (x * 255) // denom
            pixels[x, y] = (
                (x_ratio + index * 41) % 256,
                (y_ratio + index * 73) % 256,
                ((x_ratio // 2 + y_ratio // 2) + index * 109) % 256,
            )
    return image


def make_triplet(index: int, l_resolution: int, r_resolution: int) -> Tuple[Image.Image, Image.Image, Image.Image]:
    hr_image = make_pattern_image(r_resolution, index)
    lr_image = hr_image.resize((l_resolution, l_resolution), RESAMPLE_BICUBIC)
    sr_image = lr_image.resize((r_resolution, r_resolution), RESAMPLE_BICUBIC)
    return lr_image, hr_image, sr_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a small RGB dataset tree that matches the SR triplet layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--out", required=True, type=Path, help="Output root to create.")
    parser.add_argument(
        "--l-resolution",
        required=True,
        type=positive_int,
        help="Low-resolution size used in lr_<L> and sr_<L>_<R>.",
    )
    parser.add_argument(
        "--r-resolution",
        required=True,
        type=positive_int,
        help="High-resolution size used in hr_<R> and sr_<L>_<R>.",
    )
    parser.add_argument(
        "--count",
        type=positive_int,
        default=3,
        help="Number of PNG triplets to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty output root.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.l_resolution >= args.r_resolution:
        raise SystemExit("expected --l-resolution to be smaller than --r-resolution")

    prepare_output_root(args.out, args.overwrite)

    lr_dir = args.out / f"lr_{args.l_resolution}"
    hr_dir = args.out / f"hr_{args.r_resolution}"
    sr_dir = args.out / f"sr_{args.l_resolution}_{args.r_resolution}"
    for directory in (lr_dir, hr_dir, sr_dir):
        directory.mkdir(parents=True, exist_ok=True)

    for index in range(args.count):
        lr_image, hr_image, sr_image = make_triplet(index, args.l_resolution, args.r_resolution)
        filename = f"{index:05d}.png"
        lr_image.save(lr_dir / filename, format="PNG")
        hr_image.save(hr_dir / filename, format="PNG")
        sr_image.save(sr_dir / filename, format="PNG")

    print(
        f"created {args.count} RGB PNG triplets under {args.out} "
        f"(lr_{args.l_resolution}, hr_{args.r_resolution}, sr_{args.l_resolution}_{args.r_resolution})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
