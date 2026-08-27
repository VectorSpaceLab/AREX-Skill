#!/usr/bin/env python3
"""Validate OASIS Reddit JSON and Twitter CSV profile files.

This script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REDDIT_REQUIRED_FIELDS = (
    "realname",
    "username",
    "bio",
    "persona",
    "age",
    "gender",
    "mbti",
    "country",
)
TWITTER_REQUIRED_FIELDS = (
    "name",
    "username",
    "user_char",
    "description",
)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _is_integer_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value >= 0
    if isinstance(value, str):
        return value.strip().isdigit()
    return False


def _format_errors(kind: str, path: Path, errors: list[str]) -> int:
    print(f"{kind} invalid: {path}", file=sys.stderr)
    for error in errors[:20]:
        print(f"  - {error}", file=sys.stderr)
    if len(errors) > 20:
        print(f"  - ... {len(errors) - 20} more error(s)", file=sys.stderr)
    return 1


def _validate_reddit_json(path: Path) -> int:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return _format_errors("reddit-json", path, ["file does not exist"])
    except OSError as exc:
        return _format_errors("reddit-json", path, [f"unable to read file: {exc}"])
    except json.JSONDecodeError as exc:
        return _format_errors("reddit-json", path, [f"invalid JSON: {exc}"])

    if not isinstance(payload, list):
        return _format_errors(
            "reddit-json",
            path,
            ["root value must be a JSON array of profile objects"],
        )

    if not payload:
        errors.append("profile array is empty")

    for index, row in enumerate(payload, start=1):
        if not isinstance(row, dict):
            errors.append(f"record {index}: expected an object, got {type(row).__name__}")
            continue

        missing = [field for field in REDDIT_REQUIRED_FIELDS if field not in row]
        if missing:
            errors.append(
                f"record {index}: missing required fields: {', '.join(missing)}"
            )

        for field in REDDIT_REQUIRED_FIELDS:
            if field not in row:
                continue
            value = row[field]
            if field == "age":
                if not _is_integer_like(value):
                    errors.append(f"record {index}: age must be an integer-like value")
            elif not _is_nonempty_string(value):
                errors.append(f"record {index}: {field} must be a non-empty string")

    if errors:
        return _format_errors("reddit-json", path, errors)

    print(f"reddit-json OK: {len(payload)} profile(s) validated.")
    return 0


def _normalize_headers(fieldnames: list[str | None]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw_name in fieldnames:
        if raw_name is None:
            continue
        normalized = raw_name.strip()
        if normalized and normalized not in mapping:
            mapping[normalized] = raw_name
    return mapping


def _validate_twitter_csv(path: Path) -> int:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                return _format_errors(
                    "twitter-csv",
                    path,
                    ["CSV header is missing"],
                )
            header_map = _normalize_headers(reader.fieldnames)
            missing_headers = [
                field for field in TWITTER_REQUIRED_FIELDS if field not in header_map
            ]
            if missing_headers:
                errors.append(
                    "missing required columns: " + ", ".join(missing_headers)
                )

            rows = list(reader)
    except FileNotFoundError:
        return _format_errors("twitter-csv", path, ["file does not exist"])
    except OSError as exc:
        return _format_errors("twitter-csv", path, [f"unable to read file: {exc}"])

    if not rows:
        errors.append("CSV contains no profile rows")

    for line_no, row in enumerate(rows, start=2):
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: expected a row dictionary")
            continue
        for field in TWITTER_REQUIRED_FIELDS:
            raw_key = header_map.get(field)
            value = row.get(raw_key, "") if raw_key is not None else ""
            if not _is_nonempty_string(value):
                errors.append(f"line {line_no}: {field} must be a non-empty string")

    if errors:
        return _format_errors("twitter-csv", path, errors)

    print(f"twitter-csv OK: {len(rows)} profile row(s) validated.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate OASIS Reddit JSON or Twitter CSV profile files.")
    parser.add_argument(
        "--kind",
        required=True,
        choices=("reddit-json", "twitter-csv"),
        help="Profile file format to validate.",
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the profile file to validate.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.path)
    if args.kind == "reddit-json":
        return _validate_reddit_json(path)
    return _validate_twitter_csv(path)


if __name__ == "__main__":
    raise SystemExit(main())
