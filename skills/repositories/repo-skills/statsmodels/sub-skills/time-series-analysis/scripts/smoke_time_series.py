#!/usr/bin/env python3
"""Tiny statsmodels time-series smoke check."""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ARIMA/STL/ADF smoke checks on synthetic data.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    idx = pd.date_range("2020-01-01", periods=48, freq="ME")
    t = np.arange(48)
    series = pd.Series(0.3 * t + np.sin(2 * np.pi * t / 12), index=idx)
    arima = ARIMA(series, order=(1, 1, 0)).fit()
    fc = arima.get_forecast(steps=3).summary_frame()
    stl = STL(series, period=12, robust=True).fit()
    adf = adfuller(series.diff().dropna(), maxlag=1, regression="c", autolag=None)
    ok = bool(np.isfinite(arima.params).all() and fc.shape[0] == 3 and np.isfinite(stl.trend).all() and np.isfinite(adf[0]))
    report = {"ok": ok, "arima_param_count": int(len(arima.params)), "forecast_rows": int(fc.shape[0]), "adf_stat": float(adf[0])}
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
