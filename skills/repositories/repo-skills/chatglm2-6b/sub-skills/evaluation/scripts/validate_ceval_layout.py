#!/usr/bin/env python3
"""Validate a C-Eval-style JSONL tree without loading model weights."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

LABELS = {"A": 0, "B": 1, "C": 2, "D": 3}


def find_files(root: Path, split: str) -> list[Path]:
    base = root / split if (root / split).is_dir() else root
    return sorted(base.rglob("*.jsonl"))


def validate_file(path: Path, strict_label_type: bool, max_records: int | None) -> tuple[int, list[str], dict[str, int]]:
    errors: list[str] = []
    labels: dict[str, int] = {"integer": 0, "letter": 0}
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if max_records is not None and count >= max_records:
                break
            if not line.strip():
                continue
            count += 1
            try:
                record: Any = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no}: invalid JSON ({exc.msg})")
                continue
            if not isinstance(record, dict):
                errors.append(f"{path}:{line_no}: record is not an object")
                continue
            if not isinstance(record.get("inputs_pretokenized"), str) or not record["inputs_pretokenized"].strip():
                errors.append(f"{path}:{line_no}: missing non-empty inputs_pretokenized")
            label = record.get("label")
            if isinstance(label, bool):
                errors.append(f"{path}:{line_no}: label must not be boolean")
            elif isinstance(label, int):
                if label not in range(4):
                    errors.append(f"{path}:{line_no}: integer label must be 0, 1, 2, or 3")
                else:
                    labels["integer"] += 1
            elif isinstance(label, str) and label.upper() in LABELS and not strict_label_type:
                labels["letter"] += 1
            else:
                expected = "integer 0-3" if strict_label_type else "integer 0-3 or letter A-D"
                errors.append(f"{path}:{line_no}: label must be {expected}")
    return count, errors, labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="CEval root or a directory containing JSONL files")
    parser.add_argument("--split", choices=("val", "test", "all"), default="all")
    parser.add_argument("--max-records", type=int, default=None, help="Limit records inspected per file")
    parser.add_argument("--strict-label-type", action="store_true", help="Require integer labels exactly as the source comparison expects")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"missing root directory: {args.root}", file=sys.stderr)
        return 2
    splits = ("val", "test") if args.split == "all" else (args.split,)
    files: list[Path] = []
    for split in splits:
        files.extend(find_files(args.root, split))
    files = sorted(set(files))
    if not files:
        print(f"no .jsonl files found under {args.root} for split={args.split}", file=sys.stderr)
        return 2
    total = 0
    all_errors: list[str] = []
    totals = {"integer": 0, "letter": 0}
    for path in files:
        count, errors, labels = validate_file(path, args.strict_label_type, args.max_records)
        total += count
        all_errors.extend(errors)
        for key, value in labels.items():
            totals[key] += value
        print(f"{path}: records={count} errors={len(errors)}")
    print(json.dumps({"files": len(files), "records": total, "labels": totals, "errors": len(all_errors)}, indent=2))
    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
