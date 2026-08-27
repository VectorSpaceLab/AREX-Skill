#!/usr/bin/env python3
"""Validate a trusted NAVSIM submission pickle without loading datasets or network resources.

This intentionally checks only the portable metadata and basic two-stage
prediction container shape. Python pickle is executable serialization: never
run this validator on an untrusted file.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REQUIRED_METADATA = ("team_name", "authors", "email", "institution", "country / region")
STAGE_NAMES = ("first_stage_predictions", "second_stage_predictions")


class ValidationError(ValueError):
    """A user-correctable submission format error."""


def _shape_of_poses(trajectory: Any) -> Tuple[int, int]:
    """Return a two-dimensional pose shape from a Trajectory-like object."""
    if isinstance(trajectory, Mapping):
        poses = trajectory.get("poses")
    else:
        poses = getattr(trajectory, "poses", None)
    if poses is None:
        raise ValidationError("prediction value has no 'poses' attribute/key")

    shape = getattr(poses, "shape", None)
    if shape is not None:
        try:
            dims = tuple(int(dimension) for dimension in shape)
        except (TypeError, ValueError):
            dims = ()
        if len(dims) == 2:
            return dims[0], dims[1]
        raise ValidationError("trajectory poses must have exactly two dimensions")

    if not isinstance(poses, (list, tuple)):
        raise ValidationError("trajectory poses need a shape or nested list/tuple representation")
    rows = len(poses)
    if rows == 0:
        raise ValidationError("trajectory poses cannot be empty")
    widths = []
    for row in poses:
        if not isinstance(row, (list, tuple)):
            raise ValidationError("trajectory poses must be a nested sequence")
        widths.append(len(row))
    if len(set(widths)) != 1:
        raise ValidationError("trajectory pose rows have inconsistent widths")
    return rows, widths[0]


def _check_numeric_poses(trajectory: Any, path: str) -> Tuple[int, int]:
    """Check shape and, where cheaply possible, reject non-finite pose values."""
    rows, width = _shape_of_poses(trajectory)
    if rows < 1 or width != 3:
        raise ValidationError(f"{path} poses must have shape (N, 3), got ({rows}, {width})")

    poses = trajectory.get("poses") if isinstance(trajectory, Mapping) else getattr(trajectory, "poses", None)
    try:
        iterator: Iterable[Any] = (value for row in poses for value in row)
        for value in iterator:
            if not math.isfinite(float(value)):
                raise ValidationError(f"{path} contains a non-finite pose value")
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(f"{path} contains a non-numeric pose value")
    return rows, width


def _validate_metadata(submission: Mapping[str, Any]) -> None:
    """Validate required identity fields without imposing server policy."""
    for field in REQUIRED_METADATA:
        if field not in submission:
            raise ValidationError(f"missing required metadata field: {field!r}")
        value = submission[field]
        if not isinstance(value, str) or not value.strip() or value.strip() == "MUST_SET":
            raise ValidationError(f"metadata field {field!r} must be a non-empty string")
    if "@" not in submission["email"].strip():
        raise ValidationError("metadata field 'email' should contain '@'")


def _validate_stage(submission: Mapping[str, Any], stage_name: str) -> Dict[str, Any]:
    """Validate one stage's list-of-dictionaries container."""
    stage = submission.get(stage_name)
    if not isinstance(stage, list) or not stage:
        raise ValidationError(f"{stage_name} must be a non-empty list of prediction dictionaries")

    total_predictions = 0
    stage_sizes: List[int] = []
    for dictionary_index, prediction_map in enumerate(stage):
        if not isinstance(prediction_map, dict) or not prediction_map:
            raise ValidationError(
                f"{stage_name}[{dictionary_index}] must be a non-empty dictionary keyed by scene token"
            )
        stage_sizes.append(len(prediction_map))
        for token, trajectory in prediction_map.items():
            if not isinstance(token, str) or not token.strip():
                raise ValidationError(f"{stage_name}[{dictionary_index}] contains a blank/non-string token")
            _check_numeric_poses(trajectory, f"{stage_name}[{dictionary_index}][{token!r}]")
            total_predictions += 1
    return {"maps": len(stage), "predictions": total_predictions, "map_sizes": stage_sizes}


def validate_submission(path: Path) -> Dict[str, Any]:
    """Load and validate a trusted pickle, returning a compact report."""
    try:
        with path.open("rb") as handle:
            submission = pickle.load(handle)
    except FileNotFoundError:
        raise ValidationError(f"submission file does not exist: {path}")
    except (OSError, pickle.PickleError, EOFError, AttributeError, ImportError, ModuleNotFoundError) as exc:
        raise ValidationError(f"could not load pickle {path}: {exc}")

    if not isinstance(submission, dict):
        raise ValidationError("top-level pickle value must be a dictionary")
    _validate_metadata(submission)
    stages = {stage_name: _validate_stage(submission, stage_name) for stage_name in STAGE_NAMES}
    return {
        "path": str(path),
        "status": "valid-basic-schema",
        "metadata_fields": list(REQUIRED_METADATA),
        "stages": stages,
        "warning": "basic local check only; server coverage, numeric semantics, and challenge rules remain external",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate NAVSIM submission.pkl metadata and basic two-stage containers (no network/data access)."
    )
    parser.add_argument("submission", type=Path, help="trusted local submission pickle")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point; return 0 for a valid basic schema and 2 otherwise."""
    args = _parser().parse_args(argv)
    try:
        report = validate_submission(args.submission)
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "error": str(exc)}))
        else:
            print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        first = report["stages"]["first_stage_predictions"]["predictions"]
        second = report["stages"]["second_stage_predictions"]["predictions"]
        print(f"VALID BASIC SCHEMA: {args.submission} (first-stage={first}, second-stage={second})")
        print(report["warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
