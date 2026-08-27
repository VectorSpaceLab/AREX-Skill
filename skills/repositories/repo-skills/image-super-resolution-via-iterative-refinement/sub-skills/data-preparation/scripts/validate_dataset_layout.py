#!/usr/bin/env python3
"""Validate LR/HR/SR image-directory layouts for SR datasets.

The script checks that a dataset root contains lr_<L>, hr_<R>, and sr_<L>_<R>
directories, counts supported image files in each subtree, and verifies that the
relative image paths match.

It is self-contained and does not import the source repository.

Example:
    python scripts/validate_dataset_layout.py \
        --root ./tiny_fixture \
        --l-resolution 16 \
        --r-resolution 128
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".ppm", ".bmp"}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def collect_image_relpaths(root: Path) -> List[str]:
    relpaths: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for filename in sorted(filenames):
            candidate = Path(dirpath) / filename
            if supported_image(candidate):
                relpaths.append(candidate.relative_to(root).as_posix())
    return sorted(relpaths)


def layout_roots(root: Path, l_resolution: int, r_resolution: int) -> Dict[str, Path]:
    return {
        f"lr_{l_resolution}": root / f"lr_{l_resolution}",
        f"hr_{r_resolution}": root / f"hr_{r_resolution}",
        f"sr_{l_resolution}_{r_resolution}": root / f"sr_{l_resolution}_{r_resolution}",
    }


def format_list(values: Sequence[str], limit: int = 5) -> str:
    if not values:
        return "[]"
    shown = list(values[:limit])
    suffix = "" if len(values) <= limit else f" ... (+{len(values) - limit} more)"
    return "[" + ", ".join(shown) + "]" + suffix


def compare_layouts(layouts: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not layouts:
        return False, ["no image directories were found"]

    names = list(layouts.keys())
    reference_paths = layouts[names[0]]

    for name, paths in layouts.items():
        if not paths:
            errors.append(f"{name}: no supported image files found")

    if errors:
        return False, errors

    counts = {name: len(paths) for name, paths in layouts.items()}
    unique_counts = set(counts.values())
    if len(unique_counts) != 1:
        joined = ", ".join(f"{name}={counts[name]}" for name in layouts)
        errors.append(f"count mismatch: {joined}")

    ref_set = set(reference_paths)
    for name, paths in layouts.items():
        current_set = set(paths)
        if current_set != ref_set:
            only_ref = sorted(ref_set - current_set)
            only_current = sorted(current_set - ref_set)
            if only_ref:
                errors.append(f"{name}: missing relative paths {format_list(only_ref)}")
            if only_current:
                errors.append(f"{name}: unexpected relative paths {format_list(only_current)}")

    return not errors, errors


def validate_dataset_layout(root: Path, l_resolution: int, r_resolution: int) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if l_resolution >= r_resolution:
        errors.append("expected l-resolution to be smaller than r-resolution for SR triplets")
        return False, errors

    if not root.is_dir():
        errors.append(f"{root} is not a directory")
        return False, errors

    roots = layout_roots(root, l_resolution, r_resolution)
    layouts: Dict[str, List[str]] = {}
    for name, path in roots.items():
        if not path.is_dir():
            errors.append(f"missing directory: {path}")
            continue
        layouts[name] = collect_image_relpaths(path)

    if errors:
        return False, errors

    ok, layout_errors = compare_layouts(layouts)
    if not ok:
        errors.extend(layout_errors)
        return False, errors

    summary = [f"{name}={len(paths)}" for name, paths in layouts.items()]
    return True, [f"layout ok: {', '.join(summary)}"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an LR/HR/SR image-directory dataset layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        required=True,
        type=Path,
        help="Dataset root that contains lr_<L>, hr_<R>, and sr_<L>_<R> directories.",
    )
    parser.add_argument(
        "--l-resolution",
        required=True,
        type=positive_int,
        help="Low-resolution size used in the directory name.",
    )
    parser.add_argument(
        "--r-resolution",
        required=True,
        type=positive_int,
        help="High-resolution size used in the directory name.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ok, messages = validate_dataset_layout(args.root, args.l_resolution, args.r_resolution)
    for message in messages:
        prefix = "OK" if ok else "ERROR"
        print(f"{prefix}: {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
