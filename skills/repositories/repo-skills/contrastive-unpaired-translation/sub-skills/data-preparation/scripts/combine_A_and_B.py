#!/usr/bin/env python3
"""Combine matching A/B image trees into side-by-side AB images.

The helper expects two folder trees with the same split names and matching file
names. It writes concatenated images into fold_AB/<split>/.

Example:
    python scripts/combine_A_and_B.py --fold_A /data/A --fold_B /data/B --fold_AB /data/AB
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def image_names(folder: Path, use_ab: bool) -> list[str]:
    names = []
    for child in sorted(folder.iterdir()):
        if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES:
            if use_ab and "_A." not in child.name:
                continue
            names.append(child.name)
    return names


def combine_split(fold_a: Path, fold_b: Path, fold_ab: Path, split: str, num_imgs: int, use_ab: bool, strict: bool) -> int:
    img_fold_a = fold_a / split
    img_fold_b = fold_b / split
    if not img_fold_a.is_dir():
        raise FileNotFoundError(f"missing A split directory: {img_fold_a}")
    if not img_fold_b.is_dir():
        raise FileNotFoundError(f"missing B split directory: {img_fold_b}")

    names = image_names(img_fold_a, use_ab)
    if not names:
        raise ValueError(f"no images found in {img_fold_a}")
    names = names[: min(num_imgs, len(names))]

    output_split = fold_ab / split
    output_split.mkdir(parents=True, exist_ok=True)
    written = 0
    missing = []
    for name_a in names:
        name_b = name_a.replace("_A.", "_B.") if use_ab else name_a
        path_a = img_fold_a / name_a
        path_b = img_fold_b / name_b
        if not path_b.is_file():
            missing.append(str(path_b))
            if strict:
                continue
            print(f"skip missing pair: {path_a} -> {path_b}")
            continue

        im_a = cv2.imread(str(path_a), cv2.IMREAD_COLOR)
        im_b = cv2.imread(str(path_b), cv2.IMREAD_COLOR)
        if im_a is None or im_b is None:
            raise ValueError(f"failed to read image pair: {path_a}, {path_b}")
        if im_a.shape[0] != im_b.shape[0]:
            raise ValueError(f"image heights differ: {path_a} {im_a.shape} vs {path_b} {im_b.shape}")
        out_name = name_a.replace("_A.", ".") if use_ab else name_a
        im_ab = np.concatenate([im_a, im_b], axis=1)
        out_path = output_split / out_name
        if not cv2.imwrite(str(out_path), im_ab):
            raise ValueError(f"failed to write {out_path}")
        written += 1

    if strict and missing:
        sample = "\n".join(missing[:5])
        raise FileNotFoundError(f"missing {len(missing)} B-side pairs, first entries:\n{sample}")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Combine matching A/B split trees into side-by-side AB images.")
    parser.add_argument("--fold_A", required=True, help="Input root for A images; contains split subdirectories.")
    parser.add_argument("--fold_B", required=True, help="Input root for B images; contains split subdirectories.")
    parser.add_argument("--fold_AB", required=True, help="Output root for combined AB images.")
    parser.add_argument("--num_imgs", type=int, default=1_000_000, help="Maximum images per split.")
    parser.add_argument("--use_AB", action="store_true", help="Match names like 0001_A.jpg to 0001_B.jpg and write 0001.jpg.")
    parser.add_argument("--strict", action="store_true", help="Fail if any selected A image lacks a B-side pair.")
    args = parser.parse_args(argv)

    fold_a = Path(args.fold_A)
    fold_b = Path(args.fold_B)
    fold_ab = Path(args.fold_AB)
    if not fold_a.is_dir():
        raise SystemExit(f"fold_A is not a directory: {fold_a}")
    if not fold_b.is_dir():
        raise SystemExit(f"fold_B is not a directory: {fold_b}")

    splits = [child.name for child in sorted(fold_a.iterdir()) if child.is_dir()]
    if not splits:
        raise SystemExit(f"fold_A has no split subdirectories: {fold_a}")

    total = 0
    for split in splits:
        written = combine_split(fold_a, fold_b, fold_ab, split, args.num_imgs, args.use_AB, args.strict)
        print(f"split={split}: wrote {written} images")
        total += written
    print(f"done: wrote {total} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
