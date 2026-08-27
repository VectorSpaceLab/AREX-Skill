#!/usr/bin/env python3
"""Validate and summarize a COCO-style detection annotation JSON.

This helper is intentionally self-contained: it does not import MMYOLO,
MMDetection, pycocotools, OpenCV, or matplotlib. It is suitable for tiny
fixtures and pre-training data checks.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple

Issue = Dict[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate basic COCO detection JSON consistency and print a "
            "dataset summary. Exits non-zero when validation errors exist."
        )
    )
    parser.add_argument("ann_file", help="Path to a COCO-style annotation JSON file.")
    parser.add_argument(
        "--image-root",
        default=None,
        help=(
            "Optional image directory used to check images[*].file_name "
            "existence. Relative file names are joined under this directory."
        ),
    )
    parser.add_argument(
        "--require-annotations",
        action="store_true",
        help="Fail if the annotation file contains no annotations.",
    )
    parser.add_argument(
        "--allow-out-of-bounds",
        action="store_true",
        help="Warn instead of fail when bboxes extend outside image dimensions.",
    )
    parser.add_argument(
        "--strict-area",
        action="store_true",
        help="Fail when annotation area is missing, non-numeric, or inconsistent.",
    )
    parser.add_argument(
        "--area-tolerance",
        type=float,
        default=1e-3,
        help=(
            "Relative tolerance for comparing annotation area to bbox width*height "
            "when area is present. Default: 1e-3."
        ),
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return non-zero if warnings are present even when there are no errors.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=20,
        help="Maximum errors/warnings/category rows to print in text mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON summary instead of text.",
    )
    return parser.parse_args()


def add_issue(issues: List[Issue], code: str, message: str) -> None:
    issues.append({"code": code, "message": message})


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def require_int_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_json(path: Path, errors: List[Issue]) -> Optional[MutableMapping[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        add_issue(errors, "file-not-found", f"annotation file does not exist: {path}")
        return None
    except json.JSONDecodeError as exc:
        add_issue(errors, "json-decode", f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return None
    except OSError as exc:
        add_issue(errors, "file-read", f"could not read annotation file: {exc}")
        return None
    if not isinstance(data, MutableMapping):
        add_issue(errors, "top-level-type", "top-level COCO value must be a JSON object")
        return None
    return data


def get_list(data: MutableMapping[str, Any], key: str, errors: List[Issue]) -> List[Any]:
    value = data.get(key)
    if value is None:
        add_issue(errors, "missing-key", f"missing top-level key '{key}'")
        return []
    if not isinstance(value, list):
        add_issue(errors, "bad-key-type", f"top-level key '{key}' must be a list")
        return []
    return value


def check_unique_int_ids(
    rows: Iterable[Any],
    row_name: str,
    errors: List[Issue],
) -> Tuple[Dict[int, Dict[str, Any]], Counter]:
    by_id: Dict[int, Dict[str, Any]] = {}
    id_counter: Counter = Counter()
    for index, row in enumerate(rows):
        if not isinstance(row, MutableMapping):
            add_issue(errors, f"{row_name}-type", f"{row_name}[{index}] must be an object")
            continue
        row_id = row.get("id")
        if not require_int_id(row_id):
            add_issue(errors, f"{row_name}-id", f"{row_name}[{index}].id must be an integer")
            continue
        id_counter[row_id] += 1
        if row_id in by_id:
            add_issue(errors, f"duplicate-{row_name}-id", f"duplicate {row_name} id {row_id}")
        else:
            by_id[row_id] = dict(row)
    return by_id, id_counter


def validate_images(
    images: List[Any],
    image_root: Optional[Path],
    errors: List[Issue],
    warnings: List[Issue],
) -> Dict[int, Dict[str, Any]]:
    by_id, _ = check_unique_int_ids(images, "image", errors)
    for image_id, image in by_id.items():
        file_name = image.get("file_name")
        width = image.get("width")
        height = image.get("height")
        if not isinstance(file_name, str) or not file_name:
            add_issue(errors, "image-file-name", f"image id {image_id} has missing/invalid file_name")
        else:
            file_path = Path(file_name)
            if file_path.is_absolute():
                add_issue(warnings, "absolute-file-name", f"image id {image_id} uses an absolute file_name")
            if image_root is not None:
                resolved = file_path if file_path.is_absolute() else image_root / file_name
                if not resolved.exists():
                    add_issue(warnings, "missing-image-file", f"image file not found for id {image_id}: {file_name}")
        if not is_number(width) or width <= 0:
            add_issue(errors, "image-width", f"image id {image_id} has invalid width {width!r}")
        if not is_number(height) or height <= 0:
            add_issue(errors, "image-height", f"image id {image_id} has invalid height {height!r}")
    return by_id


def validate_categories(
    categories: List[Any],
    errors: List[Issue],
    warnings: List[Issue],
) -> Dict[int, Dict[str, Any]]:
    by_id, _ = check_unique_int_ids(categories, "category", errors)
    names: Counter = Counter()
    for cat_id, category in by_id.items():
        if cat_id < 0:
            add_issue(errors, "category-id-negative", f"category id {cat_id} is negative")
        name = category.get("name")
        if not isinstance(name, str) or not name.strip():
            add_issue(errors, "category-name", f"category id {cat_id} has missing/invalid name")
        else:
            names[name] += 1
    for name, count in names.items():
        if count > 1:
            add_issue(warnings, "duplicate-category-name", f"category name {name!r} appears {count} times")
    return by_id


def bbox_issue_prefix(ann_id: Any) -> str:
    return f"annotation id {ann_id}"


def validate_annotations(
    annotations: List[Any],
    images_by_id: Dict[int, Dict[str, Any]],
    categories_by_id: Dict[int, Dict[str, Any]],
    args: argparse.Namespace,
    errors: List[Issue],
    warnings: List[Issue],
) -> Tuple[Counter, Counter, List[float]]:
    by_id, _ = check_unique_int_ids(annotations, "annotation", errors)
    image_counts: Counter = Counter()
    category_counts: Counter = Counter()
    areas: List[float] = []

    if args.require_annotations and not annotations:
        add_issue(errors, "empty-annotations", "annotation file contains no annotations")

    for ann_id, ann in by_id.items():
        prefix = bbox_issue_prefix(ann_id)
        image_id = ann.get("image_id")
        category_id = ann.get("category_id")
        if not require_int_id(image_id):
            add_issue(errors, "annotation-image-id", f"{prefix} has invalid image_id {image_id!r}")
        elif image_id not in images_by_id:
            add_issue(errors, "unknown-image-id", f"{prefix} references missing image_id {image_id}")
        else:
            image_counts[image_id] += 1

        if not require_int_id(category_id):
            add_issue(errors, "annotation-category-id", f"{prefix} has invalid category_id {category_id!r}")
        elif category_id not in categories_by_id:
            add_issue(errors, "unknown-category-id", f"{prefix} references missing category_id {category_id}")
        else:
            category_counts[category_id] += 1

        bbox = ann.get("bbox")
        bbox_ok = False
        bbox_area: Optional[float] = None
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(is_number(v) for v in bbox):
            add_issue(errors, "bbox-format", f"{prefix} bbox must be four finite numbers [x, y, width, height]")
        else:
            x, y, width, height = [float(v) for v in bbox]
            if width <= 0 or height <= 0:
                add_issue(errors, "bbox-size", f"{prefix} bbox width/height must be positive, got {bbox!r}")
            else:
                bbox_ok = True
                bbox_area = width * height
                areas.append(bbox_area)
                if require_int_id(image_id) and image_id in images_by_id:
                    img = images_by_id[image_id]
                    img_w = img.get("width")
                    img_h = img.get("height")
                    if is_number(img_w) and is_number(img_h):
                        out = x < -1e-6 or y < -1e-6 or x + width > float(img_w) + 1e-6 or y + height > float(img_h) + 1e-6
                        if out:
                            target = warnings if args.allow_out_of_bounds else errors
                            add_issue(
                                target,
                                "bbox-out-of-bounds",
                                f"{prefix} bbox {bbox!r} exceeds image {image_id} size {img_w}x{img_h}",
                            )
        area = ann.get("area")
        if area is None:
            if args.strict_area:
                add_issue(errors, "missing-area", f"{prefix} is missing area")
        elif not is_number(area):
            add_issue(errors if args.strict_area else warnings, "area-type", f"{prefix} area is not a finite number")
        elif area <= 0:
            add_issue(errors if args.strict_area else warnings, "area-nonpositive", f"{prefix} area is non-positive: {area!r}")
        elif bbox_ok and bbox_area is not None:
            tolerance = args.area_tolerance * max(1.0, bbox_area)
            if abs(float(area) - bbox_area) > tolerance:
                add_issue(
                    errors if args.strict_area else warnings,
                    "area-mismatch",
                    f"{prefix} area {area!r} differs from bbox area {bbox_area:.6g}",
                )

        iscrowd = ann.get("iscrowd")
        if iscrowd is not None and iscrowd not in (0, 1, False, True):
            add_issue(warnings, "iscrowd-value", f"{prefix} has unusual iscrowd value {iscrowd!r}")

    return image_counts, category_counts, areas


def summarize(
    ann_file: Path,
    images: List[Any],
    categories: List[Any],
    annotations: List[Any],
    images_by_id: Dict[int, Dict[str, Any]],
    categories_by_id: Dict[int, Dict[str, Any]],
    image_counts: Counter,
    category_counts: Counter,
    areas: List[float],
    errors: List[Issue],
    warnings: List[Issue],
) -> Dict[str, Any]:
    categories_summary = []
    for cat_id, category in sorted(categories_by_id.items(), key=lambda item: item[0]):
        categories_summary.append(
            {
                "id": cat_id,
                "name": category.get("name"),
                "annotations": category_counts.get(cat_id, 0),
            }
        )
    empty_images = [image_id for image_id in images_by_id if image_counts.get(image_id, 0) == 0]
    empty_categories = [cat_id for cat_id in categories_by_id if category_counts.get(cat_id, 0) == 0]
    if empty_images:
        add_issue(warnings, "images-without-annotations", f"{len(empty_images)} images have no annotations")
    if empty_categories:
        add_issue(warnings, "categories-without-annotations", f"{len(empty_categories)} categories have no annotations")

    area_summary: Dict[str, Optional[float]] = {"min": None, "max": None, "mean": None}
    if areas:
        area_summary = {
            "min": min(areas),
            "max": max(areas),
            "mean": sum(areas) / len(areas),
        }

    return {
        "ann_file": str(ann_file),
        "counts": {
            "images": len(images),
            "valid_image_ids": len(images_by_id),
            "categories": len(categories),
            "valid_category_ids": len(categories_by_id),
            "annotations": len(annotations),
        },
        "bbox_area": area_summary,
        "categories": categories_summary,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def print_text(summary: Dict[str, Any], max_examples: int) -> None:
    counts = summary["counts"]
    print("COCO annotation summary")
    print(f"  file: {summary['ann_file']}")
    print(
        "  counts: "
        f"images={counts['images']} "
        f"categories={counts['categories']} "
        f"annotations={counts['annotations']}"
    )
    bbox_area = summary["bbox_area"]
    if bbox_area["min"] is not None:
        print(
            "  bbox area: "
            f"min={bbox_area['min']:.6g} mean={bbox_area['mean']:.6g} max={bbox_area['max']:.6g}"
        )
    print("  categories:")
    for row in summary["categories"][:max_examples]:
        print(f"    id={row['id']} name={row['name']!r} annotations={row['annotations']}")
    if len(summary["categories"]) > max_examples:
        print(f"    ... {len(summary['categories']) - max_examples} more categories")

    print(f"  errors: {summary['error_count']}")
    for issue in summary["errors"][:max_examples]:
        print(f"    [{issue['code']}] {issue['message']}")
    if len(summary["errors"]) > max_examples:
        print(f"    ... {len(summary['errors']) - max_examples} more errors")

    print(f"  warnings: {summary['warning_count']}")
    for issue in summary["warnings"][:max_examples]:
        print(f"    [{issue['code']}] {issue['message']}")
    if len(summary["warnings"]) > max_examples:
        print(f"    ... {len(summary['warnings']) - max_examples} more warnings")


def main() -> int:
    args = parse_args()
    errors: List[Issue] = []
    warnings: List[Issue] = []
    ann_file = Path(args.ann_file)
    image_root = Path(args.image_root) if args.image_root else None

    data = load_json(ann_file, errors)
    if data is None:
        summary = {
            "ann_file": str(ann_file),
            "counts": {"images": 0, "valid_image_ids": 0, "categories": 0, "valid_category_ids": 0, "annotations": 0},
            "bbox_area": {"min": None, "max": None, "mean": None},
            "categories": [],
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }
        if args.json:
            json.dump(summary, sys.stdout, indent=2)
            print()
        else:
            print_text(summary, args.max_examples)
        return 1

    images = get_list(data, "images", errors)
    categories = get_list(data, "categories", errors)
    annotations = get_list(data, "annotations", errors)

    images_by_id = validate_images(images, image_root, errors, warnings)
    categories_by_id = validate_categories(categories, errors, warnings)
    image_counts, category_counts, areas = validate_annotations(
        annotations, images_by_id, categories_by_id, args, errors, warnings
    )
    summary = summarize(
        ann_file,
        images,
        categories,
        annotations,
        images_by_id,
        categories_by_id,
        image_counts,
        category_counts,
        areas,
        errors,
        warnings,
    )

    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        print()
    else:
        print_text(summary, args.max_examples)

    if errors or (args.strict_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
