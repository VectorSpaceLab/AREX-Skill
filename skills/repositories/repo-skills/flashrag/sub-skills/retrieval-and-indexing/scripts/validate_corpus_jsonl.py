#!/usr/bin/env python3
"""Validate and summarize a FlashRAG corpus JSONL file.

This helper intentionally avoids importing FlashRAG or chunking/indexing dependencies.
It checks the corpus shape used by FlashRAG retrieval and reports common risks
before expensive chunking or indexing jobs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a FlashRAG corpus JSONL file.")
    parser.add_argument("corpus_path", type=Path, help="Path to a JSONL corpus file.")
    parser.add_argument("--sample", type=int, default=20, help="Number of valid records to inspect in detail.")
    parser.add_argument("--max-errors", type=int, default=20, help="Maximum detailed errors to print.")
    parser.add_argument(
        "--require-title-newline",
        action="store_true",
        help="Warn when sampled contents do not contain the title/body newline expected by chunking.",
    )
    parser.add_argument(
        "--allow-missing-id",
        action="store_true",
        help="Do not fail when records are missing id fields.",
    )
    return parser.parse_args()


def preview(value: Any, limit: int = 80) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main() -> int:
    args = parse_args()
    path = args.corpus_path
    if not path.exists():
        print(f"ERROR: corpus file does not exist: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"ERROR: corpus path is not a file: {path}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    id_counter: Counter[str] = Counter()
    field_counter: Counter[str] = Counter()
    contents_lengths: list[int] = []
    sampled = 0
    total_lines = 0
    valid_records = 0
    missing_id_count = 0
    empty_contents_count = 0
    no_newline_count = 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            total_lines += 1
            line = raw_line.rstrip("\n")
            if not line.strip():
                errors.append(f"line {line_number}: blank line")
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_number}: expected JSON object, got {type(record).__name__}")
                continue

            valid_records += 1
            field_counter.update(record.keys())

            if "id" not in record:
                missing_id_count += 1
                if not args.allow_missing_id:
                    errors.append(f"line {line_number}: missing id")
            else:
                id_counter.update([str(record["id"])])

            contents = record.get("contents")
            if not isinstance(contents, str):
                errors.append(f"line {line_number}: contents must be a string, got {preview(contents)}")
                continue
            if not contents.strip():
                empty_contents_count += 1
                errors.append(f"line {line_number}: contents is empty")
                continue

            contents_lengths.append(len(contents))
            if sampled < args.sample:
                sampled += 1
                if "\n" not in contents:
                    no_newline_count += 1
                    if args.require_title_newline:
                        warnings.append(
                            f"line {line_number}: sampled contents lacks title/body newline: {preview(contents)}"
                        )

    duplicate_ids = [record_id for record_id, count in id_counter.items() if count > 1]
    if duplicate_ids:
        shown = ", ".join(duplicate_ids[:10])
        errors.append(f"duplicate id values: {shown}" + (" ..." if len(duplicate_ids) > 10 else ""))

    print("FlashRAG corpus validation summary")
    print(f"path: {path}")
    print(f"lines: {total_lines}")
    print(f"valid_records: {valid_records}")
    print(f"unique_ids: {len(id_counter)}")
    print(f"missing_id_records: {missing_id_count}")
    print(f"empty_contents_records: {empty_contents_count}")
    if contents_lengths:
        sorted_lengths = sorted(contents_lengths)
        median = sorted_lengths[len(sorted_lengths) // 2]
        print(f"contents_length_min: {sorted_lengths[0]}")
        print(f"contents_length_median: {median}")
        print(f"contents_length_max: {sorted_lengths[-1]}")
    if field_counter:
        common_fields = ", ".join(f"{key}:{count}" for key, count in field_counter.most_common(12))
        print(f"common_fields: {common_fields}")
    if sampled:
        print(f"sampled_records: {sampled}")
        print(f"sampled_without_title_newline: {no_newline_count}")

    for warning in warnings[: args.max_errors]:
        print(f"WARNING: {warning}", file=sys.stderr)
    if len(warnings) > args.max_errors:
        print(f"WARNING: {len(warnings) - args.max_errors} additional warnings suppressed", file=sys.stderr)

    for error in errors[: args.max_errors]:
        print(f"ERROR: {error}", file=sys.stderr)
    if len(errors) > args.max_errors:
        print(f"ERROR: {len(errors) - args.max_errors} additional errors suppressed", file=sys.stderr)

    if errors:
        print("status: failed")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
