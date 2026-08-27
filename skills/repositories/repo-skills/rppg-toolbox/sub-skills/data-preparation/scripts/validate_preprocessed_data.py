#!/usr/bin/env python3
"""Read-only validation for paired rPPG-Toolbox NPY cache clips.

The standard cache stores inputs as rank-4 temporal/spatial/channel arrays and
labels as rank-1 temporal arrays. This helper accepts either input/label
 directories or a CSV containing an ``input_files`` column. It never writes,
renames, deletes, or repairs files.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np


_INPUT_TOKEN = re.compile(r"_input(?=\d+(?:\.npy)?$)")


def _label_name(path: Path) -> Path:
    """Return the sibling label path implied by a standard input filename."""
    match = _INPUT_TOKEN.search(path.name)
    if match:
        return path.with_name(path.name[: match.start()] + "_label" + path.name[match.end() :])
    stem = path.stem
    if "input" in stem:
        return path.with_name(stem.replace("input", "label", 1) + path.suffix)
    raise ValueError(f"cannot infer label name from {path.name!r}")


def _csv_inputs(csv_path: Path) -> List[Path]:
    """Read input paths from a CSV, preserving row order and rejecting bad rows."""
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "input_files" not in reader.fieldnames:
            raise ValueError("CSV must contain an 'input_files' column")
        result: List[Path] = []
        for row_number, row in enumerate(reader, start=2):
            raw = (row.get("input_files") or "").strip()
            if not raw:
                raise ValueError(f"CSV row {row_number} has an empty input_files value")
            path = Path(raw).expanduser()
            # Absolute paths and paths valid from the caller win. A relative path
            # may also be relative to the CSV directory, which makes inspection
            # portable without changing the file list.
            if not path.is_absolute() and not path.exists():
                path = csv_path.parent / path
            result.append(path)
    return result


def _pairs_from_dirs(input_dir: Path, label_dir: Path) -> List[Tuple[Path, Path]]:
    """Discover direct/recursive NPY inputs and their implied labels."""
    inputs = sorted(input_dir.rglob("*_input*.npy"))
    pairs: List[Tuple[Path, Path]] = []
    for input_path in inputs:
        relative = input_path.relative_to(input_dir)
        try:
            label_relative = _label_name(relative)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        pairs.append((input_path, label_dir / label_relative))
    return pairs


def _is_numeric(array: np.ndarray) -> bool:
    """Return whether an array has a supported non-object, non-complex dtype."""
    return np.issubdtype(array.dtype, np.number) and not np.issubdtype(
        array.dtype, np.complexfloating
    )


def _check_array(path: Path, expected_rank: int, role: str) -> Tuple[np.ndarray, str]:
    """Load and validate basic NPY properties without enabling pickle."""
    if path.suffix.lower() != ".npy":
        return np.empty(0), f"{role} is not an NPY file: {path}"
    if not path.is_file():
        return np.empty(0), f"missing {role}: {path}"
    try:
        array = np.load(path, allow_pickle=False)
    except Exception as exc:  # malformed or object NPY
        return np.empty(0), f"cannot load {role} {path}: {exc}"
    if array.ndim != expected_rank:
        return array, f"{role} rank {array.ndim}, expected {expected_rank}: {path}"
    if not _is_numeric(array):
        return array, f"{role} dtype {array.dtype} is not a real numeric dtype: {path}"
    if any(size <= 0 for size in array.shape):
        return array, f"{role} has an empty dimension {array.shape}: {path}"
    if not np.isfinite(array).all():
        return array, f"{role} contains NaN or infinity: {path}"
    return array, ""


def validate_pairs(pairs: Sequence[Tuple[Path, Path]], data_format: str) -> List[str]:
    """Validate all pairs and return human-readable errors."""
    errors: List[str] = []
    if not pairs:
        return ["no input NPY files were selected"]
    for input_path, label_path in pairs:
        input_array, error = _check_array(input_path, 4, "input")
        if error:
            errors.append(error)
            continue
        label_array, error = _check_array(label_path, 1, "label")
        if error:
            errors.append(error)
            continue
        if input_array.shape[0] != label_array.shape[0]:
            errors.append(
                f"temporal length mismatch: input {input_array.shape[0]} vs "
                f"label {label_array.shape[0]} ({input_path})"
            )
        # Both layouts are rank-4. The temporal axis is always first; only the
        # channel axis differs. Spatial/channel dimensions must be non-empty.
        channel_axis = 3 if data_format == "NDHWC" else 1
        if input_array.shape[channel_axis] <= 0:
            errors.append(f"{data_format} channel dimension is empty: {input_path}")
        spatial_axes = (1, 2) if data_format == "NDHWC" else (2, 3)
        if any(input_array.shape[axis] <= 0 for axis in spatial_axes):
            errors.append(f"{data_format} spatial dimensions are empty: {input_path}")
    return errors


def build_pairs(args: argparse.Namespace) -> List[Tuple[Path, Path]]:
    """Resolve CLI inputs into input/label pairs without modifying anything."""
    if args.file_list:
        inputs = _csv_inputs(args.file_list)
        pairs = []
        for input_path in inputs:
            try:
                label_path = _label_name(input_path)
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            pairs.append((input_path, label_path))
        return pairs
    return _pairs_from_dirs(args.input_dir, args.label_dir)


def make_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Read-only validation of paired standard rPPG NPY cache clips."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--file-list", type=Path, help="CSV with an input_files column"
    )
    source.add_argument("--input-dir", type=Path, help="directory containing *_input*.npy")
    parser.add_argument(
        "--label-dir",
        type=Path,
        help="directory containing matching labels (required with --input-dir)",
    )
    parser.add_argument(
        "--data-format",
        choices=("NDHWC", "NDCHW"),
        default="NDHWC",
        help="layout of the input arrays being inspected (default: NDHWC)",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="maximum detailed errors to print (default: 20; does not stop checking)",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run validation and return a shell-friendly status code."""
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be positive")
    if bool(args.input_dir) != bool(args.label_dir):
        parser.error("--input-dir and --label-dir must be provided together")
    try:
        pairs = build_pairs(args)
        errors = validate_pairs(pairs, args.data_format)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Checked {len(pairs)} pair(s) using {args.data_format} input expectations.")
    if errors:
        print(f"FAILED: {len(errors)} issue(s)", file=sys.stderr)
        for error in errors[: args.max_errors]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > args.max_errors:
            print(f"- ... {len(errors) - args.max_errors} more", file=sys.stderr)
        return 1
    print("OK: ranks, numeric dtypes, finite values, dimensions, and temporal lengths are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
