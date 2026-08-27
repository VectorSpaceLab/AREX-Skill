#!/usr/bin/env python3
"""Validate Chinese-LLaMA-Alpaca training data before launching long runs.

This helper intentionally uses only the Python standard library. It checks the
public data shapes consumed by the bundled PEFT training scripts:

* SFT mode: JSON array of records with string instruction, input, and output.
* PT mode: UTF-8 plain text files with non-empty training text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

REQUIRED_SFT_FIELDS = ("instruction", "input", "output")


class ValidationError(Exception):
    """Collectable validation failure."""


def _iter_input_files(path: Path, mode: str) -> list[Path]:
    if path.is_dir():
        suffix = ".json" if mode == "sft" else ".txt"
        files = sorted(p for p in path.iterdir() if p.is_file() and p.suffix == suffix)
        if not files:
            raise ValidationError(f"{path}: no {suffix} files found for --mode {mode}")
        return files
    if not path.exists():
        raise ValidationError(f"{path}: path does not exist")
    if not path.is_file():
        raise ValidationError(f"{path}: expected a file or directory")
    return [path]


def _limited(records: Sequence[object], max_records: int | None) -> Sequence[object]:
    if max_records is None:
        return records
    return records[:max_records]


def _validate_sft_file(path: Path, max_records: int | None) -> tuple[int, int]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path}: not valid UTF-8: {exc}") from exc

    if not isinstance(data, list):
        raise ValidationError(f"{path}: top-level JSON value must be a list of instruction records")
    if not data:
        raise ValidationError(f"{path}: JSON list is empty")

    errors: list[str] = []
    checked = 0
    for idx, record in enumerate(_limited(data, max_records), start=1):
        checked += 1
        prefix = f"{path}: record {idx}"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: expected object with keys {', '.join(REQUIRED_SFT_FIELDS)}")
            continue
        for field in REQUIRED_SFT_FIELDS:
            if field not in record:
                errors.append(f"{prefix}: missing required field '{field}'")
        for field in REQUIRED_SFT_FIELDS:
            if field in record and not isinstance(record[field], str):
                errors.append(f"{prefix}: field '{field}' must be a string, got {type(record[field]).__name__}")
        instruction = record.get("instruction")
        output = record.get("output")
        if isinstance(instruction, str) and not instruction.strip():
            errors.append(f"{prefix}: field 'instruction' must not be empty")
        if isinstance(output, str) and not output.strip():
            errors.append(f"{prefix}: field 'output' must not be empty")
    if checked == 0:
        raise ValidationError(f"{path}: --max-records selected zero records")
    if errors:
        preview = "\n".join(f"  - {msg}" for msg in errors[:20])
        extra = "" if len(errors) <= 20 else f"\n  ... {len(errors) - 20} more error(s)"
        raise ValidationError(f"{path}: SFT schema validation failed:\n{preview}{extra}")
    return checked, len(data)


def _validate_pt_file(path: Path, max_records: int | None) -> tuple[int, int]:
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path}: not valid UTF-8: {exc}") from exc

    if not lines:
        raise ValidationError(f"{path}: text file is empty")

    checked_lines = lines if max_records is None else lines[:max_records]
    if not checked_lines:
        raise ValidationError(f"{path}: --max-records selected zero lines")

    non_empty = sum(1 for line in checked_lines if line.strip())
    total_chars = sum(len(line) for line in checked_lines)
    if non_empty == 0:
        raise ValidationError(f"{path}: checked lines contain only whitespace")
    if total_chars < 8:
        raise ValidationError(f"{path}: checked text is extremely short ({total_chars} characters); provide real CLM text")
    return len(checked_lines), len(lines)


def validate(mode: str, input_path: Path, max_records: int | None) -> int:
    files = _iter_input_files(input_path, mode)
    summaries: list[str] = []
    for file in files:
        if mode == "sft":
            checked, total = _validate_sft_file(file, max_records)
            summaries.append(f"{file}: checked {checked}/{total} instruction record(s)")
        else:
            checked, total = _validate_pt_file(file, max_records)
            summaries.append(f"{file}: checked {checked}/{total} text line(s)")
    print(f"OK: {mode} training data validation passed for {len(files)} file(s).")
    for summary in summaries:
        print(f"  {summary}")
    return 0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Chinese-LLaMA-Alpaca PT or SFT training data shape.")
    parser.add_argument("--mode", choices=("sft", "pt"), required=True, help="Training data mode to validate.")
    parser.add_argument("--input", required=True, type=Path, help="JSON/TXT file or directory of JSON/TXT files.")
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Validate only the first N SFT records or PT text lines for a quick schema check.",
    )
    args = parser.parse_args(argv)
    if args.max_records is not None and args.max_records < 1:
        parser.error("--max-records must be >= 1 when provided")
    return args


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return validate(args.mode, args.input, args.max_records)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
