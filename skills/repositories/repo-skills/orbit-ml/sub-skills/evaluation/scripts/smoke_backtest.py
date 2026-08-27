#!/usr/bin/env python3
"""Run a tiny deterministic Orbit backtest smoke check.

Purpose
-------
Exercise the evaluation surface using only the installed Orbit package and
synthetic data. The script builds a small series, runs `TimeSeriesSplitter`
and `BackTester`, then prints the split summary and metric table.

Usage
-----
python smoke_backtest.py
python smoke_backtest.py --window-type rolling
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

os.environ.setdefault("MPLBACKEND", "Agg")


@dataclass
class DeterministicTrendModel:
    """Minimal fit/predict model compatible with Orbit's BackTester.

    The model fits a least-squares line against the day offset of the supplied
    datetime column and predicts on the same offset scale for every dataframe
    passed to `predict()`.
    """

    date_col: str = "date"
    response_col: str = "y"

    def fit(self, df: pd.DataFrame):
        frame = df[[self.date_col, self.response_col]].copy()
        frame[self.date_col] = pd.to_datetime(frame[self.date_col])
        self._origin = frame[self.date_col].min()
        x = self._to_offset(frame[self.date_col])
        y = frame[self.response_col].to_numpy(dtype=float)
        if len(x) < 2:
            self._coef = np.array([0.0, float(y.mean()) if len(y) else 0.0])
        else:
            self._coef = np.polyfit(x, y, deg=1)
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        frame = df[[self.date_col]].copy()
        frame[self.date_col] = pd.to_datetime(frame[self.date_col])
        x = self._to_offset(frame[self.date_col])
        yhat = np.polyval(self._coef, x)
        return pd.DataFrame({self.date_col: frame[self.date_col].values, "prediction": yhat})

    def _to_offset(self, dates: pd.Series | Iterable[pd.Timestamp]) -> np.ndarray:
        dates = pd.to_datetime(pd.Series(dates))
        return (dates - self._origin).dt.days.to_numpy(dtype=float)


def build_series(n_periods: int) -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", periods=n_periods, freq="D")
    t = np.arange(n_periods, dtype=float)
    y = 12.0 + 0.6 * t + 0.2 * np.sin(t / 3.0)
    return pd.DataFrame({"date": dates, "y": y})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-periods", type=int, default=32, help="Length of the synthetic series.")
    parser.add_argument("--min-train-len", type=int, default=16, help="Minimum training window length.")
    parser.add_argument("--forecast-len", type=int, default=4, help="Forecast horizon per split.")
    parser.add_argument("--incremental-len", type=int, default=4, help="Step size between splits.")
    parser.add_argument("--window-type", choices=["expanding", "rolling"], default="expanding", help="Split window type.")
    parser.add_argument("--json", action="store_true", help="Print the metric summary as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        from orbit.diagnostics.backtest import BackTester, TimeSeriesSplitter

        df = build_series(args.n_periods)
        model = DeterministicTrendModel(date_col="date", response_col="y")

        splitter = TimeSeriesSplitter(
            df=df,
            date_col="date",
            min_train_len=args.min_train_len,
            incremental_len=args.incremental_len,
            forecast_len=args.forecast_len,
            window_type=args.window_type,
        )

        print("=== Split summary ===")
        print(splitter)

        bt = BackTester(
            model=model,
            df=df,
            min_train_len=args.min_train_len,
            incremental_len=args.incremental_len,
            forecast_len=args.forecast_len,
            window_type=args.window_type,
        )
        bt.fit_predict()

        score_df = bt.score(include_training_metrics=True)
        pred_df = bt.get_predicted_df()

        payload = {
            "metric_rows": int(score_df.shape[0]),
            "prediction_rows": int(pred_df.shape[0]),
            "split_keys": sorted(int(x) for x in pred_df["split_key"].unique()),
        }

        print("=== Metric table ===")
        print(score_df.to_string(index=False))
        print("=== Rows by split ===")
        print(pred_df.groupby("split_key").size().to_string())
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("evaluation smoke: ok")
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except ModuleNotFoundError as exc:
        print(f"evaluation smoke missing dependency: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"evaluation smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
