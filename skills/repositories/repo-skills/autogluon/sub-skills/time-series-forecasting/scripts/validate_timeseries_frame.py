#!/usr/bin/env python3
"""Validate small AutoGluon TimeSeriesDataFrame inputs without training models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


def _load_pandas():
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError("Could not import pandas. Install pandas before validating time-series data.") from exc
    return pd


def _read_table(path: str | Path):
    pd = _load_pandas()
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file extension {suffix!r}; use CSV or Parquet")


def _build_fixture():
    pd = _load_pandas()
    timestamps = pd.date_range("2024-01-01", periods=8, freq="D")
    return pd.DataFrame(
        {
            "item_id": ["A"] * len(timestamps) + ["B"] * len(timestamps),
            "timestamp": list(timestamps) * 2,
            "target": [10, 12, 13, 15, 16, 17, 18, 20, 4, 5, 7, 6, 8, 9, 10, 11],
            "promotion": [0, 0, 1, 0, 0, 1, 0, 0] * 2,
        }
    )


def _load_autogluon():
    try:
        from autogluon.timeseries import TimeSeriesDataFrame
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "Could not import autogluon.timeseries. Install AutoGluon TimeSeries before validating package behavior."
        ) from exc
    return TimeSeriesDataFrame


def _find_missing_columns(columns: Iterable[str], required: Iterable[str]) -> list[str]:
    available = set(columns)
    return [column for column in required if column not in available]


def _future_grid(ts_df, prediction_length: int):
    pd = _load_pandas()
    freq = ts_df.freq
    if freq is None:
        raise ValueError("Cannot build a future horizon grid because the time series frequency is irregular or unknown")
    tuples = []
    offset = pd.tseries.frequencies.to_offset(freq)
    for item_id in ts_df.item_ids:
        item_frame = ts_df.loc[item_id]
        last_timestamp = item_frame.index.max()
        future_index = pd.date_range(last_timestamp + offset, periods=prediction_length, freq=offset)
        tuples.extend((item_id, timestamp) for timestamp in future_index)
    return pd.MultiIndex.from_tuples(tuples, names=["item_id", "timestamp"])


def validate(args: argparse.Namespace) -> dict:
    pd = _load_pandas()
    TimeSeriesDataFrame = _load_autogluon()

    raw = _read_table(args.input) if args.input else _build_fixture()
    static_features = _read_table(args.static_features) if args.static_features else None

    required_columns = [args.id_column or "item_id", args.timestamp_column or "timestamp", args.target]
    missing_columns = _find_missing_columns(raw.columns, required_columns)
    if missing_columns:
        raise ValueError(f"Input data is missing required columns: {missing_columns}")

    if args.target not in raw.columns:
        raise ValueError(f"Target column {args.target!r} is missing")
    if not pd.api.types.is_numeric_dtype(raw[args.target]):
        raise ValueError(f"Target column {args.target!r} must be numeric, found dtype {raw[args.target].dtype}")

    known_missing = _find_missing_columns(raw.columns, args.known_covariates)
    if known_missing:
        raise ValueError(f"Known covariate columns are missing from training data: {known_missing}")

    ts_df = TimeSeriesDataFrame(
        raw,
        static_features=static_features,
        id_column=args.id_column,
        timestamp_column=args.timestamp_column,
    ).sort_index()

    report = {
        "ok": True,
        "num_items": int(ts_df.num_items),
        "num_rows": int(len(ts_df)),
        "item_ids_preview": [str(item_id) for item_id in list(ts_df.item_ids[:5])],
        "freq": ts_df.freq,
        "target": args.target,
        "known_covariates": list(args.known_covariates),
        "static_features_columns": list(ts_df.static_features.columns) if ts_df.static_features is not None else [],
        "min_timesteps_per_item": int(ts_df.num_timesteps_per_item().min()),
        "max_timesteps_per_item": int(ts_df.num_timesteps_per_item().max()),
    }

    try:
        report["strict_inferred_freq"] = ts_df.infer_frequency(raise_if_irregular=True)
    except Exception as exc:
        report["strict_inferred_freq_error"] = str(exc)
        if args.require_regular:
            raise

    if args.prediction_length is not None:
        prediction_length = int(args.prediction_length)
        if prediction_length < 1:
            raise ValueError("--prediction-length must be >= 1")
        counts = ts_df.num_timesteps_per_item()
        default_fit_threshold = (1 + 1) * prediction_length
        too_short = counts[counts <= default_fit_threshold]
        report["prediction_length"] = prediction_length
        report["items_too_short_for_default_validation"] = {str(k): int(v) for k, v in too_short.items()}
        if args.fail_on_short_series and not too_short.empty:
            raise ValueError(
                "Some items are too short for default validation with this prediction_length: "
                f"{report['items_too_short_for_default_validation']}"
            )

        if args.future_covariates:
            future_raw = _read_table(args.future_covariates)
            future_ts = TimeSeriesDataFrame(
                future_raw,
                id_column=args.id_column,
                timestamp_column=args.timestamp_column,
            ).sort_index()
            missing_future_columns = _find_missing_columns(future_ts.columns, args.known_covariates)
            if missing_future_columns:
                raise ValueError(f"Future covariates are missing columns: {missing_future_columns}")
            required_index = _future_grid(ts_df, prediction_length)
            missing_index = required_index.difference(future_ts.index)
            report["future_covariate_missing_rows"] = len(missing_index)
            if len(missing_index) > 0:
                preview = [(str(item_id), str(timestamp)) for item_id, timestamp in list(missing_index[:5])]
                report["future_covariate_missing_preview"] = preview
                raise ValueError(f"Future covariates are missing {len(missing_index)} required horizon rows")

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an AutoGluon TimeSeriesDataFrame schema, frequency, static features, and forecast horizon.",
    )
    parser.add_argument("--input", help="CSV or Parquet file with time-series rows. Omit to use a tiny built-in fixture.")
    parser.add_argument("--static-features", help="Optional CSV or Parquet file with static item features.")
    parser.add_argument("--future-covariates", help="Optional CSV or Parquet file with future known covariate rows.")
    parser.add_argument("--id-column", help="Column to use as item_id when input does not use the default name.")
    parser.add_argument("--timestamp-column", help="Column to use as timestamp when input does not use the default name.")
    parser.add_argument("--target", default="target", help="Target column name. Default: target.")
    parser.add_argument("--known-covariates", nargs="*", default=[], help="Known future covariate column names.")
    parser.add_argument("--prediction-length", type=int, help="Forecast horizon used for length and future-covariate checks.")
    parser.add_argument("--require-regular", action="store_true", help="Fail if a single regular frequency cannot be inferred.")
    parser.add_argument(
        "--fail-on-short-series",
        action="store_true",
        help="Fail if items are too short for default num_val_windows=1 validation.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = validate(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
