#!/usr/bin/env python3
"""Validate a local BEIR-format dataset directory.

Examples:
    python validate_beir_dataset.py ./tiny-beir --split test
    python validate_beir_dataset.py ./prefixed-beir --split test --prefix fiqa
    python validate_beir_dataset.py ./tiny-beir --split dev --max-errors 20

The validator checks corpus.jsonl, queries.jsonl, and qrels/<split>.tsv using
BEIR's local file conventions. With --prefix, it validates <prefix>-queries.jsonl
and <prefix>-qrels/<split>.tsv while corpus.jsonl remains unprefixed. It imports
only the Python standard library and performs no network access.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ValidationErrorCollector:
    def __init__(self, max_errors: int) -> None:
        self.max_errors = max_errors
        self.errors: list[str] = []

    def add(self, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(message)

    @property
    def truncated(self) -> bool:
        return len(self.errors) >= self.max_errors

    def has_errors(self) -> bool:
        return bool(self.errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate BEIR corpus/query/qrels files in a dataset directory.")
    parser.add_argument("dataset_dir", type=Path, help="Dataset directory containing BEIR-format files.")
    parser.add_argument("--split", default="test", help="Qrels split filename to validate, without .tsv. Default: test.")
    parser.add_argument(
        "--prefix",
        default=None,
        help="Optional BEIR prefix. Validates <prefix>-queries.jsonl and <prefix>-qrels/<split>.tsv.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Maximum number of errors to print before stopping detailed collection. Default: 50.",
    )
    return parser.parse_args()


def expected_paths(dataset_dir: Path, split: str, prefix: str | None) -> tuple[Path, Path, Path]:
    query_file = f"{prefix}-queries.jsonl" if prefix else "queries.jsonl"
    qrels_folder = f"{prefix}-qrels" if prefix else "qrels"
    return dataset_dir / "corpus.jsonl", dataset_dir / query_file, dataset_dir / qrels_folder / f"{split}.tsv"


def validate_existing_file(path: Path, extension: str, label: str, errors: ValidationErrorCollector) -> None:
    if not path.exists():
        errors.add(f"missing {label}: expected {path}")
        return
    if not path.is_file():
        errors.add(f"{label} is not a file: {path}")
        return
    if path.suffix != f".{extension}":
        errors.add(f"{label} must have .{extension} extension: {path}")


def require_string(row: dict[str, Any], field: str, location: str, errors: ValidationErrorCollector) -> str | None:
    value = row.get(field)
    if not isinstance(value, str):
        errors.add(f"{location} field {field!r} must be a string")
        return None
    if value == "":
        errors.add(f"{location} field {field!r} must not be empty")
        return None
    return value


def read_jsonl_ids(
    path: Path,
    label: str,
    required_fields: tuple[str, ...],
    errors: ValidationErrorCollector,
) -> set[str]:
    ids: set[str] = set()
    if not path.is_file():
        return ids

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if errors.truncated:
                    break
                line = raw_line.rstrip("\n")
                location = f"{path}:{line_number}"
                if not line.strip():
                    errors.add(f"{location} empty JSONL line")
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.add(f"{location} invalid JSON: {exc.msg}")
                    continue
                if not isinstance(row, dict):
                    errors.add(f"{location} JSONL row must be an object")
                    continue
                row_id = require_string(row, "_id", location, errors)
                for field in required_fields:
                    require_string(row, field, location, errors)
                if row_id is None:
                    continue
                if row_id in ids:
                    errors.add(f"{location} duplicate _id {row_id!r} in {label}")
                ids.add(row_id)
    except OSError as exc:
        errors.add(f"failed to read {label} {path}: {exc}")

    if not ids:
        errors.add(f"{label} contains no valid rows: {path}")
    return ids


def parse_score(raw_score: str, location: str, errors: ValidationErrorCollector) -> None:
    try:
        int(raw_score)
    except ValueError:
        errors.add(f"{location} score {raw_score!r} must be integer-compatible for GenericDataLoader")


def validate_qrels(
    path: Path,
    query_ids: set[str],
    corpus_ids: set[str],
    errors: ValidationErrorCollector,
) -> int:
    if not path.is_file():
        return 0
    row_count = 0

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            header = handle.readline()
            if header == "":
                errors.add(f"{path} is empty")
                return 0
            header_fields = header.rstrip("\n\r").split("\t")
            if header_fields != ["query-id", "corpus-id", "score"]:
                errors.add(
                    f"{path}:1 header must be 'query-id<TAB>corpus-id<TAB>score', got {header_fields!r}"
                )
            for line_number, raw_line in enumerate(handle, start=2):
                if errors.truncated:
                    break
                line = raw_line.rstrip("\n\r")
                location = f"{path}:{line_number}"
                if not line.strip():
                    errors.add(f"{location} empty qrels row")
                    continue
                fields = line.split("\t")
                if len(fields) != 3:
                    errors.add(f"{location} qrels row must have exactly 3 tab-separated fields, got {len(fields)}")
                    continue
                query_id, corpus_id, score = fields
                row_count += 1
                if query_id == "":
                    errors.add(f"{location} query-id must not be empty")
                elif query_id not in query_ids:
                    errors.add(f"{location} query-id {query_id!r} is not present in queries")
                if corpus_id == "":
                    errors.add(f"{location} corpus-id must not be empty")
                elif corpus_id not in corpus_ids:
                    errors.add(f"{location} corpus-id {corpus_id!r} is not present in corpus")
                parse_score(score, location, errors)
    except OSError as exc:
        errors.add(f"failed to read qrels {path}: {exc}")

    if row_count == 0:
        errors.add(f"qrels contains no data rows: {path}")
    return row_count


def validate_args(args: argparse.Namespace) -> None:
    if args.max_errors < 1:
        raise SystemExit("error: --max-errors must be at least 1")
    if args.split == "" or "/" in args.split or "\\" in args.split:
        raise SystemExit("error: --split must be a non-empty filename stem such as 'test' or 'dev'")
    if args.prefix is not None and args.prefix == "":
        raise SystemExit("error: --prefix must not be empty when provided")


def main() -> None:
    args = parse_args()
    validate_args(args)
    dataset_dir = args.dataset_dir.expanduser().resolve()
    errors = ValidationErrorCollector(max_errors=args.max_errors)

    if not dataset_dir.exists():
        raise SystemExit(f"error: dataset directory does not exist: {dataset_dir}")
    if not dataset_dir.is_dir():
        raise SystemExit(f"error: dataset path is not a directory: {dataset_dir}")

    corpus_file, query_file, qrels_file = expected_paths(dataset_dir, args.split, args.prefix)
    validate_existing_file(corpus_file, "jsonl", "corpus file", errors)
    validate_existing_file(query_file, "jsonl", "query file", errors)
    validate_existing_file(qrels_file, "tsv", "qrels file", errors)

    corpus_ids = read_jsonl_ids(corpus_file, "corpus", ("text", "title"), errors)
    query_ids = read_jsonl_ids(query_file, "queries", ("text",), errors)
    qrels_rows = validate_qrels(qrels_file, query_ids, corpus_ids, errors)

    if errors.has_errors():
        print("BEIR dataset validation failed:")
        for message in errors.errors:
            print(f"- {message}")
        if errors.truncated:
            print(f"- stopped after {args.max_errors} errors; fix these first or raise --max-errors")
        raise SystemExit(1)

    prefix_note = f" with prefix {args.prefix!r}" if args.prefix else ""
    print(f"BEIR dataset validation passed for {dataset_dir}{prefix_note} split {args.split!r}")
    print(f"corpus rows: {len(corpus_ids)}")
    print(f"query rows: {len(query_ids)}")
    print(f"qrels rows: {qrels_rows}")
    print(f"paths: corpus={corpus_file}, queries={query_file}, qrels={qrels_file}")


if __name__ == "__main__":
    main()
