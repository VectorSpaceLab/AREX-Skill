#!/usr/bin/env python3
"""Create a deterministic tiny custom CSV for Informer2020 smoke workflows.

The generated file follows the custom-data loader assumptions used by
Informer2020: a parseable `date` column, numeric covariates, and a target column.

Example:
  python make_tiny_forecast_csv.py --output /tmp/tiny_informer.csv --rows 160 --freq h
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a tiny Informer2020 custom forecasting CSV")
    parser.add_argument("--output", type=Path, default=Path("tiny_informer_custom.csv"), help="CSV path to write")
    parser.add_argument("--rows", type=int, default=160, help="Number of timestamp rows to generate")
    parser.add_argument("--freq", default="h", help="Pandas-compatible frequency, e.g. h, 15min, d")
    parser.add_argument("--start", default="2021-01-01", help="Start timestamp accepted by pandas.date_range")
    parser.add_argument("--covariates", type=int, default=2, help="Number of non-target feature columns")
    parser.add_argument("--target", default="target", help="Name of the target column")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.rows <= 0:
        raise SystemExit("--rows must be positive")
    if args.covariates < 0:
        raise SystemExit("--covariates must be non-negative")

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - defensive user-facing guard
        raise SystemExit("pandas is required to generate timestamp ranges for this helper") from exc

    try:
        dates = pd.date_range(args.start, periods=args.rows, freq=args.freq)
    except Exception as exc:
        raise SystemExit(f"Could not generate dates for freq={args.freq!r}: {exc}") from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date"] + [f"feat_{idx}" for idx in range(args.covariates)] + [args.target]

    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        denom = max(args.rows - 1, 1)
        for i, timestamp in enumerate(dates):
            trend = i / denom
            row = {"date": timestamp.isoformat()}
            cov_values = []
            for idx in range(args.covariates):
                value = math.sin(i / (5.0 + idx)) + math.cos(i / (9.0 + idx)) + (idx + 1) * 0.05 * trend
                cov_values.append(value)
                row[f"feat_{idx}"] = f"{value:.6f}"
            if cov_values:
                target_value = 0.6 * cov_values[0] + 0.2 * cov_values[-1] + 0.1 * math.sin(i / 11.0) + 0.2 * trend
            else:
                target_value = math.sin(i / 7.0) + 0.2 * trend
            row[args.target] = f"{target_value:.6f}"
            writer.writerow(row)

    channels = args.covariates + 1
    print(f"Wrote {args.rows} rows to {args.output}")
    print(f"Target: {args.target}; total channels after date: {channels}")
    print("Suggested dimensions:")
    print(f"  features=M  -> enc_in={channels} dec_in={channels} c_out={channels}")
    print("  features=MS -> enc_in={0} dec_in={0} c_out=1".format(channels))
    print("  features=S  -> enc_in=1 dec_in=1 c_out=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
