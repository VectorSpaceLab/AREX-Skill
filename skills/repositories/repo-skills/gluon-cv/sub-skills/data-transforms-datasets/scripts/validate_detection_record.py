#!/usr/bin/env python3
"""Validate a minimal object-detection JSON record file for GluonCV-style data.

The validator is intentionally independent of GluonCV and MXNet. It accepts a
small, practical JSON schema and checks image paths, non-empty classes, and
bounding-box coordinate order before a dataset is converted to VOC/LST/RecordIO
or passed into GluonCV transforms.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple


IMAGE_KEYS = ("image", "image_path", "path", "file", "filename")
RECORD_KEYS = ("records", "images", "items", "annotations")
ANNOTATION_KEYS = ("annotations", "objects", "labels", "targets")
CLASS_KEYS = ("classes", "class_names", "labels")
CLASS_ID_KEYS = ("class_id", "class", "category_id", "category", "label", "name")
BBOX_KEYS = ("bbox", "box")


@dataclass
class Issue:
    level: str
    where: str
    message: str


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate JSON detection records with GluonCV-style boxes "
            "[xmin, ymin, xmax, ymax, class_id]."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Accepted JSON examples:
  {
    "classes": ["dog", "bike"],
    "records": [
      {"image": "images/0001.jpg", "width": 640, "height": 480,
       "boxes": [[10, 20, 110, 200, 0], [50, 60, 300, 350, "bike"]]}
    ]
  }

  [
    {"image_path": "images/0001.jpg",
     "annotations": [{"bbox": [10, 20, 110, 200], "class_id": 0}]}
  ]

Examples:
  # Validate coordinates and class references only.
  python validate_detection_record.py records.json

  # Also check that image files exist under a dataset root.
  python validate_detection_record.py records.json --image-root /data/custom --check-files

  # Allow normalized boxes such as [0.1, 0.2, 0.7, 0.9, 0].
  python validate_detection_record.py records.json --normalized
""",
    )
    parser.add_argument("json_file", help="Path to a JSON detection record file.")
    parser.add_argument(
        "--image-root",
        default="",
        help="Root prepended to relative image paths when --check-files is set.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Require every image path to exist. By default, paths are only checked for being present.",
    )
    parser.add_argument(
        "--normalized",
        action="store_true",
        help="Treat box coordinates as normalized values and require them to be in [0, 1].",
    )
    parser.add_argument(
        "--allow-negative",
        action="store_true",
        help="Allow negative absolute coordinates when dimensions are unknown. Ordered boxes are still required.",
    )
    parser.add_argument(
        "--allow-empty-records",
        action="store_true",
        help="Permit images without boxes. Useful for validation sets; not recommended for detector training.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Stop reporting after this many errors. Use 0 for no limit.",
    )
    return parser.parse_args(argv)


def add(issues: List[Issue], level: str, where: str, message: str, max_errors: int) -> None:
    if max_errors and level == "error" and sum(i.level == "error" for i in issues) >= max_errors:
        return
    issues.append(Issue(level=level, where=where, message=message))


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def as_records(data: Any) -> Tuple[List[Any], List[str]]:
    """Return records and top-level class names if present."""
    classes: List[str] = []
    if isinstance(data, list):
        return data, classes
    if not isinstance(data, Mapping):
        raise ValueError("top-level JSON must be a list or object")

    for key in CLASS_KEYS:
        value = data.get(key)
        if isinstance(value, list) and all(not isinstance(x, Mapping) for x in value):
            classes = [str(x) for x in value]
            break
        if isinstance(value, list) and all(isinstance(x, Mapping) for x in value):
            extracted = []
            for item in value:
                if "name" in item:
                    extracted.append(str(item["name"]))
            if extracted:
                classes = extracted
                break

    for key in RECORD_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return value, classes

    # A single-record object is accepted if it has an image key.
    if any(k in data for k in IMAGE_KEYS):
        return [data], classes
    raise ValueError("object JSON must contain one of records/images/items/annotations or an image path")


