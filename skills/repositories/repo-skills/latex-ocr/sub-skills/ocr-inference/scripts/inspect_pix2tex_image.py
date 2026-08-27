#!/usr/bin/env python3
"""Inspect an equation image before pix2tex inference.

This helper does not instantiate LatexOCR or download checkpoints.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def pad_like_pix2tex(img: Image.Image, divable: int = 32) -> Image.Image:
    data = np.array(img.convert("LA"))
    alpha = data[..., -1]
    if alpha.var() == 0:
        gray_data = data[..., 0].astype(np.uint8)
    else:
        gray_data = (255 - alpha).astype(np.uint8)
    if gray_data.max() != gray_data.min():
        gray_data = ((gray_data - gray_data.min()) / (gray_data.max() - gray_data.min()) * 255).astype(np.uint8)
    threshold = 128
    gray = 255 * ((gray_data < threshold) if gray_data.mean() > threshold else (gray_data > threshold)).astype(np.uint8)
    bbox = Image.fromarray(gray).getbbox()
    if bbox is None:
        raise ValueError("no foreground pixels detected")
    rect = Image.fromarray(gray_data).crop(bbox).convert("L")
    w, h = rect.size
    padded_w = divable * ((w + divable - 1) // divable)
    padded_h = divable * ((h + divable - 1) // divable)
    padded = Image.new("L", (padded_w, padded_h), 255)
    padded.paste(rect, (0, 0))
    return padded


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a pix2tex input image without running OCR")
    parser.add_argument("image", type=Path)
    parser.add_argument("--pad-preview", type=Path, default=None, help="optional path to write padded grayscale preview")
    args = parser.parse_args()

    img = Image.open(args.image)
    report = {"path": str(args.image), "mode": img.mode, "size": list(img.size), "warnings": []}
    if min(img.size) < 100:
        report["warnings"].append("one dimension is below 100 px; GUI upsamples very small captures")
    if max(img.size) > 2000:
        report["warnings"].append("very large image; crop tighter or downscale before OCR")
    try:
        padded = pad_like_pix2tex(ImageOps.exif_transpose(img))
        report["padded_size"] = list(padded.size)
        if args.pad_preview:
            padded.save(args.pad_preview)
            report["pad_preview"] = str(args.pad_preview)
    except Exception as exc:  # noqa: BLE001
        report["pad_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if "pad_error" not in report else 1


if __name__ == "__main__":
    raise SystemExit(main())
