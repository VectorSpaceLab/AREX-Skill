#!/usr/bin/env python3
"""Validate Chai .aligned.pqt MSA files without running inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import string
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ["sequence", "source_database", "pairing_key", "comment"]
STRICT_SOURCES = {"query", "uniprot", "uniref90", "bfd_uniclust", "mgnify"}
INTERNAL_SOURCES = STRICT_SOURCES | {
    "BFD",
    "paired",
    "main",
    "singleton",
    "none",
    "pdb70",
    "uniprot_n3",
    "uniref90_n3",
    "mgnify_n3",
}
ALLOWED_A3M_CHARACTERS = set(string.ascii_letters) | {"-", "."}


@dataclass
class ValidationResult:
    path: str
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows: int = 0
    query_sequence: str | None = None
    expected_basename: str | None = None
    aligned_length: int | None = None
    sources: list[str] = field(default_factory=list)
    pairing_keys: int = 0

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "rows": self.rows,
            "query_sequence": self.query_sequence,
            "expected_basename": self.expected_basename,
            "aligned_length": self.aligned_length,
            "sources": self.sources,
            "non_empty_pairing_keys": self.pairing_keys,
        }


def expected_basename(query_sequence: str) -> str:
    sequence_hash = hashlib.sha256(query_sequence.upper().encode()).hexdigest()
    return f"{sequence_hash}.aligned.pqt"


def aligned_length(sequence: str) -> int:
    return sum(character in string.ascii_uppercase or character == "-" for character in sequence)


def invalid_a3m_characters(sequence: str) -> set[str]:
    return set(sequence) - ALLOWED_A3M_CHARACTERS


def collect_paths(inputs: list[Path]) -> list[Path]:
    collected_paths: list[Path] = []
    for input_path in inputs:
        if input_path.is_dir():
            collected_paths.extend(sorted(input_path.glob("*.aligned.pqt")))
        else:
            collected_paths.append(input_path)
    return collected_paths


def read_parquet(path: Path):
    try:
        import pandas as pd
    except ImportError as import_error:  # pragma: no cover - exercised by users without pandas
        raise RuntimeError(
            "pandas is required to read .aligned.pqt files. Install Chai Lab or pandas with a parquet engine."
        ) from import_error
    return pd.read_parquet(path)


def validate_file(path: Path, *, allow_internal_sources: bool = False) -> ValidationResult:
    result = ValidationResult(path=str(path))
    if not path.exists():
        result.add_error("file does not exist")
        return result
    if not path.is_file():
        result.add_error("path is not a file")
        return result

    try:
        table = read_parquet(path)
    except Exception as read_error:  # pragma: no cover - depends on parquet engine/user data
        result.add_error(f"could not read parquet: {read_error}")
        return result

    result.rows = int(len(table))
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in table.columns]
    if missing_columns:
        result.add_error(f"missing required columns: {', '.join(missing_columns)}")
        return result

    extra_columns = [column for column in table.columns if column not in REQUIRED_COLUMNS]
    if extra_columns:
        result.add_warning(f"extra columns ignored by Chai validator: {', '.join(map(str, extra_columns))}")

    if table.empty:
        result.add_error("table is empty")
        return result

    for column in REQUIRED_COLUMNS:
        null_count = int(table[column].isnull().sum())
        if null_count:
            result.add_error(f"column {column!r} contains {null_count} null value(s); use empty strings instead")

    if result.errors:
        return result

    for column in REQUIRED_COLUMNS:
        non_strings = [index for index, value in table[column].items() if not isinstance(value, str)]
        if non_strings:
            preview = ", ".join(str(index) for index in non_strings[:5])
            result.add_error(f"column {column!r} has non-string values at rows: {preview}")

    if result.errors:
        return result

    sources = [str(source) for source in table["source_database"].tolist()]
    result.sources = sorted(set(sources))
    allowed_sources = INTERNAL_SOURCES if allow_internal_sources else STRICT_SOURCES
    invalid_sources = sorted(set(sources) - allowed_sources)
    if invalid_sources:
        source_mode = "internal" if allow_internal_sources else "strict public"
        result.add_error(f"invalid {source_mode} source_database value(s): {', '.join(invalid_sources)}")

    first_source = str(table.iloc[0]["source_database"])
    if first_source != "query":
        result.add_error(f"first row source_database is {first_source!r}; expected 'query'")

    query_row_count = sum(source == "query" for source in sources)
    if query_row_count != 1:
        result.add_error(f"expected exactly one query row; found {query_row_count}")

    sequences = [str(sequence) for sequence in table["sequence"].tolist()]
    query_sequence = sequences[0]
    result.query_sequence = query_sequence
    result.expected_basename = expected_basename(query_sequence)
    result.aligned_length = aligned_length(query_sequence)

    if path.name != result.expected_basename:
        result.add_error(f"filename is {path.name!r}; expected {result.expected_basename!r}")

    if result.aligned_length == 0:
        result.add_error("query sequence has zero aligned length")

    observed_lengths = [aligned_length(sequence) for sequence in sequences]
    mismatched_rows = [
        row_number
        for row_number, row_length in enumerate(observed_lengths)
        if row_length != result.aligned_length
    ]
    if mismatched_rows:
        preview = ", ".join(str(row_number) for row_number in mismatched_rows[:10])
        result.add_error(
            f"aligned length mismatch versus query length {result.aligned_length}; rows: {preview}"
        )

    for row_number, sequence in enumerate(sequences):
        invalid_characters = invalid_a3m_characters(sequence)
        if invalid_characters:
            preview = "".join(sorted(invalid_characters))
            result.add_error(f"row {row_number} contains non-A3M character(s): {preview!r}")
            break

    result.pairing_keys = sum(bool(key) for key in table["pairing_key"].tolist())
    if result.pairing_keys and len(set(table["pairing_key"].tolist()) - {""}) == result.pairing_keys:
        result.add_warning(
            "all non-empty pairing_key values are unique within this file; pairing only works across files when keys match"
        )

    return result


def print_text_results(results: list[ValidationResult]) -> None:
    for result in results:
        status = "OK" if result.ok else "ERROR"
        print(f"[{status}] {result.path}")
        if result.expected_basename:
            print(f"  expected_basename: {result.expected_basename}")
        if result.rows:
            print(f"  rows: {result.rows}; aligned_length: {result.aligned_length}; sources: {', '.join(result.sources)}")
            print(f"  non_empty_pairing_keys: {result.pairing_keys}")
        for warning in result.warnings:
            print(f"  warning: {warning}")
        for error in result.errors:
            print(f"  error: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Chai .aligned.pqt files for schema, query row, source labels, "
            "A3M aligned lengths, and sha256(query.upper()) filenames."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="One or more .aligned.pqt files or directories containing .aligned.pqt files.",
    )
    parser.add_argument(
        "--allow-internal-sources",
        action="store_true",
        help="Allow all source labels defined by Chai internals instead of only public/default MSA sources.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON array of validation results.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = collect_paths(args.paths)
    if not paths:
        print("No .aligned.pqt files found.", file=sys.stderr)
        return 2

    results = [
        validate_file(path, allow_internal_sources=args.allow_internal_sources)
        for path in paths
    ]

    if args.json:
        print(json.dumps([result.to_jsonable() for result in results], indent=2, sort_keys=True))
    else:
        print_text_results(results)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
