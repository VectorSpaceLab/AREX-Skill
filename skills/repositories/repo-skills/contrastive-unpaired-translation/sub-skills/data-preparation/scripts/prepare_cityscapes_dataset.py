#!/usr/bin/env python3
"""Prepare Cityscapes images for CUT/pix2pix-style training.

This is a self-contained, safer adaptation of the repository helper. It reads
local Cityscapes gtFine and leftImg8bit trees, creates paired side-by-side
images, and also writes CUT-style trainA/trainB/testA/testB folders.

Example:
    python scripts/prepare_cityscapes_dataset.py \
      --gtFine_dir /data/gtFine_trainvaltest \
      --leftImg8bit_dir /data/leftImg8bit_trainvaltest \
      --output_dir /data/cityscapes_cut
"""
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
from PIL import Image


def load_resized_img(path: str, size: int) -> Image.Image:
    return Image.open(path).convert("RGB").resize((size, size))


def check_matching_pair(segmap_path: str, photo_path: str) -> None:
    segmap_identifier = os.path.basename(segmap_path).replace("_gtFine_color", "")
    photo_identifier = os.path.basename(photo_path).replace("_leftImg8bit", "")
    if segmap_identifier != photo_identifier:
        raise ValueError(f"{segmap_path!r} and {photo_path!r} do not match")


def process_cityscapes(gt_fine_dir: Path, left_img_dir: Path, output_dir: Path, phase: str, size: int, quality: int) -> int:
    save_phase = "test" if phase == "val" else phase
    paired_dir = output_dir / save_phase
    dir_a = output_dir / f"{save_phase}A"
    dir_b = output_dir / f"{save_phase}B"
    paired_dir.mkdir(parents=True, exist_ok=True)
    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)

    segmap_expr = str(gt_fine_dir / phase / "*" / "*_color.png")
    photo_expr = str(left_img_dir / phase / "*" / "*_leftImg8bit.png")
    segmap_paths = sorted(glob.glob(segmap_expr))
    photo_paths = sorted(glob.glob(photo_expr))

    if len(segmap_paths) != len(photo_paths):
        raise ValueError(
            f"phase={phase}: found {len(segmap_paths)} segmaps for {segmap_expr} "
            f"and {len(photo_paths)} photos for {photo_expr}"
        )
    if not segmap_paths:
        raise ValueError(f"phase={phase}: no matching Cityscapes files found")

    report_every = max(1, len(segmap_paths) // 10)
    for i, (segmap_path, photo_path) in enumerate(zip(segmap_paths, photo_paths)):
        check_matching_pair(segmap_path, photo_path)
        segmap = load_resized_img(segmap_path, size)
        photo = load_resized_img(photo_path, size)

        sidebyside = Image.new("RGB", (size * 2, size))
        # Preserve the source helper's convention: photo first, label second.
        sidebyside.paste(photo, (0, 0))
        sidebyside.paste(segmap, (size, 0))
        sidebyside.save(paired_dir / f"{i}.jpg", format="JPEG", subsampling=0, quality=quality)

        photo.save(dir_a / f"{i}_A.jpg", format="JPEG", subsampling=0, quality=quality)
        segmap.save(dir_b / f"{i}_B.jpg", format="JPEG", subsampling=0, quality=quality)

        if i % report_every == 0:
            print(f"{phase}: wrote {i + 1}/{len(segmap_paths)}")
    return len(segmap_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare local Cityscapes data for CUT and pix2pix workflows.")
    parser.add_argument("--gtFine_dir", required=True, help="Path to the unzipped gtFine_trainvaltest directory.")
    parser.add_argument("--leftImg8bit_dir", required=True, help="Path to the unzipped leftImg8bit_trainvaltest directory.")
    parser.add_argument("--output_dir", required=True, help="Directory where prepared images will be written.")
    parser.add_argument("--image_size", type=int, default=256, help="Square output size for each half of the paired image.")
    parser.add_argument("--jpeg_quality", type=int, default=100, help="JPEG quality for generated files.")
    parser.add_argument("--phases", nargs="+", default=["val", "train"], choices=["train", "val"], help="Cityscapes phases to process; val is written as test.")
    args = parser.parse_args(argv)

    gt_fine_dir = Path(args.gtFine_dir)
    left_img_dir = Path(args.leftImg8bit_dir)
    output_dir = Path(args.output_dir)

    if not gt_fine_dir.exists():
        raise SystemExit(f"gtFine_dir does not exist: {gt_fine_dir}")
    if not left_img_dir.exists():
        raise SystemExit(f"leftImg8bit_dir does not exist: {left_img_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    counts = {}
    for phase in args.phases:
        counts[phase] = process_cityscapes(gt_fine_dir, left_img_dir, output_dir, phase, args.image_size, args.jpeg_quality)
    print("done", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
