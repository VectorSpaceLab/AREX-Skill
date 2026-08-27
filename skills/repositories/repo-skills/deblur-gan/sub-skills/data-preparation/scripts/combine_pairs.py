#!/usr/bin/env python3
"""Concatenate paired blur/sharp images into DeblurGAN AB files.

This is a safer, path-normalized wrapper around the repository's original
`datasets/combine_A_and_B.py` helper. It keeps the same core behavior while
adding clearer validation and portable path handling.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

IMG_EXTENSIONS = {
    ".jpg", ".JPG", ".jpeg", ".JPEG",
    ".png", ".PNG", ".ppm", ".PPM", ".bmp", ".BMP",
}


def is_image_file(path: Path) -> bool:
    return path.suffix in IMG_EXTENSIONS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create DeblurGAN AB image pairs")
    parser.add_argument("--fold_A", required=True, help="input directory for image A")
    parser.add_argument("--fold_B", required=True, help="input directory for image B")
    parser.add_argument("--fold_AB", required=True, help="output directory")
    parser.add_argument("--num_imgs", type=int, default=1_000_000, help="maximum images per split")
    parser.add_argument("--use_AB", action="store_true", help="map _A filenames to _B and strip _A from the output name")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fold_A = Path(args.fold_A).expanduser().resolve()
    fold_B = Path(args.fold_B).expanduser().resolve()
    fold_AB = Path(args.fold_AB).expanduser().resolve()

    if not fold_A.is_dir():
        raise SystemExit(f"fold_A is not a directory: {fold_A}")
    if not fold_B.is_dir():
        raise SystemExit(f"fold_B is not a directory: {fold_B}")

    split_names = [p.name for p in sorted(fold_A.iterdir()) if p.is_dir()]
    if not split_names:
        raise SystemExit(f"no split directories found under {fold_A}")

    for split_name in split_names:
        img_fold_A = fold_A / split_name
        img_fold_B = fold_B / split_name
        img_fold_AB = fold_AB / split_name

        if not img_fold_B.is_dir():
            print(f"[skip] missing matching split in B: {img_fold_B}")
            continue

        images = [p for p in sorted(img_fold_A.iterdir()) if p.is_file() and is_image_file(p)]
        if args.use_AB:
            images = [p for p in images if "_A." in p.name]
        images = images[: args.num_imgs]

        img_fold_AB.mkdir(parents=True, exist_ok=True)
        print(f"split = {split_name}, use {len(images)}/{len([p for p in img_fold_A.iterdir() if p.is_file() and is_image_file(p)])} images")

        for path_A in images:
            name_B = path_A.name.replace("_A.", "_B.") if args.use_AB else path_A.name
            path_B = img_fold_B / name_B

            if not path_B.is_file():
                print(f"[skip] missing pair for {path_A.name}: {path_B.name}")
                continue

            im_A = cv2.imread(str(path_A), cv2.IMREAD_COLOR)
            im_B = cv2.imread(str(path_B), cv2.IMREAD_COLOR)
            if im_A is None:
                print(f"[skip] could not read A image: {path_A}")
                continue
            if im_B is None:
                print(f"[skip] could not read B image: {path_B}")
                continue

            im_AB = np.concatenate([im_A, im_B], axis=1)
            out_name = path_A.name.replace("_A.", ".") if args.use_AB else path_A.name
            out_path = img_fold_AB / out_name
            if not cv2.imwrite(str(out_path), im_AB):
                raise SystemExit(f"failed to write paired image: {out_path}")

        print(f"split = {split_name}, output written to {img_fold_AB}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
