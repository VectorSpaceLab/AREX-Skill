#!/usr/bin/env python3
"""Tiny CPU smoke check for NeuralProphet quantile and conformal intervals.

The script generates synthetic data, makes train/calibration/test splits,
trains a one-step quantile model, runs naive split conformal prediction, and
prints interval columns plus an uncertainty evaluation summary. It uses no
network and writes no files.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from neuralprophet import NeuralProphet, set_log_level, set_random_seed, uncertainty_evaluate


def make_synthetic_series(points: int, freq: str, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(points, dtype=float)
    ds = pd.date_range("2021-01-01", periods=points, freq=freq)
    y = 20.0 + 0.04 * t + np.sin(2.0 * np.pi * t / 14.0) + 0.15 * rng.standard_normal(points)
    return pd.DataFrame({"ds": ds, "y": y})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=120, help="Synthetic observations to generate; minimum 60.")
    parser.add_argument("--freq", default="D", help="Pandas frequency string for generated ds values.")
    parser.add_argument("--epochs", type=int, default=8, help="Training epochs for the tiny model.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for data generation and model fitting.")
    parser.add_argument("--alpha", type=float, default=0.1, help="Naive conformal error rate; 0.1 targets 90%% coverage.")
    args = parser.parse_args()

    if args.points < 60:
        parser.error("--points must be at least 60 so train/calibration/test splits are non-trivial.")
    if not 0.0 < args.alpha < 1.0:
        parser.error("--alpha must be between 0 and 1.")
    if args.epochs < 1:
        parser.error("--epochs must be at least 1.")

    set_log_level("ERROR")
    set_random_seed(args.seed)

    df = make_synthetic_series(points=args.points, freq=args.freq, seed=args.seed)
    model = NeuralProphet(
        quantiles=[0.05, 0.95],
        n_forecasts=1,
        n_lags=0,
        epochs=args.epochs,
        batch_size=16,
        learning_rate=0.1,
        accelerator="cpu",
    )

    train_cal_df, test_df = model.split_df(df, freq=args.freq, valid_p=0.2)
    train_df, cal_df = model.split_df(train_cal_df, freq=args.freq, valid_p=0.25)

    model.fit(train_df, freq=args.freq, progress=None, minimal=True, deterministic=True)

    forecast = model.conformal_predict(
        test_df,
        calibration_df=cal_df,
        alpha=args.alpha,
        method="naive",
        show_all_PI=True,
        decompose=False,
    )

    interval_cols = [col for col in forecast.columns if isinstance(col, str) and ("qhat" in col or "%" in col)]
    if not interval_cols:
        raise RuntimeError("No interval columns were produced by conformal_predict.")

    print(f"split rows: train={len(train_df)} calibration={len(cal_df)} test={len(test_df)}")
    print("interval columns:")
    for col in interval_cols:
        print(f"  - {col}")

    evaluation = uncertainty_evaluate(forecast)
    print("\nevaluation summary:")
    print(evaluation.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
