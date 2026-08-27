#!/usr/bin/env python3
"""Validate local file layout for common TSLib run.py commands.

This script does not import TSLib, train models, or download data. It catches
missing local files that would otherwise trigger Hugging Face fallback behavior.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ANOMALY_FILES = {
    "PSM": ["train.csv", "test.csv", "test_label.csv"],
    "MSL": ["MSL_train.npy", "MSL_test.npy", "MSL_test_label.npy"],
    "SMAP": ["SMAP_train.npy", "SMAP_test.npy", "SMAP_test_label.npy"],
    "SMD": ["SMD_train.npy", "SMD_test.npy", "SMD_test_label.npy"],
    "SWAT": ["swat_train2.csv", "swat2.csv"],
}
M4_FILES = ["M4-info.csv", "training.npz", "test.npz"]


def check_csv(path: Path, target: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing CSV: {path}"]
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [f"empty CSV: {path}"]
    if "date" not in header:
        errors.append("CSV must contain a 'date' column")
    if target not in header:
        errors.append(f"target column {target!r} not found")
    non_date = [c for c in header if c != "date"]
    if not non_date:
        errors.append("CSV needs at least one numeric non-date column")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local files for a TSLib task without downloading data.")
    parser.add_argument("--task", required=True, choices=["long_term_forecast", "short_term_forecast", "zero_shot_forecast", "imputation", "anomaly_detection", "classification"])
    parser.add_argument("--data", required=True, help="TSLib --data value, e.g. custom, ETTh1, m4, PSM, UEA")
    parser.add_argument("--root-path", required=True, help="TSLib --root_path directory")
    parser.add_argument("--data-path", default="", help="TSLib --data_path CSV filename where applicable")
    parser.add_argument("--target", default="OT", help="Target column for CSV tasks")
    parser.add_argument("--model-id", default="", help="TSLib --model_id, needed for UEA classification")
    args = parser.parse_args()

    root = Path(args.root_path)
    errors: list[str] = []

    if args.task in {"long_term_forecast", "zero_shot_forecast", "imputation"} and args.data != "m4":
        if not args.data_path:
            errors.append("--data-path is required for CSV loaders")
        else:
            errors.extend(check_csv(root / args.data_path, args.target))

    if args.task == "short_term_forecast" or args.data == "m4":
        for name in M4_FILES:
            if not (root / name).exists():
                errors.append(f"missing M4 file: {root / name}")

    if args.task == "anomaly_detection":
        for name in ANOMALY_FILES.get(args.data, []):
            if not (root / name).exists():
                errors.append(f"missing anomaly file: {root / name}")
        if args.data not in ANOMALY_FILES:
            errors.append(f"unknown anomaly --data value {args.data!r}; expected one of {sorted(ANOMALY_FILES)}")

    if args.task == "classification" or args.data == "UEA":
        if not args.model_id:
            errors.append("--model-id is required for UEA classification file checks")
        else:
            for split in ["TRAIN", "TEST"]:
                path = root / f"{args.model_id}_{split}.ts"
                if not path.exists():
                    errors.append(f"missing UEA file: {path}")

    if errors:
        print("FAIL")
        for e in errors:
            print("-", e)
        return 1
    print("OK local files found for", args.task, args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
