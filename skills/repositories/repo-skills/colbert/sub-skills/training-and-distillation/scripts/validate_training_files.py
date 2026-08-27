#!/usr/bin/env python3
"""Validate ColBERT training triples, queries, and collection files without training."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


class ValidationError(Exception):
    """Raised when validation detects an unsafe or incompatible file."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ColBERT triples JSONL plus queries/collection TSV files without importing ColBERT or starting training."
    )
    parser.add_argument("--triples", type=Path, required=True, help="Path to JSONL triples/examples file.")
    parser.add_argument("--queries", type=Path, required=True, help="Path to queries TSV: qid<TAB>query text.")
    parser.add_argument("--collection", type=Path, required=True, help="Path to collection TSV: pid<TAB>passage[<TAB>title].")
    parser.add_argument("--nway", type=int, default=2, help="Expected passages per query example. Default: 2.")
    parser.add_argument("--max-errors", type=int, default=20, help="Stop after this many validation errors. Default: 20.")
    parser.add_argument("--sample", type=int, default=0, help="Only validate this many triples lines; 0 validates all lines.")
    parser.add_argument("--allow-mixed-scores", action="store_true", help="Allow a single example to mix scored and unscored passage entries.")
    parser.add_argument("--allow-noncontiguous-collection-ids", action="store_true", help="Do not require collection pid to equal zero-based row index.")
    return parser.parse_args()


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise ValidationError(f"{label} file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"{label} path is not a file: {path}")


def parse_int(value: Any, context: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{context} must be an integer, not boolean")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} must be an integer: {value!r}") from exc


def load_queries(path: Path) -> tuple[dict[int, str], list[str]]:
    queries: dict[int, str] = {}
    errors: list[str] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            if not row or all(not cell for cell in row):
                continue
            if len(row) < 2:
                errors.append(f"queries line {line_number}: expected at least 2 TSV fields")
                continue
            try:
                qid = parse_int(row[0], f"queries line {line_number} qid")
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if qid in queries:
                errors.append(f"queries line {line_number}: duplicate qid {qid}")
                continue
            if not row[1].strip():
                errors.append(f"queries line {line_number}: empty query text for qid {qid}")
            queries[qid] = row[1]

    if not queries:
        errors.append("queries file has no usable query rows")
    return queries, errors


def load_collection(path: Path, require_contiguous_ids: bool) -> tuple[dict[int, str], list[str]]:
    collection: dict[int, str] = {}
    errors: list[str] = []
    data_row_index = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for physical_line, row in enumerate(reader, start=1):
            if not row or all(not cell for cell in row):
                continue
            if row[0] == "id" and physical_line == 1:
                continue
            if len(row) < 2:
                errors.append(f"collection line {physical_line}: expected at least 2 TSV fields")
                data_row_index += 1
                continue
            try:
                pid = parse_int(row[0], f"collection line {physical_line} pid")
            except ValueError as exc:
                errors.append(str(exc))
                data_row_index += 1
                continue
            if require_contiguous_ids and pid != data_row_index:
                errors.append(f"collection line {physical_line}: pid {pid} should equal zero-based data row index {data_row_index}")
            if pid in collection:
                errors.append(f"collection line {physical_line}: duplicate pid {pid}")
                data_row_index += 1
                continue
            if not row[1].strip():
                errors.append(f"collection line {physical_line}: empty passage for pid {pid}")
            collection[pid] = row[1]
            data_row_index += 1

    if not collection:
        errors.append("collection file has no usable passage rows")
    return collection, errors


def passage_pid_and_score(entry: Any, line_number: int, position: int) -> tuple[int, bool]:
    if isinstance(entry, list):
        if len(entry) != 2:
            raise ValueError(f"triples line {line_number}: passage entry {position} scored form must be [pid, score]")
        pid = parse_int(entry[0], f"triples line {line_number} passage {position} pid")
        if not isinstance(entry[1], (int, float)) or isinstance(entry[1], bool):
            raise ValueError(f"triples line {line_number}: passage entry {position} score must be numeric")
        return pid, True

    pid = parse_int(entry, f"triples line {line_number} passage {position} pid")
    return pid, False


def iter_json_lines(path: Path) -> Iterable[tuple[int, Sequence[Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"triples line {line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(value, list):
                raise ValueError(f"triples line {line_number}: expected a JSON array")
            yield line_number, value


def validate_triples(
    path: Path,
    query_ids: set[int],
    passage_ids: set[int],
    nway: int,
    max_errors: int,
    sample: int,
    allow_mixed_scores: bool,
) -> tuple[int, list[str], dict[str, int]]:
    errors: list[str] = []
    stats = {
        "scored_examples": 0,
        "unscored_examples": 0,
        "mixed_score_examples": 0,
        "extra_passage_fields": 0,
    }
    count = 0

    try:
        for line_number, example in iter_json_lines(path):
            if sample and count >= sample:
                break
            count += 1

            if len(example) < nway + 1:
                errors.append(f"triples line {line_number}: expected qid plus at least {nway} passages, got {len(example)} fields")
                if len(errors) >= max_errors:
                    break
                continue
            if len(example) > nway + 1:
                stats["extra_passage_fields"] += 1

            try:
                qid = parse_int(example[0], f"triples line {line_number} qid")
            except ValueError as exc:
                errors.append(str(exc))
                if len(errors) >= max_errors:
                    break
                continue

            if qid not in query_ids:
                errors.append(f"triples line {line_number}: qid {qid} not found in queries")

            score_flags: list[bool] = []
            for position, entry in enumerate(example[1 : nway + 1], start=1):
                try:
                    pid, has_score = passage_pid_and_score(entry, line_number, position)
                except ValueError as exc:
                    errors.append(str(exc))
                    continue
                score_flags.append(has_score)
                if pid not in passage_ids:
                    errors.append(f"triples line {line_number}: pid {pid} not found in collection")

            if score_flags:
                if all(score_flags):
                    stats["scored_examples"] += 1
                elif not any(score_flags):
                    stats["unscored_examples"] += 1
                else:
                    stats["mixed_score_examples"] += 1
                    if not allow_mixed_scores:
                        errors.append(f"triples line {line_number}: mixes scored and unscored passage entries")

            if len(errors) >= max_errors:
                break
    except ValueError as exc:
        errors.append(str(exc))

    if count == 0:
        errors.append("triples file has no usable JSON array rows")

    return count, errors, stats


def main() -> int:
    args = parse_args()
    if args.nway < 2:
        print("ERROR: --nway must be at least 2", file=sys.stderr)
        return 2
    if args.max_errors < 1:
        print("ERROR: --max-errors must be at least 1", file=sys.stderr)
        return 2
    if args.sample < 0:
        print("ERROR: --sample must be non-negative", file=sys.stderr)
        return 2

    try:
        require_file(args.triples, "triples")
        require_file(args.queries, "queries")
        require_file(args.collection, "collection")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    queries, query_errors = load_queries(args.queries)
    collection, collection_errors = load_collection(args.collection, not args.allow_noncontiguous_collection_ids)
    errors = query_errors + collection_errors

    remaining_error_budget = max(1, args.max_errors - len(errors))
    triple_count, triple_errors, stats = validate_triples(
        args.triples,
        set(queries),
        set(collection),
        args.nway,
        remaining_error_budget,
        args.sample,
        args.allow_mixed_scores,
    )
    errors.extend(triple_errors)

    print("ColBERT training file validation summary")
    print(f"  queries: {len(queries)}")
    print(f"  collection passages: {len(collection)}")
    print(f"  triples checked: {triple_count}")
    print(f"  nway expected: {args.nway}")
    print(f"  scored examples: {stats['scored_examples']}")
    print(f"  unscored examples: {stats['unscored_examples']}")
    print(f"  mixed-score examples: {stats['mixed_score_examples']}")
    print(f"  examples with extra passage fields: {stats['extra_passage_fields']}")

    if stats["extra_passage_fields"]:
        print("  note: ColBERT consumes only the first nway passage entries from longer examples")

    if errors:
        print("\nValidation failed:", file=sys.stderr)
        for error in errors[: args.max_errors]:
            print(f"  - {error}", file=sys.stderr)
        if len(errors) > args.max_errors:
            print(f"  - ... {len(errors) - args.max_errors} more errors", file=sys.stderr)
        return 1

    print("Validation passed: files are shape-compatible for ColBERT training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
