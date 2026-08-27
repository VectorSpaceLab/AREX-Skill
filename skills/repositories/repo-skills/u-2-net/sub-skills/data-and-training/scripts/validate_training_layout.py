#!/usr/bin/env python3
"""Validate U-2-Net DUTS-style training image/mask layout.

This helper checks filename-stem pairing under the source training layout without
loading tensors or starting the long training loop.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_IMAGE_SUBDIR = Path("DUTS") / "DUTS-TR" / "DUTS-TR" / "im_aug"
DEFAULT_LABEL_SUBDIR = Path("DUTS") / "DUTS-TR" / "DUTS-TR" / "gt_aug"


def normalize_ext(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("extension must not be empty")
    return value if value.startswith(".") else f".{value}"


def collect_files(directory: Path, extension: str) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob(f"*{extension}") if path.is_file())


def check_layout(data_root: Path, image_subdir: Path, label_subdir: Path, image_ext: str, label_ext: str, max_pairs: Optional[int]) -> Tuple[Dict[str, object], int]:
    image_dir = data_root / image_subdir
    label_dir = data_root / label_subdir
    images = collect_files(image_dir, image_ext)
    checked = images[:max_pairs] if max_pairs is not None else images
    labels = collect_files(label_dir, label_ext)
    image_stems = {p.stem for p in images}
    missing = []
    pairs = []
    for image in checked:
        expected = label_dir / f"{image.stem}{label_ext}"
        record = {"image": str(image), "expected_label": str(expected), "label_exists": expected.is_file()}
        pairs.append(record)
        if not expected.is_file():
            missing.append(record)
    orphans = [str(p) for p in labels if p.stem not in image_stems]
    errors = []
    if not image_dir.is_dir():
        errors.append(f"image directory does not exist: {image_dir}")
    if not label_dir.is_dir():
        errors.append(f"label directory does not exist: {label_dir}")
    if image_dir.is_dir() and not images:
        errors.append(f"no image files matching *{image_ext} found in {image_dir}")
    if missing:
        errors.append(f"{len(missing)} checked image(s) are missing labels")
    result: Dict[str, object] = {
        "status": "ok" if not errors else "error",
        "data_root": str(data_root),
        "image_dir": str(image_dir),
        "label_dir": str(label_dir),
        "image_ext": image_ext,
        "label_ext": label_ext,
        "image_dir_exists": image_dir.is_dir(),
        "label_dir_exists": label_dir.is_dir(),
        "total_images": len(images),
        "total_labels": len(labels),
        "checked_images": len(checked),
        "missing_label_count": len(missing),
        "orphan_label_count": len(orphans),
        "missing_labels": missing,
        "orphan_labels": orphans,
        "checked_pairs": pairs,
        "errors": errors,
    }
    return result, 0 if not errors else 1


def print_human(result: Dict[str, object]) -> None:
    print(f"status: {result['status']}")
    print(f"image_dir: {result['image_dir']} (exists={result['image_dir_exists']})")
    print(f"label_dir: {result['label_dir']} (exists={result['label_dir_exists']})")
    print(f"counts: total_images={result['total_images']} total_labels={result['total_labels']} checked_images={result['checked_images']} missing_labels={result['missing_label_count']} orphan_labels={result['orphan_label_count']}")
    for error in result.get("errors") or []:
        print(f"error: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate U-2-Net training layout by checking im_aug image stems against gt_aug mask stems.")
    parser.add_argument("--data-root", default="train_data", help="Training data root containing the DUTS/DUTS-TR/DUTS-TR tree.")
    parser.add_argument("--image-subdir", default=str(DEFAULT_IMAGE_SUBDIR))
    parser.add_argument("--label-subdir", default=str(DEFAULT_LABEL_SUBDIR))
    parser.add_argument("--image-ext", type=normalize_ext, default=".jpg")
    parser.add_argument("--label-ext", type=normalize_ext, default=".png")
    parser.add_argument("--max-pairs", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    parser.add_argument("--json-indent", type=int, default=2)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.max_pairs is not None and args.max_pairs < 1:
        parser.error("--max-pairs must be positive")
    result, code = check_layout(Path(args.data_root), Path(args.image_subdir), Path(args.label_subdir), args.image_ext, args.label_ext, args.max_pairs)
    if args.json:
        print(json.dumps(result, indent=args.json_indent, sort_keys=True))
    else:
        print_human(result)
    return code


if __name__ == "__main__":
    sys.exit(main())
