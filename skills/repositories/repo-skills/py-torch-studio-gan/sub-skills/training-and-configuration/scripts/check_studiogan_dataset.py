#!/usr/bin/env python3
"""Check a StudioGAN ImageFolder-style training dataset without loading tensors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

IMAGE_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif", ".tiff", ".webp",
}


def path_arg(value: str) -> Path:
    return Path(value).expanduser()


def iter_images(directory: Path) -> Iterable[Path]:
    for item in directory.rglob("*"):
        if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES:
            yield item


def scan_split(root: Path, split: str) -> Tuple[Dict[str, int], List[str]]:
    split_dir = root / split
    errors: List[str] = []
    counts: Dict[str, int] = {}
    if not split_dir.exists():
        return counts, [f"missing {split}/ split under {root}"]
    if not split_dir.is_dir():
        return counts, [f"{split}/ exists but is not a directory: {split_dir}"]
    try:
        class_dirs = sorted(path for path in split_dir.iterdir() if path.is_dir())
    except OSError as exc:
        return counts, [f"cannot read {split}/ split: {exc}"]
    if not class_dirs:
        errors.append(f"{split}/ contains no class subdirectories")
        return counts, errors
    for class_dir in class_dirs:
        try:
            counts[class_dir.name] = sum(1 for _ in iter_images(class_dir))
        except OSError as exc:
            errors.append(f"cannot scan {split}/{class_dir.name}: {exc}")
    return counts, errors


def validate_counts(counts: Dict[str, int], split: str, min_classes: int, min_images_per_class: int,
                    expect_num_classes: int | None) -> List[str]:
    errors: List[str] = []
    if len(counts) < min_classes:
        errors.append(f"{split}/ has {len(counts)} class(es), expected at least {min_classes}")
    if expect_num_classes is not None and len(counts) != expect_num_classes:
        errors.append(f"{split}/ has {len(counts)} class(es), expected DATA.num_classes={expect_num_classes}")
    sparse = {name: count for name, count in counts.items() if count < min_images_per_class}
    if sparse:
        details = ", ".join(f"{name}:{count}" for name, count in sorted(sparse.items())[:20])
        more = " ..." if len(sparse) > 20 else ""
        errors.append(f"{split}/ classes below --min-images-per-class={min_images_per_class}: {details}{more}")
    return errors


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate StudioGAN ImageFolder layout for custom datasets. "
            "The checker scans file names only; it does not decode images, download data, or write files."
        )
    )
    parser.add_argument("--data-dir", required=True, type=path_arg, help="Dataset root containing train/<class>/image files.")
    parser.add_argument("--require-valid", action="store_true", help="Require a valid/<class>/ split and matching class names.")
    parser.add_argument("--min-classes", type=int, default=1, help="Minimum number of class directories in train/. Default: 1.")
    parser.add_argument("--min-images-per-class", type=int, default=1, help="Minimum supported images per class. Default: 1.")
    parser.add_argument("--expect-num-classes", type=int, help="Expected DATA.num_classes value for conditional configs.")
    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()
    errors: List[str] = []

    if args.min_classes <= 0:
        errors.append("--min-classes must be positive")
    if args.min_images_per_class <= 0:
        errors.append("--min-images-per-class must be positive")
    if args.expect_num_classes is not None and args.expect_num_classes <= 0:
        errors.append("--expect-num-classes must be positive when supplied")
    if not args.data_dir.exists() or not args.data_dir.is_dir():
        errors.append(f"--data-dir is not an existing directory: {args.data_dir}")

    train_counts: Dict[str, int] = {}
    valid_counts: Dict[str, int] = {}
    if not errors:
        train_counts, split_errors = scan_split(args.data_dir, "train")
        errors.extend(split_errors)
        errors.extend(validate_counts(train_counts, "train", args.min_classes, args.min_images_per_class, args.expect_num_classes))

        valid_dir = args.data_dir / "valid"
        if args.require_valid or valid_dir.exists():
            valid_counts, split_errors = scan_split(args.data_dir, "valid")
            errors.extend(split_errors)
            if valid_counts:
                errors.extend(validate_counts(valid_counts, "valid", args.min_classes, args.min_images_per_class, args.expect_num_classes))
                train_classes = set(train_counts)
                valid_classes = set(valid_counts)
                missing = sorted(train_classes - valid_classes)
                extra = sorted(valid_classes - train_classes)
                if missing:
                    errors.append("valid/ is missing train class(es): " + ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else ""))
                if extra:
                    errors.append("valid/ has class(es) not present in train/: " + ", ".join(extra[:20]) + (" ..." if len(extra) > 20 else ""))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"OK: train split has {len(train_counts)} class(es) and {sum(train_counts.values())} supported image file(s).")
    if valid_counts:
        print(f"OK: valid split has {len(valid_counts)} class(es) and {sum(valid_counts.values())} supported image file(s).")
    else:
        print("NOTE: no valid split was checked; use --require-valid when validation/reference metrics need valid/<class>/.")
    print("NOTE: this checker did not decode image contents or verify labels against a YAML file unless --expect-num-classes was supplied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
