#!/usr/bin/env python3
"""Validate custom EvalScope dataset shapes used by ms-swift.

Supported formats:
- general_mcq: CSV files named {subset}_val.csv and optional {subset}_dev.csv
- general_qa: JSONL files named {subset}.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


OPTION_COLUMNS = tuple("ABCDEFGHIJ")


class ValidationErrorCollector:
    def __init__(self, max_errors: int) -> None:
        self.max_errors = max_errors
        self.errors: List[str] = []

    def add(self, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(message)
        elif len(self.errors) == self.max_errors:
            self.errors.append("additional errors suppressed")

    @property
    def ok(self) -> bool:
        return not self.errors


def normalize_header(fieldnames: Sequence[str] | None) -> List[str]:
    if not fieldnames:
        return []
    return [fieldname.strip().lstrip("\ufeff") for fieldname in fieldnames]


def non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def discover_mcq_subsets(dataset_dir: Path) -> List[str]:
    return sorted(path.name[:-8] for path in dataset_dir.glob("*_val.csv") if path.name.endswith("_val.csv"))


def discover_qa_subsets(dataset_dir: Path) -> List[str]:
    return sorted(path.stem for path in dataset_dir.glob("*.jsonl"))


def validate_mcq_file(path: Path, subset: str, split_name: str, collector: ValidationErrorCollector) -> int:
    if not path.exists():
        collector.add(f"{path}: missing required {split_name} file for subset '{subset}'")
        return 0
    row_count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        header = normalize_header(reader.fieldnames)
        if not header:
            collector.add(f"{path}: empty CSV header")
            return 0
        option_columns = [column for column in OPTION_COLUMNS if column in header]
        missing_required = [column for column in ("question", "answer") if column not in header]
        if missing_required:
            collector.add(f"{path}: missing required columns: {', '.join(missing_required)}")
        if len(option_columns) < 2:
            collector.add(f"{path}: expected at least two option columns from A-J")
        for row_number, row in enumerate(reader, start=2):
            row_count += 1
            clean_row: Dict[str, str] = {str(key).strip().lstrip("\ufeff"): value for key, value in row.items() if key is not None}
            if not non_empty(clean_row.get("question")):
                collector.add(f"{path}:{row_number}: question is empty")
            present_options = [column for column in option_columns if non_empty(clean_row.get(column))]
            if len(present_options) < 2:
                collector.add(f"{path}:{row_number}: expected at least two non-empty options")
            answer = (clean_row.get("answer") or "").strip().upper()
            if not answer:
                collector.add(f"{path}:{row_number}: answer is empty")
            elif answer not in present_options:
                collector.add(
                    f"{path}:{row_number}: answer '{answer}' is not one of present options {','.join(present_options)}")
    if split_name == "val" and row_count == 0:
        collector.add(f"{path}: validation split must contain at least one row")
    return row_count


def validate_mcq(dataset_dir: Path, subsets: Sequence[str], max_errors: int) -> Tuple[bool, List[str]]:
    collector = ValidationErrorCollector(max_errors)
    selected_subsets = list(subsets) or discover_mcq_subsets(dataset_dir)
    if not selected_subsets:
        collector.add(f"{dataset_dir}: no *_val.csv files found")
        return False, collector.errors
    summaries = []
    for subset in selected_subsets:
        val_path = dataset_dir / f"{subset}_val.csv"
        dev_path = dataset_dir / f"{subset}_dev.csv"
        val_rows = validate_mcq_file(val_path, subset, "val", collector)
        dev_rows = validate_mcq_file(dev_path, subset, "dev", collector) if dev_path.exists() else 0
        summaries.append(f"subset={subset} val_rows={val_rows} dev_rows={dev_rows}")
    if collector.ok:
        return True, summaries
    return False, collector.errors


def validate_qa_file(path: Path, subset: str, collector: ValidationErrorCollector) -> int:
    if not path.exists():
        collector.add(f"{path}: missing required JSONL file for subset '{subset}'")
        return 0
    row_count = 0
    with path.open("r", encoding="utf-8") as file_obj:
        for line_number, raw_line in enumerate(file_obj, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                collector.add(f"{path}:{line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                collector.add(f"{path}:{line_number}: expected JSON object")
                continue
            if not non_empty(record.get("query")):
                collector.add(f"{path}:{line_number}: query must be a non-empty string")
            if not non_empty(record.get("response")):
                collector.add(f"{path}:{line_number}: response must be a non-empty string")
    if row_count == 0:
        collector.add(f"{path}: JSONL file must contain at least one non-empty record")
    return row_count


def validate_qa(dataset_dir: Path, subsets: Sequence[str], max_errors: int) -> Tuple[bool, List[str]]:
    collector = ValidationErrorCollector(max_errors)
    selected_subsets = list(subsets) or discover_qa_subsets(dataset_dir)
    if not selected_subsets:
        collector.add(f"{dataset_dir}: no *.jsonl files found")
        return False, collector.errors
    summaries = []
    for subset in selected_subsets:
        row_count = validate_qa_file(dataset_dir / f"{subset}.jsonl", subset, collector)
        summaries.append(f"subset={subset} rows={row_count}")
    if collector.ok:
        return True, summaries
    return False, collector.errors


def print_lines(title: str, lines: Iterable[str]) -> None:
    print(title)
    for line in lines:
        print(f"- {line}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate custom datasets for ms-swift EvalScope evaluation.")
    parser.add_argument("format", choices=["mcq", "qa"], help="Dataset format: mcq for general_mcq, qa for general_qa.")
    parser.add_argument("dataset_dir", type=Path, help="Directory containing custom evaluation files.")
    parser.add_argument("--subset", action="append", default=[], help="Subset name to validate; repeat if needed.")
    parser.add_argument("--max-errors", type=int, default=20, help="Maximum detailed errors to print.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    dataset_dir = args.dataset_dir
    if not dataset_dir.exists():
        parser.error(f"dataset_dir does not exist: {dataset_dir}")
    if not dataset_dir.is_dir():
        parser.error(f"dataset_dir is not a directory: {dataset_dir}")
    if args.max_errors < 1:
        parser.error("--max-errors must be at least 1")

    if args.format == "mcq":
        ok, lines = validate_mcq(dataset_dir, args.subset, args.max_errors)
    else:
        ok, lines = validate_qa(dataset_dir, args.subset, args.max_errors)

    if ok:
        print_lines("OK: custom eval dataset shape is valid", lines)
        return 0
    print_lines("ERROR: custom eval dataset shape is invalid", lines)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
