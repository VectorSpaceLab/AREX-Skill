#!/usr/bin/env python3
"""Whiten image backgrounds using matching foreground segmentation masks.

Adapted from DragGAN's StyleGAN-Human `bg_white.py` into a self-contained skill
helper. It performs CPU image processing only and does not require model weights.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def bg_white(seg: np.ndarray, raw: np.ndarray, blur_level: int = 3, gaussian: int = 81) -> np.ndarray:
    seg = cv2.blur(seg, (blur_level, blur_level))
    empty = np.ones_like(seg)
    seg_bg = (empty - seg) * 255
    seg_bg = cv2.GaussianBlur(seg_bg, (gaussian, gaussian), 0)
    background_mask = cv2.cvtColor(255 - cv2.cvtColor(seg, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    masked_fg = (raw * (1 / 255)) * (seg * (1 / 255))
    masked_bg = (seg_bg * (1 / 255)) * (background_mask * (1 / 255))
    return np.uint8(cv2.add(masked_bg, masked_fg) * 255)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create white-background images from raw images and segmentation masks.")
    parser.add_argument("--raw-img-dir", required=True, type=Path, help="Directory of raw RGB images.")
    parser.add_argument("--raw-seg-dir", required=True, type=Path, help="Directory of segmentation masks with matching filenames.")
    parser.add_argument("--outdir", required=True, type=Path, help="Output directory.")
    parser.add_argument("--blur-level", type=int, default=3)
    parser.add_argument("--gaussian", type=int, default=81, help="Odd Gaussian kernel size used for background smoothing.")
    args = parser.parse_args()

    if args.gaussian % 2 != 1 or args.gaussian <= 0:
        print("ERROR: --gaussian must be a positive odd integer.", file=sys.stderr)
        return 2
    raw_dir = args.raw_img_dir.expanduser().resolve()
    seg_dir = args.raw_seg_dir.expanduser().resolve()
    outdir = args.outdir.expanduser().resolve()
    if not raw_dir.is_dir() or not seg_dir.is_dir():
        print("ERROR: raw and segmentation paths must both be directories.", file=sys.stderr)
        return 2
    outdir.mkdir(parents=True, exist_ok=True)

    failures = 0
    count = 0
    for raw_path in sorted(p for p in raw_dir.iterdir() if p.is_file()):
        seg_path = seg_dir / raw_path.name
        if not seg_path.exists():
            print(f"WARN: missing segmentation mask for {raw_path.name}", file=sys.stderr)
            failures += 1
            continue
        raw = cv2.imread(str(raw_path))
        seg = cv2.imread(str(seg_path))
        if raw is None or seg is None:
            print(f"WARN: could not read raw/mask pair for {raw_path.name}", file=sys.stderr)
            failures += 1
            continue
        white = bg_white(seg, raw, blur_level=args.blur_level, gaussian=args.gaussian)
        cv2.imwrite(str(outdir / raw_path.name), white)
        count += 1
    print(f"processed={count} failures={failures} outdir={outdir}")
    return 1 if count == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
