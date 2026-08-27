#!/usr/bin/env python3
"""Deterministically extract six-feature actuator samples as JSON.

The script accepts the documented deployment-log envelope or a portable JSON
fixture. It is intentionally standard-library-only: no torch, network, plot,
training, or implicit file overwrite is performed.
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
FEATURE_NAMES = (
    "position_error_t",
    "position_error_t_minus_1",
    "position_error_t_minus_2",
    "velocity_t",
    "velocity_t_minus_1",
    "velocity_t_minus_2",
)


class InputError(ValueError):
    pass


def _to_python(value: Any) -> Any:
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist") and not isinstance(value, (list, tuple, str, bytes)):
        value = value.tolist()
    return value


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
        records, source = envelope[1], "hardware_closed_loop"
    elif isinstance(payload, dict) and "records" in payload:
        records, source = payload["records"], "records"
    elif isinstance(payload, list):
        records, source = payload, "record-list"
    else:
        raise InputError("expected hardware_closed_loop, records, or a JSON list of records")
    records = _to_python(records)
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


def normalize_records(records: Sequence[Any]) -> List[dict]:
    if len(records) < MIN_RECORDS:
        raise InputError(
            f"short history: {len(records)} records; at least {MIN_RECORDS} complete records are required"
        )
    normalized: List[dict] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise InputError(f"record {index}: expected an object/dict")
        row = {}
        for field in FIELDS:
            if field not in record:
                raise InputError(f"record {index}: missing {field}")
            try:
                values = _flatten_numbers(record[field])
            except InputError as exc:
                raise InputError(f"record {index}: {field} {exc}") from exc
            if len(values) != JOINTS:
                raise InputError(
                    f"record {index}: {field} has {len(values)} values; expected 12"
                )
            row[field] = values
        normalized.append(row)
    return normalized


def extract(records: Sequence[dict]) -> dict:
    # Match utils.py: target/feature rows are emitted joint-major and t=2..T-2.
    errors = [
        [
            records[t]["joint_pos"][j] - records[t]["joint_pos_target"][j]
            for j in range(JOINTS)
        ]
        for t in range(len(records))
    ]
    velocities = [row["joint_vel"] for row in records]
    tau_ests = [row["tau_est"] for row in records]

    xs: List[List[float]] = []
    ys: List[List[float]] = []
    time_indices: List[int] = []
    for joint in range(JOINTS):
        for t in range(2, len(records) - 1):
            xs.append(
                [
                    errors[t][joint],
                    errors[t - 1][joint],
                    errors[t - 2][joint],
                    velocities[t][joint],
                    velocities[t - 1][joint],
                    velocities[t - 2][joint],
                ]
            )
            ys.append([tau_ests[t][joint]])
            time_indices.append(t)

    return {
        "schema_version": 1,
        "feature_names": list(FEATURE_NAMES),
        "target_name": "tau_est",
        "num_joints": JOINTS,
        "history": 3,
        "source_records": len(records),
        "samples_per_joint": len(records) - 3,
        "num_samples": len(xs),
        "sample_order": "joint-major, then time index t=2..T-2",
        "time_indices_by_joint": time_indices,
        "xs": xs,
        "ys": ys,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely extract six-feature/one-target actuator data as JSON."
    )
    parser.add_argument("input", type=Path, help="trusted .pkl/.pickle log or portable .json fixture")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="explicit new JSON path; omit to write JSON to stdout, or use '-' for stdout",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacing an existing --output (never needed for stdout)",
    )
    args = parser.parse_args(argv)

    try:
        _, payload = _load(args.input)
        _, records = _records_from_payload(payload)
        normalized = normalize_records(records)
        result = extract(normalized)
        encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"

        if args.output is None or str(args.output) == "-":
            sys.stdout.write(encoded)
            return 0

        output = args.output
        if not output.parent.is_dir():
            raise InputError("output parent does not exist; create it explicitly first")
        if output.exists() and not args.force:
            raise InputError("output exists; choose a new path or pass --force explicitly")
        mode = "w" if args.force else "x"
        with output.open(mode, encoding="utf-8") as handle:
            handle.write(encoded)
        print(f"wrote {output} ({result['num_samples']} samples)", file=sys.stderr)
        return 0
    except (InputError, OSError) as exc:
        print(f"prepare_actuator_data.py: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
