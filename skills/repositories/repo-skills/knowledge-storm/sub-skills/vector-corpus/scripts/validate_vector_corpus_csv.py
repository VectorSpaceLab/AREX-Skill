#!/usr/bin/env python3
"""Validate a CSV corpus for knowledge-storm VectorRM/Qdrant workflows.

The checker uses only the Python standard library so that --help and schema
validation are safe before installing heavy STORM, embedding, or Qdrant
dependencies.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = ("content", "url")
OPTIONAL_COLUMNS = ("title", "description")


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _format_column_list(columns: Iterable[str]) -> str:
    return ", ".join(columns)


def validate_vector_corpus_csv(input_path: Path, strict_unique_url: bool = False) -> int:
    """Validate a VectorRM corpus CSV and return a process-style exit code."""
    errors: list[str] = []
    warnings: list[str] = []

    if input_path.suffix.lower() != ".csv":
        errors.append(f"ERROR: input path must end with .csv: {input_path}")
    if not input_path.exists():
        errors.append(f"ERROR: input path does not exist: {input_path}")
    if input_path.exists() and not input_path.is_file():
        errors.append(f"ERROR: input path is not a file: {input_path}")
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        print(f"FAIL: {len(errors)} error(s), 0 warning(s), checked 0 data row(s).")
        return 1

    row_count = 0
    seen_urls: dict[str, int] = {}

    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            if sample == "":
                errors.append("ERROR: CSV is empty.")
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                errors.append(
                    "ERROR: CSV has no header row. Required columns: "
                    + _format_column_list(REQUIRED_COLUMNS)
                )
            else:
                headers = [h.strip() if h is not None else "" for h in reader.fieldnames]
                missing = [column for column in REQUIRED_COLUMNS if column not in headers]
                if missing:
                    errors.append(
                        "ERROR: missing required column(s): " + _format_column_list(missing)
                    )
                missing_optional = [column for column in OPTIONAL_COLUMNS if column not in headers]
                if missing_optional:
                    warnings.append(
                        "WARNING: optional column(s) not present: "
                        + _format_column_list(missing_optional)
                    )

                if not missing:
                    for row in reader:
                        row_count += 1
                        line_no = reader.line_num
                        content = row.get("content")
                        url = row.get("url")
                        if _is_blank(content):
                            errors.append(f"ERROR: row {line_no} has empty content")
                        if _is_blank(url):
                            errors.append(f"ERROR: row {line_no} has empty url")
                            continue
                        normalized_url = str(url).strip()
                        first_line = seen_urls.get(normalized_url)
                        if first_line is not None:
                            message = (
                                f"duplicate url value {normalized_url!r} first seen at row "
                                f"{first_line}, repeated at row {line_no}"
                            )
                            if strict_unique_url:
                                errors.append("ERROR: " + message)
                            else:
                                warnings.append("WARNING: " + message)
                        else:
                            seen_urls[normalized_url] = line_no
    except UnicodeDecodeError as exc:
        errors.append(f"ERROR: unable to decode CSV as UTF-8: {exc}")
    except csv.Error as exc:
        errors.append(f"ERROR: unable to parse CSV: {exc}")
    except OSError as exc:
        errors.append(f"ERROR: unable to read CSV: {exc}")

    for message in warnings:
        print(message, file=sys.stderr)
    for message in errors:
        print(message, file=sys.stderr)

    if errors:
        print(
            f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s), "
            f"checked {row_count} data row(s)."
        )
        return 1

    print(
        f"OK: checked {row_count} data row(s); required columns present: "
        f"{_format_column_list(REQUIRED_COLUMNS)}; warnings: {len(warnings)}."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a CSV corpus for knowledge-storm VectorRM/Qdrant workflows."
    )
    parser.add_argument(
        "--input-path",
        required=True,
        type=Path,
        help="Path to a CSV with required columns 'content' and 'url'.",
    )
    parser.add_argument(
        "--strict-unique-url",
        action="store_true",
        help="Treat duplicate url values as errors instead of warnings.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return validate_vector_corpus_csv(args.input_path, args.strict_unique_url)


if __name__ == "__main__":
    raise SystemExit(main())
