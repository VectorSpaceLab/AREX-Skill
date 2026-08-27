#!/usr/bin/env python3
"""Validate local tabular input columns for DataFlow foundation workflows.

Usage examples:
  python scripts/validate_tabular_input.py records.jsonl --required id text
  python scripts/validate_tabular_input.py records.csv --required id,text --print-schema
  python scripts/validate_tabular_input.py --self-check-help

The script is offline-safe for local files and reads through DataFlow's public
FileStorage API so validation matches DataFlow step-0 loading behavior.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataflow.utils.storage import FileStorage


SUPPORTED_SUFFIX_TO_CACHE_TYPE = {
    ".json": "json",
    ".jsonl": "jsonl",
    ".csv": "csv",
    ".parquet": "parquet",
    ".pickle": "pickle",
    ".xlsx": "xlsx",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate required columns and file suffix for a local DataFlow tabular fixture.",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Local JSON, JSONL, CSV, Parquet, Pickle, or XLSX file to validate.",
    )
    parser.add_argument(
        "--required",
        nargs="*",
        default=[],
        help="Required columns. Accepts space-separated names and/or comma-separated groups.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow an input file with zero rows. Columns are still checked.",
    )
    parser.add_argument(
        "--print-schema",
        action="store_true",
        help="Print discovered columns and row count as JSON.",
    )
    parser.add_argument(
        "--self-check-help",
        action="store_true",
        help="Verify that argparse --help text is available, then exit.",
    )
    return parser


def normalize_required(raw_values: list[str]) -> list[str]:
    required: list[str] = []
    for value in raw_values:
        for part in value.split(","):
            column = part.strip()
            if column and column not in required:
                required.append(column)
    return required


def validate_path(path: Path) -> str:
    if str(path).startswith(("hf:", "ms:")):
        raise ValueError("Remote hf:/ms: dataset sources are not offline-safe for this validator; use a local fixture file.")
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIX_TO_CACHE_TYPE:
        supported = ", ".join(sorted(SUPPORTED_SUFFIX_TO_CACHE_TYPE))
        raise ValueError(f"Unsupported suffix {suffix!r}. Supported suffixes: {supported}")
    return SUPPORTED_SUFFIX_TO_CACHE_TYPE[suffix]


def read_dataframe(path: Path, cache_type: str):
    storage = FileStorage(
        first_entry_file_name=str(path),
        cache_path=str(path.parent / ".dataflow_validation_cache"),
        file_name_prefix="validation",
        cache_type=cache_type,
    ).reset()
    storage.step()
    return storage.read(output_type="dataframe")


def validate_file(path: Path, required: list[str], allow_empty: bool) -> dict:
    cache_type = validate_path(path)
    dataframe = read_dataframe(path, cache_type)
    columns = list(dataframe.columns)
    missing = [column for column in required if column not in columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}; available columns: {columns}")
    row_count = int(len(dataframe))
    if row_count == 0 and not allow_empty:
        raise ValueError("Input file has zero rows. Pass --allow-empty if this is intentional.")
    return {
        "path": str(path),
        "cache_type": cache_type,
        "columns": columns,
        "row_count": row_count,
        "required": required,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_check_help:
        help_text = parser.format_help()
        if "--help" not in help_text or "--required" not in help_text:
            raise AssertionError("argparse help text did not include expected options")
        print("OK: argparse --help text is available.")
        return 0

    if args.input_file is None:
        parser.error("input_file is required unless --self-check-help is used")

    required = normalize_required(args.required)
    result = validate_file(path=args.input_file, required=required, allow_empty=args.allow_empty)
    if args.print_schema:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "OK: {path} has {row_count} rows and required columns {required}".format(
                path=result["path"],
                row_count=result["row_count"],
                required=result["required"],
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
