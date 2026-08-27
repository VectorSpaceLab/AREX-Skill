#!/usr/bin/env python3
"""Validate feature-by-sample omics matrices and optional sample metadata.

The checker is intentionally read-only and dependency-free. It validates common
CSV/TSV inputs before OmicVerse bulk, metabolomics, proteomics, microbiome, or
enrichment workflows transpose/load them into pandas or AnnData.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

MISSING_TOKENS = {"", "na", "nan", "n/a", "null", "none", "."}


def infer_delimiter(path: Path, explicit: str | None) -> str:
    if explicit is not None:
        return "\t" if explicit == "\\t" else explicit
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=["\t", ",", ";"])
        return dialect.delimiter
    except csv.Error:
        suffix = path.suffix.lower()
        if suffix in {".tsv", ".tab"}:
            return "\t"
        return ","


def read_table(path: Path, delimiter: str) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        return [[cell.strip() for cell in row] for row in reader if row and any(cell.strip() for cell in row)]


def duplicates(values: Iterable[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def parse_required_columns(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def is_missing(value: str) -> bool:
    return value.strip().lower() in MISSING_TOKENS


def is_number(value: str) -> bool:
    if is_missing(value):
        return True
    try:
        number = float(value)
    except ValueError:
        return False
    return math.isfinite(number)


def preview(items: Sequence[str], limit: int = 8) -> str:
    shown = list(items[:limit])
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(shown) + suffix


def validate_matrix(rows: list[list[str]], path: Path, max_bad_cells: int) -> tuple[list[str], list[str], list[str], int, int]:
    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        return [], [], [f"{path}: file is empty"], 0, 0
    header = rows[0]
    if len(header) < 2:
        errors.append(f"{path}: matrix needs one feature-id column plus at least one sample column")
        return [], [], errors, 0, 0

    feature_header = header[0] or "<blank>"
    samples = [cell.strip() for cell in header[1:]]
    blank_sample_positions = [str(index + 2) for index, value in enumerate(samples) if not value]
    if blank_sample_positions:
        errors.append(f"{path}: blank sample IDs in header columns {preview(blank_sample_positions)}")
    sample_dups = duplicates([sample for sample in samples if sample])
    if sample_dups:
        errors.append(f"{path}: duplicate sample IDs: {preview(sample_dups)}")

    features: list[str] = []
    bad_cells: list[str] = []
    missing_cells = 0
    width = len(header)

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != width:
            errors.append(f"{path}: row {row_number} has {len(row)} columns, expected {width}")
            continue
        feature_id = row[0].strip()
        if not feature_id:
            errors.append(f"{path}: blank feature ID at row {row_number}")
        features.append(feature_id)
        for column_number, value in enumerate(row[1:], start=2):
            if is_missing(value):
                missing_cells += 1
                continue
            if not is_number(value):
                bad_cells.append(f"row {row_number}, column {column_number} ({header[column_number - 1]}={value!r})")
                if len(bad_cells) >= max_bad_cells:
                    break
        if len(bad_cells) >= max_bad_cells:
            break

    feature_dups = duplicates([feature for feature in features if feature])
    if feature_dups:
        errors.append(f"{path}: duplicate feature IDs in {feature_header}: {preview(feature_dups)}")
    if bad_cells:
        errors.append(f"{path}: nonnumeric abundance cells: {preview(bad_cells, limit=max_bad_cells)}")
    if missing_cells:
        warnings.append(f"{path}: {missing_cells} missing abundance cells allowed by token policy")

    return samples, features, errors + warnings, len(rows) - 1, missing_cells


def validate_metadata(
    rows: list[list[str]],
    path: Path,
    sample_id_column: str,
    required_columns: Sequence[str],
) -> tuple[set[str], list[str]]:
    messages: list[str] = []
    if not rows:
        return set(), [f"{path}: metadata file is empty"]
    header = rows[0]
    if sample_id_column not in header:
        return set(), [
            f"{path}: sample id column {sample_id_column!r} not found; available columns: {preview(header)}"
        ]
    missing_required = [col for col in required_columns if col not in header]
    if missing_required:
        messages.append(f"{path}: missing required metadata columns: {preview(missing_required)}")

    sample_index = header.index(sample_id_column)
    sample_ids: list[str] = []
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            messages.append(f"{path}: metadata row {row_number} has {len(row)} columns, expected {len(header)}")
            continue
        sample_id = row[sample_index].strip()
        if not sample_id:
            messages.append(f"{path}: blank metadata sample ID at row {row_number}")
        sample_ids.append(sample_id)

    sample_dups = duplicates([sample for sample in sample_ids if sample])
    if sample_dups:
        messages.append(f"{path}: duplicate metadata sample IDs: {preview(sample_dups)}")
    return set(sample_ids), messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a feature-by-sample CSV/TSV matrix and optional sample metadata.",
    )
    parser.add_argument("matrix", type=Path, help="Feature-by-sample matrix file. First column is feature IDs; remaining columns are sample IDs.")
    parser.add_argument("--metadata", type=Path, help="Optional sample metadata CSV/TSV file.")
    parser.add_argument("--sample-id-column", default="sample", help="Metadata column containing sample IDs. Default: sample")
    parser.add_argument("--required-metadata-cols", default="", help="Comma-separated metadata columns that must exist, for example group,batch,time.")
    parser.add_argument("--delimiter", help="Matrix delimiter. Defaults to inference; use '\\t' for tab.")
    parser.add_argument("--metadata-delimiter", help="Metadata delimiter. Defaults to inference; use '\\t' for tab.")
    parser.add_argument("--allow-extra-metadata", action="store_true", help="Allow metadata rows for samples not present in the matrix.")
    parser.add_argument("--max-bad-cells", type=int, default=10, help="Maximum nonnumeric cells to report before stopping scan. Default: 10")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    messages: list[str] = []
    hard_errors: list[str] = []

    matrix_path = args.matrix
    if not matrix_path.is_file():
        print(f"ERROR: matrix file not found: {matrix_path}", file=sys.stderr)
        return 2

    delimiter = infer_delimiter(matrix_path, args.delimiter)
    matrix_rows = read_table(matrix_path, delimiter)
    samples, features, matrix_messages, n_features, missing_cells = validate_matrix(
        matrix_rows,
        matrix_path,
        max(1, args.max_bad_cells),
    )
    messages.extend(matrix_messages)

    metadata_samples: set[str] | None = None
    required_columns = parse_required_columns(args.required_metadata_cols)
    if args.metadata:
        if not args.metadata.is_file():
            hard_errors.append(f"metadata file not found: {args.metadata}")
        else:
            metadata_delimiter = infer_delimiter(args.metadata, args.metadata_delimiter)
            metadata_rows = read_table(args.metadata, metadata_delimiter)
            metadata_samples, metadata_messages = validate_metadata(
                metadata_rows,
                args.metadata,
                args.sample_id_column,
                required_columns,
            )
            messages.extend(metadata_messages)
            matrix_sample_set = set(samples)
            missing_in_metadata = sorted(matrix_sample_set - metadata_samples)
            extra_metadata = sorted(metadata_samples - matrix_sample_set)
            if missing_in_metadata:
                messages.append(f"metadata is missing matrix samples: {preview(missing_in_metadata)}")
            if extra_metadata and not args.allow_extra_metadata:
                messages.append(f"metadata has samples not in matrix: {preview(extra_metadata)}")
    elif required_columns:
        messages.append("--required-metadata-cols was provided but --metadata is absent")

    error_markers = (
        "duplicate",
        "nonnumeric",
        "missing required",
        "not found",
        "blank",
        "has samples not in matrix",
        "missing matrix samples",
        "not a column",
        "expected",
        "file is empty",
        "needs one feature-id",
        "absent",
    )
    hard_errors.extend(
        message for message in messages
        if any(marker in message.lower() for marker in error_markers)
        and "missing abundance cells allowed" not in message.lower()
    )

    print("Multiomics table check")
    print(f"  matrix: {matrix_path}")
    print(f"  delimiter: {delimiter!r}")
    print(f"  features: {n_features}")
    print(f"  samples: {len(samples)}")
    print(f"  missing abundance cells: {missing_cells}")
    if args.metadata:
        print(f"  metadata: {args.metadata}")
        print(f"  metadata samples: {len(metadata_samples or set())}")
        print(f"  required metadata columns: {required_columns or 'none'}")

    if messages:
        print("Messages:")
        for message in messages:
            prefix = "ERROR" if message in hard_errors else "WARN"
            print(f"  {prefix}: {message}")

    if hard_errors:
        print("Result: FAIL", file=sys.stderr)
        return 1
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
