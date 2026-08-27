#!/usr/bin/env python3
"""Run a bounded Lazy Predict time-series forecasting smoke test.

Examples:
    python scripts/smoke_forecasting.py --predictions --exogenous
    python scripts/smoke_forecasting.py --forecasters Naive,Ridge_TS --horizon 12

The script uses synthetic data and CPU-safe default forecasters. It does not
require the Lazy Predict source repository, network access, or optional model
weights.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from lazypredict.TimeSeriesForecasting import LazyForecaster


def parse_forecasters(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded LazyForecaster smoke test.")
    parser.add_argument("--horizon", type=int, default=12, help="Forecast horizon / y_test length.")
    parser.add_argument("--forecasters", default="Naive,Ridge_TS", help="Comma-separated forecaster names.")
    parser.add_argument("--exogenous", action="store_true", help="Include aligned exogenous features.")
    parser.add_argument("--predictions", action="store_true", help="Require non-empty predictions DataFrame.")
    parser.add_argument("--n-lags", type=int, default=5, help="Lag features for ML forecasters.")
    args = parser.parse_args(argv)

    if args.horizon < 2:
        parser.error("--horizon must be at least 2")
    if args.n_lags < 1:
        parser.error("--n-lags must be positive")

    n_train = max(60, args.n_lags + 30)
    t = np.arange(n_train + args.horizon, dtype=float)
    rng = np.random.default_rng(42)
    y = 10.0 + 0.08 * t + 2.0 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 0.25, len(t))
    y_train, y_test = y[:n_train], y[n_train:]

    X_train = X_test = None
    if args.exogenous:
        X = np.column_stack([np.sin(t / 3.0), np.cos(t / 5.0)])
        X_train, X_test = X[:n_train], X[n_train:]

    fcst = LazyForecaster(
        verbose=0,
        ignore_warnings=True,
        predictions=args.predictions,
        forecasters=parse_forecasters(args.forecasters),
        n_lags=args.n_lags,
        max_models=len(parse_forecasters(args.forecasters)),
    )
    scores, predictions = fcst.fit(y_train, y_test, X_train, X_test)

    assert not scores.empty, "forecast scores are empty"
    for column in ["MAE", "RMSE", "Time Taken"]:
        assert column in scores.columns, f"missing forecast score column {column}"
    if args.predictions:
        assert not predictions.empty, "predictions=True should return forecasts"
        assert predictions.shape[0] == len(y_test), "prediction horizon mismatch"

    print(json.dumps({
        "ok": True,
        "forecasters": list(map(str, scores.index)),
        "score_shape": list(scores.shape),
        "prediction_shape": list(predictions.shape),
        "exogenous": bool(args.exogenous),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke failure path
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise
