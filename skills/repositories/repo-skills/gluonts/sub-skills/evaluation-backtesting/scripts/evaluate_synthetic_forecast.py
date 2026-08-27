#!/usr/bin/env python3
"""Checkout-independent GluonTS evaluation/backtesting smoke."""

from __future__ import annotations

import argparse
import math
import sys
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message=r"Using `json`-module for json-handling.*",
    category=UserWarning,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a tiny deterministic GluonTS SeasonalNaivePredictor with "
            "make_evaluation_predictions, Evaluator, and backtest_metrics."
        )
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Frequency string for the synthetic ListDataset (default: D).",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=4,
        help="Trailing forecast horizon to hold out and evaluate (default: 4).",
    )
    parser.add_argument(
        "--season-length",
        type=int,
        default=4,
        help="Season length for SeasonalNaivePredictor (default: 4).",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=20,
        help="Number of samples requested from predictors that use sampling (default: 20).",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="Evaluator worker count; 0 disables multiprocessing (default: 0).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=32,
        help="Evaluator multiprocessing chunk size when workers are enabled (default: 32).",
    )
    parser.add_argument(
        "--item-metrics-csv",
        "--output-csv",
        dest="item_metrics_csv",
        type=Path,
        default=None,
        help="Optional path where item metrics CSV should be written.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a compact item-metric preview in addition to the success line.",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.prediction_length <= 0:
        raise ValueError("--prediction-length must be positive")
    if args.season_length <= 0:
        raise ValueError("--season-length must be positive")
    if args.num_samples <= 0:
        raise ValueError("--num-samples must be positive")
    if args.num_workers < 0:
        raise ValueError("--num-workers must be non-negative")
    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be positive")


def build_dataset(freq: str):
    from gluonts.dataset.common import ListDataset

    # Each target has 8 history points plus a 4-step trailing holdout. The
    # final holdout repeats the previous season exactly, so seasonal naive
    # should forecast it perfectly while still exercising aggregate/item metrics.
    entries = [
        {
            "item_id": "weekday-pattern",
            "start": "2024-01-01",
            "target": [10.0, 11.0, 12.0, 13.0, 10.0, 11.0, 12.0, 13.0, 10.0, 11.0, 12.0, 13.0],
        },
        {
            "item_id": "level-shift-pattern",
            "start": "2024-01-01",
            "target": [20.0, 21.0, 22.0, 23.0, 20.0, 21.0, 22.0, 23.0, 20.0, 21.0, 22.0, 23.0],
        },
    ]
    return ListDataset(entries, freq=freq), len(entries)


def assert_alignment(forecasts, targets, prediction_length: int) -> None:
    if len(forecasts) != len(targets):
        raise AssertionError(
            f"forecast/target count mismatch: {len(forecasts)} != {len(targets)}"
        )

    for idx, (forecast, target) in enumerate(zip(forecasts, targets)):
        if len(forecast.index) != prediction_length:
            raise AssertionError(
                f"forecast {idx} horizon mismatch: {len(forecast.index)} != {prediction_length}"
            )
        if not forecast.index.isin(target.index).all():
            raise AssertionError(f"forecast {idx} index is outside target index")
        expected_index = target.index[-prediction_length:]
        if not forecast.index.equals(expected_index):
            raise AssertionError(
                f"forecast {idx} is not aligned to trailing holdout: "
                f"{forecast.index} != {expected_index}"
            )


def assert_metric_keys(agg_metrics: dict, item_metrics) -> None:
    expected_agg = {
        "MSE",
        "abs_error",
        "abs_target_sum",
        "MASE",
        "MAPE",
        "sMAPE",
        "MSIS",
        "RMSE",
        "ND",
        "QuantileLoss[0.5]",
        "Coverage[0.5]",
        "wQuantileLoss[0.5]",
        "mean_wQuantileLoss",
        "MAE_Coverage",
    }
    expected_item = {
        "item_id",
        "forecast_start",
        "MSE",
        "abs_error",
        "seasonal_error",
        "QuantileLoss[0.5]",
        "Coverage[0.5]",
    }

    missing_agg = sorted(expected_agg - set(agg_metrics))
    missing_item = sorted(expected_item - set(item_metrics.columns))
    if missing_agg or missing_item:
        raise AssertionError(
            f"missing metric keys: aggregate={missing_agg}, item={missing_item}"
        )

    for key in ["MSE", "abs_error", "RMSE", "ND", "mean_wQuantileLoss"]:
        value = float(agg_metrics[key])
        if not math.isfinite(value):
            raise AssertionError(f"aggregate metric {key} is not finite: {value}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        from gluonts.env import env as gluonts_env
        from gluonts.evaluation import Evaluator, backtest_metrics, make_evaluation_predictions
        from gluonts.model.seasonal_naive import SeasonalNaivePredictor
    except ImportError as exc:
        print(f"ERROR: required GluonTS imports failed: {exc}", file=sys.stderr)
        return 2

    dataset, expected_items = build_dataset(args.freq)
    predictor = SeasonalNaivePredictor(
        prediction_length=args.prediction_length,
        season_length=args.season_length,
    )
    evaluator = Evaluator(
        quantiles=(0.1, 0.5, 0.9),
        num_workers=args.num_workers,
        chunk_size=args.chunk_size,
        allow_nan_forecast=False,
    )

    # Keep smoke output concise even when GluonTS would otherwise show progress bars.
    with gluonts_env._let(use_tqdm=False):
        forecast_it, target_it = make_evaluation_predictions(
            dataset=dataset,
            predictor=predictor,
            num_samples=args.num_samples,
        )
        forecasts = list(forecast_it)
        targets = list(target_it)
        assert len(forecasts) == expected_items
        assert_alignment(forecasts, targets, args.prediction_length)

        agg_metrics, item_metrics = evaluator(
            iter(targets),
            iter(forecasts),
            num_series=expected_items,
        )
        assert_metric_keys(agg_metrics, item_metrics)
        if len(item_metrics) != expected_items:
            raise AssertionError(
                f"item metric row count mismatch: {len(item_metrics)} != {expected_items}"
            )

        # Cross-check the one-call wrapper on the same deterministic dataset.
        backtest_agg, backtest_items = backtest_metrics(
            test_dataset=dataset,
            predictor=predictor,
            evaluator=evaluator,
            num_samples=args.num_samples,
        )
        assert_metric_keys(backtest_agg, backtest_items)
        if not math.isclose(
            float(backtest_agg["MSE"]),
            float(agg_metrics["MSE"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise AssertionError("backtest_metrics MSE does not match direct Evaluator MSE")

    if args.item_metrics_csv is not None:
        args.item_metrics_csv.parent.mkdir(parents=True, exist_ok=True)
        item_metrics.to_csv(args.item_metrics_csv, index=False)

    if args.verbose:
        preview_columns = [
            column
            for column in ["item_id", "forecast_start", "MSE", "abs_error", "Coverage[0.5]"]
            if column in item_metrics.columns
        ]
        print(item_metrics[preview_columns].to_string(index=False))

    csv_note = f", item_metrics_csv={args.item_metrics_csv}" if args.item_metrics_csv else ""
    print(
        "OK gluonts evaluation smoke: "
        f"items={expected_items}, prediction_length={args.prediction_length}, "
        f"MSE={float(agg_metrics['MSE']):.6g}, ND={float(agg_metrics['ND']):.6g}"
        f"{csv_note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
