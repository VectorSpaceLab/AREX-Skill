#!/usr/bin/env python3
"""Tiny offline forecasting smoke check for Orbit ETS/LGT.

The script is intentionally self-contained:
- it generates synthetic data in memory,
- it does not download datasets,
- it does not rely on repository notebooks or tests,
- it uses only public `orbit` APIs.

Default checks:
1. ETS + Stan MAP + bootstrap percentiles + future-frame creation.
2. LGT + Pyro SVI + regressor fit/predict + coefficient extraction.

Use `--skip-stan` or `--skip-pyro` only when deliberately narrowing the
backend check.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

import numpy as np
import pandas as pd


def _require_columns(df: pd.DataFrame, required: Sequence[str], label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise AssertionError(f"{label} missing required columns: {missing}")


def _assert_finite(series: pd.Series, label: str) -> None:
    values = np.asarray(series)
    if not np.all(np.isfinite(values)):
        raise AssertionError(f"{label} contains non-finite values")


def _make_base_frame() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=18, freq="D")
    t = np.arange(len(dates), dtype=float)
    x = np.linspace(0.25, 1.25, len(dates))
    y = 12.0 + 0.35 * t + 0.8 * np.sin(t / 2.5) + 1.5 * x
    return pd.DataFrame({"ds": dates, "y": y, "x": x})


def smoke_ets_map() -> None:
    from orbit.models import ETS

    train = _make_base_frame()[["ds", "y"]].iloc[:14].reset_index(drop=True)
    model = ETS(
        response_col="y",
        date_col="ds",
        seasonality=1,
        estimator="stan-map",
        n_bootstrap_draws=25,
        prediction_percentiles=[10, 90],
        seed=2024,
        verbose=False,
    )
    model.fit(train)

    future = model.make_future_df(periods=3)
    pred = model.predict(future, seed=2024)
    _require_columns(pred, ["ds", "prediction_10", "prediction", "prediction_90"], "ETS prediction")
    if pred.shape[0] != 3:
        raise AssertionError(f"ETS prediction row count mismatch: {pred.shape[0]}")
    _assert_finite(pred["prediction"], "ETS prediction")

    decomposed = model.predict(future, decompose=True, seed=2024)
    _require_columns(decomposed, ["ds", "prediction", "trend", "seasonality"], "ETS decomposed prediction")
    if not {"prediction_10", "prediction_90", "trend_10", "trend_90", "seasonality_10", "seasonality_90"}.issubset(decomposed.columns):
        raise AssertionError("ETS decomposed prediction is missing percentile component columns")
    if decomposed.shape[0] != 3:
        raise AssertionError(f"ETS decomposed row count mismatch: {decomposed.shape[0]}")


def smoke_lgt_pyro() -> None:
    from orbit.models import LGT

    df = _make_base_frame()
    train = df.iloc[:14].reset_index(drop=True)
    future = pd.DataFrame(
        {
            "ds": pd.date_range(train["ds"].iloc[-1], periods=5, freq="D")[1:],
            "x": np.linspace(1.3, 1.7, 4),
        }
    )

    model = LGT(
        response_col="y",
        date_col="ds",
        seasonality=1,
        regressor_col=["x"],
        regressor_sign=["+"],
        estimator="pyro-svi",
        num_steps=10,
        num_sample=10,
        num_particles=10,
        prediction_percentiles=[],
        seed=2024,
        verbose=False,
    )
    model.fit(train, point_method="median")
    pred = model.predict(future, decompose=True, seed=2024)
    _require_columns(pred, ["ds", "prediction", "trend", "seasonality", "regression"], "LGT prediction")
    if pred.shape[0] != 4:
        raise AssertionError(f"LGT prediction row count mismatch: {pred.shape[0]}")
    _assert_finite(pred["prediction"], "LGT prediction")

    coef = model.get_regression_coefs()
    _require_columns(coef, ["regressor", "regressor_sign", "coefficient"], "LGT regression coefficients")
    if coef.shape[0] != 1:
        raise AssertionError(f"LGT coefficient row count mismatch: {coef.shape[0]}")
    _assert_finite(coef["coefficient"], "LGT regression coefficients")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny offline Orbit forecasting smoke check.")
    parser.add_argument("--skip-stan", action="store_true", help="Skip the ETS MAP / Stan-backed smoke check.")
    parser.add_argument("--skip-pyro", action="store_true", help="Skip the LGT Pyro-SVI smoke check.")
    args = parser.parse_args()

    try:
        if not args.skip_stan:
            smoke_ets_map()
            print("ETS MAP smoke: ok")

        if not args.skip_pyro:
            smoke_lgt_pyro()
            print("LGT Pyro-SVI smoke: ok")
    except ModuleNotFoundError as exc:
        print(f"forecasting smoke missing dependency: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"forecasting smoke failed: {exc}", file=sys.stderr)
        return 1

    print("forecasting smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
