#!/usr/bin/env python3
"""Validate ColBERT collection, query, and ranking TSV inputs.

This helper intentionally avoids importing ColBERT so it can run before the
retrieval environment is fully installed. It validates shape, readability, and
common constraints used by ColBERT's data loaders.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable


class ValidationError(Exception):
    """Raised when a validation check fails."""


def readable_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"path does not exist: {path}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"path is not a file: {path}")
    try:
        with path.open("r", encoding="utf-8"):
            pass
    except OSError as exc:
        raise argparse.ArgumentTypeError(f"path is not readable: {path}: {exc}") from exc
    return path


def iter_tsv(path: Path) -> Iterable[tuple[int, list[str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            if not row or all(cell == "" for cell in row):
                yield line_number, []
            else:
                yield line_number, row


def parse_int(value: str, label: str, line_number: int) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f"line {line_number}: {label} must be an integer, got {value!r}") from exc


def parse_float(value: str, label: str, line_number: int) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValidationError(f"line {line_number}: {label} must be numeric, got {value!r}") from exc


def validate_collection(path: Path, max_errors: int) -> tuple[int, list[str]]:
    errors: list[str] = []
    physical_rows = 0
    data_rows = 0
    header_seen = False

    for line_number, row in iter_tsv(path):
        physical_rows += 1
        if not row:
            errors.append(f"line {line_number}: blank rows are not valid collection entries")
        elif len(row) < 2:
            errors.append(f"line {line_number}: collection rows need at least pid and passage columns")
        elif physical_rows == 1 and row[0] == "id":
            header_seen = True
            if len(row) >= 2 and row[1] not in {"text", "passage", "content"}:
                errors.append(f"line {line_number}: collection header second column is unusual: {row[1]!r}")
        else:
            expected_pid = data_rows
            parsed_pid = parse_int(row[0], "pid", line_number)
            if parsed_pid != expected_pid:
                errors.append(
                    f"line {line_number}: pid must equal zero-based passage offset {expected_pid}, got {parsed_pid}"
                )
            if not row[1].strip():
                errors.append(f"line {line_number}: passage text is empty")
            data_rows += 1

        if len(errors) >= max_errors:
            break

    if physical_rows == 0:
        errors.append("file is empty")
    elif data_rows == 0:
        label = "after header" if header_seen else ""
        errors.append(f"collection contains no passage rows {label}".strip())

    return data_rows, errors


def validate_queries(path: Path, max_errors: int) -> tuple[int, list[str]]:
    errors: list[str] = []
    seen_qids: set[int] = set()
    rows = 0

    for line_number, row in iter_tsv(path):
        if not row:
            errors.append(f"line {line_number}: blank rows are not valid query entries")
        elif len(row) < 2:
            errors.append(f"line {line_number}: query rows need at least qid and query text columns")
        else:
            qid = parse_int(row[0], "qid", line_number)
            if qid in seen_qids:
                errors.append(f"line {line_number}: repeated qid {qid}")
            seen_qids.add(qid)
            if not row[1].strip():
                errors.append(f"line {line_number}: query text is empty")
            rows += 1

        if len(errors) >= max_errors:
            break

    if rows == 0:
        errors.append("file contains no query rows")

    return rows, errors


def validate_ranking(path: Path, max_errors: int) -> tuple[int, list[str]]:
    errors: list[str] = []
    rows = 0

    for line_number, row in iter_tsv(path):
        if not row:
            errors.append(f"line {line_number}: blank rows are not valid ranking entries")
        elif len(row) < 3:
            errors.append(f"line {line_number}: ranking rows need at least qid, pid, and rank columns")
        else:
            parse_int(row[0], "qid", line_number)
            parse_int(row[1], "pid", line_number)
            rank = parse_int(row[2], "rank", line_number)
            if rank < 1:
                errors.append(f"line {line_number}: rank must be one-based and positive, got {rank}")
            if len(row) >= 4 and row[3] != "":
                parse_float(row[3], "score", line_number)
            rows += 1

        if len(errors) >= max_errors:
            break

    if rows == 0:
        errors.append("file contains no ranking rows")

    return rows, errors


def report(label: str, path: Path, rows: int, errors: list[str]) -> bool:
    if errors:
        print(f"[FAIL] {label}: {path} ({rows} parsed rows)", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return False

    print(f"[OK] {label}: {path} ({rows} rows)")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ColBERT collection/query/ranking TSV files before indexing or search.",
    )
    parser.add_argument("--collection", type=readable_path, help="collection TSV: pid<TAB>passage[<TAB>title]")
    parser.add_argument("--queries", type=readable_path, help="queries TSV: qid<TAB>query text")
    parser.add_argument("--ranking", type=readable_path, help="ranking TSV: qid<TAB>pid<TAB>rank[<TAB>score]")
    parser.add_argument("--max-errors", type=int, default=20, help="stop each file check after this many errors")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not any([args.collection, args.queries, args.ranking]):
        parser.error("provide at least one of --collection, --queries, or --ranking")

    if args.max_errors < 1:
        parser.error("--max-errors must be positive")

    ok = True

    try:
        if args.collection:
            rows, errors = validate_collection(args.collection, args.max_errors)
            ok = report("collection", args.collection, rows, errors) and ok
        if args.queries:
            rows, errors = validate_queries(args.queries, args.max_errors)
            ok = report("queries", args.queries, rows, errors) and ok
        if args.ranking:
            rows, errors = validate_ranking(args.ranking, args.max_errors)
            ok = report("ranking", args.ranking, rows, errors) and ok
    except ValidationError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