def get_first(mapping: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def collect_classes(record: Any, top_classes: Sequence[str]) -> List[str]:
    classes = list(top_classes)
    if isinstance(record, Mapping):
        for key in CLASS_KEYS:
            value = record.get(key)
            if isinstance(value, list) and all(not isinstance(x, Mapping) for x in value):
                classes = [str(x) for x in value]
            elif isinstance(value, list) and all(isinstance(x, Mapping) for x in value):
                extracted = [str(x["name"]) for x in value if "name" in x]
                if extracted:
                    classes = extracted
    return classes


def class_ref_from_mapping(obj: Mapping[str, Any]) -> Any:
    return get_first(obj, CLASS_ID_KEYS)


def normalize_box_entry(entry: Any) -> Tuple[Optional[Sequence[Any]], Any]:
    """Return (bbox4, class_ref) from one annotation-like item."""
    if isinstance(entry, Mapping):
        bbox = get_first(entry, BBOX_KEYS)
        return bbox, class_ref_from_mapping(entry)
    if isinstance(entry, (list, tuple)):
        if len(entry) >= 5:
            return entry[:4], entry[4]
        if len(entry) == 4:
            return entry, None
    return None, None


def iter_annotations(record: Any) -> Iterable[Tuple[str, Any]]:
    if not isinstance(record, Mapping):
        yield "record", record
        return

    boxes = record.get("boxes")
    classes = record.get("classes") or record.get("class_ids") or record.get("labels")
    if isinstance(boxes, list):
        for i, box in enumerate(boxes):
            if isinstance(box, Mapping):
                yield f"boxes[{i}]", box
            elif isinstance(box, (list, tuple)) and len(box) == 4 and isinstance(classes, list) and i < len(classes):
                yield f"boxes[{i}]", list(box) + [classes[i]]
            else:
                yield f"boxes[{i}]", box

    for key in ANNOTATION_KEYS:
        value = record.get(key)
        if isinstance(value, list):
            for i, obj in enumerate(value):
                yield f"{key}[{i}]", obj
            return


def to_float(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def validate_class_ref(
    class_ref: Any,
    classes: Sequence[str],
    where: str,
    issues: List[Issue],
    max_errors: int,
) -> None:
    if class_ref is None:
        add(issues, "error", where, "missing class id/name for box", max_errors)
        return
    if isinstance(class_ref, bool):
        add(issues, "error", where, "class id cannot be boolean", max_errors)
        return
    if isinstance(class_ref, int):
        if class_ref < 0:
            add(issues, "error", where, f"class id must be non-negative, got {class_ref}", max_errors)
        elif classes and class_ref >= len(classes):
            add(
                issues,
                "error",
                where,
                f"class id {class_ref} outside class list of length {len(classes)}",
                max_errors,
            )
        return
    if isinstance(class_ref, float) and class_ref.is_integer():
        validate_class_ref(int(class_ref), classes, where, issues, max_errors)
        return
    name = str(class_ref).strip()
    if not name:
        add(issues, "error", where, "empty class name", max_errors)
    elif classes and name not in classes:
        add(issues, "error", where, f"class name {name!r} not in class list", max_errors)


def validate_box(
    bbox: Any,
    class_ref: Any,
    classes: Sequence[str],
    width: Optional[float],
    height: Optional[float],
    normalized: bool,
    allow_negative: bool,
    where: str,
    issues: List[Issue],
    max_errors: int,
) -> None:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        add(issues, "error", where, "bbox must be a list [xmin, ymin, xmax, ymax]", max_errors)
        return
    coords = [to_float(x) for x in bbox]
    if any(x is None for x in coords):
        add(issues, "error", where, "bbox coordinates must be finite numbers", max_errors)
        return
    xmin, ymin, xmax, ymax = coords  # type: ignore[misc]
    if not xmin < xmax:
        add(issues, "error", where, f"expected xmin < xmax, got {xmin} >= {xmax}", max_errors)
    if not ymin < ymax:
        add(issues, "error", where, f"expected ymin < ymax, got {ymin} >= {ymax}", max_errors)

    if normalized:
        for name, value in zip(("xmin", "ymin", "xmax", "ymax"), (xmin, ymin, xmax, ymax)):
            if value < 0 or value > 1:
                add(issues, "error", where, f"normalized {name} must be in [0, 1], got {value}", max_errors)
    else:
        if not allow_negative and (xmin < 0 or ymin < 0):
            add(issues, "error", where, f"coordinates must be non-negative, got xmin={xmin}, ymin={ymin}", max_errors)
        if width is not None and xmax > width:
            add(issues, "error", where, f"xmax {xmax} exceeds width {width}", max_errors)
        if height is not None and ymax > height:
            add(issues, "error", where, f"ymax {ymax} exceeds height {height}", max_errors)

    validate_class_ref(class_ref, classes, where, issues, max_errors)


def resolve_image(path_value: Any, image_root: str) -> Optional[str]:
    if path_value is None:
        return None
    path = str(path_value).strip()
    if not path:
        return None
    if os.path.isabs(path) or not image_root:
        return os.path.expanduser(path)
    return os.path.join(os.path.expanduser(image_root), path)


def validate_record(
    record: Any,
    record_index: int,
    top_classes: Sequence[str],
    args: argparse.Namespace,
    issues: List[Issue],
) -> int:
    where = f"record[{record_index}]"
    if not isinstance(record, Mapping):
        add(issues, "error", where, "record must be an object", args.max_errors)
        return 0

    classes = collect_classes(record, top_classes)
    if classes:
        empty = [i for i, c in enumerate(classes) if not str(c).strip()]
        if empty:
            add(issues, "error", where, f"class list contains empty entries at indices {empty}", args.max_errors)
        duplicates = sorted({c for c in classes if classes.count(c) > 1})
        if duplicates:
            add(issues, "warning", where, f"duplicate class names: {duplicates}", args.max_errors)

    image_path_value = get_first(record, IMAGE_KEYS)
    resolved = resolve_image(image_path_value, args.image_root)
    if resolved is None:
        add(issues, "error", where, "missing image path", args.max_errors)
    elif args.check_files and not os.path.isfile(resolved):
        add(issues, "error", where, f"image file does not exist: {resolved}", args.max_errors)

    width = to_float(record.get("width")) if "width" in record else None
    height = to_float(record.get("height")) if "height" in record else None
    if ("width" in record and width is None) or ("height" in record and height is None):
        add(issues, "error", where, "width/height must be finite numbers when provided", args.max_errors)
    if width is not None and width <= 0:
        add(issues, "error", where, f"width must be positive, got {width}", args.max_errors)
    if height is not None and height <= 0:
        add(issues, "error", where, f"height must be positive, got {height}", args.max_errors)

    count = 0
    for ann_where, annotation in iter_annotations(record):
        bbox, class_ref = normalize_box_entry(annotation)
        count += 1
        validate_box(
            bbox,
            class_ref,
            classes,
            width,
            height,
            args.normalized,
            args.allow_negative,
            f"{where}.{ann_where}",
            issues,
            args.max_errors,
        )
    if count == 0 and not args.allow_empty_records:
        add(issues, "error", where, "record has no boxes/annotations", args.max_errors)
    return count


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    issues: List[Issue] = []
    try:
        data = read_json(args.json_file)
        records, classes = as_records(data)
    except Exception as exc:  # noqa: BLE001 - user-facing CLI should print the parse error.
        print(f"ERROR: cannot read detection records: {exc}", file=sys.stderr)
        return 2

    if classes:
        empty = [i for i, c in enumerate(classes) if not str(c).strip()]
        if empty:
            add(issues, "error", "classes", f"top-level class list contains empty entries at indices {empty}", args.max_errors)
    else:
        add(
            issues,
            "warning",
            "classes",
            "no top-level class list found; numeric class ids will only be checked for non-negativity",
            args.max_errors,
        )

    total_boxes = 0
    for i, record in enumerate(records):
        total_boxes += validate_record(record, i, classes, args, issues)
        if args.max_errors and sum(x.level == "error" for x in issues) >= args.max_errors:
            add(issues, "warning", "summary", f"stopped after {args.max_errors} errors", args.max_errors)
            break

    for issue in issues:
        stream = sys.stderr if issue.level == "error" else sys.stdout
        print(f"{issue.level.upper()}: {issue.where}: {issue.message}", file=stream)

    errors = sum(1 for issue in issues if issue.level == "error")
    warnings = sum(1 for issue in issues if issue.level == "warning")
    print(
        f"Validated {len(records)} record(s), {total_boxes} box(es): {errors} error(s), {warnings} warning(s)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
