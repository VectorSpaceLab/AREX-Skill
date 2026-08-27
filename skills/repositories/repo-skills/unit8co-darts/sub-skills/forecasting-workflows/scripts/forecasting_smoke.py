#!/usr/bin/env python3
"""Tiny Darts core forecasting smoke on generated monthly data."""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.metrics import mae, rmse
from darts.models import ExponentialSmoothing, NaiveSeasonal


def run() -> dict:
    dates = pd.date_range("2020-01-01", periods=48, freq="MS")
    values = 100.0 + np.arange(48) * 0.5 + 10.0 * np.sin(np.arange(48) * 2 * np.pi / 12)
    series = TimeSeries.from_times_and_values(dates, values, columns=["sales"])
    horizon = 12
    train, val = series[:-horizon], series[-horizon:]

    baseline = NaiveSeasonal(K=12)
    baseline.fit(train)
    baseline_forecast = baseline.predict(horizon)
    assert len(baseline_forecast) == horizon

    model = ExponentialSmoothing()
    model.fit(train)
    forecast = model.predict(horizon, num_samples=20)
    assert len(forecast) == horizon
    assert forecast.n_components == 1

    point = forecast.quantile(0.5) if forecast.is_stochastic else forecast
    baseline_mae = float(mae(val, baseline_forecast))
    model_rmse = float(rmse(val, point))
    assert np.isfinite(baseline_mae)
    assert np.isfinite(model_rmse)

    return {
        "status": "ok",
        "horizon": horizon,
        "baseline_length": len(baseline_forecast),
        "forecast_length": len(forecast),
        "forecast_samples": forecast.n_samples,
        "baseline_mae": baseline_mae,
        "model_rmse": model_rmse,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true", help="print compact JSON")
    args = parser.parse_args()
    result = run()
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))


if __name__ == "__main__":
    main()
