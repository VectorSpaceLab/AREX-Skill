#!/usr/bin/env python3
"""Create side-by-side aligned train/test images from trainA/trainB/testA/testB.

This helper mirrors the repository's aligned export utility while adding clearer
validation and messages. It expects same-length A/B split folders with matching
image sizes.

Example:
    python scripts/make_dataset_aligned.py --dataset-path /data/my_dataset
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def get_file_paths(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"missing folder: {folder}")
    return [child for child in sorted(folder.iterdir()) if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES]


def align_images(a_paths: list[Path], b_paths: list[Path], target_path: Path) -> int:
    if len(a_paths) != len(b_paths):
        raise ValueError(f"A/B image counts differ: {len(a_paths)} vs {len(b_paths)}")
    if not a_paths:
        raise ValueError("no images found to align")
    target_path.mkdir(parents=True, exist_ok=True)

    for i, (path_a, path_b) in enumerate(zip(a_paths, b_paths)):
        img_a = Image.open(path_a).convert("RGB")
        img_b = Image.open(path_b).convert("RGB")
        if img_a.size != img_b.size:
            raise ValueError(f"image sizes differ for pair {path_a.name}, {path_b.name}: {img_a.size} vs {img_b.size}")
        aligned_image = Image.new("RGB", (img_a.size[0] * 2, img_a.size[1]))
        aligned_image.paste(img_a, (0, 0))
        aligned_image.paste(img_b, (img_a.size[0], 0))
        aligned_image.save(target_path / f"{i:04d}.jpg")
    return len(a_paths)


def process_split(dataset_path: Path, split: str) -> int:
    a_paths = get_file_paths(dataset_path / f"{split}A")
    b_paths = get_file_paths(dataset_path / f"{split}B")
    count = align_images(a_paths, b_paths, dataset_path / split)
    print(f"{split}: wrote {count} aligned images")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create aligned side-by-side train/test images from trainA/trainB/testA/testB folders.")
    parser.add_argument("--dataset-path", required=True, help="Dataset root with trainA, trainB, testA, and testB folders.")
    parser.add_argument("--splits", nargs="+", default=["test", "train"], choices=["train", "test", "val"], help="Split prefixes to process.")
    args = parser.parse_args(argv)

    dataset_path = Path(args.dataset_path)
    if not dataset_path.is_dir():
        raise SystemExit(f"dataset path is not a directory: {dataset_path}")

    total = 0
    for split in args.splits:
        total += process_split(dataset_path, split)
    print(f"done: wrote {total} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
