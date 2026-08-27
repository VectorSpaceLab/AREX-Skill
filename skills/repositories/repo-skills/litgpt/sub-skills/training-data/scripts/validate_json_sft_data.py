#!/usr/bin/env python3
"""Validate LitGPT JSON/JSONL supervised-finetuning data without training.

This script mirrors the safe path/schema checks from LitGPT's JSON data module:
- file input must be .json or .jsonl and contain SFT sample objects
- directory input must contain train.{json,jsonl} and val.{json,jsonl}
- directory input must not use val_split_fraction
- a single file without val_split_fraction defaults to 0.05 in LitGPT

It does not import LitGPT, load tokenizers, download data, or start training.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = (".json", ".jsonl")
REQUIRED_KEYS = ("instruction", "output")
OPTIONAL_KEYS = ("input",)


@dataclass
class Diagnostic:
    severity: str
    location: str
    message: str
    fix: str


@dataclass
class SplitSummary:
    split: str
    path: str
    samples: int
    with_input: int
    missing_input: int


@dataclass
class ValidationResult:
    ok: bool
    mode: str
    path: str
    val_split_fraction: float | None
    diagnostics: list[Diagnostic]
    splits: list[SplitSummary]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate LitGPT JSON/JSONL supervised-finetuning data without tokenizing or training."
    )
    parser.add_argument("json_path", type=Path, help="JSON/JSONL file or directory with train/val split files.")
    parser.add_argument(
        "--val-split-fraction",
        type=float,
        default=None,
        help="Validation split fraction for a single file. Must be omitted for split directories.",
    )
    parser.add_argument(
        "--require-input",
        action="store_true",
        help="Require every sample to include an input key; LitGPT itself treats input as optional.",
    )
    parser.add_argument("--max-errors", type=int, default=50, help="Stop reporting detailed row errors after this count.")
    parser.add_argument("--json-report", action="store_true", help="Print a machine-readable JSON report.")
    return parser.parse_args()


def diagnostic(severity: str, location: str, message: str, fix: str) -> Diagnostic:
    return Diagnostic(severity=severity, location=location, message=message, fix=fix)


def validate_val_fraction(value: float | None, diagnostics: list[Diagnostic]) -> None:
    if value is None:
        return
    if not 0 < value < 1:
        diagnostics.append(
            diagnostic(
                "error",
                "--val-split-fraction",
                f"Expected a fraction strictly between 0 and 1, got {value!r}.",
                "Use a value such as 0.05 or 0.1 for a single file, or omit it for split directories.",
            )
        )


def load_json_file(path: Path, diagnostics: list[Diagnostic], max_errors: int) -> list[Any] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        diagnostics.append(
            diagnostic(
                "error",
                str(path),
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}.",
                "Fix JSON syntax; a .json file must contain one JSON list of sample objects.",
            )
        )
        return None
    except OSError as exc:
        diagnostics.append(
            diagnostic("error", str(path), f"Could not read file: {exc}.", "Check file permissions and path.")
        )
        return None

    if not isinstance(data, list):
        diagnostics.append(
            diagnostic(
                "error",
                str(path),
                f"Expected top-level JSON list, got {type(data).__name__}.",
                "Wrap samples in a list, or use .jsonl with one object per line.",
            )
        )
        return None
    return data


def load_jsonl_file(path: Path, diagnostics: list[Diagnostic], max_errors: int) -> list[Any] | None:
    records: list[Any] = []
    errors = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    errors += 1
                    if errors <= max_errors:
                        diagnostics.append(
                            diagnostic(
                                "error",
                                f"{path}:{line_number}",
                                "Blank JSONL line is invalid; LitGPT json.loads would fail on it.",
                                "Remove blank lines from JSONL files.",
                            )
                        )
                    continue
                try:
                    records.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    errors += 1
                    if errors <= max_errors:
                        diagnostics.append(
                            diagnostic(
                                "error",
                                f"{path}:{line_number}",
                                f"Invalid JSONL record at column {exc.colno}: {exc.msg}.",
                                "Fix or remove this line; each non-empty JSONL line must be one JSON object.",
                            )
                        )
        if errors > max_errors:
            diagnostics.append(
                diagnostic(
                    "error",
                    str(path),
                    f"Suppressed {errors - max_errors} additional JSONL parse errors.",
                    "Fix the first reported JSONL errors and rerun validation.",
                )
            )
    except OSError as exc:
        diagnostics.append(
            diagnostic("error", str(path), f"Could not read file: {exc}.", "Check file permissions and path.")
        )
        return None
    return records


def load_records(path: Path, diagnostics: list[Diagnostic], max_errors: int) -> list[Any] | None:
    if path.suffix == ".json":
        return load_json_file(path, diagnostics, max_errors)
    if path.suffix == ".jsonl":
        return load_jsonl_file(path, diagnostics, max_errors)
    diagnostics.append(
        diagnostic(
            "error",
            str(path),
            f"Unsupported file suffix {path.suffix!r}.",
            "Use .json for a list of objects or .jsonl for one object per line.",
        )
    )
    return None


def validate_records(
    records: list[Any] | None,
    split: str,
    path: Path,
    diagnostics: list[Diagnostic],
    require_input: bool,
    max_errors: int,
) -> SplitSummary | None:
    if records is None:
        return None
    errors = 0
    with_input = 0
    for index, record in enumerate(records):
        location = f"{path}:{index + 1}"
        if not isinstance(record, dict):
            errors += 1
            if errors <= max_errors:
                diagnostics.append(
                    diagnostic(
                        "error",
                        location,
                        f"Expected sample object, got {type(record).__name__}.",
                        "Replace this row with an object containing instruction and output keys.",
                    )
                )
            continue
        for key in REQUIRED_KEYS:
            if key not in record:
                errors += 1
                if errors <= max_errors:
                    diagnostics.append(
                        diagnostic(
                            "error",
                            location,
                            f"Missing required key {key!r}.",
                            f"Add {key!r} as a string field to this sample.",
                        )
                    )
            elif not isinstance(record[key], str):
                errors += 1
                if errors <= max_errors:
                    diagnostics.append(
                        diagnostic(
                            "error",
                            location,
                            f"Key {key!r} must be a string, got {type(record[key]).__name__}.",
                            f"Convert {key!r} to a string value.",
                        )
                    )
        if "input" in record:
            with_input += 1
            if not isinstance(record["input"], str):
                diagnostics.append(
                    diagnostic(
                        "warning",
                        location,
                        f"Optional key 'input' should be a string, got {type(record['input']).__name__}.",
                        "Convert input to a string or remove it if unused.",
                    )
                )
        elif require_input:
            errors += 1
            if errors <= max_errors:
                diagnostics.append(
                    diagnostic(
                        "error",
                        location,
                        "Missing optional key 'input' while --require-input is set.",
                        "Add input as a string, often an empty string for Alpaca-style data.",
                    )
                )
    if errors > max_errors:
        diagnostics.append(
            diagnostic(
                "error",
                str(path),
                f"Suppressed {errors - max_errors} additional schema errors.",
                "Fix the first reported row errors and rerun validation.",
            )
        )
    if not records:
        diagnostics.append(
            diagnostic(
                "warning",
                str(path),
                "Dataset split contains zero samples.",
                "Add samples before training; empty splits fail or produce unusable training.",
            )
        )
    return SplitSummary(
        split=split,
        path=str(path),
        samples=len(records),
        with_input=with_input,
        missing_input=max(0, len(records) - with_input),
    )


def find_split(directory: Path, split: str) -> Path | None:
    for suffix in SUPPORTED_SUFFIXES:
        candidate = directory / f"{split}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def validate_path(args: argparse.Namespace) -> ValidationResult:
    diagnostics: list[Diagnostic] = []
    summaries: list[SplitSummary] = []
    path = args.json_path
    validate_val_fraction(args.val_split_fraction, diagnostics)

    if not path.exists():
        diagnostics.append(
            diagnostic(
                "error",
                str(path),
                "Path does not exist.",
                "Pass an existing .json/.jsonl file or a directory containing train/val split files.",
            )
        )
        return ValidationResult(False, "missing", str(path), args.val_split_fraction, diagnostics, summaries)

    if path.is_file():
        if args.val_split_fraction is None:
            diagnostics.append(
                diagnostic(
                    "warning",
                    str(path),
                    "Single file provided without --val-split-fraction; LitGPT defaults to 0.05.",
                    "Set --val-split-fraction explicitly to document the intended split.",
                )
            )
        records = load_records(path, diagnostics, args.max_errors)
        summary = validate_records(records, "single-file", path, diagnostics, args.require_input, args.max_errors)
        if summary is not None:
            summaries.append(summary)
        ok = not any(item.severity == "error" for item in diagnostics)
        return ValidationResult(ok, "single-file", str(path), args.val_split_fraction, diagnostics, summaries)

    if path.is_dir():
        if args.val_split_fraction is not None:
            diagnostics.append(
                diagnostic(
                    "error",
                    str(path),
                    "Directory input must not set --val-split-fraction.",
                    "Remove --val-split-fraction; split directories define train and val membership explicitly.",
                )
            )
        train_path = find_split(path, "train")
        val_path = find_split(path, "val")
        if train_path is None or val_path is None:
            diagnostics.append(
                diagnostic(
                    "error",
                    str(path),
                    "Directory must contain train.json/train.jsonl and val.json/val.jsonl.",
                    "Add both split files, or pass one .json/.jsonl file with --val-split-fraction.",
                )
            )
        for split, split_path in (("train", train_path), ("val", val_path)):
            if split_path is None:
                continue
            records = load_records(split_path, diagnostics, args.max_errors)
            summary = validate_records(records, split, split_path, diagnostics, args.require_input, args.max_errors)
            if summary is not None:
                summaries.append(summary)
        ok = not any(item.severity == "error" for item in diagnostics)
        return ValidationResult(ok, "split-directory", str(path), args.val_split_fraction, diagnostics, summaries)

    diagnostics.append(
        diagnostic("error", str(path), "Path is neither a regular file nor a directory.", "Use a file or directory.")
    )
    return ValidationResult(False, "unsupported", str(path), args.val_split_fraction, diagnostics, summaries)


def print_human(result: ValidationResult) -> None:
    status = "OK" if result.ok else "FAILED"
    print(f"LitGPT JSON SFT validation: {status}")
    print(f"Path: {result.path}")
    print(f"Mode: {result.mode}")
    if result.val_split_fraction is not None:
        print(f"val_split_fraction: {result.val_split_fraction}")
    if result.splits:
        print("Splits:")
        for split in result.splits:
            print(
                f"  - {split.split}: {split.samples} samples "
                f"({split.with_input} with input, {split.missing_input} missing input) at {split.path}"
            )
    if result.diagnostics:
        print("Diagnostics:")
        for item in result.diagnostics:
            print(f"  [{item.severity.upper()}] {item.location}: {item.message}")
            print(f"    Fix: {item.fix}")


def main() -> int:
    args = parse_args()
    result = validate_path(args)
    if args.json_report:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "mode": result.mode,
                    "path": result.path,
                    "val_split_fraction": result.val_split_fraction,
                    "splits": [asdict(split) for split in result.splits],
                    "diagnostics": [asdict(item) for item in result.diagnostics],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
