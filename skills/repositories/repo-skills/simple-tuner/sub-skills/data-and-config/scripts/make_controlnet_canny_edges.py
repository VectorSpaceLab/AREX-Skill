#!/usr/bin/env python3
"""Create paired source/edge directories for SimpleTuner ControlNet Canny data.

Adapted from SimpleTuner's source Canny example, but with argparse, no hardcoded
paths, deterministic ordering, dry-run support, and safe no-overwrite defaults.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".jxl"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Canny edge conditioning images and a copied-original directory "
            "for SimpleTuner ControlNet dataloaders."
        )
    )
    parser.add_argument("--input-dir", required=True, help="Directory containing source images.")
    parser.add_argument("--output-original-dir", required=True, help="Directory to receive copied original images.")
    parser.add_argument("--output-edges-dir", required=True, help="Directory to receive generated Canny edge images.")
    parser.add_argument("--low-threshold", type=int, default=100, help="Canny low threshold, default: 100.")
    parser.add_argument("--high-threshold", type=int, default=200, help="Canny high threshold, default: 200.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs instead of skipping them.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned operations without creating directories or files.")
    return parser.parse_args(argv)


def import_image_dependencies():
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError("opencv-python is required to generate Canny edges; install cv2/opencv-python first.") from exc
    try:
        import numpy as np  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError("Pillow and numpy are required to read/write images for Canny generation.") from exc
    try:  # Optional JXL plugin for Pillow; do not require it for --help or non-JXL inputs.
        import pillow_jxl  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        pass
    return cv2, np, Image


def iter_images(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def validate_args(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    input_dir = Path(args.input_dir).expanduser()
    output_original_dir = Path(args.output_original_dir).expanduser()
    output_edges_dir = Path(args.output_edges_dir).expanduser()

    if args.low_threshold < 0 or args.high_threshold < 0:
        raise ValueError("Canny thresholds must be non-negative.")
    if args.high_threshold <= args.low_threshold:
        raise ValueError("--high-threshold must be greater than --low-threshold.")
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")
    if output_original_dir.resolve() == output_edges_dir.resolve():
        raise ValueError("Original-output and edge-output directories must be different.")
    return input_dir, output_original_dir, output_edges_dir


def load_grayscale(path: Path, cv2, np, Image):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is not None:
        return image
    try:
        with Image.open(path) as pil_image:
            return np.asarray(pil_image.convert("L"))
    except Exception as exc:  # noqa: BLE001 - report per-file decode failures without aborting the whole batch.
        raise RuntimeError(f"failed to decode image: {exc}") from exc


def save_edge(path: Path, edge_array, Image) -> None:
    image = Image.fromarray(edge_array)
    image.save(path)


def process(args: argparse.Namespace) -> int:
    input_dir, output_original_dir, output_edges_dir = validate_args(args)
    images = list(iter_images(input_dir))
    if not images:
        print(f"No supported image files found in {input_dir}.")
        return 0

    if args.dry_run:
        print(f"DRY RUN: would process {len(images)} image(s).")
        print(f"DRY RUN: originals -> {output_original_dir}")
        print(f"DRY RUN: edges     -> {output_edges_dir}")
        for image_path in images:
            original_out = output_original_dir / image_path.name
            edge_out = output_edges_dir / image_path.name
            action = "overwrite" if args.overwrite else "create-or-skip-existing"
            print(f"DRY RUN: {action}: {image_path.name} -> {original_out.name}, {edge_out.name}")
        return 0

    output_original_dir.mkdir(parents=True, exist_ok=True)
    output_edges_dir.mkdir(parents=True, exist_ok=True)

    cv2, np, Image = import_image_dependencies()

    processed = 0
    skipped = 0
    failed = 0
    for image_path in images:
        original_out = output_original_dir / image_path.name
        edge_out = output_edges_dir / image_path.name
        if not args.overwrite and (original_out.exists() or edge_out.exists()):
            print(f"SKIP existing output for {image_path.name}")
            skipped += 1
            continue
        try:
            grayscale = load_grayscale(image_path, cv2, np, Image)
            edges = cv2.Canny(grayscale, args.low_threshold, args.high_threshold)
            shutil.copy2(image_path, original_out)
            save_edge(edge_out, edges, Image)
        except Exception as exc:  # noqa: BLE001 - keep batch deterministic and report failed item.
            print(f"ERROR {image_path.name}: {exc}", file=sys.stderr)
            failed += 1
            continue
        print(f"OK {image_path.name}")
        processed += 1

    print(f"Done: {processed} processed, {skipped} skipped, {failed} failed.")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return process(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
