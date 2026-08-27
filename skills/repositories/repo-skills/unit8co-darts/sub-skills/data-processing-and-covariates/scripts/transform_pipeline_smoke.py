#!/usr/bin/env python3
"""Tiny Darts preprocessing and covariate-span smoke."""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.dataprocessing import Pipeline
from darts.dataprocessing.transformers import MissingValuesFiller, Scaler
from darts.utils.timeseries_generation import datetime_attribute_timeseries


def _future_offset(freq, horizon: int):
    try:
        return horizon * freq
    except TypeError:
        return horizon


def run() -> dict:
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    values = np.linspace(10.0, 29.0, 20)
    values[3] = np.nan
    series = TimeSeries.from_times_and_values(dates, values, columns=["sales"])
    train, val = series[:-5], series[-5:]

    pipe = Pipeline([MissingValuesFiller(), Scaler()])
    train_t = pipe.fit_transform(train)
    val_t = pipe.transform(val)
    assert not np.isnan(train_t.values()).any()
    assert not np.isnan(val_t.values()).any()

    # Toy forecast on transformed scale; inverse transform should restore original scale semantics.
    forecast_t = TimeSeries.from_times_and_values(
        pd.date_range(val.start_time(), periods=len(val), freq=val.freq),
        np.full(len(val), float(train_t.values()[-1, 0])),
        columns=["sales"],
    )
    forecast = pipe.inverse_transform(forecast_t, partial=True)
    assert forecast.n_components == 1
    assert len(forecast) == len(val)

    horizon = 5
    extended_index = pd.date_range(
        series.start_time(), periods=len(series) + horizon, freq=series.freq
    )
    dummy = TimeSeries.from_times_and_values(extended_index, np.arange(len(extended_index)))
    dow = datetime_attribute_timeseries(dummy, attribute="dayofweek", one_hot=False)
    month = datetime_attribute_timeseries(dummy, attribute="month", one_hot=False)
    future_covariates = dow.stack(month)
    required_end = series.end_time() + _future_offset(series.freq, horizon)
    assert future_covariates.end_time() >= required_end
    assert future_covariates.n_components == 2

    return {
        "status": "ok",
        "train_length": len(train),
        "validation_length": len(val),
        "forecast_length": len(forecast),
        "future_covariate_components": list(map(str, future_covariates.components)),
        "future_covariate_end": str(future_covariates.end_time()),
        "required_future_end": str(required_end),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="print only JSON result")
    args = parser.parse_args()
    result = run()
    if args.quiet:
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
