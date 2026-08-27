#!/usr/bin/env python3
"""Tiny Darts metrics and optional SHAP signature smoke."""
from __future__ import annotations

import argparse
import inspect
import json

import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.metrics import ic, iw, mae, mql, rmse


def run(check_shap: bool = False) -> dict:
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    actual = TimeSeries.from_times_and_values(dates, np.linspace(1.0, 10.0, 10), columns=["y"])
    point = TimeSeries.from_times_and_values(dates, np.linspace(1.1, 9.9, 10), columns=["y"])

    samples = np.stack(
        [np.linspace(0.8, 9.8, 10), np.linspace(1.0, 10.0, 10), np.linspace(1.2, 10.2, 10)],
        axis=-1,
    ).reshape(10, 1, 3)
    stochastic = TimeSeries.from_times_and_values(dates, samples, columns=["y"])
    assert stochastic.n_samples == 3

    out = {
        "status": "ok",
        "mae": float(mae(actual, point)),
        "rmse": float(rmse(actual, point)),
        "ic": float(ic(actual, stochastic, q_interval=(0.1, 0.9), time_reduction=np.nanmean)),
        "iw": float(iw(actual, stochastic, q_interval=(0.1, 0.9), time_reduction=np.nanmean)),
        "mql": float(np.nanmean(mql(actual, stochastic, q=[0.1, 0.5, 0.9]))),
        "shap_checked": False,
    }
    assert all(np.isfinite(v) for k, v in out.items() if isinstance(v, float))

    if check_shap:
        from darts.explainability import ShapExplainer

        out["shap_checked"] = True
        out["shap_signature"] = str(inspect.signature(ShapExplainer))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-shap", action="store_true", help="also import ShapExplainer and print its signature")
    args = parser.parse_args()
    print(json.dumps(run(check_shap=args.check_shap), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
