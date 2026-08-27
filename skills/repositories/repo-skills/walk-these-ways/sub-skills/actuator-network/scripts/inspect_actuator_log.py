#!/usr/bin/env python3
"""Read-only validator for Go1 actuator logs and portable JSON fixtures.

This helper deliberately does not import torch, matplotlib, or repository
modules. Pickle input must be trusted because unpickling can execute code.
"""

from __future__ import annotations

import argparse
import json
import math
import numbers
import pickle
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple


FIELDS: Tuple[str, ...] = (
    "joint_pos",
    "joint_pos_target",
    "joint_vel",
    "tau_est",
    "torques",
)
JOINTS = 12
MIN_RECORDS = 4


class InputError(ValueError):
    """A user-correctable input or schema error."""


def _to_python(value: Any) -> Any:
    """Convert common array/tensor-like wrappers without importing them."""
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist") and not isinstance(value, (list, tuple, str, bytes)):
        value = value.tolist()
    return value


def _shape(value: Any) -> List[Any]:
    value = _to_python(value)
    if isinstance(value, (list, tuple)):
        if not value:
            return [0]
        child_shapes = [_shape(child) for child in value]
        if all(shape == child_shapes[0] for shape in child_shapes[1:]):
            return [len(value)] + child_shapes[0]
        return [len(value), "ragged"]
    return []


def _flatten_numbers(value: Any) -> List[float]:
    value = _to_python(value)
    if isinstance(value, (list, tuple)):
        result: List[float] = []
        for child in value:
            result.extend(_flatten_numbers(child))
        return result
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise InputError("contains a non-numeric value")
    number = float(value)
    if not math.isfinite(number):
        raise InputError("contains NaN or infinity")
    return [number]


def _records_from_payload(payload: Any) -> Tuple[str, Sequence[Any]]:
    if isinstance(payload, dict) and "hardware_closed_loop" in payload:
        envelope = payload["hardware_closed_loop"]
        if not isinstance(envelope, (list, tuple)) or len(envelope) < 2:
            raise InputError("hardware_closed_loop must be [config, records]")
        records = _to_python(envelope[1])
        source = "hardware_closed_loop"
    elif isinstance(payload, dict) and "records" in payload:
        records = payload["records"]
        source = "records"
    elif isinstance(payload, list):
        records = payload
        source = "record-list"
    else:
        raise InputError(
            "expected hardware_closed_loop, records, or a JSON list of records"
        )

    if not isinstance(records, (list, tuple)):
        raise InputError("records must be a list")
    return source, records


def _load(path: Path) -> Tuple[str, Any]:
    if not path.is_file():
        raise InputError("input file does not exist or is not a regular file")
    try:
        if path.suffix.lower() == ".json":
            with path.open("r", encoding="utf-8") as handle:
                return "json", json.load(handle)
        with path.open("rb") as handle:
            return "pickle", pickle.load(handle)
    except EOFError as exc:
        raise InputError("pickle is incomplete (EOFError)") from exc
    except (OSError, json.JSONDecodeError, pickle.UnpicklingError) as exc:
        raise InputError("could not read input: " + str(exc)) from exc


def validate_records(records: Sequence[Any], max_errors: int = 10) -> Tuple[List[dict], List[str]]:
    normalized: List[dict] = []
    errors: List[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            if len(errors) < max_errors:
                errors.append(f"record {index}: expected an object/dict")
            continue
        row = {}
        row_errors = []
        for field in FIELDS:
            if field not in record:
                row_errors.append(f"missing {field}")
                continue
            try:
                values = _flatten_numbers(record[field])
            except InputError as exc:
                row_errors.append(f"{field} {exc}")
                continue
            if len(values) != JOINTS:
                row_errors.append(
                    f"{field} has {_shape(record[field])} / {len(values)} values; expected 12"
                )
                continue
            row[field] = values
        if row_errors:
            if len(errors) < max_errors:
                errors.append(f"record {index}: " + "; ".join(row_errors))
        else:
            normalized.append(row)
    if len(records) < MIN_RECORDS:
        errors.append(
            f"short history: {len(records)} records; at least {MIN_RECORDS} complete records are required"
        )
    if errors and len(errors) >= max_errors:
        errors.append("additional validation errors omitted")
    return normalized, errors


def report(path: Path, max_errors: int) -> dict:
    file_format, payload = _load(path)
    envelope, records = _records_from_payload(payload)
    normalized, errors = validate_records(records, max_errors=max_errors)
    valid = not errors and len(normalized) == len(records)
    record_count = len(records)
    samples_per_joint = max(record_count - 3, 0) if valid else 0
    return {
        "input_name": path.name,
        "format": file_format,
        "envelope": envelope,
        "valid": valid,
        "record_count": record_count,
        "complete_record_count": len(normalized),
        "joint_count": JOINTS,
        "required_fields": list(FIELDS),
        "minimum_records": MIN_RECORDS,
        "samples_per_joint": samples_per_joint,
        "sample_count": JOINTS * samples_per_joint,
        "first_record_shapes": {
            field: _shape(records[0][field])
            for field in FIELDS
            if records and isinstance(records[0], dict) and field in records[0]
        },
        "errors": errors,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only schema/shape validator for actuator pickle logs or JSON fixtures."
    )
    parser.add_argument("input", type=Path, help="trusted .pkl/.pickle log or portable .json fixture")
    parser.add_argument("--max-errors", type=int, default=10, help="maximum detailed errors (default: 10)")
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be positive")
    try:
        result = report(args.input, args.max_errors)
    except InputError as exc:
        result = {
            "input_name": args.input.name,
            "valid": False,
            "required_fields": list(FIELDS),
            "minimum_records": MIN_RECORDS,
            "errors": [str(exc)],
        }
        print(json.dumps(result, sort_keys=True), file=sys.stdout)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
