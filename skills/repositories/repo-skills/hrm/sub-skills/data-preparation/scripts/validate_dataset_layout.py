#!/usr/bin/env python3
"""Validate an HRM converted puzzle dataset layout.

This checker is self-contained and validates the dataset files produced by the
HRM ARC, Sudoku, and Maze builders without importing the original repository.

Example:
  python validate_dataset_layout.py data/arc-aug-1000 --splits train test
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


REQUIRED_METADATA_FIELDS = {
    "pad_id",
    "ignore_label_id",
    "blank_identifier_id",
    "vocab_size",
    "seq_len",
    "num_puzzle_identifiers",
    "total_groups",
    "mean_puzzle_examples",
    "sets",
}
ARRAY_FIELDS = ["inputs", "labels", "puzzle_identifiers", "puzzle_indices", "group_indices"]


class ValidationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing metadata file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"metadata in {path} must be a JSON object")
    return data


def _load_npy(path: Path, mmap: bool) -> np.ndarray:
    try:
        return np.load(path, mmap_mode="r" if mmap else None)
    except FileNotFoundError as exc:
        raise ValidationError(f"missing array file: {path}") from exc
    except Exception as exc:  # numpy emits several exception types here
        raise ValidationError(f"cannot load {path}: {exc}") from exc


def _check_int_array(name: str, arr: np.ndarray, ndim: int | None = None) -> None:
    if ndim is not None and arr.ndim != ndim:
        raise ValidationError(f"{name} must be {ndim}D, got shape {arr.shape}")
    if not np.issubdtype(arr.dtype, np.integer):
        raise ValidationError(f"{name} must use an integer dtype, got {arr.dtype}")


def _check_monotone_indices(name: str, arr: np.ndarray, lower: int, upper: int) -> None:
    _check_int_array(name, arr, ndim=1)
    if arr.size < 2:
        raise ValidationError(f"{name} must contain at least start and end offsets")
    if int(arr[0]) != lower:
        raise ValidationError(f"{name}[0] must be {lower}, got {int(arr[0])}")
    if np.any(arr[1:] < arr[:-1]):
        raise ValidationError(f"{name} must be non-decreasing")
    if int(arr[-1]) > upper:
        raise ValidationError(f"{name}[-1] must be <= {upper}, got {int(arr[-1])}")


def validate_subset(dataset_dir: Path, split: str, subset: str, mmap: bool) -> dict[str, Any]:
    split_dir = dataset_dir / split
    metadata = _load_json(split_dir / "dataset.json")
    missing = sorted(REQUIRED_METADATA_FIELDS - metadata.keys())
    if missing:
        raise ValidationError(f"{split}/dataset.json missing fields: {missing}")
    if subset not in metadata["sets"]:
        raise ValidationError(f"subset {subset!r} not listed in {split}/dataset.json sets={metadata['sets']!r}")

    arrays = {
        field: _load_npy(split_dir / f"{subset}__{field}.npy", mmap=mmap)
        for field in ARRAY_FIELDS
    }

    inputs = arrays["inputs"]
    labels = arrays["labels"]
    puzzle_identifiers = arrays["puzzle_identifiers"]
    puzzle_indices = arrays["puzzle_indices"]
    group_indices = arrays["group_indices"]

    _check_int_array("inputs", inputs, ndim=2)
    _check_int_array("labels", labels, ndim=2)
    _check_int_array("puzzle_identifiers", puzzle_identifiers, ndim=1)

    if inputs.shape != labels.shape:
        raise ValidationError(f"inputs and labels must have identical shape, got {inputs.shape} vs {labels.shape}")
    if inputs.shape[1] != int(metadata["seq_len"]):
        raise ValidationError(f"seq_len mismatch: metadata {metadata['seq_len']} vs inputs width {inputs.shape[1]}")

    n_examples = int(inputs.shape[0])
    n_puzzles = int(puzzle_identifiers.shape[0])
    _check_monotone_indices("puzzle_indices", puzzle_indices, 0, n_examples)
    _check_monotone_indices("group_indices", group_indices, 0, n_puzzles)
    if puzzle_indices.size != n_puzzles + 1:
        raise ValidationError(
            f"puzzle_indices length must be num_puzzles + 1 ({n_puzzles + 1}), got {puzzle_indices.size}"
        )
    if int(group_indices[-1]) != n_puzzles:
        raise ValidationError(f"group_indices[-1] must equal num_puzzles {n_puzzles}, got {int(group_indices[-1])}")
    if int(metadata["total_groups"]) != group_indices.size - 1:
        raise ValidationError(
            f"metadata total_groups {metadata['total_groups']} does not match group count {group_indices.size - 1}"
        )

    vocab_size = int(metadata["vocab_size"])
    for name, arr in [("inputs", inputs), ("labels", labels)]:
        if arr.size:
            min_value = int(np.min(arr))
            max_value = int(np.max(arr))
            if min_value < 0 or max_value >= vocab_size:
                raise ValidationError(f"{name} token range [{min_value}, {max_value}] is outside [0, {vocab_size})")

    if puzzle_identifiers.size and int(np.max(puzzle_identifiers)) >= int(metadata["num_puzzle_identifiers"]):
        raise ValidationError("puzzle_identifiers contains ids outside metadata num_puzzle_identifiers")

    identifiers_path = dataset_dir / "identifiers.json"
    identifiers = None
    if identifiers_path.exists():
        with identifiers_path.open("r", encoding="utf-8") as handle:
            identifiers = json.load(handle)
        if not isinstance(identifiers, list):
            raise ValidationError("identifiers.json must contain a JSON list")
        if len(identifiers) < int(metadata["num_puzzle_identifiers"]):
            raise ValidationError("identifiers.json has fewer entries than metadata num_puzzle_identifiers")

    return {
        "split": split,
        "subset": subset,
        "examples": n_examples,
        "puzzles": n_puzzles,
        "groups": int(group_indices.size - 1),
        "seq_len": int(metadata["seq_len"]),
        "vocab_size": vocab_size,
        "sets": list(metadata["sets"]),
        "identifiers_present": identifiers is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HRM converted dataset arrays and metadata.")
    parser.add_argument("dataset_dir", type=Path, help="Dataset root containing identifiers.json plus train/test directories.")
    parser.add_argument("--splits", nargs="+", default=["train", "test"], help="Splits to validate, default: train test.")
    parser.add_argument("--subsets", nargs="*", help="Subsets to validate. Defaults to metadata sets for each split.")
    parser.add_argument("--no-mmap", action="store_true", help="Load arrays fully instead of using numpy mmap.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.expanduser().resolve()
    summaries = []
    try:
        for split in args.splits:
            split_dir = dataset_dir / split
            metadata = _load_json(split_dir / "dataset.json")
            subsets = args.subsets or list(metadata.get("sets", []))
            if not subsets:
                raise ValidationError(f"no subsets listed for split {split}")
            for subset in subsets:
                summaries.append(validate_subset(dataset_dir, split, subset, mmap=not args.no_mmap))
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}")
        return 2

    output = {"ok": True, "dataset_dir": os.fspath(dataset_dir), "subsets": summaries}
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"OK: validated {len(summaries)} HRM dataset subset(s) under {dataset_dir}")
        for summary in summaries:
            print(
                f"  {summary['split']}/{summary['subset']}: "
                f"examples={summary['examples']} puzzles={summary['puzzles']} "
                f"groups={summary['groups']} seq_len={summary['seq_len']} vocab={summary['vocab_size']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
