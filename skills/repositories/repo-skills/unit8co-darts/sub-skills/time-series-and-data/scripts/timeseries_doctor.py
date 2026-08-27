#!/usr/bin/env python3
"""Tiny Darts TimeSeries construction and validation smoke.

This script uses generated in-memory data only. It is safe to run in a normal
Darts environment and does not depend on the original repository checkout.
"""
from __future__ import annotations

import argparse
import json

import pandas as pd
from darts import TimeSeries


def run() -> dict:
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-04"]),
            "sales": [10.0, 11.0, 13.0],
            "returns": [1.0, 0.0, 2.0],
        }
    )
    static_covariates = pd.DataFrame(
        {"kind": ["target", "target"], "unit": ["items", "items"]},
        index=["sales", "returns"],
    )
    series = TimeSeries.from_dataframe(
        df,
        time_col="timestamp",
        value_cols=["sales", "returns"],
        fill_missing_dates=True,
        freq="D",
        static_covariates=static_covariates,
    )
    assert len(series) == 4, len(series)
    assert series.n_components == 2, series.n_components
    assert list(series.components) == ["sales", "returns"]
    assert series.static_covariates is not None
    assert series.static_covariates.shape[0] in (1, series.n_components)

    grouped = pd.DataFrame(
        {
            "store": ["A", "A", "B", "B"],
            "region": ["west", "west", "east", "east"],
            "timestamp": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"]
            ),
            "sales": [10.0, 11.0, 7.0, 9.0],
        }
    )
    series_list = TimeSeries.from_group_dataframe(
        grouped,
        group_cols="store",
        time_col="timestamp",
        value_cols="sales",
        static_cols="region",
        fill_missing_dates=True,
        freq="D",
    )
    assert len(series_list) == 2
    assert all(len(ts) == 2 for ts in series_list)

    train, val = series[:3], series[3:]
    assert len(train) == 3
    assert len(val) == 1

    return {
        "status": "ok",
        "single_series": {
            "length": len(series),
            "components": list(map(str, series.components)),
            "n_samples": series.n_samples,
            "start": str(series.start_time()),
            "end": str(series.end_time()),
        },
        "grouped_series_count": len(series_list),
        "split_lengths": [len(train), len(val)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a human summary")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Darts TimeSeries doctor: ok")
        print(result)


if __name__ == "__main__":
    main()
