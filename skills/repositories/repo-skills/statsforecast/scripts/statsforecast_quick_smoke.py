#!/usr/bin/env python3
"""Run a deterministic package-level StatsForecast smoke test.

The smoke combines the repo's public quick-start pattern with compact CI-style
fit/forecast parity checks. It uses synthetic in-memory data only and does not
need the StatsForecast source repository.
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, Naive, SeasonalNaive
from statsforecast.utils import generate_series


def build_future_x(df: pd.DataFrame, h: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = df.copy()
    train["weekday"] = train["ds"].dt.dayofweek.astype(float)
    future_rows = []
    for uid, g in train.groupby("unique_id", observed=True):
        last = g["ds"].max()
        for step in range(1, h + 1):
            ds = last + pd.Timedelta(days=step)
            future_rows.append({"unique_id": uid, "ds": ds, "weekday": float(ds.dayofweek)})
    return train, pd.DataFrame(future_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny StatsForecast end-to-end smoke test.")
    parser.add_argument("--n-series", type=int, default=2, help="Number of synthetic series.")
    parser.add_argument("--length", type=int, default=36, help="Training observations per series.")
    parser.add_argument("--horizon", type=int, default=4, help="Forecast horizon.")
    parser.add_argument("--use-auto-arima", action="store_true", help="Include AutoARIMA for an exogenous-regressor check; slower than baseline models.")
    parser.add_argument("--json", action="store_true", help="Print JSON output only.")
    args = parser.parse_args()

    if args.length <= max(8, args.horizon + 2):
        raise SystemExit("--length must be comfortably larger than --horizon")

    df = generate_series(
        n_series=args.n_series,
        min_length=args.length,
        max_length=args.length,
        equal_ends=True,
        freq="D",
        seed=0,
    )

    baseline_models = [Naive(), SeasonalNaive(season_length=7)]
    sf = StatsForecast(models=baseline_models, freq="D", n_jobs=1)
    forecast_df = sf.forecast(df=df, h=args.horizon, level=[80])
    cv_df = sf.cross_validation(df=df, h=min(2, args.horizon), n_windows=2)

    report = {
        "status": "ok",
        "baseline_rows": len(forecast_df),
        "baseline_columns": list(forecast_df.columns),
        "cv_rows": len(cv_df),
        "auto_arima_exog_rows": None,
    }

    if args.use_auto_arima:
        train, future = build_future_x(df, h=args.horizon)
        auto = StatsForecast(models=[AutoARIMA(season_length=7, alias="AutoARIMAWeekly")], freq="D", n_jobs=1)
        auto_df = auto.forecast(df=train, h=args.horizon, X_df=future)
        report["auto_arima_exog_rows"] = len(auto_df)
        report["auto_arima_exog_columns"] = list(auto_df.columns)

    expected_rows = args.n_series * args.horizon
    if report["baseline_rows"] != expected_rows:
        raise AssertionError(f"expected {expected_rows} forecast rows, got {report['baseline_rows']}")
    if "Naive" not in forecast_df or "SeasonalNaive" not in forecast_df:
        raise AssertionError("missing expected baseline model columns")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("statsforecast quick smoke ok")
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
