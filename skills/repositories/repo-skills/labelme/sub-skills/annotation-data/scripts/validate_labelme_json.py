#!/usr/bin/env python3
"""Validate or summarize labelme Annotation Files without importing labelme."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from labelme_json_core import load_label_file, parse_labels  # noqa: E402, I001


_EXPECTED_POINT_COUNTS = {
    "point": 1,
    "rectangle": 2,
    "line": 2,
    "circle": 2,
    "mask": 2,
    "oriented_rectangle": 4,
}


def _validate_flags(value: object, *, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be dict: {value!r}")
    if not all(
        isinstance(key, str) and isinstance(flag, bool) for key, flag in value.items()
    ):
        raise TypeError(f"{field} must be dict of str to bool: {value!r}")


def _validate_codec_shape_contract(path: Path) -> None:
    """Apply the current ``labelme._label_file`` shape invariants.

    The historical ``examples/utils.py`` reader defaults a missing
    ``shape_type`` to ``polygon`` for compatibility.  The installed codec does
    not: it requires the field and enforces exact point counts for fixed-size
    shapes.  Keep this validator aligned with the codec so a successful check
    is useful before a GUI load or a conversion.
    """
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("top-level JSON value must be an object")
    _validate_flags(raw.get("flags"), field="flags")
    for field in ("imageHeight", "imageWidth"):
        value = raw.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise TypeError(f"{field} must be int: {value!r}")

    shapes = raw.get("shapes")
    if not isinstance(shapes, list):
        raise TypeError(f"shapes must be list: {shapes!r}")

    for index, shape in enumerate(shapes):
        prefix = f"shapes[{index}]"
        if not isinstance(shape, dict):
            raise TypeError(f"{prefix} must be dict: {shape!r}")
        if "shape_type" not in shape:
            raise ValueError(f"{prefix}: shape_type is required")
        if not isinstance(shape["shape_type"], str):
            raise TypeError(
                f"{prefix}: shape_type must be str: {shape['shape_type']!r}"
            )

        points = shape.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError(f"{prefix}: points must be a non-empty list")
        if not all(
            isinstance(point, list)
            and len(point) == 2
            and all(
                isinstance(coordinate, int | float) and not isinstance(coordinate, bool)
                for coordinate in point
            )
            for point in points
        ):
            raise ValueError(f"{prefix}: points must be list of [x, y]")
        try:
            coordinates_are_finite = all(
                math.isfinite(coordinate) for point in points for coordinate in point
            )
        except OverflowError:
            coordinates_are_finite = False
        if not coordinates_are_finite:
            raise ValueError(
                f"{prefix}: points must contain finite coordinates: {points!r}"
            )

        expected = _EXPECTED_POINT_COUNTS.get(shape["shape_type"])
        if expected is not None and len(points) != expected:
            noun = "point" if expected == 1 else "points"
            raise ValueError(
                f"{prefix}: points must contain exactly {expected} {noun} for "
                f"shape_type={shape['shape_type']!r}: {points!r}"
            )

        _validate_flags(shape.get("flags"), field=f"{prefix}.flags")
        if shape.get("description") is not None and not isinstance(
            shape["description"], str
        ):
            raise TypeError(
                f"{prefix}: description must be str: {shape['description']!r}"
            )
        group_id = shape.get("group_id")
        if group_id is not None and (
            isinstance(group_id, bool) or not isinstance(group_id, int)
        ):
            raise TypeError(f"{prefix}: group_id must be int: {group_id!r}")


def _validate_loaded_masks(shapes: list[dict[str, Any]]) -> None:
    for index, shape in enumerate(shapes):
        if shape["shape_type"] == "mask":
            mask = shape["mask"]
            if mask is None or mask.ndim != 2:
                shape_index = f"shapes[{index}]"
                actual = None if mask is None else mask.shape
                raise ValueError(
                    f"{shape_index}: mask must decode to a 2D image, got {actual}"
                )


def _summarize(
    path: Path, *, require_image_file: bool, labels: set[str] | None
) -> dict[str, Any]:
    _validate_codec_shape_contract(path)
    data = load_label_file(path, require_image_file=require_image_file)
    _validate_loaded_masks(data.shapes)
    shape_types = Counter(shape["shape_type"] for shape in data.shapes)
    shape_labels = Counter(shape["label"] for shape in data.shapes)
    unknown_labels = sorted(set(shape_labels) - labels) if labels is not None else []
    return {
        "path": str(path),
        "imagePath": data.raw.get("imagePath"),
        "imageDataEmbedded": data.raw.get("imageData") is not None,
        "imageHeight": data.raw.get("imageHeight"),
        "imageWidth": data.raw.get("imageWidth"),
        "numShapes": len(data.shapes),
        "numFlags": len(data.flags),
        "shapeTypes": dict(sorted(shape_types.items())),
        "shapeLabels": dict(sorted(shape_labels.items())),
        "unknownLabels": unknown_labels,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_files", nargs="+", type=Path)
    parser.add_argument(
        "--labels",
        help="label file or comma-separated label list for exact vocabulary checks",
    )
    parser.add_argument(
        "--allow-missing-image-file",
        action="store_true",
        help="do not fail when imageData is null and imagePath is unavailable",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    labels = set(parse_labels(args.labels)) if args.labels else None
    summaries = []
    ok = True
    for path in args.json_files:
        try:
            summary = _summarize(
                path,
                require_image_file=not args.allow_missing_image_file,
                labels=labels,
            )
            if summary["unknownLabels"]:
                ok = False
                summary["error"] = "labels missing from supplied vocabulary"
            summaries.append(summary)
        except Exception as exc:
            ok = False
            summaries.append(
                {"path": str(path), "error": f"{type(exc).__name__}: {exc}"}
            )

    if args.json:
        print(json.dumps(summaries, indent=2, sort_keys=True))
    else:
        for item in summaries:
            print(item["path"])
            if "error" in item:
                print(f"  ERROR: {item['error']}")
                if item.get("unknownLabels"):
                    print(f"  unknown labels: {', '.join(item['unknownLabels'])}")
                continue
            print(f"  image: {item['imagePath']} embedded={item['imageDataEmbedded']}")
            print(f"  shapes: {item['numShapes']} {item['shapeTypes']}")
            print(
                "  labels: "
                f"{', '.join(item['shapeLabels']) if item['shapeLabels'] else '<none>'}"
            )
            print(f"  flags: {item['numFlags']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
