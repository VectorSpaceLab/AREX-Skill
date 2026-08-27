#!/usr/bin/env python3
"""Validate a Pytorch-UNet image/mask dataset layout without training.

The checker is intentionally safe: it does not download data, does not import
W&B, does not mutate the dataset, and only opens a bounded number of image/mask
pairs to verify names, dimensions, scale, and mask values.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
from PIL import Image


def emit(payload: Dict[str, Any], code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Pytorch-UNet image/mask dataset layout")
    parser.add_argument("--images", required=True, help="Directory containing input images")
    parser.add_argument("--masks", required=True, help="Directory containing target masks")
    parser.add_argument("--carvana", action="store_true", help="Expect masks named <image-id>_mask.<ext>")
    parser.add_argument("--mask-suffix", default=None, help="Override mask suffix. Defaults to _mask with --carvana, otherwise empty.")
    parser.add_argument("--scale", type=float, default=1.0, help="Training scale to validate; must be >0 and <=1")
    parser.add_argument("--max-pairs", type=int, default=50, help="Maximum image/mask pairs to open for dimension and mask-value checks")
    parser.add_argument("--allow-subdirs", action="store_true", help="Do not fail when immediate subdirectories are present")
    return parser.parse_args()


def visible_files(directory: Path) -> List[Path]:
    return sorted(p for p in directory.iterdir() if p.is_file() and not p.name.startswith("."))


def hidden_files(directory: Path) -> List[str]:
    return sorted(p.name for p in directory.iterdir() if p.is_file() and p.name.startswith("."))


def immediate_subdirs(directory: Path) -> List[str]:
    return sorted(p.name for p in directory.iterdir() if p.is_dir() and not p.name.startswith("."))


def stem(path: Path) -> str:
    return path.stem


def duplicate_stems(files: Iterable[Path]) -> Dict[str, List[str]]:
    by_id: Dict[str, List[str]] = defaultdict(list)
    for path in files:
        by_id[stem(path)].append(path.name)
    return {key: names for key, names in sorted(by_id.items()) if len(names) > 1}


def mask_id(path: Path, suffix: str) -> str:
    value = stem(path)
    if suffix and value.endswith(suffix):
        return value[: -len(suffix)]
    return value


def values_for_json(values: np.ndarray, max_values: int) -> Tuple[List[Any], bool]:
    truncated = int(values.shape[0]) > max_values
    return values[:max_values].tolist(), truncated


def mask_values(path: Path, max_values: int = 32) -> Dict[str, Any]:
    try:
        arr = np.asarray(Image.open(path))
    except Exception as exc:  # Pillow reports useful format and corruption errors.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if arr.ndim == 2:
        unique = np.unique(arr)
        values, truncated = values_for_json(unique, max_values)
        return {"ok": True, "ndim": 2, "count": int(unique.size), "values": values, "truncated": truncated}
    if arr.ndim == 3:
        flat = arr.reshape(-1, arr.shape[-1])
        unique = np.unique(flat, axis=0)
        values, truncated = values_for_json(unique, max_values)
        return {"ok": True, "ndim": 3, "count": int(unique.shape[0]), "values": values, "truncated": truncated}
    return {"ok": False, "error": f"mask array must have 2 or 3 dimensions, found {arr.ndim}"}


def normalize_mask_value(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value, separators=(",", ":"))
    return json.dumps(value)


def summarize_combined_values(mask_summaries: List[Dict[str, Any]], max_values: int = 64) -> Dict[str, Any]:
    seen: Dict[str, Any] = {}
    skipped = 0
    for summary in mask_summaries:
        if not summary.get("ok"):
            skipped += 1
            continue
        for value in summary.get("values", []):
            seen.setdefault(normalize_mask_value(value), value)
    ordered = [seen[key] for key in sorted(seen)]
    return {"count_sampled_unique": len(ordered), "values": ordered[:max_values], "truncated": len(ordered) > max_values, "skipped_masks": skipped}


def main() -> None:
    args = parse_args()
    images = Path(args.images)
    masks = Path(args.masks)
    suffix = args.mask_suffix if args.mask_suffix is not None else ("_mask" if args.carvana else "")
    errors: List[Dict[str, Any]] = []
    warnings: List[str] = []

    if not images.is_dir():
        emit({"ok": False, "errors": [{"type": "missing-images-dir", "path": str(images)}]}, 2)
    if not masks.is_dir():
        emit({"ok": False, "errors": [{"type": "missing-masks-dir", "path": str(masks)}]}, 2)
    if not (0 < args.scale <= 1):
        errors.append({"type": "invalid-scale", "scale": args.scale, "message": "scale must satisfy 0 < scale <= 1"})
    if args.max_pairs <= 0:
        errors.append({"type": "invalid-max-pairs", "max_pairs": args.max_pairs})

    image_subdirs = immediate_subdirs(images)
    mask_subdirs = immediate_subdirs(masks)
    if (image_subdirs or mask_subdirs) and not args.allow_subdirs:
        errors.append({"type": "subdirectories-present", "image_subdirs": image_subdirs, "mask_subdirs": mask_subdirs})

    image_files = visible_files(images)
    mask_files = visible_files(masks)
    hidden = {"images": hidden_files(images), "masks": hidden_files(masks)}
    if not image_files:
        errors.append({"type": "no-input-files", "directory": str(images)})

    image_duplicates = duplicate_stems(image_files)
    if image_duplicates:
        errors.append({"type": "duplicate-image-ids", "duplicates": image_duplicates, "message": "only one visible image file per ID is compatible with BasicDataset"})

    checked_pairs: List[Dict[str, Any]] = []
    mask_value_summaries: List[Dict[str, Any]] = []
    matched_mask_names = set()
    for img in image_files[: args.max_pairs]:
        image_key = stem(img)
        matches = sorted(masks.glob(image_key + suffix + ".*"))
        matches = [m for m in matches if m.is_file() and not m.name.startswith(".")]
        if len(matches) != 1:
            errors.append({"type": "mask-match-count", "image": img.name, "expected_mask_pattern": image_key + suffix + ".*", "count": len(matches), "matches": [m.name for m in matches[:10]]})
            continue
        mask = matches[0]
        matched_mask_names.add(mask.name)
        try:
            with Image.open(img) as im, Image.open(mask) as ma:
                image_size: Tuple[int, int] = im.size
                mask_size: Tuple[int, int] = ma.size
                mode = im.mode
                mask_mode = ma.mode
        except Exception as exc:
            errors.append({"type": "open-failed", "image": img.name, "mask": mask.name, "error": f"{type(exc).__name__}: {exc}"})
            continue
        if image_size != mask_size:
            errors.append({"type": "size-mismatch", "image": img.name, "mask": mask.name, "image_size": list(image_size), "mask_size": list(mask_size)})
        new_w, new_h = int(args.scale * image_size[0]), int(args.scale * image_size[1])
        if new_w <= 0 or new_h <= 0:
            errors.append({"type": "scale-too-small", "image": img.name, "image_size": list(image_size), "scale": args.scale, "resized": [new_w, new_h]})
        mv = mask_values(mask)
        mask_value_summaries.append({"mask": mask.name, **mv})
        checked_pairs.append({"image": img.name, "mask": mask.name, "image_size": list(image_size), "image_mode": mode, "mask_mode": mask_mode, "resized": [new_w, new_h]})

    if len(image_files) > args.max_pairs:
        warnings.append(f"checked first {args.max_pairs} of {len(image_files)} visible image files")

    if mask_files:
        expected_mask_ids = {stem(p) for p in image_files[: args.max_pairs]}
        extra_masks = [p.name for p in mask_files if p.name not in matched_mask_names and mask_id(p, suffix) not in expected_mask_ids]
        if extra_masks:
            warnings.append(f"{len(extra_masks)} visible mask files were not matched by checked image IDs")

    payload = {
        "ok": not errors,
        "images_dir": str(images),
        "masks_dir": str(masks),
        "mask_suffix": suffix,
        "scale": args.scale,
        "visible_image_files": len(image_files),
        "visible_mask_files": len(mask_files),
        "hidden_files_ignored": {"images": len(hidden["images"]), "masks": len(hidden["masks"]), "image_examples": hidden["images"][:10], "mask_examples": hidden["masks"][:10]},
        "checked_pairs": checked_pairs,
        "mask_values_sample": mask_value_summaries,
        "combined_mask_values_sample": summarize_combined_values(mask_value_summaries),
        "warnings": warnings,
        "errors": errors,
    }
    emit(payload, 0 if not errors else 1)


if __name__ == "__main__":
    main()
