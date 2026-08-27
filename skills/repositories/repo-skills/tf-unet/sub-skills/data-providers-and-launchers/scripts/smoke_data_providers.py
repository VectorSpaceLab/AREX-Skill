#!/usr/bin/env python3
"""Validate tf_unet data-provider contracts on synthetic fixtures."""

from __future__ import annotations

import argparse
import pathlib
import tempfile

import numpy as np
from PIL import Image

from tf_unet import image_gen
from tf_unet.image_util import ImageDataProvider, SimpleDataProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny tf_unet data-provider smoke.")
    parser.add_argument("--size", type=int, default=32, help="Synthetic image size for the toy generators.")
    parser.add_argument("--border", type=int, default=5, help="Toy-generator border that keeps the smoke tiny.")
    return parser.parse_args()


def make_simple_provider(size: int) -> SimpleDataProvider:
    grid = np.linspace(0.0, 1.0, size, dtype=np.float32)
    base_a = np.outer(grid, grid).astype(np.float32)
    base_b = np.outer(grid[::-1], grid).astype(np.float32)
    data = np.stack([base_a, base_b], axis=0)[..., np.newaxis]

    labels = np.zeros((2, size, size, 3), dtype=np.float32)

    mask_a = np.zeros((size, size), dtype=bool)
    mask_a[size // 4 : size // 2, size // 4 : size // 2] = True
    labels[0, ..., 0] = (~mask_a).astype(np.float32)
    labels[0, ..., 1] = mask_a.astype(np.float32)

    mask_b = np.zeros((size, size), dtype=bool)
    mask_b[size // 3 : (2 * size) // 3, size // 3 : (2 * size) // 3] = True
    labels[1, ..., 0] = (~mask_b).astype(np.float32)
    labels[1, ..., 2] = mask_b.astype(np.float32)

    return SimpleDataProvider(data, labels)


def write_image_pair(root: pathlib.Path) -> None:
    data = np.zeros((16, 16), dtype=np.uint8)
    data[4:12, 4:12] = 200

    mask = np.zeros((16, 16), dtype=np.uint8)
    mask[6:10, 6:10] = 255

    Image.fromarray(data).save(root / "sample.tif")
    Image.fromarray(mask).save(root / "sample_mask.tif")


def main() -> int:
    args = parse_args()

    simple = make_simple_provider(args.size)
    x_simple, y_simple = simple(1)
    print(f"simple-shape: {x_simple.shape} {y_simple.shape} {simple.channels} {simple.n_class}")

    gray = image_gen.GrayScaleDataProvider(args.size, args.size, cnt=1, border=args.border)
    x_gray, y_gray = gray(1)
    print(f"gray-shape: {x_gray.shape} {y_gray.shape} {gray.channels} {gray.n_class}")

    rgb = image_gen.RgbDataProvider(args.size, args.size, cnt=1, border=args.border)
    x_rgb, y_rgb = rgb(1)
    print(f"rgb-shape: {x_rgb.shape} {y_rgb.shape} {rgb.channels} {rgb.n_class}")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        write_image_pair(root)
        image_provider = ImageDataProvider(str(root / "*.tif"), shuffle_data=False)
        x_image, y_image = image_provider(1)
        print(f"image-shape: {x_image.shape} {y_image.shape} {image_provider.channels} {image_provider.n_class}")

    print("tf_unet data-provider smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
