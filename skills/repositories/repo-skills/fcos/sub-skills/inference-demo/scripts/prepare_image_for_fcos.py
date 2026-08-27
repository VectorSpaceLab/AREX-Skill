#!/usr/bin/env python3
"""Validate and prepare a local image for FCOS.detect.

The script reads a local image with Pillow, validates that it is 3-channel RGB,
resizes it so the shorter side has the requested size, converts to BGR, and
writes a NumPy .npy array. It does not download images or run FCOS.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a 3-channel local image as a resized BGR NumPy array for FCOS")
    parser.add_argument("image", help="Local image path")
    parser.add_argument("--output", default="fcos-prepared-bgr.npy", help="Output .npy path")
    parser.add_argument("--short-side", type=int, default=800, help="Resize shorter side to this many pixels")
    parser.add_argument("--allow-rgba", action="store_true", help="Convert RGBA images to RGB by dropping alpha")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        parser.error(f"image does not exist: {image_path}")
    if args.short_side <= 0:
        parser.error("--short-side must be positive")

    with Image.open(image_path) as img:
        if img.mode == "RGBA" and args.allow_rgba:
            img = img.convert("RGB")
        elif img.mode != "RGB":
            raise SystemExit(f"Expected RGB image; got mode {img.mode}. Convert it first or pass --allow-rgba for RGBA.")
        w, h = img.size
        scale = float(args.short_side) / float(min(w, h))
        new_size = (int(round(w * scale)), int(round(h * scale)))
        img = img.resize(new_size, Image.BILINEAR)
        rgb = np.asarray(img, dtype=np.uint8)

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise SystemExit(f"Expected HxWx3 RGB array, got shape {rgb.shape}")
    bgr = rgb[..., ::-1].copy()
    out = Path(args.output)
    np.save(out, bgr)
    print(f"wrote {out} shape={tuple(bgr.shape)} dtype={bgr.dtype} color_order=BGR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
