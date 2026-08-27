#!/usr/bin/env python3
"""Validate COCO-style prediction JSON before Detectron2 visualization.

This helper performs schema and metadata-hint checks only. It does not import
Detectron2, register datasets, read images, draw masks, or create output files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


REQUIRED_FIELDS = ("image_id", "category_id", "bbox", "score")


class IssueCollector:
    def __init__(self, max_errors: int) -> None:
        self.max_errors = max_errors
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def truncated(self) -> bool:
        return len(self.errors) >= self.max_errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def parse_category_ids(raw_values: Sequence[str] | None) -> set[int] | None:
    if not raw_values:
        return None
    parsed: set[int] = set()
    for raw_value in raw_values:
        for token in raw_value.split(","):
            token = token.strip()
            if not token:
                continue
            parsed.add(int(token))
    return parsed


def load_thing_classes(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    payload = load_json(path)
    if isinstance(payload, list) and all(isinstance(item, str) for item in payload):
        return payload
    if isinstance(payload, dict):
        value = payload.get("thing_classes")
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
    raise ValueError("thing classes file must be a JSON string list or contain key 'thing_classes'")


def validate_bbox(index: int, bbox: Any, issues: IssueCollector) -> None:
    if not isinstance(bbox, list) or len(bbox) != 4:
        issues.error(f"prediction[{index}].bbox must be a list of four numbers in XYWH_ABS order")
        return
    if not all(is_number(value) for value in bbox):
        issues.error(f"prediction[{index}].bbox contains non-finite or non-numeric values")
        return
    _, _, width, height = bbox
    if width < 0 or height < 0:
        issues.error(f"prediction[{index}].bbox has negative width or height")
    if width == 0 or height == 0:
        issues.warning(f"prediction[{index}].bbox has zero width or height")


def validate_segmentation(index: int, segmentation: Any, issues: IssueCollector) -> None:
    if segmentation is None:
        return
    if isinstance(segmentation, dict):
        size = segmentation.get("size")
        counts = segmentation.get("counts")
        if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) for v in size)):
            issues.error(f"prediction[{index}].segmentation RLE needs integer size [height, width]")
        if not isinstance(counts, (str, list)):
            issues.error(f"prediction[{index}].segmentation RLE needs counts as string or list")
        return
    if isinstance(segmentation, list):
        for polygon_index, polygon in enumerate(segmentation):
            if not isinstance(polygon, list):
                issues.error(f"prediction[{index}].segmentation[{polygon_index}] must be a polygon list")
                continue
            if len(polygon) < 6 or len(polygon) % 2:
                issues.error(
                    f"prediction[{index}].segmentation[{polygon_index}] needs an even length >= 6"
                )
                continue
            if not all(is_number(value) for value in polygon):
                issues.error(
                    f"prediction[{index}].segmentation[{polygon_index}] contains non-numeric values"
                )
        return
    issues.error(f"prediction[{index}].segmentation must be polygon list or RLE dict when present")


def validate_prediction(
    index: int,
    item: Any,
    issues: IssueCollector,
    allowed_category_ids: set[int] | None,
    require_segmentation: bool,
) -> tuple[Any, int | None]:
    if not isinstance(item, dict):
        issues.error(f"prediction[{index}] must be an object")
        return None, None

    for field in REQUIRED_FIELDS:
        if field not in item:
            issues.error(f"prediction[{index}] missing required field '{field}'")

    image_id = item.get("image_id")
    if isinstance(image_id, bool) or not isinstance(image_id, (int, str)):
        issues.error(f"prediction[{index}].image_id must be a string or integer")

    category_id = item.get("category_id")
    category_int: int | None = None
    if isinstance(category_id, bool) or not isinstance(category_id, int):
        issues.error(f"prediction[{index}].category_id must be an integer dataset category id")
    else:
        category_int = category_id
        if allowed_category_ids is not None and category_id not in allowed_category_ids:
            issues.error(f"prediction[{index}].category_id {category_id} is not in allowed ids")

    validate_bbox(index, item.get("bbox"), issues)

    score = item.get("score")
    if not is_number(score):
        issues.error(f"prediction[{index}].score must be a finite number")
    elif not 0.0 <= score <= 1.0:
        issues.warning(f"prediction[{index}].score {score} is outside the usual [0, 1] range")

    if require_segmentation and "segmentation" not in item:
        issues.error(f"prediction[{index}] missing required segmentation")
    if "segmentation" in item:
        validate_segmentation(index, item.get("segmentation"), issues)

    return image_id, category_int


def contiguous_metadata_warnings(category_ids: Iterable[int], thing_classes: list[str] | None) -> list[str]:
    if thing_classes is None:
        return []
    category_set = set(category_ids)
    if not category_set:
        return []
    warnings: list[str] = []
    class_count = len(thing_classes)
    if min(category_set) >= 1 and max(category_set) > class_count - 1:
        warnings.append(
            "category ids look like dataset ids rather than contiguous class ids; map them before setting Instances.pred_classes"
        )
    if any(category_id < 0 for category_id in category_set):
        warnings.append("negative category ids are not valid contiguous Detectron2 class ids")
    if any(0 <= category_id < class_count for category_id in category_set):
        warnings.append(
            "some category ids fit thing_classes directly; confirm whether JSON uses dataset ids or contiguous ids"
        )
    return warnings


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate COCO-style prediction JSON fields before visualization."
    )
    parser.add_argument("--input", required=True, type=Path, help="Prediction JSON file to validate.")
    parser.add_argument(
        "--category-ids",
        nargs="*",
        help="Optional allowed dataset category ids, comma-separated or space-separated.",
    )
    parser.add_argument(
        "--thing-classes-json",
        type=Path,
        help="Optional JSON list, or object with thing_classes, used for metadata warnings.",
    )
    parser.add_argument(
        "--require-segmentation",
        action="store_true",
        help="Require every prediction to include a segmentation field.",
    )
    parser.add_argument("--max-errors", type=int, default=25, help="Maximum errors to print.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be at least 1")

    try:
        predictions = load_json(args.input)
        allowed_category_ids = parse_category_ids(args.category_ids)
        thing_classes = load_thing_classes(args.thing_classes_json)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"failed to load validation inputs: {exc}", file=sys.stderr)
        return 2

    issues = IssueCollector(max_errors=args.max_errors)
    image_ids: list[Any] = []
    category_ids: list[int] = []

    if not isinstance(predictions, list):
        issues.error("top-level prediction JSON must be a list")
    else:
        for index, item in enumerate(predictions):
            image_id, category_id = validate_prediction(
                index,
                item,
                issues,
                allowed_category_ids,
                args.require_segmentation,
            )
            if image_id is not None:
                image_ids.append(image_id)
            if category_id is not None:
                category_ids.append(category_id)
            if issues.truncated:
                break

    for warning in contiguous_metadata_warnings(category_ids, thing_classes):
        issues.warning(warning)

    category_counter = Counter(category_ids)
    payload = {
        "ok": not issues.errors,
        "num_predictions": len(predictions) if isinstance(predictions, list) else None,
        "num_images": len(set(image_ids)),
        "category_counts": dict(sorted(category_counter.items())),
        "errors": issues.errors,
        "warnings": issues.warnings,
        "truncated_errors": issues.truncated,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"ok: {payload['ok']}")
        print(f"predictions: {payload['num_predictions']}")
        print(f"images: {payload['num_images']}")
        print(f"categories: {payload['category_counts']}")
        for error in issues.errors:
            print(f"error: {error}", file=sys.stderr)
        for warning in issues.warnings:
            print(f"warning: {warning}", file=sys.stderr)

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
