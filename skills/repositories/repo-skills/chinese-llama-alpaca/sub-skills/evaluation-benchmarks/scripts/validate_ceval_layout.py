#!/usr/bin/env python3
"""Validate the C-Eval directory layout expected by the bundled evaluator.

This helper performs only filesystem and CSV-header checks. It does not load a
model, run generation, download C-Eval, or allocate GPUs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable

BASE_COLUMNS = {"question", "A", "B", "C", "D"}
ANSWER_COLUMNS = BASE_COLUMNS | {"answer"}


class LayoutError(Exception):
    pass


def _read_header(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            return set(next(reader))
        except StopIteration as exc:
            raise LayoutError(f"{path}: empty CSV") from exc


def validate(data_dir: Path, subject_mapping: Path | None = None, max_subjects: int | None = None) -> int:
    errors: list[str] = []
    for split in ("dev", "val", "test"):
        d = data_dir / split
        if not d.is_dir():
            errors.append(f"missing directory: {d}")
    if errors:
        raise LayoutError("\n".join(errors))

    val_files = sorted((data_dir / "val").glob("*_val.csv"))
    if not val_files:
        raise LayoutError(f"{data_dir / 'val'}: no *_val.csv files found")
    if max_subjects is not None:
        val_files = val_files[:max_subjects]

    mapping_subjects: set[str] | None = None
    if subject_mapping:
        with subject_mapping.open("r", encoding="utf-8") as f:
            mapping = json.load(f)
        mapping_subjects = set(mapping)

    checked = 0
    for val_file in val_files:
        subject = val_file.name.removesuffix("_val.csv")
        if mapping_subjects is not None and subject not in mapping_subjects:
            errors.append(f"{subject}: not present in subject_mapping.json")
        related = {
            "val": val_file,
            "dev": data_dir / "dev" / f"{subject}_dev.csv",
            "test": data_dir / "test" / f"{subject}_test.csv",
        }
        for split, path in related.items():
            if not path.is_file():
                errors.append(f"{subject}: missing {split} file {path}")
                continue
            try:
                header = _read_header(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path}: {type(exc).__name__}: {exc}")
                continue
            required = BASE_COLUMNS if split == "test" else ANSWER_COLUMNS
            missing = sorted(required - header)
            if missing:
                errors.append(f"{path}: missing columns {missing}")
        checked += 1
    if errors:
        preview = "\n".join(f"  - {e}" for e in errors[:30])
        extra = "" if len(errors) <= 30 else f"\n  ... {len(errors) - 30} more error(s)"
        raise LayoutError(f"C-Eval layout validation failed:\n{preview}{extra}")
    print(f"OK: checked {checked} C-Eval subject(s) under {data_dir}")
    return 0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate C-Eval dev/val/test CSV layout.")
    parser.add_argument("--data-dir", required=True, type=Path, help="C-Eval root containing dev/, val/, and test/.")
    parser.add_argument("--subject-mapping", type=Path, default=None, help="Optional subject_mapping.json to cross-check subjects.")
    parser.add_argument("--max-subjects", type=int, default=None, help="Validate only first N val subjects for a quick check.")
    args = parser.parse_args(argv)
    if args.max_subjects is not None and args.max_subjects < 1:
        parser.error("--max-subjects must be >= 1")
    return args


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return validate(args.data_dir, args.subject_mapping, args.max_subjects)
    except LayoutError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
