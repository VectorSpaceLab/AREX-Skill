#!/usr/bin/env python3
"""Prepare Cityscapes files for pytorch-CycleGAN-and-pix2pix workflows.

This self-contained helper expects Cityscapes files to be downloaded and
extracted already. It performs no network access. For each matched photo/label
pair it writes:
- paired pix2pix images in train/ or test/ with A=photo on the left and
  B=color label map on the right,
- unpaired CycleGAN-style trainA/trainB or testA/testB images.

The Cityscapes val split is written as test output, matching the repository's
original convention.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image


def cityscapes_id(path: Path, suffix: str) -> str:
    name = path.stem
    if not name.endswith(suffix):
        raise ValueError(f"{path} does not end with expected suffix {suffix!r}")
    return name[: -len(suffix)]


def collect_color_labels(gtfine_dir: Path, phase: str) -> List[Path]:
    return sorted((gtfine_dir / phase).glob("*/*_gtFine_color.png"))


def collect_photos(left_img_dir: Path, phase: str) -> List[Path]:
    return sorted((left_img_dir / phase).glob("*/*_leftImg8bit.png"))


def check_pairs(labels: Sequence[Path], photos: Sequence[Path]) -> List[Tuple[Path, Path, str]]:
    if len(labels) != len(photos):
        raise RuntimeError(
            f"label/photo count mismatch: {len(labels)} color label(s) vs {len(photos)} photo(s). "
            "Check gtFine_dir, leftImg8bit_dir, and phase."
        )
    pairs: List[Tuple[Path, Path, str]] = []
    for label, photo in zip(labels, photos):
        label_id = cityscapes_id(label, "_gtFine_color")
        photo_id = cityscapes_id(photo, "_leftImg8bit")
        if label_id != photo_id:
            raise RuntimeError(f"mismatched Cityscapes pair: {label} vs {photo}")
        pairs.append((label, photo, label_id))
    return pairs


def resized_rgb(path: Path, size: Tuple[int, int]) -> Image.Image:
    return Image.open(path).convert("RGB").resize(size)


def safe_name(identifier: str, index: int) -> str:
    # Keep the original city/shot/frame identifier when present, but provide a
    # deterministic fallback for unusual tiny fixtures.
    if identifier:
        return f"{identifier}.jpg"
    return f"{index:06d}.jpg"


def process_phase(
    *,
    gtfine_dir: Path,
    left_img_dir: Path,
    output_dir: Path,
    phase: str,
    save_phase: str,
    size: Tuple[int, int],
    limit: int | None,
    quality: int,
    dry_run: bool,
) -> int:
    labels = collect_color_labels(gtfine_dir, phase)
    photos = collect_photos(left_img_dir, phase)
    pairs = check_pairs(labels, photos)
    if limit is not None:
        pairs = pairs[:limit]
    if not pairs:
        raise RuntimeError(f"no matched Cityscapes pairs found for phase {phase!r}")

    paired_dir = output_dir / save_phase
    photo_dir = output_dir / f"{save_phase}A"
    label_dir = output_dir / f"{save_phase}B"
    print(f"{phase} -> {save_phase}: {len(pairs)} pair(s)")
    if dry_run:
        print(f"dry-run: would write paired images to {paired_dir}, photos to {photo_dir}, labels to {label_dir}")
        return len(pairs)

    paired_dir.mkdir(parents=True, exist_ok=True)
    photo_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    for index, (label_path, photo_path, identifier) in enumerate(pairs):
        label = resized_rgb(label_path, size)
        photo = resized_rgb(photo_path, size)
        name = safe_name(identifier, index)

        side_by_side = Image.new("RGB", (size[0] * 2, size[1]))
        side_by_side.paste(photo, (0, 0))
        side_by_side.paste(label, (size[0], 0))
        side_by_side.save(paired_dir / name, format="JPEG", subsampling=0, quality=quality)
        photo.save(photo_dir / name, format="JPEG", subsampling=0, quality=quality)
        label.save(label_dir / name, format="JPEG", subsampling=0, quality=quality)

        if index == 0 or (index + 1) == len(pairs) or ((index + 1) % max(1, len(pairs) // 10) == 0):
            print(f"  wrote {index + 1}/{len(pairs)}")
    return len(pairs)


def parse_phases(values: Iterable[str]) -> List[Tuple[str, str]]:
    mapping = {"train": "train", "val": "test", "test": "test"}
    pairs: List[Tuple[str, str]] = []
    for value in values:
        phase = value.strip()
        if not phase:
            continue
        if phase not in mapping:
            raise argparse.ArgumentTypeError(f"unsupported phase {phase!r}; choose train, val, or test")
        pairs.append((phase, mapping[phase]))
    if not pairs:
        raise argparse.ArgumentTypeError("no phases supplied")
    return pairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert already-downloaded Cityscapes gtFine and leftImg8bit trees for pix2pix/CycleGAN.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--gtFine-dir", "--gtFine_dir", dest="gtfine_dir", required=True, type=Path, help="Extracted gtFine directory containing train/val/test city folders.")
    parser.add_argument("--leftImg8bit-dir", "--leftImg8bit_dir", dest="left_img_dir", required=True, type=Path, help="Extracted leftImg8bit directory containing train/val/test city folders.")
    parser.add_argument("--output-dir", "--output_dir", dest="output_dir", required=True, type=Path, help="Output dataset root to create.")
    parser.add_argument("--phases", default="train,val", help="Comma-separated Cityscapes phases to process. val maps to output test.")
    parser.add_argument("--size", default="256x256", help="Output WxH size for each half before side-by-side pairing.")
    parser.add_argument("--limit", type=int, help="Optional maximum pairs per phase for smoke fixtures.")
    parser.add_argument("--quality", type=int, default=100, help="JPEG quality.")
    parser.add_argument("--dry-run", action="store_true", help="Check matching pairs and print planned outputs without writing images.")
    return parser


def parse_size(value: str) -> Tuple[int, int]:
    if "x" not in value.lower():
        raise argparse.ArgumentTypeError("--size must look like WIDTHxHEIGHT, e.g. 256x256")
    left, right = value.lower().split("x", 1)
    try:
        width = int(left)
        height = int(right)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--size must contain integer width and height") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("--size dimensions must be positive")
    return width, height


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if not args.gtfine_dir.is_dir():
        parser.error(f"--gtFine-dir is not a directory: {args.gtfine_dir}")
    if not args.left_img_dir.is_dir():
        parser.error(f"--leftImg8bit-dir is not a directory: {args.left_img_dir}")
    try:
        phase_pairs = parse_phases(args.phases.split(","))
        size = parse_size(args.size)
        total = 0
        for phase, save_phase in phase_pairs:
            total += process_phase(
                gtfine_dir=args.gtfine_dir,
                left_img_dir=args.left_img_dir,
                output_dir=args.output_dir,
                phase=phase,
                save_phase=save_phase,
                size=size,
                limit=args.limit,
                quality=args.quality,
                dry_run=args.dry_run,
            )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"done: {total} Cityscapes pair(s) processed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
