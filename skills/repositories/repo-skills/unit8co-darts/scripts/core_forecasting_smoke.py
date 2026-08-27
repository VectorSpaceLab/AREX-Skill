#!/usr/bin/env python3
"""Root-level Darts core forecasting smoke using generated data."""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.metrics import mae
from darts.models import ExponentialSmoothing, NaiveSeasonal


def run() -> dict:
    dates = pd.date_range("2021-01-01", periods=36, freq="MS")
    values = 50 + np.arange(36) + 5 * np.sin(np.arange(36) * 2 * np.pi / 12)
    series = TimeSeries.from_times_and_values(dates, values, columns=["value"])
    train, val = series[:-6], series[-6:]

    baseline = NaiveSeasonal(K=12)
    baseline.fit(train)
    base_forecast = baseline.predict(6)

    model = ExponentialSmoothing()
    model.fit(train)
    forecast = model.predict(6, num_samples=10)
    point = forecast.quantile(0.5) if forecast.is_stochastic else forecast

    score = float(mae(val, point))
    assert len(base_forecast) == 6
    assert len(forecast) == 6
    assert np.isfinite(score)
    return {
        "status": "ok",
        "horizon": 6,
        "forecast_samples": forecast.n_samples,
        "mae": score,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()
    result = run()
    print(json.dumps(result, indent=2 if args.json else None, sort_keys=True))


if __name__ == "__main__":
    main()
