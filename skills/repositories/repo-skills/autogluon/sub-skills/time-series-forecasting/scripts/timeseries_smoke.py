#!/usr/bin/env python3
"""Tiny AutoGluon time-series smoke check with optional lightweight local-model fit."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def _load_pandas():
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError("Could not import pandas. Install pandas before running this smoke check.") from exc
    return pd


def _load_autogluon():
    try:
        from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "Could not import autogluon.timeseries. Install AutoGluon TimeSeries before running this smoke check."
        ) from exc
    return TimeSeriesDataFrame, TimeSeriesPredictor


def build_tiny_frame(periods: int = 10):
    pd = _load_pandas()
    timestamps = pd.date_range("2024-01-01", periods=periods, freq="D")
    first = [float(value) for value in range(1, periods + 1)]
    second = [float(value + (value % 3)) for value in range(2, periods + 2)]
    return pd.DataFrame(
        {
            "item_id": ["A"] * periods + ["B"] * periods,
            "timestamp": list(timestamps) * 2,
            "target": first + second,
            "promotion": [0, 1] * periods,
        }
    )


def run(args: argparse.Namespace) -> dict:
    pd = _load_pandas()
    TimeSeriesDataFrame, TimeSeriesPredictor = _load_autogluon()
    raw = build_tiny_frame(periods=args.periods)
    static = pd.DataFrame(
        {"item_id": ["A", "B"], "segment": pd.Series(["core", "trial"], dtype="category"), "scale": [1.0, 0.5]}
    )
    data = TimeSeriesDataFrame(raw, static_features=static).sort_index()
    train_data, test_data = data.train_test_split(args.prediction_length)

    report = {
        "ok": True,
        "fit_ran": False,
        "num_items": int(data.num_items),
        "freq": data.freq,
        "train_rows": int(len(train_data)),
        "test_rows": int(len(test_data)),
        "static_features_columns": list(data.static_features.columns),
    }

    if args.fit:
        with tempfile.TemporaryDirectory(prefix="ag-timeseries-smoke-") as parent_dir:
            model_dir = Path(parent_dir) / "predictor"
            predictor = TimeSeriesPredictor(
                prediction_length=args.prediction_length,
                target="target",
                path=model_dir,
                eval_metric="WQL",
                verbosity=0,
                log_to_file=False,
                quantile_levels=[0.1, 0.5, 0.9],
            )
            predictor.fit(
                train_data,
                hyperparameters={"Naive": {}, "SeasonalNaive": {}},
                time_limit=args.time_limit,
                enable_ensemble=False,
                verbosity=0,
            )
            predictions = predictor.predict(train_data)
            scores = predictor.evaluate(test_data)
            report.update(
                {
                    "fit_ran": True,
                    "prediction_rows": int(len(predictions)),
                    "prediction_columns": [str(column) for column in predictions.columns],
                    "score_keys": sorted(scores.keys()),
                }
            )

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny AutoGluon time-series construction smoke check; fit only when --fit is passed.",
    )
    parser.add_argument("--fit", action="store_true", help="Run a tiny local-model predictor fit in a temporary directory.")
    parser.add_argument("--prediction-length", type=int, default=2, help="Forecast horizon for split and optional fit.")
    parser.add_argument("--periods", type=int, default=10, help="Rows per item in the built-in fixture.")
    parser.add_argument("--time-limit", type=int, default=30, help="Optional fit time limit in seconds.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.prediction_length < 1:
        print("ERROR: --prediction-length must be >= 1", file=sys.stderr)
        return 1
    if args.periods <= 2 * args.prediction_length:
        print("ERROR: --periods should be greater than 2 * --prediction-length for the tiny fit split", file=sys.stderr)
        return 1
    try:
        report = run(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
