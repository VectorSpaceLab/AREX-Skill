#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from maestro.trainer.common.datasets.jsonl import JSONLDataset

REQUIRED_KEYS = ("image", "prefix", "suffix")
DEFAULT_SPLITS = ("train", "valid", "test")


def validate_split(split_root: Path, annotations_name: str) -> tuple[int, list[str]]:
    issues: list[str] = []
    valid_entries = 0

    if not split_root.is_dir():
        issues.append(f"{split_root.name}: missing split directory")
        return valid_entries, issues

    annotations_path = split_root / annotations_name
    if not annotations_path.is_file():
        issues.append(f"{split_root.name}: missing annotation file '{annotations_name}'")
        return valid_entries, issues

    try:
        with annotations_path.open(encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, 1):
                text = raw_line.strip()
                if not text:
                    issues.append(f"{split_root.name}:{line_no}: empty line")
                    continue

                try:
                    record = json.loads(text)
                except json.JSONDecodeError as exc:
                    issues.append(f"{split_root.name}:{line_no}: invalid JSON ({exc})")
                    continue

                if not isinstance(record, dict):
                    issues.append(f"{split_root.name}:{line_no}: JSON value must be an object")
                    continue

                missing = [key for key in REQUIRED_KEYS if key not in record]
                if missing:
                    issues.append(f"{split_root.name}:{line_no}: missing key(s) {', '.join(missing)}")
                    continue

                invalid_type = False
                for key in REQUIRED_KEYS:
                    value = record[key]
                    if not isinstance(value, str) or not value.strip():
                        issues.append(f"{split_root.name}:{line_no}: key '{key}' must be a non-empty string")
                        invalid_type = True
                        break
                if invalid_type:
                    continue

                image_path = split_root / record["image"]
                if not image_path.is_file():
                    issues.append(
                        f"{split_root.name}:{line_no}: image file not found '{image_path.name}' in split directory"
                    )
                    continue

                valid_entries += 1
    except OSError as exc:
        issues.append(f"{split_root.name}: could not read '{annotations_path.name}': {exc}")
        return 0, issues

    if valid_entries == 0:
        issues.append(f"{split_root.name}: no valid entries")

    return valid_entries, issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Maestro JSONL dataset split layout and report missing records, keys, or images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "dataset_root",
        type=Path,
        help="Dataset root containing train, valid, and test split directories.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=list(DEFAULT_SPLITS),
        help="Split directory names to validate.",
    )
    parser.add_argument(
        "--annotations-name",
        default=JSONLDataset.ROBOFLOW_JSONL_FILENAME,
        help="Annotation file name inside each split directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.dataset_root.is_dir():
        print(f"Dataset root not found: {args.dataset_root}", file=sys.stderr)
        return 1

    total_valid = 0
    all_issues: list[str] = []

    for split_name in args.splits:
        valid_entries, issues = validate_split(args.dataset_root / split_name, args.annotations_name)
        total_valid += valid_entries
        all_issues.extend(issues)
        print(f"{split_name}: {valid_entries} valid entries")

    if all_issues:
        print("\nProblems detected:", file=sys.stderr)
        for issue in all_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print(f"Validated {len(args.splits)} split(s) with {total_valid} valid entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
