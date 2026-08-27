#!/usr/bin/env python3
"""Tiny network-free smoke check for Orbit KTR / KTRLite.

Default mode runs KTRLite. Use --model ktr or --model both to exercise KTR as well.
The script never downloads data or installs backends.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np
import pandas as pd


def make_daily_series(
    n_obs: int = 56,
    seed: int = 7,
    freq: str = "D",
    with_regressor: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    t = np.arange(n_obs, dtype=float)

    level = 5.0 + 0.04 * t
    seas7 = 0.9 * np.sin(2.0 * np.pi * t / 7.0) + 0.35 * np.cos(2.0 * np.pi * t / 7.0)
    seas14 = 0.6 * np.sin(2.0 * np.pi * t / 14.0) - 0.25 * np.cos(2.0 * np.pi * t / 14.0)
    noise = rng.normal(scale=0.05, size=n_obs)

    data = {
        "date": pd.date_range("2021-01-01", periods=n_obs, freq=freq),
    }

    if with_regressor:
        promo = np.sin(2.0 * np.pi * t / 14.0) + 0.15 * rng.normal(size=n_obs)
        data["promo"] = promo
        response = level + seas7 + seas14 + 0.35 * promo + noise
    else:
        response = level + seas7 + seas14 + noise

    data["response"] = response
    df = pd.DataFrame(data)
    split = n_obs - 14
    train = df.iloc[:split].reset_index(drop=True)
    test = df.iloc[split:].reset_index(drop=True)
    return train, test


def _assert_columns(frame: pd.DataFrame, expected: set[str], label: str) -> None:
    missing = expected.difference(frame.columns)
    if missing:
        raise AssertionError(f"{label} is missing columns: {sorted(missing)}")


def run_ktrlite(freq: str) -> dict[str, Any]:
    from orbit.models import KTRLite

    train, test = make_daily_series(freq=freq, with_regressor=False)
    model = KTRLite(
        response_col="response",
        date_col="date",
        level_segments=3,
        seasonality=[7, 14],
        seasonality_fs_order=[2, 3],
        seasonality_segments=1,
        date_freq=freq,
        estimator="stan-map",
        suppress_stan_log=True,
        n_bootstrap_draws=-1,
    )
    model.fit(train)
    pred = model.predict(test, decompose=True)
    level_knots = model.get_level_knots()
    levels = model.get_levels()
    bic = model.get_bic()

    _assert_columns(pred, {"date", "prediction", "trend", "seasonality_7", "seasonality_14"}, "KTRLite predict")
    if not np.isfinite(pred["prediction"].to_numpy()).all():
        raise AssertionError("KTRLite prediction contains non-finite values")
    if level_knots.empty:
        raise AssertionError("KTRLite level knots frame is empty")
    if levels.empty:
        raise AssertionError("KTRLite levels frame is empty")
    if not np.isfinite(np.asarray(bic)).all():
        raise AssertionError("KTRLite BIC is not finite")

    return {
        "model": "ktrlite",
        "prediction_shape": list(pred.shape),
        "level_knots_shape": list(level_knots.shape),
        "levels_shape": list(levels.shape),
        "bic": float(bic),
    }


def run_ktr(freq: str) -> dict[str, Any]:
    from orbit.models import KTR

    train, test = make_daily_series(freq=freq, with_regressor=True)
    model = KTR(
        response_col="response",
        date_col="date",
        regressor_col=["promo"],
        regressor_sign=["="],
        regressor_init_knot_loc=[0.0],
        regressor_init_knot_scale=[1.0],
        regressor_knot_scale=[0.1],
        regression_segments=1,
        level_segments=3,
        seasonality=[7, 14],
        seasonality_fs_order=[2, 3],
        seasonality_segments=1,
        date_freq=freq,
        estimator="pyro-svi",
        num_steps=20,
        num_sample=12,
        n_bootstrap_draws=-1,
        seed=123,
    )
    model.fit(train)
    pred = model.predict(test, decompose=True)
    coef_mid, coef_lo, coef_hi = model.get_regression_coefs(include_ci=True)
    coef_knots = model.get_regression_coef_knots()
    level_knots = model.get_level_knots()
    levels = model.get_levels()

    _assert_columns(
        pred,
        {
            "date",
            "prediction",
            "prediction_5",
            "prediction_95",
            "trend",
            "regression",
            "seasonality_7",
            "seasonality_14",
        },
        "KTR predict",
    )
    if not np.isfinite(pred["prediction"].to_numpy()).all():
        raise AssertionError("KTR prediction contains non-finite values")
    if coef_mid.empty or coef_lo.empty or coef_hi.empty:
        raise AssertionError("KTR regression coefficient frames are empty")
    if coef_knots.empty:
        raise AssertionError("KTR regression knot frame is empty")
    if level_knots.empty:
        raise AssertionError("KTR level knot frame is empty")
    if levels.empty:
        raise AssertionError("KTR levels frame is empty")
    if "promo" not in coef_mid.columns:
        raise AssertionError("KTR regression coefficients are missing the promo column")
    if "promo" not in coef_knots.columns:
        raise AssertionError("KTR regression knots are missing the promo column")

    return {
        "model": "ktr",
        "prediction_shape": list(pred.shape),
        "coef_mid_shape": list(coef_mid.shape),
        "coef_knots_shape": list(coef_knots.shape),
        "level_knots_shape": list(level_knots.shape),
        "levels_shape": list(levels.shape),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=("ktrlite", "ktr", "both"),
        default="ktrlite",
        help="Which smoke path to run.",
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Date frequency for the synthetic series.",
    )
    args = parser.parse_args()

    results: dict[str, Any] = {}
    if args.model in {"ktrlite", "both"}:
        results["ktrlite"] = run_ktrlite(args.freq)
    if args.model in {"ktr", "both"}:
        results["ktr"] = run_ktr(args.freq)

    print(json.dumps(results, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
