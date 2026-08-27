#!/usr/bin/env python3
"""Validate a CLAM dataset CSV and render a split-generation command.

This helper is intentionally safe: it does not import CLAM, create split files,
or train models. It checks the metadata shape that CLAM's split script expects
and prints the command a user can run from a CLAM working copy after adding any
custom task branch required by their dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
import sys
from collections import Counter, defaultdict
from pathlib import Path


def parse_label_dict(raw: str) -> dict[str, int]:
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"label dict must be JSON: {exc}") from exc
    if not isinstance(loaded, dict) or not loaded:
        raise argparse.ArgumentTypeError("label dict must be a non-empty JSON object")
    result: dict[str, int] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise argparse.ArgumentTypeError("label dict keys must be strings")
        if not isinstance(value, int) or value < 0:
            raise argparse.ArgumentTypeError("label dict values must be non-negative integers")
        result[key] = value
    values = sorted(result.values())
    expected = list(range(len(set(values))))
    if sorted(set(values)) != expected:
        raise argparse.ArgumentTypeError(
            f"label dict values should be contiguous class ids {expected}; got {sorted(set(values))}"
        )
    return result


def positive_fraction(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("fraction must be between 0 and 1")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def load_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row")
        rows = list(reader)
    return list(reader.fieldnames), rows


def validate_rows(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    label_col: str,
    label_dict: dict[str, int],
    ignore_labels: set[str],
) -> tuple[Counter[str], dict[str, set[str]], list[str]]:
    required = {"case_id", "slide_id", label_col}
    missing = sorted(required.difference(fieldnames))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    if not rows:
        raise ValueError("CSV has no data rows")

    label_counts: Counter[str] = Counter()
    slide_to_cases: dict[str, set[str]] = defaultdict(set)
    blank_errors: list[str] = []
    unknown_labels: set[str] = set()

    for row_index, row in enumerate(rows, start=2):
        case_id = (row.get("case_id") or "").strip()
        slide_id = (row.get("slide_id") or "").strip()
        label = (row.get(label_col) or "").strip()
        if not case_id:
            blank_errors.append(f"row {row_index}: blank case_id")
        if not slide_id:
            blank_errors.append(f"row {row_index}: blank slide_id")
        if not label:
            blank_errors.append(f"row {row_index}: blank {label_col}")
        if label and label not in ignore_labels:
            if label not in label_dict:
                unknown_labels.add(label)
            else:
                label_counts[label] += 1
        if slide_id and case_id:
            slide_to_cases[slide_id].add(case_id)

    if blank_errors:
        preview = "; ".join(blank_errors[:8])
        more = "" if len(blank_errors) <= 8 else f"; plus {len(blank_errors) - 8} more"
        raise ValueError(preview + more)
    if unknown_labels:
        raise ValueError(
            "labels missing from label_dict: " + ", ".join(sorted(unknown_labels))
        )
    if not label_counts:
        raise ValueError("no rows remain after applying ignored labels")

    duplicate_slide_cases = {
        slide_id: cases for slide_id, cases in slide_to_cases.items() if len(cases) > 1
    }
    warnings: list[str] = []
    if duplicate_slide_cases:
        examples = ", ".join(sorted(duplicate_slide_cases)[:5])
        warnings.append(
            "some slide_id values map to multiple case_id values; confirm this is intentional: " + examples
        )

    return label_counts, slide_to_cases, warnings


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a CLAM dataset CSV and render a create_splits_seq.py command."
    )
    parser.add_argument("--csv", required=True, type=Path, help="dataset CSV to inspect")
    parser.add_argument("--task", required=True, help="CLAM task name to use in create_splits_seq.py")
    parser.add_argument(
        "--label-dict",
        required=True,
        type=parse_label_dict,
        help='JSON label mapping, e.g. \'{"normal": 0, "tumor": 1}\'',
    )
    parser.add_argument("--label-col", default="label", help="label column name (default: label)")
    parser.add_argument(
        "--ignore-label",
        action="append",
        default=[],
        help="label value to ignore; repeat for multiple labels",
    )
    parser.add_argument("--seed", type=int, default=1, help="split seed for create_splits_seq.py")
    parser.add_argument("--k", type=positive_int, default=10, help="number of folds")
    parser.add_argument("--label-frac", type=positive_fraction, default=1.0)
    parser.add_argument("--val-frac", type=positive_fraction, default=0.1)
    parser.add_argument("--test-frac", type=positive_fraction, default=0.1)
    parser.add_argument(
        "--patient-voting",
        choices=("max", "maj"),
        default="max",
        help="patient label aggregation to mirror in custom split branches",
    )
    parser.add_argument(
        "--output-mode",
        choices=("command", "json"),
        default="command",
        help="print shell command or JSON summary",
    )
    args = parser.parse_args(argv)

    try:
        fieldnames, rows = load_rows(args.csv)
        label_counts, slide_to_cases, warnings = validate_rows(
            fieldnames,
            rows,
            args.label_col,
            args.label_dict,
            set(args.ignore_label),
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    class_count = len(set(args.label_dict.values()))
    usable_rows = sum(label_counts.values())
    patient_count = len({case for cases in slide_to_cases.values() for case in cases})
    min_class_count = min(label_counts.values())
    estimated_val_min = math.floor(min_class_count * args.val_frac)
    estimated_test_min = math.floor(min_class_count * args.test_frac)
    if estimated_val_min < 1 or estimated_test_min < 1:
        warnings.append(
            "small class counts may round validation/test counts to zero in create_splits_seq.py"
        )

    command = [
        "python",
        "create_splits_seq.py",
        "--task",
        args.task,
        "--seed",
        str(args.seed),
        "--k",
        str(args.k),
        "--label_frac",
        str(args.label_frac),
        "--val_frac",
        str(args.val_frac),
        "--test_frac",
        str(args.test_frac),
    ]

    split_dir = f"splits/{args.task}_{int(args.label_frac * 100)}"
    summary = {
        "csv": str(args.csv),
        "task": args.task,
        "rows": len(rows),
        "usable_rows": usable_rows,
        "patients": patient_count,
        "classes": class_count,
        "label_counts": dict(label_counts),
        "label_col": args.label_col,
        "patient_voting": args.patient_voting,
        "expected_split_dir": split_dir,
        "command": command,
        "warnings": warnings,
        "note": "For custom tasks, add matching task branches to create_splits_seq.py, main.py, and eval.py before running.",
    }

    if args.output_mode == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Dataset CSV looks usable for CLAM split planning.")
        print(f"Rows: {len(rows)} total, {usable_rows} usable after ignores")
        print(f"Patients: {patient_count}")
        print("Label counts: " + ", ".join(f"{k}={v}" for k, v in sorted(label_counts.items())))
        print(f"Expected split directory: {split_dir}")
        print("Command to run after task branches are in place:")
        print(quote_command(command))
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        print("Reminder: this helper does not create splits or modify CLAM scripts.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
