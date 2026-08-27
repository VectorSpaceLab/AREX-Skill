#!/usr/bin/env python3
"""Safely split a classification annotation CSV without loading any model.

The helper mirrors the companion workflow's three split concepts while making
validation and output replacement explicit. It uses only the Python standard
library so that ``--help`` and tiny-fixture checks do not require the legacy
training environment.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, NoReturn

REQUIRED_COLUMNS = ("path", "classification", "label")
OUTPUT_NAMES = {
    "train": "train_annotations.csv",
    "val": "val_annotations.csv",
    "test": "test_annotations.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and split a flat-image classification CSV. "
            "No models, downloads, loggers, or training are started."
        )
    )
    parser.add_argument("--input-csv", type=Path, required=True, help="source annotation CSV")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for split CSVs")
    parser.add_argument(
        "--split-type",
        choices=("random", "location", "sequence"),
        default="location",
        help="random stratified rows, Location groups, or 30-second Photo_Time groups (default: location)",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="fraction assigned to test (default: 0.2)")
    parser.add_argument("--val-size", type=float, default=0.2, help="fraction assigned to validation (default: 0.2)")
    parser.add_argument("--seed", type=int, default=42, help="deterministic assignment seed (default: 42)")
    parser.add_argument("--overwrite", action="store_true", help="replace existing split files")
    parser.add_argument("--dry-run", action="store_true", help="validate and report counts without writing files")
    return parser.parse_args()


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        fail(f"input CSV does not exist: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("input CSV has no header")
        headers = list(reader.fieldnames)
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            fail(f"missing required columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        fail("input CSV has no data rows")
    for number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if row.get(column, "").strip() == "":
                fail(f"row {number} has an empty {column!r}")
        try:
            int(row["classification"])
        except ValueError as exc:
            fail(f"row {number} classification is not an integer: {row['classification']!r}")
    return headers, rows


def optional_column(headers: Iterable[str], *names: str) -> str | None:
    header_set = set(headers)
    for name in names:
        if name in header_set:
            return name
    return None


def validate_sizes(test_size: float, val_size: float) -> None:
    if not (0 <= test_size < 1 and 0 <= val_size < 1 and test_size + val_size < 1):
        fail("test-size and val-size must be non-negative and sum to less than 1")


def random_split(rows: list[dict[str, str]], test_size: float, val_size: float, seed: int) -> dict[str, list[dict[str, str]]]:
    """Make a deterministic, class-aware row split like the source utility."""
    by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_class[row["classification"]].append(row)
    rng = random.Random(seed)
    output = {name: [] for name in OUTPUT_NAMES}
    for class_id, class_rows in sorted(by_class.items()):
        rng.shuffle(class_rows)
        n_test = int(round(len(class_rows) * test_size))
        n_val = int(round(len(class_rows) * val_size))
        if n_test + n_val > len(class_rows):
            n_val = max(0, len(class_rows) - n_test)
        output["test"].extend(class_rows[:n_test])
        output["val"].extend(class_rows[n_test : n_test + n_val])
        output["train"].extend(class_rows[n_test + n_val :])
    for values in output.values():
        rng.shuffle(values)
    return output


def assign_groups(
    rows: list[dict[str, str]], group_keys: list[str], test_size: float, val_size: float, seed: int
) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row, key in zip(rows, group_keys):
        groups[key].append(row)
    targets = {"train": 1 - test_size - val_size, "val": val_size, "test": test_size}
    counts = {name: 0 for name in OUTPUT_NAMES}
    output = {name: [] for name in OUTPUT_NAMES}
    group_items = list(groups.items())
    random.Random(seed).shuffle(group_items)
    # Place large groups first; the ratio heuristic approximates requested row proportions
    # while preserving every group as an indivisible unit.
    group_items.sort(key=lambda item: len(item[1]), reverse=True)
    for key, group_rows in group_items:
        eligible = [name for name, target in targets.items() if target > 0]
        destination = min(
            eligible,
            key=lambda name: counts[name] / max(targets[name] * len(rows), 1),
        )
        output[destination].extend(group_rows)
        counts[destination] += len(group_rows)
    return output


def parse_sequence_key(value: str, row_number: int) -> str:
    text = value.strip().replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError as exc:
        fail(f"row {row_number} has invalid Photo_Time {value!r}; use YYYY-MM-DD HH:MM:SS")
    # Epoch flooring matches fixed 30-second bins, rather than splitting a burst by frame.
    return str(math.floor(timestamp.timestamp() / 30))


def split_rows(headers: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    validate_sizes(args.test_size, args.val_size)
    if args.split_type == "random":
        return random_split(rows, args.test_size, args.val_size, args.seed)
    if args.split_type == "location":
        column = optional_column(headers, "Location")
        if column is None:
            fail("location split requires the exact source column 'Location'")
        keys = [row[column] for row in rows]
    else:
        column = optional_column(headers, "Photo_Time", "Photo_time")
        if column is None:
            fail("sequence split requires 'Photo_Time' (or the accepted compatibility spelling 'Photo_time')")
        keys = [parse_sequence_key(row[column], index + 2) for index, row in enumerate(rows)]
    return assign_groups(rows, keys, args.test_size, args.val_size, args.seed)


def write_outputs(headers: list[str], splits: dict[str, list[dict[str, str]]], args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destinations = {name: args.output_dir / filename for name, filename in OUTPUT_NAMES.items()}
    existing = [path for path in destinations.values() if path.exists()]
    if existing and not args.overwrite:
        fail("split output exists; choose a new output directory or pass --overwrite")
    for name, path in destinations.items():
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(splits[name])
        temporary.replace(path)


def main() -> int:
    args = parse_args()
    try:
        headers, rows = load_rows(args.input_csv)
        splits = split_rows(headers, rows, args)
        counts = ", ".join(f"{name}={len(splits[name])}" for name in ("train", "val", "test"))
        print(f"validated {len(rows)} rows; {counts}; split_type={args.split_type}")
        if not args.dry_run:
            write_outputs(headers, splits, args)
            print(f"wrote split annotations to {args.output_dir}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
