#!/usr/bin/env python3
"""Tiny NeuralProphet component smoke test.

Exercises future regressors, custom events, and multi-series IDs on generated
CPU data. It is intentionally small and network-free.

Example:
    python smoke_components.py --epochs 1 --periods 4
"""

from __future__ import annotations

import argparse
import sys
import warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny NeuralProphet component smoke test.")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for each tiny model.")
    parser.add_argument("--periods", type=int, default=4, help="Future periods for the regressor/event check.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.periods < 1:
        print("--periods must be positive", file=sys.stderr)
        return 2

    warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
    import pandas as pd
    from neuralprophet import NeuralProphet, set_log_level, set_random_seed

    set_log_level("ERROR")
    set_random_seed(7)

    rows = 48 + args.periods
    base = pd.DataFrame(
        {
            "ds": pd.date_range("2022-01-01", periods=rows, freq="D"),
            "y": [float((i % 10) + 0.05 * i) for i in range(rows)],
        }
    )
    base["temperature"] = [15.0 + (i % 5) for i in range(rows)]
    history = base.iloc[:-args.periods].copy()
    future_regs = pd.DataFrame({"temperature": base["temperature"].iloc[-args.periods:].to_numpy()})
    events = pd.DataFrame({"event": ["promo", "promo"], "ds": pd.to_datetime(["2022-01-15", "2022-02-05"])})

    model = NeuralProphet(
        n_changepoints=0,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        epochs=args.epochs,
        batch_size=16,
        learning_rate=0.1,
        accelerator="cpu",
        collect_metrics=False,
    )
    model.add_future_regressor("temperature")
    model.add_events("promo", lower_window=-1, upper_window=1)
    history_with_events = model.create_df_with_events(history, events)
    model.fit(history_with_events, freq="D", progress=None)
    future = model.make_future_dataframe(
        history_with_events,
        periods=args.periods,
        regressors_df=future_regs,
        events_df=events,
        n_historic_predictions=2,
    )
    forecast = model.predict(future)

    panel_base = history[["ds", "y"]].copy()
    panel_a = panel_base.copy(); panel_a["ID"] = "series_a"
    panel_b = panel_base.copy(); panel_b["ID"] = "series_b"; panel_b["y"] = panel_b["y"] * 1.1
    panel = pd.concat([panel_a, panel_b], ignore_index=True)
    global_model = NeuralProphet(
        n_changepoints=0,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        trend_global_local="local",
        season_global_local="global",
        epochs=args.epochs,
        batch_size=16,
        learning_rate=0.1,
        accelerator="cpu",
        collect_metrics=False,
    )
    global_model.fit(panel, freq="D", progress=None)

    yhat_cols = [c for c in forecast.columns if c.startswith("yhat")]
    if not yhat_cols:
        print("component forecast did not contain yhat columns", file=sys.stderr)
        return 1
    print({"component_forecast_rows": len(forecast), "yhat_columns": yhat_cols, "panel_ids": sorted(panel["ID"].unique())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
