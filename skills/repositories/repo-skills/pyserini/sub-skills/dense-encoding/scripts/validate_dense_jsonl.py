#!/usr/bin/env python3
"""Validate JSONL inputs or encoded JSONL vectors for Pyserini dense workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator


def iter_jsonl_paths(input_path: Path) -> Iterator[Path]:
    if input_path.is_file():
        yield input_path
        return
    if not input_path.is_dir():
        raise FileNotFoundError(f"input does not exist: {input_path}")
    for child in sorted(input_path.iterdir()):
        if child.is_file() and child.suffix.lower() in {".json", ".jsonl", ".ndjson"}:
            yield child


def decode_delimiter(value: str) -> str:
    return value.encode("utf-8").decode("unicode_escape")


def find_docid(record: dict, docid_field: str | None) -> tuple[str | None, str | None]:
    candidates = [docid_field] if docid_field else ["id", "_id", "docid"]
    for key in candidates:
        if key and key in record and record[key] not in (None, ""):
            return key, str(record[key])
    return None, None


def parse_fields(record: dict, fields: list[str], delimiter: str) -> tuple[list[str | None], str | None]:
    if all(field in record for field in fields):
        return [None if record[field] is None else str(record[field]) for field in fields], None
    if "contents" not in record:
        missing = [field for field in fields if field not in record]
        return [], f"missing direct fields {missing} and no contents field"
    contents = record["contents"]
    if not isinstance(contents, str):
        return [], "contents must be a string when direct fields are absent"
    parsed = contents
    if parsed.count(delimiter) == len(fields) and parsed.endswith(delimiter):
        parsed = parsed[: -len(delimiter)]
    values = parsed.split(delimiter)
    if len(values) != len(fields):
        return [], f"contents split into {len(values)} fields, expected {len(fields)}"
    return values, None


def validate_vector(value, expected_dimension: int | None) -> str | None:
    if not isinstance(value, list):
        return "vector must be a JSON array"
    if expected_dimension is not None and len(value) != expected_dimension:
        return f"vector dimension {len(value)} != expected {expected_dimension}"
    for index, element in enumerate(value):
        if not isinstance(element, (int, float)) or isinstance(element, bool):
            return f"vector element {index} is not numeric"
    return None


def validate_file(path: Path, args: argparse.Namespace, delimiter: str) -> tuple[int, list[str], Counter]:
    errors: list[str] = []
    stats: Counter = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                if args.allow_blank_lines:
                    continue
                errors.append(f"{path}:{line_number}: blank line")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"{path}:{line_number}: record must be a JSON object")
                continue

            docid_key, docid = find_docid(record, args.docid_field)
            if docid is None:
                expected = args.docid_field or "id/_id/docid"
                errors.append(f"{path}:{line_number}: missing document id field ({expected})")
            else:
                stats["docs"] += 1
                stats[f"docid:{docid_key}"] += 1

            fields, field_error = parse_fields(record, args.fields, delimiter)
            if field_error:
                errors.append(f"{path}:{line_number}: {field_error}")
            else:
                for field_name, value in zip(args.fields, fields):
                    if value in (None, ""):
                        stats[f"empty:{field_name}"] += 1
                    else:
                        stats[f"field:{field_name}"] += 1

            has_vector = args.vector_field in record
            if args.require_vector and not has_vector:
                errors.append(f"{path}:{line_number}: missing vector field {args.vector_field!r}")
            if has_vector:
                vector_error = validate_vector(record[args.vector_field], args.dimension)
                if vector_error:
                    errors.append(f"{path}:{line_number}: {vector_error}")
                else:
                    stats["vectors"] += 1
                    stats[f"dimension:{len(record[args.vector_field])}"] += 1

            if len(errors) >= args.max_errors:
                errors.append(f"stopped after {args.max_errors} errors")
                return line_number, errors, stats
    return line_number if 'line_number' in locals() else 0, errors, stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate JSONL for Pyserini dense corpus encoding or encoded-vector indexing."
    )
    parser.add_argument("--input", required=True, help="JSONL file or directory containing JSONL files.")
    parser.add_argument("--fields", nargs="+", default=["text"], help="Fields expected by pyserini.encode input --fields.")
    parser.add_argument("--docid-field", default=None, help="Custom document id key; defaults to id/_id/docid.")
    parser.add_argument("--delimiter", default="\\n", help="Delimiter used to split contents when direct fields are absent.")
    parser.add_argument("--vector-field", default="vector", help="Vector field name for encoded JSONL validation.")
    parser.add_argument("--require-vector", action="store_true", help="Require vector arrays on every row.")
    parser.add_argument("--dimension", type=int, default=None, help="Expected dense vector dimension.")
    parser.add_argument("--allow-blank-lines", action="store_true", help="Ignore blank lines instead of reporting errors.")
    parser.add_argument("--max-errors", type=int, default=20, help="Stop after this many errors.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    delimiter = decode_delimiter(args.delimiter)
    input_path = Path(args.input)

    try:
        paths = list(iter_jsonl_paths(input_path))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not paths:
        print(f"ERROR: no JSONL-like files found under {input_path}", file=sys.stderr)
        return 2

    total_stats: Counter = Counter()
    total_lines = 0
    all_errors: list[str] = []
    for path in paths:
        line_count, errors, stats = validate_file(path, args, delimiter)
        total_lines += line_count
        total_stats.update(stats)
        all_errors.extend(errors)
        if len(all_errors) >= args.max_errors:
            break

    if all_errors:
        for error in all_errors[: args.max_errors + 1]:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"Checked {len(paths)} file(s), {total_lines} line(s), found {len(all_errors)} error(s).",
            file=sys.stderr,
        )
        return 1

    print(f"OK: checked {len(paths)} file(s), {total_lines} line(s), {total_stats['docs']} document(s).")
    if total_stats["vectors"]:
        dimensions = sorted(
            (key.split(":", 1)[1], count)
            for key, count in total_stats.items()
            if key.startswith("dimension:")
        )
        print("Vectors: " + ", ".join(f"dim {dim} x {count}" for dim, count in dimensions))
    empty_fields = sorted((key.split(":", 1)[1], count) for key, count in total_stats.items() if key.startswith("empty:"))
    if empty_fields:
        print("Warnings: empty fields " + ", ".join(f"{field} x {count}" for field, count in empty_fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
