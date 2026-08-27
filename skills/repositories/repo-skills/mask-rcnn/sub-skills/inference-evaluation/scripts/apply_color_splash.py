#!/usr/bin/env python3
"""Apply a Mask_RCNN-style color splash effect to a saved image and mask.

Examples:
  python apply_color_splash.py --image image.npy --mask mask.npy --output splash.png
  python apply_color_splash.py --image image.png --mask mask.npy --output splash.png

The script is safe by default: it only reads the provided inputs and writes one
output file. It does not run inference, download data, or use the original repo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def load_image(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path)
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("Pillow is required to load common image formats") from exc
    return np.array(Image.open(path).convert("RGB"))


def save_image(path: Path, image: np.ndarray) -> None:
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("Pillow is required to save common image formats") from exc
    Image.fromarray(image.astype(np.uint8)).save(path)


def color_splash(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[-1] != 3:
        raise ValueError("image must be [H, W, 3]")
    if mask.ndim == 2:
        mask = mask[..., np.newaxis]
    if mask.ndim != 3:
        raise ValueError("mask must be [H, W, N] or [H, W]")
    if mask.shape[0] != image.shape[0] or mask.shape[1] != image.shape[1]:
        raise ValueError("mask and image must have the same height/width")
    gray = np.mean(image, axis=2, keepdims=True).astype(image.dtype)
    gray = np.repeat(gray, 3, axis=2)
    combined = np.sum(mask, axis=-1, keepdims=True) >= 1
    return np.where(combined, image, gray).astype(np.uint8)


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply a color splash effect to an image and mask.")
    ap.add_argument("--image", type=Path, required=True, help="Input image file (.npy or common image format).")
    ap.add_argument("--mask", type=Path, required=True, help="Instance mask array saved as .npy.")
    ap.add_argument("--output", type=Path, required=True, help="Output image path.")
    args = ap.parse_args()

    image = load_image(args.image)
    mask = np.load(args.mask)
    splash = color_splash(image, mask)
    save_image(args.output, splash)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
