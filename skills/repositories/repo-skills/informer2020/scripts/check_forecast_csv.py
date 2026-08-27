#!/usr/bin/env python3
"""Validate an Informer2020 custom forecasting CSV before a long run.

This helper mirrors the repository's custom-data loader assumptions without
launching training: `date` must parse as timestamps, the target must exist,
selected feature columns must be numeric, and the 70/10/20 custom split must be
large enough for the chosen windows.

Examples:
  python check_forecast_csv.py --csv /tmp/tiny.csv --target target --features M --seq-len 16 --pred-len 4
  python check_forecast_csv.py --csv real.csv --target OT --features MS --cols HUFL HULL MUFL MULL LUFL LULL OT
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check an Informer2020 custom forecasting CSV")
    parser.add_argument("--csv", required=True, type=Path, help="CSV file to validate")
    parser.add_argument("--target", default="target", help="Target column name")
    parser.add_argument("--features", choices=["S", "M", "MS"], default="M", help="Informer2020 feature mode")
    parser.add_argument("--cols", nargs="*", help="Optional column list as it would be passed to the source CLI")
    parser.add_argument("--seq-len", type=int, default=16, help="Encoder window length")
    parser.add_argument("--pred-len", type=int, default=4, help="Prediction horizon")
    parser.add_argument("--freq", help="Optional pandas frequency string to validate")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    return parser.parse_args()


def validate(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import pandas as pd
        from pandas.tseries.frequencies import to_offset
    except ImportError as exc:  # pragma: no cover - defensive user-facing guard
        return {"ok": False, "errors": [f"pandas is required for validation: {exc}"], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    if args.seq_len <= 0 or args.pred_len <= 0:
        errors.append("--seq-len and --pred-len must be positive")
    if not args.csv.exists():
        errors.append(f"CSV does not exist: {args.csv}")
        return {"ok": False, "errors": errors, "warnings": warnings, "details": details}

    try:
        df = pd.read_csv(args.csv)
    except Exception as exc:
        errors.append(f"Could not read CSV: {exc}")
        return {"ok": False, "errors": errors, "warnings": warnings, "details": details}

    details["row_count"] = int(len(df))
    details["columns"] = list(df.columns)

    if "date" not in df.columns:
        errors.append("CSV must contain a literal 'date' column")
        parsed_dates = None
    else:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")
        bad_dates = int(parsed_dates.isna().sum())
        if bad_dates:
            errors.append(f"date column has {bad_dates} unparsable value(s)")
        elif not parsed_dates.is_monotonic_increasing:
            warnings.append("date values are parseable but not monotonic increasing")
        elif parsed_dates.duplicated().any():
            warnings.append("date values contain duplicates")

    if args.target not in df.columns:
        errors.append(f"target column {args.target!r} is missing")
        selected_covariates: list[str] = []
    else:
        if args.cols is not None and len(args.cols) > 0:
            missing = [col for col in args.cols if col not in df.columns]
            if missing:
                errors.append(f"--cols contains missing column(s): {missing}")
            if args.cols.count(args.target) != 1:
                errors.append("--cols must include the target exactly once because the loader removes it before appending it")
            if len(set(args.cols)) != len(args.cols):
                errors.append("--cols contains duplicate names")
            selected_covariates = [col for col in args.cols if col != args.target]
        else:
            selected_covariates = [col for col in df.columns if col not in {"date", args.target}]

    selected_data_columns = ([args.target] if args.features == "S" else selected_covariates + [args.target])
    for col in selected_data_columns:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            bad_numeric = int(numeric.isna().sum())
            if bad_numeric:
                errors.append(f"selected column {col!r} has {bad_numeric} non-numeric or missing value(s)")

    channel_count = len(selected_covariates) + 1 if args.target in df.columns else None
    if channel_count is not None:
        if args.features == "S":
            dims = {"enc_in": 1, "dec_in": 1, "c_out": 1}
        elif args.features == "M":
            dims = {"enc_in": channel_count, "dec_in": channel_count, "c_out": channel_count}
        else:
            dims = {"enc_in": channel_count, "dec_in": channel_count, "c_out": 1}
        details["selected_covariates"] = selected_covariates
        details["channel_count_after_date"] = channel_count
        details["suggested_dimensions"] = dims

    n = len(df)
    train_rows = int(n * 0.7)
    test_rows = int(n * 0.2)
    val_rows = n - train_rows - test_rows
    train_windows = train_rows - args.seq_len - args.pred_len + 1
    val_windows = val_rows - args.pred_len + 1
    test_windows = test_rows - args.pred_len + 1
    prediction_history_ok = n >= args.seq_len
    details["custom_split"] = {
        "train_rows": train_rows,
        "val_rows": val_rows,
        "test_rows": test_rows,
        "train_windows": train_windows,
        "val_windows": val_windows,
        "test_windows": test_windows,
        "prediction_history_ok": prediction_history_ok,
    }
    if train_windows <= 0:
        errors.append("training split is too short for seq_len + pred_len")
    if val_windows <= 0:
        errors.append("validation split is too short for pred_len after the loader's seq_len overlap")
    if test_windows <= 0:
        errors.append("test split is too short for pred_len after the loader's seq_len overlap")
    if not prediction_history_ok:
        errors.append("prediction mode needs at least seq_len source rows")

    if args.freq:
        try:
            offset = to_offset(args.freq)
            details["freq_offset"] = str(offset)
        except Exception as exc:
            errors.append(f"frequency {args.freq!r} is not accepted by pandas: {exc}")
        if parsed_dates is not None and len(parsed_dates) >= 3 and parsed_dates.notna().all():
            inferred = pd.infer_freq(parsed_dates)
            details["inferred_frequency"] = inferred
            if inferred is None:
                warnings.append("could not infer a regular frequency from the date column")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "details": details}


def main() -> int:
    args = parse_args()
    report = validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "FAILED"
        print(f"Informer2020 CSV validation: {status}")
        for key, value in report["details"].items():
            print(f"- {key}: {value}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
