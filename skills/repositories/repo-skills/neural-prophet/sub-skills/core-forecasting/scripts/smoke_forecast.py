#!/usr/bin/env python3
"""Tiny NeuralProphet CPU fit/predict smoke test.

Purpose: verify that an installed NeuralProphet package can fit a minimal model
and produce forecast columns without network access or external data.

Example:
    python smoke_forecast.py --epochs 1 --periods 3
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path


def add_repo_root_to_path() -> None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "neuralprophet" / "__init__.py").exists():
            sys.path.insert(0, str(parent))
            return


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny CPU NeuralProphet fit/predict smoke test.")
    parser.add_argument("--periods", type=int, default=3, help="Future periods to append after fitting.")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for the tiny smoke run.")
    parser.add_argument("--rows", type=int, default=48, help="Number of synthetic daily history rows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rows < 16:
        print("--rows must be at least 16 for a stable smoke test", file=sys.stderr)
        return 2
    if args.periods < 0:
        print("--periods must be non-negative", file=sys.stderr)
        return 2

    warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
    add_repo_root_to_path()
    import pandas as pd
    from neuralprophet import NeuralProphet, set_log_level, set_random_seed

    set_log_level("ERROR")
    set_random_seed(42)

    df = pd.DataFrame(
        {
            "ds": pd.date_range("2022-01-01", periods=args.rows, freq="D"),
            "y": [float((i % 7) + 0.1 * (i // 7)) for i in range(args.rows)],
        }
    )
    model = NeuralProphet(
        n_changepoints=0,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        epochs=args.epochs,
        batch_size=min(16, args.rows),
        learning_rate=0.1,
        collect_metrics=False,
        accelerator="cpu",
    )
    metrics = model.fit(df, freq="D", progress=None)
    future = model.make_future_dataframe(df, periods=args.periods, n_historic_predictions=2)
    forecast = model.predict(future)
    yhat_cols = [col for col in forecast.columns if col.startswith("yhat")]
    if not yhat_cols:
        print("forecast did not contain any yhat columns", file=sys.stderr)
        return 1
    print({"metrics_is_none": metrics is None, "forecast_rows": len(forecast), "yhat_columns": yhat_cols})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
