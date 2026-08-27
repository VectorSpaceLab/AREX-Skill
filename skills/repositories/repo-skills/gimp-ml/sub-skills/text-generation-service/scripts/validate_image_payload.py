#!/usr/bin/env python3
"""Validate the service's local JSON/base64 raw-image protocol.

This tool only reads a JSON document. It never contacts a service, provider,
or filesystem output path. Decoding is in-memory and the wire dtype is fixed
at uint8 by the observed service contract.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate image/mask base64, positive shape, uint8 dtype, and "
            "decoded byte length without network access."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("-"),
        help="JSON file to read; use '-' or omit to read stdin.",
    )
    parser.add_argument(
        "--field",
        action="append",
        choices=("image", "mask"),
        help="Field to validate; repeat for both. Default: image.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate image and mask when mask is present; useful for edit payloads.",
    )
    parser.add_argument(
        "--dtype",
        default="uint8",
        help="Expected dtype metadata (the service wire contract permits only uint8).",
    )
    parser.add_argument(
        "--decode",
        action="store_true",
        help="Report an in-memory decode preview after validation; never writes bytes.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        if str(path) == "-":
            return json.load(sys.stdin)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"input JSON does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def validate_shape(value: Any, field: str) -> list[int]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field}_shape must be a non-empty JSON array of positive integers")
    shape: list[int] = []
    for index, dimension in enumerate(value):
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0:
            raise ValueError(f"{field}_shape[{index}] must be a positive integer")
        shape.append(dimension)
    return shape


def decode_field(payload: dict[str, Any], field: str, expected_dtype: str) -> tuple[bytes, list[int]]:
    if field not in payload:
        raise ValueError(f"missing required field {field!r}")
    shape_key = f"{field}_shape"
    if shape_key not in payload:
        raise ValueError(f"missing required field {shape_key!r}")
    encoded = payload[field]
    if not isinstance(encoded, str):
        raise ValueError(f"{field} must be a base64 JSON string")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field} is not valid standard base64: {exc}") from exc

    shape = validate_shape(payload[shape_key], field)
    dtype_metadata = payload.get("dtype", "uint8")
    if dtype_metadata != expected_dtype:
        raise ValueError(
            f"dtype metadata {dtype_metadata!r} does not match requested {expected_dtype!r}"
        )
    if expected_dtype != "uint8":
        raise ValueError("the service protocol is fixed to dtype uint8; use --dtype uint8")

    elements = math.prod(shape)
    expected_bytes = elements  # uint8 has one byte per element.
    if len(raw) != expected_bytes:
        raise ValueError(
            f"{field} byte length mismatch: decoded {len(raw)} bytes, "
            f"shape {shape} requires {expected_bytes} uint8 bytes"
        )
    return raw, shape


def main() -> int:
    args = parse_args()
    if args.dtype != "uint8":
        print("ERROR: only dtype uint8 is valid for this service protocol", file=sys.stderr)
        return 2
    try:
        payload = load_json(args.input)
        if not isinstance(payload, dict):
            raise ValueError("top-level JSON value must be an object")
        if args.all:
            fields = ["image"]
            if "mask" in payload or "mask_shape" in payload:
                fields.append("mask")
        else:
            fields = args.field or ["image"]

        for field in fields:
            raw, shape = decode_field(payload, field, args.dtype)
            line = f"OK {field}: shape={shape} dtype=uint8 bytes={len(raw)}"
            if args.decode:
                preview = raw[:16].hex(" ") or "<empty>"
                line += f" preview={preview}"
            print(line)
        return 0
    except (OSError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
