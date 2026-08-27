#!/usr/bin/env python3
"""Crop DIV2K images into sub-images for SR configs."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import re
import sys
from pathlib import Path

import cv2
import numpy as np

IMAGE_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return number


def scan_images(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def ensure_folder(path: Path, label: str) -> None:
    if not path.is_dir():
        raise FileNotFoundError(f"missing {label}: {path}")


def make_output_folder(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"output folder already exists: {path}")
    path.mkdir(parents=True, exist_ok=False)


def build_grid(length: int, crop_size: int, step: int, thresh_size: int):
    if length < crop_size:
        raise ValueError(
            f"image side {length} is smaller than crop size {crop_size}")
    grid = np.arange(0, length - crop_size + 1, step)
    if grid.size == 0:
        grid = np.array([0], dtype=np.int64)
    if length - (grid[-1] + crop_size) > thresh_size:
        grid = np.append(grid, length - crop_size)
    return grid


def crop_one(job):
    input_path, output_dir, crop_size, step, thresh_size, compression_level = job
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    image = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError(f"failed to read image: {input_path}")
    if image.ndim not in (2, 3):
        raise ValueError(f"expected a 2D or 3D image, got ndim={image.ndim}: {input_path}")

    height, width = image.shape[:2]
    h_grid = build_grid(height, crop_size, step, thresh_size)
    w_grid = build_grid(width, crop_size, step, thresh_size)

    stem = re.sub(r"x[2348]", "", input_path.stem)
    extension = input_path.suffix if input_path.suffix else ".png"
    patch_count = 0

    for y in h_grid:
        for x in w_grid:
            patch_count += 1
            patch = image[y:y + crop_size, x:x + crop_size, ...]
            output_path = output_dir / f"{stem}_s{patch_count:03d}{extension}"
            ok = cv2.imwrite(
                str(output_path), patch,
                [cv2.IMWRITE_PNG_COMPRESSION, compression_level])
            if not ok:
                raise RuntimeError(f"failed to write patch: {output_path}")

    return input_path.name, patch_count, str(output_dir)


def process_folder(input_folder: Path, output_folder: Path, crop_size: int,
                   step: int, thresh_size: int, compression_level: int,
                   n_thread: int) -> None:
    ensure_folder(input_folder, "input folder")
    make_output_folder(output_folder)

    image_paths = scan_images(input_folder)
    if not image_paths:
        raise RuntimeError(f"no images found in {input_folder}")

    jobs = [(
        path,
        output_folder,
        crop_size,
        step,
        thresh_size,
        compression_level,
    ) for path in image_paths]

    print(f"processing {input_folder} -> {output_folder} ({len(jobs)} images)")
    with mp.Pool(processes=n_thread) as pool:
        for index, result in enumerate(pool.imap(crop_one, jobs), start=1):
            image_name, patch_count, _ = result
            print(f"[{index}/{len(jobs)}] {image_name}: {patch_count} patches")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare DIV2K patches for SR experiments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-root",
        required=True,
        help="Root folder that contains DIV2K_train_HR and DIV2K_train_LR_bicubic.",
    )
    parser.add_argument(
        "--crop-size",
        type=positive_int,
        default=480,
        help="Crop size for HR images.",
    )
    parser.add_argument(
        "--step",
        type=positive_int,
        default=240,
        help="Sliding-window step for HR images.",
    )
    parser.add_argument(
        "--thresh-size",
        type=int,
        default=0,
        help="Drop patches smaller than this threshold.",
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        default=3,
        help="PNG compression level used when saving patches.",
    )
    parser.add_argument(
        "--n-thread",
        type=positive_int,
        default=20,
        help="Worker count for multiprocessing.",
    )
    parser.add_argument(
        "--scales",
        nargs="+",
        type=positive_int,
        default=[2, 3, 4],
        help="LR scales to crop alongside the HR input.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.thresh_size < 0:
        raise ValueError("--thresh-size must be non-negative")

    data_root = Path(args.data_root)

    hr_input = data_root / "DIV2K_train_HR"
    lr_root = data_root / "DIV2K_train_LR_bicubic"

    ensure_folder(data_root, "data root")
    ensure_folder(hr_input, "DIV2K_train_HR")
    ensure_folder(lr_root, "DIV2K_train_LR_bicubic")

    outputs: list[tuple[Path, int, int, int]] = [(
        data_root / "DIV2K_train_HR_sub",
        args.crop_size,
        args.step,
        args.thresh_size,
    )]
    for scale in args.scales:
        inputs = lr_root / f"X{scale}"
        ensure_folder(inputs, f"DIV2K_train_LR_bicubic/X{scale}")
        scaled_crop = args.crop_size // scale
        scaled_step = args.step // scale
        scaled_thresh = args.thresh_size // scale
        if scaled_crop <= 0 or scaled_step <= 0:
            raise ValueError(
                f"scaled crop/step must stay positive for X{scale}: crop={scaled_crop}, step={scaled_step}")
        outputs.append((lr_root / f"X{scale}_sub", scaled_crop, scaled_step,
                        scaled_thresh))

    for output_folder, _, _, _ in outputs:
        if output_folder.exists():
            raise FileExistsError(f"output folder already exists: {output_folder}")

    try:
        process_folder(hr_input, outputs[0][0], outputs[0][1], outputs[0][2],
                       outputs[0][3], args.compression_level, args.n_thread)
        for scale, (output_folder, crop_size, step, thresh_size) in zip(
                args.scales, outputs[1:]):
            process_folder(lr_root / f"X{scale}", output_folder, crop_size,
                           step, thresh_size, args.compression_level,
                           args.n_thread)
    except Exception:
        # Leave already-created folders in place so the caller can inspect them.
        raise

    print("All processes done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
