#!/usr/bin/env python3
"""Validate qdrant-client upload fixture shapes without connecting to Qdrant."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_spec(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_vector_sizes(entries: list[str]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for entry in entries:
        if "=" not in entry:
            raise argparse.ArgumentTypeError("vector sizes must look like name=size")
        name, raw_size = entry.split("=", 1)
        name = name.strip() or "default"
        try:
            size = int(raw_size)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid vector size: {entry}") from exc
        if size <= 0:
            raise argparse.ArgumentTypeError(f"vector size must be positive: {entry}")
        sizes[name] = size
    return sizes


def expected_size_for(label: str, sizes: dict[str, int]) -> int | None:
    parts = label.split(".")
    for part in reversed(parts):
        if part in sizes:
            return sizes[part]
    return sizes.get("default")


def add_error(errors: list[str], label: str, message: str) -> None:
    errors.append(f"{label}: {message}")


def validate_dense(vector: Any, label: str, sizes: dict[str, int], errors: list[str]) -> None:
    if not isinstance(vector, list) or not vector:
        add_error(errors, label, "dense vector must be a non-empty list of numbers")
        return
    if not all(is_number(value) for value in vector):
        add_error(errors, label, "dense vector contains non-numeric values")
        return
    expected = expected_size_for(label, sizes)
    if expected is not None and len(vector) != expected:
        add_error(errors, label, f"dense vector length {len(vector)} != expected {expected}")


def validate_sparse(vector: dict[str, Any], label: str, errors: list[str]) -> None:
    indices = vector.get("indices")
    values = vector.get("values")
    if not isinstance(indices, list) or not isinstance(values, list):
        add_error(errors, label, "sparse vector must contain list fields 'indices' and 'values'")
        return
    if len(indices) != len(values):
        add_error(errors, label, f"sparse indices length {len(indices)} != values length {len(values)}")
    if not all(isinstance(index, int) and not isinstance(index, bool) for index in indices):
        add_error(errors, label, "sparse indices must be integers")
    if not all(is_number(value) for value in values):
        add_error(errors, label, "sparse values must be numeric")


def validate_vector_struct(vector: Any, label: str, sizes: dict[str, int], errors: list[str]) -> None:
    if isinstance(vector, list):
        if not vector:
            add_error(errors, label, "vector list must not be empty")
        elif all(is_number(value) for value in vector):
            validate_dense(vector, label, sizes, errors)
        elif all(isinstance(row, list) for row in vector):
            for row_index, row in enumerate(vector):
                validate_dense(row, f"{label}.{row_index}", sizes, errors)
        else:
            add_error(errors, label, "list vector must be dense numbers or multivector rows")
        return

    if isinstance(vector, dict):
        if "indices" in vector or "values" in vector:
            validate_sparse(vector, label, errors)
            return
        if not vector:
            add_error(errors, label, "named vector dict must not be empty")
            return
        for name, subvector in vector.items():
            validate_vector_struct(subvector, f"{label}.{name}", sizes, errors)
        return

    add_error(errors, label, "vector must be a dense list, sparse dict, or named vector dict")


def validate_upload_points(spec: dict[str, Any], sizes: dict[str, int], errors: list[str]) -> int:
    points = spec.get("points")
    if not isinstance(points, list):
        add_error(errors, "points", "upload-points mode requires a list field 'points'")
        return 0
    for index, point in enumerate(points):
        label = f"points.{index}"
        if not isinstance(point, dict):
            add_error(errors, label, "point must be an object")
            continue
        if "id" not in point:
            add_error(errors, label, "point is missing 'id'")
        if "vector" not in point:
            add_error(errors, label, "point is missing 'vector'")
        else:
            validate_vector_struct(point["vector"], f"{label}.vector", sizes, errors)
        if "payload" in point and not isinstance(point["payload"], dict):
            add_error(errors, f"{label}.payload", "payload must be an object when present")
    return len(points)


def validate_named_vector_arrays(
    vectors: dict[str, Any], sizes: dict[str, int], errors: list[str]
) -> int | None:
    counts: dict[str, int] = {}
    for name, records in vectors.items():
        label = f"vectors.{name}"
        if not isinstance(records, list):
            add_error(errors, label, "named upload_collection vectors must be lists of per-point vectors")
            continue
        counts[name] = len(records)
        for index, record in enumerate(records):
            validate_vector_struct(record, f"{label}.{index}", sizes, errors)
    if not counts:
        return None
    unique_counts = set(counts.values())
    if len(unique_counts) != 1:
        add_error(errors, "vectors", f"named vector counts differ: {counts}")
    return next(iter(unique_counts))


def validate_upload_collection(spec: dict[str, Any], sizes: dict[str, int], errors: list[str]) -> int:
    vectors = spec.get("vectors")
    point_count = 0

    if isinstance(vectors, list):
        point_count = len(vectors)
        for index, vector in enumerate(vectors):
            validate_vector_struct(vector, f"vectors.{index}", sizes, errors)
    elif isinstance(vectors, dict):
        named_count = validate_named_vector_arrays(vectors, sizes, errors)
        point_count = named_count or 0
    else:
        add_error(errors, "vectors", "upload-collection mode requires 'vectors' as a list or named-vector object")

    for field in ("payload", "ids"):
        if field not in spec or spec[field] is None:
            continue
        if not isinstance(spec[field], list):
            add_error(errors, field, f"{field} must be a list when supplied")
            continue
        if len(spec[field]) != point_count:
            add_error(errors, field, f"length {len(spec[field])} != vector count {point_count}")

    payload = spec.get("payload")
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            if item is not None and not isinstance(item, dict):
                add_error(errors, f"payload.{index}", "payload item must be an object or null")

    return point_count


def infer_mode(spec: Any, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode
    if isinstance(spec, dict) and "points" in spec:
        return "upload-points"
    return "upload-collection"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="JSON spec path, or '-' for stdin")
    parser.add_argument(
        "--mode",
        choices=("auto", "upload-collection", "upload-points"),
        default="auto",
        help="Fixture mode. Default: infer from top-level keys.",
    )
    parser.add_argument(
        "--vector-size",
        action="append",
        default=[],
        metavar="NAME=SIZE",
        help="Expected dense vector size. Use default=SIZE for unnamed vectors or name=SIZE for named vectors.",
    )
    parser.add_argument("--expected-count", type=int, help="Expected number of points")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    if not isinstance(spec, dict):
        print(json.dumps({"ok": False, "errors": ["spec must be a JSON object"]}, indent=2))
        return 2

    sizes = parse_vector_sizes(args.vector_size)
    mode = infer_mode(spec, args.mode)
    errors: list[str] = []

    if mode == "upload-points":
        point_count = validate_upload_points(spec, sizes, errors)
    else:
        point_count = validate_upload_collection(spec, sizes, errors)

    if args.expected_count is not None and point_count != args.expected_count:
        add_error(errors, "expected-count", f"{point_count} != expected {args.expected_count}")

    result = {"ok": not errors, "mode": mode, "point_count": point_count, "errors": errors}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
