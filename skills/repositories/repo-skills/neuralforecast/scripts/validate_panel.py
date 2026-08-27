#!/usr/bin/env python3
"""Validate a NeuralForecast-style panel dataframe.

Purpose:
- Check the long-format `unique_id` / `ds` / `y` contract and the most common
  exogenous-column errors before a model fit.
- Stay deterministic, safe, and runnable from any working directory.

Prerequisites:
- pandas installed in the current environment.
- Optional Parquet support if `--format parquet` is used.

Example:
    python scripts/validate_panel.py --data-path sample.csv --format csv
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = ("unique_id", "ds", "y")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", required=True, help="Panel file path (.csv or .parquet).")
    parser.add_argument("--format", choices=["csv", "parquet"], default="csv", help="Input file format.")
    parser.add_argument("--static-path", help="Optional static dataframe path.")
    parser.add_argument("--id-col", default="unique_id", help="Series id column name.")
    parser.add_argument("--time-col", default="ds", help="Timestamp column name.")
    parser.add_argument("--target-col", default="y", help="Target column name.")
    parser.add_argument("--sample-weight-col", default="sample_weight", help="Optional sample-weight column name.")
    parser.add_argument("--available-mask-col", default="available_mask", help="Optional availability-mask column name.")
    parser.add_argument("--strict", action="store_true", help="Fail on unsorted or duplicated panel rows.")
    return parser


def load_frame(path: str, fmt: str, time_col: str) -> pd.DataFrame:
    if fmt == "csv":
        return pd.read_csv(path, parse_dates=[time_col])
    return pd.read_parquet(path)


def ensure_columns(df: pd.DataFrame, cols: Iterable[str], label: str) -> list[str]:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing required columns: {missing}")
    return list(cols)


def main() -> int:
    args = build_parser().parse_args()
    df = load_frame(args.data_path, args.format, args.time_col)
    ensure_columns(df, (args.id_col, args.time_col, args.target_col), "Panel data")

    errors: list[str] = []
    if df[[args.id_col, args.time_col]].isna().any().any():
        errors.append("panel has null ids or timestamps")
    if df[args.target_col].isna().any():
        errors.append("panel has null target values")
    if df.duplicated([args.id_col, args.time_col]).any():
        errors.append("panel has duplicated (id, time) rows")
    if args.strict:
        ordered = df.sort_values([args.id_col, args.time_col], kind="mergesort")
        if not ordered.index.equals(df.index):
            errors.append("panel rows are not sorted by id/time")

    if args.sample_weight_col in df.columns:
        weights = pd.to_numeric(df[args.sample_weight_col], errors="coerce")
        if weights.isna().any():
            errors.append("sample_weight contains non-numeric or null values")
        if (weights < 0).any():
            errors.append("sample_weight must be non-negative")

    if args.available_mask_col in df.columns:
        mask = set(pd.Series(df[args.available_mask_col]).dropna().unique().tolist())
        if not mask.issubset({0, 1, True, False}):
            errors.append(f"available_mask must be binary-like, got {sorted(mask)}")

    if args.static_path:
        static_df = load_frame(args.static_path, args.format, args.time_col)
        ensure_columns(static_df, (args.id_col,), "Static data")
        if static_df[args.id_col].isna().any():
            errors.append("static data has null ids")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("panel validation passed")
    print(f"rows={len(df)} series={df[args.id_col].nunique()} columns={list(df.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
