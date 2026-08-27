#!/usr/bin/env python3
"""Deterministic smoke checks for core StatsForecast workflows.

The script imports the installed statsforecast package and builds a tiny panel in
memory. It does not read a repository checkout or external data.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic core StatsForecast smoke checks on generated data."
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=3,
        help="Forecast horizon for smoke checks. Default: 3.",
    )
    parser.add_argument(
        "--n-series",
        type=int,
        default=2,
        help="Number of generated panel series. Default: 2.",
    )
    parser.add_argument(
        "--periods",
        type=int,
        default=12,
        help="Historical observations per series. Default: 12.",
    )
    parser.add_argument(
        "--custom-cols",
        action="store_true",
        help="Also verify custom id/time/target column handling and fitted values.",
    )
    parser.add_argument(
        "--exog",
        action="store_true",
        help="Also verify future X_df exogenous alignment using a tiny local model.",
    )
    parser.add_argument(
        "--intervals",
        action="store_true",
        help="Also verify conformal interval output columns.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enable --custom-cols, --exog, and --intervals.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print compact JSON only.",
    )
    return parser.parse_args()


def load_dependencies():
    import numpy as np
    import pandas as pd
    from statsforecast import StatsForecast
    from statsforecast.models import Naive, SeasonalNaive
    from statsforecast.utils import ConformalIntervals

    return np, pd, StatsForecast, Naive, SeasonalNaive, ConformalIntervals


def make_panel(pd: Any, n_series: int, periods: int):
    rows = []
    start = pd.Timestamp("2024-01-01")
    for series_idx in range(n_series):
        uid = f"id_{series_idx}"
        base = 10.0 * (series_idx + 1)
        for t in range(periods):
            rows.append(
                {
                    "unique_id": uid,
                    "ds": start + pd.Timedelta(days=t),
                    "y": base + t + (0.25 if t % 2 else 0.0),
                }
            )
    return pd.DataFrame(rows)


def validate_args(args: argparse.Namespace) -> None:
    if args.horizon < 1:
        raise ValueError("--horizon must be >= 1")
    if args.n_series < 1:
        raise ValueError("--n-series must be >= 1")
    if args.periods <= args.horizon + 1:
        raise ValueError("--periods must be greater than horizon + 1 for cross-validation")
    if (args.intervals or args.all) and args.periods < 2 * args.horizon + 1:
        raise ValueError(
            "--periods must be at least 2 * horizon + 1 when interval checks are enabled"
        )


def run_basic_checks(pd: Any, StatsForecast: Any, Naive: Any, panel: Any, h: int):
    sf = StatsForecast(models=[Naive()], freq="D", n_jobs=1)
    fcst = sf.forecast(df=panel, h=h)
    sf.fit(df=panel)
    pred = sf.predict(h=h)
    fit_pred = sf.fit_predict(df=panel, h=h)

    pd.testing.assert_frame_equal(fcst, pred, check_dtype=False)
    pd.testing.assert_frame_equal(fcst, fit_pred, check_dtype=False)

    cv_h = min(h, 2)
    cv_sf = StatsForecast(models=[Naive()], freq="D", n_jobs=1)
    cv = cv_sf.cross_validation(df=panel, h=cv_h, n_windows=2, fitted=True)
    cv_fitted = cv_sf.cross_validation_fitted_values()

    required_fcst_cols = {"unique_id", "ds", "Naive"}
    required_cv_cols = {"unique_id", "ds", "cutoff", "y", "Naive"}
    if not required_fcst_cols.issubset(fcst.columns):
        raise AssertionError(f"forecast columns missing {required_fcst_cols - set(fcst.columns)}")
    if not required_cv_cols.issubset(cv.columns):
        raise AssertionError(f"cv columns missing {required_cv_cols - set(cv.columns)}")
    if "cutoff" not in cv_fitted.columns:
        raise AssertionError("cross_validation_fitted_values did not include cutoff")

    return {
        "name": "basic_forecast_fit_predict_cv",
        "forecast_shape": list(fcst.shape),
        "cv_shape": list(cv.shape),
        "cv_fitted_shape": list(cv_fitted.shape),
    }


def run_custom_column_check(pd: Any, StatsForecast: Any, Naive: Any, panel: Any, h: int):
    custom = panel.rename(
        columns={"unique_id": "item_id", "ds": "timestamp", "y": "target"}
    )
    kwargs = {"id_col": "item_id", "time_col": "timestamp", "target_col": "target"}
    sf = StatsForecast(models=[Naive()], freq="D", n_jobs=1)
    fcst = sf.forecast(df=custom, h=h, fitted=True, **kwargs)
    fitted = sf.forecast_fitted_values()
    sf.fit(df=custom, **kwargs)
    pred = sf.predict(h=h)
    pd.testing.assert_frame_equal(fcst, pred, check_dtype=False)

    expected_future = {"item_id", "timestamp", "Naive"}
    expected_fitted = {"item_id", "timestamp", "target", "Naive"}
    if not expected_future.issubset(fcst.columns):
        raise AssertionError(f"custom forecast columns missing {expected_future - set(fcst.columns)}")
    if not expected_fitted.issubset(fitted.columns):
        raise AssertionError(f"custom fitted columns missing {expected_fitted - set(fitted.columns)}")

    return {
        "name": "custom_columns",
        "forecast_columns": list(fcst.columns),
        "fitted_columns": list(fitted.columns),
    }


def run_exog_check(np: Any, pd: Any, StatsForecast: Any, panel: Any, h: int):
    class FutureXEcho:
        uses_exog = True
        alias = "FutureXEcho"

        def __repr__(self):
            return self.alias

        def new(self):
            clone = type(self)()
            clone.__dict__.update(self.__dict__)
            return clone

        def fit(self, y, X=None):
            return self

        def predict(self, h, X=None, level=None):
            if X is None:
                raise ValueError("X is required")
            return {"mean": np.asarray(X[:, 0], dtype=float)}

        def forecast(self, y, h, X=None, X_future=None, fitted=False, level=None):
            if X_future is None:
                raise ValueError("X_future is required")
            out = {"mean": np.asarray(X_future[:, 0], dtype=float)}
            if fitted:
                out["fitted"] = (
                    np.asarray(X[:, 0], dtype=float)
                    if X is not None
                    else np.full(y.shape[0], np.nan, dtype=float)
                )
            return out

    train = panel.copy()
    train["x"] = train.groupby("unique_id").cumcount().astype(float) + 1.0
    future_rows = []
    for uid, group in train.groupby("unique_id", sort=True):
        last_ds = group["ds"].max()
        last_x = float(group["x"].max())
        for step in range(1, h + 1):
            future_rows.append(
                {
                    "unique_id": uid,
                    "ds": last_ds + pd.Timedelta(days=step),
                    "x": last_x + step,
                }
            )
    x_df = pd.DataFrame(future_rows)

    sf = StatsForecast(models=[FutureXEcho()], freq="D", n_jobs=1)
    try:
        sf.forecast(df=train, h=h)
    except ValueError as exc:
        if "X_df" not in str(exc):
            raise
    else:
        raise AssertionError("missing X_df did not raise a validation error")

    out = sf.forecast(df=train, h=h, X_df=x_df)
    expected = x_df["x"].astype(float).to_numpy()
    actual = out["FutureXEcho"].astype(float).to_numpy()
    np.testing.assert_allclose(actual, expected)

    return {"name": "exogenous_x_df", "forecast_shape": list(out.shape)}


def run_interval_check(
    np: Any,
    StatsForecast: Any,
    SeasonalNaive: Any,
    ConformalIntervals: Any,
    panel: Any,
    h: int,
):
    sf = StatsForecast(models=[SeasonalNaive(season_length=2)], freq="D", n_jobs=1)
    out = sf.forecast(
        df=panel,
        h=h,
        level=[80, 95],
        prediction_intervals=ConformalIntervals(n_windows=2, h=h),
    )
    model = "SeasonalNaive"
    required = {
        model,
        f"{model}-lo-80",
        f"{model}-hi-80",
        f"{model}-lo-95",
        f"{model}-hi-95",
    }
    if not required.issubset(out.columns):
        raise AssertionError(f"interval columns missing {required - set(out.columns)}")
    values = out[list(required)].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise AssertionError("interval forecast contains non-finite values")
    return {"name": "conformal_intervals", "forecast_shape": list(out.shape)}


def main() -> int:
    args = parse_args()
    validate_args(args)
    np, pd, StatsForecast, Naive, SeasonalNaive, ConformalIntervals = load_dependencies()
    panel = make_panel(pd, args.n_series, args.periods)

    checks = [run_basic_checks(pd, StatsForecast, Naive, panel, args.horizon)]
    if args.custom_cols or args.all:
        checks.append(run_custom_column_check(pd, StatsForecast, Naive, panel, args.horizon))
    if args.exog or args.all:
        checks.append(run_exog_check(np, pd, StatsForecast, panel, args.horizon))
    if args.intervals or args.all:
        checks.append(
            run_interval_check(
                np, StatsForecast, SeasonalNaive, ConformalIntervals, panel, args.horizon
            )
        )

    result = {
        "status": "ok",
        "statsforecast_version": importlib.metadata.version("statsforecast"),
        "n_series": args.n_series,
        "periods": args.periods,
        "horizon": args.horizon,
        "checks": checks,
    }
    if args.quiet:
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - keeps CLI failure concise
        print(f"core_forecast_smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
