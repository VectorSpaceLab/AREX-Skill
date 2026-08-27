#!/usr/bin/env python3
"""Validate a CSV-like dataframe before using it with NeuralProphet.

The checker is intentionally lightweight and does not import NeuralProphet. It
verifies columns, timestamp parsing, duplicate keys, numeric targets, and a
simple frequency diagnostic.

Examples:
    python validate_neuralprophet_dataframe.py history.csv
    python validate_neuralprophet_dataframe.py --input-file history.csv
    python validate_neuralprophet_dataframe.py --demo
    python validate_neuralprophet_dataframe.py future.csv --future
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate NeuralProphet dataframe columns and timestamps.")
    parser.add_argument("csv_path", nargs="?", type=Path, help="Optional positional CSV file containing NeuralProphet data.")
    parser.add_argument("--input-file", type=Path, help="CSV file containing NeuralProphet data; equivalent to the positional path.")
    parser.add_argument("--demo", action="store_true", help="Validate a generated in-memory demo dataframe.")
    parser.add_argument("--future", action="store_true", help="Allow missing y values for future prediction data.")
    parser.add_argument("--id-column", default="ID", help="Optional series ID column name; default: ID.")
    parser.add_argument("--max-frequency-ratio", type=float, default=0.9, help="Warn if the dominant timestamp delta ratio is below this value.")
    return parser


def load_df(args: argparse.Namespace) -> pd.DataFrame:
    if args.demo:
        return pd.DataFrame({"ds": pd.date_range("2022-01-01", periods=14, freq="D"), "y": range(14)})
    input_path = args.input_file or args.csv_path
    if input_path is None:
        raise ValueError("Provide a CSV path, --input-file, or --demo.")
    return pd.read_csv(input_path)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    df = load_df(args)
    errors: list[str] = []
    warnings: list[str] = []

    if "ds" not in df.columns:
        errors.append("missing required 'ds' timestamp column")
    if not args.future and "y" not in df.columns:
        errors.append("missing required 'y' target column for training/testing data")

    if "ds" in df.columns:
        parsed = pd.to_datetime(df["ds"], errors="coerce")
        bad = int(parsed.isna().sum())
        if bad:
            errors.append(f"{bad} rows have unparseable ds timestamps")
        key_cols = [args.id_column, "ds"] if args.id_column in df.columns else ["ds"]
        dupes = int(df.duplicated(key_cols).sum())
        if dupes:
            errors.append(f"{dupes} duplicate timestamp key rows for {key_cols}")
        ordered = parsed.dropna().sort_values()
        if len(ordered) < 3:
            warnings.append("fewer than 3 valid timestamps; pass explicit freq because cadence cannot be inferred reliably")
        else:
            deltas = ordered.diff().dropna()
            if not deltas.empty:
                ratio = float(deltas.value_counts(normalize=True).iloc[0])
                if ratio < args.max_frequency_ratio:
                    warnings.append(
                        f"dominant timestamp delta ratio {ratio:.2f} is below {args.max_frequency_ratio:.2f}; pass explicit freq to NeuralProphet"
                    )
    if "y" in df.columns:
        y = pd.to_numeric(df["y"], errors="coerce")
        bad_y = int(y.isna().sum())
        if bad_y and not args.future:
            errors.append(f"{bad_y} non-numeric or missing y values in training/testing data")
        elif bad_y:
            warnings.append(f"{bad_y} missing/non-numeric y values allowed because --future was set")

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print({"rows": len(df), "columns": list(df.columns), "status": "ok"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
