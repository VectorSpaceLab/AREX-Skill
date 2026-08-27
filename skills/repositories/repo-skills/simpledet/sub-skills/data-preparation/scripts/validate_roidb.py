#!/usr/bin/env python3
"""Validate a SimpleDet roidb pickle or JSON/JSONL record file.

The script is read-only. It never downloads data, mutates records, or runs a
model. It checks the structural contract used by the SimpleDet data-preparation
sub-skill:

- `gt_class`: one foreground id per instance, with `0` reserved for background
  and `-2` reserved for CrowdHuman ignore boxes.
- `gt_bbox`: xyxy boxes in image coordinates.
- `flipped`: usually `False` in cached roidbs.
- `h`, `w`, `image_url`, and `im_id`: image metadata required by the loaders.
- `gt_poly`: optional raw polygon list for mask workflows.

Examples:

    python skills/disco/simpledet/sub-skills/data-preparation/scripts/validate_roidb.py \
      --input data/cache/coco_train2017.roidb --check-images

    python skills/disco/simpledet/sub-skills/data-preparation/scripts/validate_roidb.py \
      --input records.json --format json

    python skills/disco/simpledet/sub-skills/data-preparation/scripts/validate_roidb.py \
      --input records.jsonl --format jsonl --max-records 3
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from collections.abc import Sequence
from numbers import Integral, Real
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - NumPy is optional for JSON-only checks.
    np = None

FLOAT32_SAFE_LIMIT = 16_777_216
REQUIRED_FIELDS = ("gt_class", "gt_bbox", "flipped", "h", "w", "image_url", "im_id")


class ValidationError(Exception):
    """Raised when the input file or record shape is invalid."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a SimpleDet roidb pickle or JSON/JSONL record file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to a .roidb, .pkl, .pickle, .json, or .jsonl file")
    parser.add_argument(
        "--format",
        choices=("auto", "pickle", "json", "jsonl"),
        default="auto",
        help="Input format. Auto uses the file extension.",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Verify that every image_url exists on disk",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Validate at most this many records; 0 means all records",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    return parser.parse_args(argv)


def infer_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested

    suffix = path.suffix.lower()
    if suffix in {".roidb", ".pkl", ".pickle"}:
        return "pickle"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".json":
        return "json"
    raise ValidationError(
        f"cannot infer the input format from {path}; use --format pickle, json, or jsonl"
    )


def load_records(path: Path, fmt: str) -> List[dict[str, Any]]:
    fmt = infer_format(path, fmt)

    if fmt == "pickle":
        if np is None:
            raise ValidationError(
                "pickle roidb validation requires NumPy. Install numpy or validate a JSON/JSONL file instead."
            )
        try:
            with path.open("rb") as fh:
                obj = pickle.load(fh)
        except ModuleNotFoundError as exc:
            raise ValidationError(
                "pickle roidb validation requires NumPy to unpickle stored arrays. Install numpy or use JSON/JSONL."
            ) from exc
        except Exception as exc:
            raise ValidationError(f"failed to load pickle roidb {path}: {exc}") from exc
        return normalize_records(obj, path)

    if fmt == "json":
        try:
            with path.open("r", encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception as exc:
            raise ValidationError(f"failed to load JSON input {path}: {exc}") from exc
        return normalize_records(obj, path)

    if fmt == "jsonl":
        records: List[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if not line.strip():
                        raise ValidationError(f"blank line at {path}:{lineno}")
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(f"invalid JSON at {path}:{lineno}: {exc}") from exc
                    if not isinstance(record, dict):
                        raise ValidationError(f"JSONL records must be JSON objects, got {type(record).__name__} at line {lineno}")
                    records.append(record)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(f"failed to load JSONL input {path}: {exc}") from exc
        return records

    raise ValidationError(f"unsupported format: {fmt}")


def normalize_records(obj: Any, path: Path) -> List[dict[str, Any]]:
    if isinstance(obj, list):
        if not all(isinstance(item, dict) for item in obj):
            bad_types = {type(item).__name__ for item in obj if not isinstance(item, dict)}
            raise ValidationError(
                f"{path} must contain a list of record objects; found non-dict entry types: {', '.join(sorted(bad_types))}"
            )
        return list(obj)

    if isinstance(obj, tuple):
        if not all(isinstance(item, dict) for item in obj):
            bad_types = {type(item).__name__ for item in obj if not isinstance(item, dict)}
            raise ValidationError(
                f"{path} must contain a tuple of record objects; found non-dict entry types: {', '.join(sorted(bad_types))}"
            )
        return list(obj)

    if isinstance(obj, dict):
        for key in ("roidb", "records", "data"):
            value = obj.get(key)
            if isinstance(value, (list, tuple)):
                return normalize_records(list(value), path)
        if looks_like_record(obj):
            return [obj]
        raise ValidationError(
            f"{path} must be a list of records or a wrapper with a roidb/records/data list"
        )

    raise ValidationError(f"{path} must decode to a list of records, not {type(obj).__name__}")


def looks_like_record(obj: dict[str, Any]) -> bool:
    keys = set(obj)
    return "gt_bbox" in keys or "gt_class" in keys or "image_url" in keys or "im_id" in keys


def is_sequence(value: Any) -> bool:
    if isinstance(value, (str, bytes, bytearray, dict)):
        return False
    if np is not None and isinstance(value, np.ndarray):
        return True
    return isinstance(value, Sequence)


def maybe_numpy_scalar(value: Any) -> Any:
    if np is not None and isinstance(value, np.generic):
        return value.item()
    return value


def parse_int_like(value: Any) -> Optional[int]:
    value = maybe_numpy_scalar(value)
    if isinstance(value, bool):
        return None
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        numeric = float(value)
        if math.isfinite(numeric):
            rounded = int(round(numeric))
            if abs(numeric - rounded) <= 1e-6:
                return rounded
    return None


def parse_float_like(value: Any) -> Optional[float]:
    value = maybe_numpy_scalar(value)
    if isinstance(value, bool):
        return None
    if isinstance(value, Real):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
    return None


def seq_to_list(value: Any) -> List[Any]:
    value = maybe_numpy_scalar(value)
    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    raise ValidationError(f"expected a sequence, got {type(value).__name__}")


def validate_record(record: dict[str, Any], index: int, check_images: bool) -> Tuple[List[str], List[str], int, bool]:
    errors: List[str] = []
    warnings: List[str] = []
    box_count = 0
    has_mask = False

    if not isinstance(record, dict):
        return [f"record {index}: expected a dict, got {type(record).__name__}"], warnings, box_count, has_mask

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        errors.append(f"record {index}: missing required field(s): {', '.join(missing)}")
        return errors, warnings, box_count, has_mask

    flipped = maybe_numpy_scalar(record["flipped"])
    if not isinstance(flipped, bool):
        errors.append(f"record {index}: flipped must be a bool, got {type(flipped).__name__}")
    elif flipped:
        warnings.append(f"record {index}: flipped=True in a cached roidb; expected False")

    h = parse_int_like(record["h"])
    w = parse_int_like(record["w"])
    if h is None or w is None:
        errors.append(f"record {index}: h and w must be integer-like values")
    elif h <= 0 or w <= 0:
        errors.append(f"record {index}: h and w must be positive, got h={h}, w={w}")

    image_url = record["image_url"]
    if not isinstance(image_url, str) or not image_url.strip():
        errors.append(f"record {index}: image_url must be a non-empty string")
    elif check_images and not Path(image_url).expanduser().exists():
        errors.append(f"record {index}: image_url does not exist: {image_url}")

    im_id = parse_int_like(record["im_id"])
    if im_id is None:
        errors.append(f"record {index}: im_id must be integer-like")
    elif abs(im_id) >= FLOAT32_SAFE_LIMIT:
        errors.append(
            f"record {index}: im_id={im_id} exceeds the float32-safe limit {FLOAT32_SAFE_LIMIT - 1}"
        )

    try:
        gt_class = seq_to_list(record["gt_class"])
    except ValidationError as exc:
        errors.append(f"record {index}: gt_class {exc}")
        return errors, warnings, box_count, has_mask

    try:
        gt_bbox = seq_to_list(record["gt_bbox"])
    except ValidationError as exc:
        errors.append(f"record {index}: gt_bbox {exc}")
        return errors, warnings, box_count, has_mask

    if len(gt_class) != len(gt_bbox):
        errors.append(
            f"record {index}: gt_class has {len(gt_class)} entries but gt_bbox has {len(gt_bbox)} rows"
        )
        return errors, warnings, box_count, has_mask

    box_count = len(gt_bbox)

    for cls_index, cls in enumerate(gt_class):
        class_id = parse_int_like(cls)
        if class_id is None:
            errors.append(f"record {index}: gt_class[{cls_index}] is not integer-like: {cls!r}")
            continue
        if class_id == 0:
            errors.append(f"record {index}: gt_class[{cls_index}] is 0; background is reserved")
        elif class_id < -2:
            errors.append(f"record {index}: gt_class[{cls_index}]={class_id} is below the supported ignore label -2")

    if h is not None and w is not None:
        out_of_bounds = 0
    else:
        out_of_bounds = 0

    for box_index, box in enumerate(gt_bbox):
        try:
            coords = seq_to_list(box)
        except ValidationError as exc:
            errors.append(f"record {index}: gt_bbox[{box_index}] {exc}")
            continue
        if len(coords) != 4:
            errors.append(f"record {index}: gt_bbox[{box_index}] must have 4 values, got {len(coords)}")
            continue
        numeric_coords: List[float] = []
        for coord_index, coord in enumerate(coords):
            value = parse_float_like(coord)
            if value is None:
                errors.append(
                    f"record {index}: gt_bbox[{box_index}][{coord_index}] is not finite numeric data: {coord!r}"
                )
                break
            numeric_coords.append(value)
        else:
            x1, y1, x2, y2 = numeric_coords
            if x2 < x1 or y2 < y1:
                errors.append(
                    f"record {index}: gt_bbox[{box_index}] has inverted corners: {numeric_coords}"
                )
            if h is not None and w is not None and (x1 < 0 or y1 < 0 or x2 > w or y2 > h):
                out_of_bounds += 1

    if out_of_bounds:
        warnings.append(
            f"record {index}: {out_of_bounds} bbox(es) extend outside the stored image bounds"
        )

    gt_poly = record.get("gt_poly")
    if gt_poly is not None:
        has_mask = True
        try:
            gt_poly_list = seq_to_list(gt_poly)
        except ValidationError as exc:
            errors.append(f"record {index}: gt_poly {exc}")
            return errors, warnings, box_count, has_mask

        if len(gt_poly_list) != len(gt_class):
            errors.append(
                f"record {index}: gt_poly has {len(gt_poly_list)} entries but gt_class has {len(gt_class)} entries"
            )
            return errors, warnings, box_count, has_mask

        for inst_index, inst in enumerate(gt_poly_list):
            if inst is None:
                continue
            try:
                polys = seq_to_list(inst)
            except ValidationError as exc:
                errors.append(f"record {index}: gt_poly[{inst_index}] {exc}")
                continue
            if not polys:
                errors.append(f"record {index}: gt_poly[{inst_index}] is empty")
                continue
            for poly_index, poly in enumerate(polys):
                try:
                    coords = seq_to_list(poly)
                except ValidationError as exc:
                    errors.append(f"record {index}: gt_poly[{inst_index}][{poly_index}] {exc}")
                    continue
                if len(coords) < 6 or len(coords) % 2 != 0:
                    errors.append(
                        f"record {index}: gt_poly[{inst_index}][{poly_index}] must have an even length of at least 6, got {len(coords)}"
                    )
                    continue
                for coord_index, coord in enumerate(coords):
                    value = parse_float_like(coord)
                    if value is None:
                        errors.append(
                            f"record {index}: gt_poly[{inst_index}][{poly_index}][{coord_index}] is not finite numeric data: {coord!r}"
                        )
                        break

    return errors, warnings, box_count, has_mask


def validate_records(
    records: List[dict[str, Any]],
    check_images: bool,
    max_records: int,
) -> Tuple[List[str], List[str], dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    summary = {
        "records_total": len(records),
        "records_checked": 0,
        "boxes_total": 0,
        "mask_records": 0,
        "images_checked": bool(check_images),
        "truncated": False,
    }

    if not records:
        errors.append("input contains no records")
        return errors, warnings, summary

    if max_records > 0:
        checked = records[:max_records]
        summary["truncated"] = len(records) > max_records
    else:
        checked = records

    summary["records_checked"] = len(checked)

    for index, record in enumerate(checked):
        rec_errors, rec_warnings, box_count, has_mask = validate_record(record, index, check_images)
        errors.extend(rec_errors)
        warnings.extend(rec_warnings)
        summary["boxes_total"] += box_count
        if has_mask:
            summary["mask_records"] += 1

    if summary["boxes_total"] == 0:
        warnings.append("validated records contain no bounding boxes")

    if summary["truncated"]:
        warnings.append(
            f"validated only the first {summary['records_checked']} of {summary['records_total']} records"
        )

    return errors, warnings, summary


def print_issues(prefix: str, issues: Iterable[str]) -> None:
    for issue in issues:
        print(f"{prefix}: {issue}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    path = Path(args.input)
    if not path.exists():
        print(f"error: input file does not exist: {path}", file=sys.stderr)
        return 1

    try:
        records = load_records(path, args.format)
        errors, warnings, summary = validate_records(records, args.check_images, args.max_records)
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.strict and warnings:
        errors.extend(f"warning treated as error: {item}" for item in warnings)
        warnings = []

    if warnings:
        print_issues("warning", warnings)

    if errors:
        print_issues("error", errors)
        return 1

    print(
        "OK: validated {records_checked}/{records_total} record(s), {boxes_total} box(es), {mask_records} record(s) with masks".format(
            **summary
        )
    )
    if summary["truncated"]:
        print("OK: validation was truncated by --max-records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
