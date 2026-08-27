#!/usr/bin/env python3
"""Validate Keras-GAN image-translation dataset layouts safely.

This helper performs local filesystem checks only. It does not download data,
import Keras/TensorFlow, construct models, train, or write outputs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}


class Reporter:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def emit(self) -> None:
        for message in self.notes:
            print(f"OK: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        for message in self.errors:
            print(f"ERROR: {message}", file=sys.stderr)


def image_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    files = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(files)


def require_split(root: Path, split: str, min_files: int, reporter: Reporter) -> List[Path]:
    directory = root / split
    if not directory.is_dir():
        reporter.error(f"missing required split directory: {split}/")
        return []
    files = image_files(directory)
    if len(files) < min_files:
        reporter.error(
            f"split {split}/ has {len(files)} image file(s), expected at least {min_files}"
        )
    else:
        reporter.note(f"split {split}/ has {len(files)} image file(s)")
    return files


def optional_split(root: Path, split: str, min_files: int, reporter: Reporter) -> List[Path]:
    directory = root / split
    if not directory.exists():
        reporter.warn(f"optional split {split}/ is absent")
        return []
    if not directory.is_dir():
        reporter.warn(f"optional split {split}/ exists but is not a directory")
        return []
    files = image_files(directory)
    if len(files) < min_files:
        reporter.warn(
            f"optional split {split}/ has {len(files)} image file(s), below --min-files {min_files}"
        )
    else:
        reporter.note(f"optional split {split}/ has {len(files)} image file(s)")
    return files


def import_pillow(reporter: Reporter):
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover - message is runtime dependent
        reporter.warn(f"Pillow is not available; skipping image-dimension checks ({exc})")
        return None
    return Image


def check_images(
    split_files: Dict[str, Sequence[Path]],
    reporter: Reporter,
    *,
    paired_side_by_side: bool,
    max_images_per_split: int,
) -> None:
    Image = import_pillow(reporter)
    if Image is None:
        return

    for split, files in split_files.items():
        if max_images_per_split < 0:
            selected = list(files)
        else:
            selected = list(files[:max_images_per_split])
            if len(files) > max_images_per_split:
                reporter.warn(
                    f"split {split}/ has {len(files)} images; checked first {max_images_per_split}"
                )

        for path in selected:
            try:
                with Image.open(path) as img:
                    width, height = img.size
                    mode = img.mode
            except Exception as exc:
                reporter.error(f"{split}/{path.name}: Pillow could not open image ({exc})")
                continue

            if width <= 0 or height <= 0:
                reporter.error(f"{split}/{path.name}: invalid image size {width}x{height}")
                continue

            if mode not in {"RGB", "RGBA", "L", "P", "CMYK", "YCbCr"}:
                reporter.warn(f"{split}/{path.name}: unusual Pillow mode {mode!r}; loaders request RGB")

            if paired_side_by_side:
                if width < 2:
                    reporter.error(f"{split}/{path.name}: side-by-side pair width must be at least 2")
                if width % 2 != 0:
                    reporter.error(
                        f"{split}/{path.name}: side-by-side pair width {width} is odd; left/right halves are unequal"
                    )
                half_width = width // 2
                if half_width <= 0:
                    reporter.error(f"{split}/{path.name}: empty side-by-side half after split")
                elif half_width != height:
                    reporter.warn(
                        f"{split}/{path.name}: each half is {half_width}x{height}; loader will resize to square img_res"
                    )


def has_all_dirs(root: Path, splits: Iterable[str]) -> bool:
    return all((root / split).is_dir() for split in splits)


def validate_cyclegan(root: Path, min_files: int, reporter: Reporter) -> Dict[str, Sequence[Path]]:
    files: Dict[str, Sequence[Path]] = {}
    for split in ("trainA", "trainB", "testA", "testB"):
        files[split] = require_split(root, split, min_files, reporter)
    # Source load_batch(is_testing=True) uses valA/valB, while sample_images uses testA/testB.
    optional_split(root, "valA", min_files, reporter)
    optional_split(root, "valB", min_files, reporter)
    return files


def validate_discogan(root: Path, min_files: int, reporter: Reporter) -> Tuple[Dict[str, Sequence[Path]], bool]:
    """Validate DiscoGAN data.

    The production knowledge covers both the common unpaired-domain DiscoGAN
    expectation and this Keras-GAN checkout's stock loader. The stock loader uses
    paired side-by-side train/val images; an unpaired trainA/trainB layout needs
    a deliberate loader adaptation.
    """

    domain_splits = ("trainA", "trainB", "testA", "testB")
    paired_splits = ("train", "val")

    if has_all_dirs(root, domain_splits):
        reporter.warn(
            "using unpaired DiscoGAN domain layout; adapt the stock Keras-GAN "
            "discogan DataLoader before training because the bundled loader reads train/val side-by-side images"
        )
        files: Dict[str, Sequence[Path]] = {}
        for split in domain_splits:
            files[split] = require_split(root, split, min_files, reporter)
        # Common validation-batch adaptation mirrors CycleGAN's valA/valB convention.
        optional_split(root, "valA", min_files, reporter)
        optional_split(root, "valB", min_files, reporter)
        return files, False

    if has_all_dirs(root, paired_splits):
        reporter.note(
            "detected stock Keras-GAN DiscoGAN paired layout with train/ and val/ side-by-side images"
        )
        files = {}
        for split in paired_splits:
            files[split] = require_split(root, split, min_files, reporter)
        return files, True

    reporter.error(
        "DiscoGAN dataset must be either unpaired trainA/trainB/testA/testB "
        "for an adapted loader, or stock Keras-GAN paired train/val side-by-side images"
    )
    return {}, False


def validate_pix2pix(root: Path, min_files: int, reporter: Reporter) -> Dict[str, Sequence[Path]]:
    files: Dict[str, Sequence[Path]] = {}
    for split in ("train", "test", "val"):
        files[split] = require_split(root, split, min_files, reporter)

    if any((root / split).exists() for split in ("trainA", "trainB", "testA", "testB")):
        reporter.error(
            "Pix2Pix stock loader expects paired side-by-side images in train/test/val; "
            "separate A/B domain folders were detected and will be ignored"
        )
    return files


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate local Keras-GAN CycleGAN, DiscoGAN, or Pix2Pix "
            "dataset layout without downloads, Keras imports, training, or writes."
        )
    )
    parser.add_argument(
        "--dataset-root",
        required=True,
        type=Path,
        help="Path to the extracted dataset directory, e.g. datasets/apple2orange.",
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=("cyclegan", "discogan", "pix2pix"),
        help="Keras-GAN image-translation workflow whose data contract should be checked.",
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=1,
        help="Minimum image files required per required split (default: 1).",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Open images with Pillow when available and validate dimensions/modes.",
    )
    parser.add_argument(
        "--max-images-per-split",
        type=int,
        default=200,
        help=(
            "Maximum images to open per split when --check-images is set; use -1 "
            "to check all images (default: 200)."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    reporter = Reporter()

    if args.min_files < 0:
        reporter.error("--min-files must be non-negative")
        reporter.emit()
        return 2
    if args.max_images_per_split == 0 or args.max_images_per_split < -1:
        reporter.error("--max-images-per-split must be -1 or a positive integer")
        reporter.emit()
        return 2

    root = args.dataset_root
    if not root.exists():
        reporter.error(f"dataset root does not exist: {root}")
        reporter.emit()
        return 1
    if not root.is_dir():
        reporter.error(f"dataset root is not a directory: {root}")
        reporter.emit()
        return 1

    paired_side_by_side = False
    split_files: Dict[str, Sequence[Path]]

    if args.workflow == "cyclegan":
        split_files = validate_cyclegan(root, args.min_files, reporter)
    elif args.workflow == "discogan":
        split_files, paired_side_by_side = validate_discogan(root, args.min_files, reporter)
    else:
        split_files = validate_pix2pix(root, args.min_files, reporter)
        paired_side_by_side = True

    if args.check_images and split_files:
        check_images(
            split_files,
            reporter,
            paired_side_by_side=paired_side_by_side,
            max_images_per_split=args.max_images_per_split,
        )

    if reporter.errors:
        reporter.emit()
        return 1

    reporter.note(f"{args.workflow} dataset layout looks usable at {root}")
    reporter.emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
