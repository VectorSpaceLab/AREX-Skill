#!/usr/bin/env python3
"""Tiny NeuralProphet CPU save/load smoke test.

Generates synthetic daily data, fits a minimal CPU model, saves it as a .np
artifact, reloads with map_location="cpu", predicts, and prints the forecast
``yhat`` columns. By default all writes happen in temporary directories. Provide
--output-path only when a persistent model artifact is desired.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def build_tiny_daily_frame(n_rows: int, seed: int) -> pd.DataFrame:
    """Create a deterministic daily `ds`, `y` dataframe."""
    rng = np.random.default_rng(seed)
    ds = pd.date_range("2021-01-01", periods=n_rows, freq="D")
    trend = np.linspace(0.0, 1.0, n_rows)
    seasonal = 0.15 * np.sin(np.arange(n_rows) / 3.0)
    noise = rng.normal(0.0, 0.01, n_rows)
    y = 1.0 + trend + seasonal + noise
    return pd.DataFrame({"ds": ds, "y": y})


def yhat_columns(columns: Iterable[str]) -> list[str]:
    return [column for column in columns if column.startswith("yhat")]


def remove_no_progress_restore_conflict(model: object) -> None:
    """Avoid a NeuralProphet 1.0.0rc10 no-progress save/load conflict.

    A fit with progress disabled can leave ``enable_progress_bar=False`` in the
    stored Lightning trainer configuration. During ``load(..., map_location=...)``
    NeuralProphet restores a trainer and may add its progress-bar callback,
    which conflicts with that stale flag. Removing the flag before save keeps
    this smoke test non-interactive while preserving fitted forecaster state.
    """
    config_train = getattr(model, "config_train", None)
    trainer_config = getattr(config_train, "pl_trainer_config", None)
    if isinstance(trainer_config, dict):
        trainer_config.pop("enable_progress_bar", None)


def run_smoke(args: argparse.Namespace) -> int:
    try:
        from neuralprophet import NeuralProphet, __version__, load, save, set_log_level, set_random_seed
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        print(
            "Unable to import NeuralProphet or one of its runtime dependencies "
            f"({missing}). Run this smoke test in an environment where the "
            "neuralprophet package is installed and importable.",
            file=sys.stderr,
        )
        return 3

    if args.output_path is not None:
        model_path = Path(args.output_path)
        if model_path.exists() and not args.overwrite:
            print(f"Refusing to overwrite existing output path: {model_path}", file=sys.stderr)
            return 2
        model_path.parent.mkdir(parents=True, exist_ok=True)

    set_log_level(args.log_level, include_handlers=True)
    set_random_seed(args.seed)
    df = build_tiny_daily_frame(args.n_rows, args.seed)

    with tempfile.TemporaryDirectory(prefix="neuralprophet-smoke-") as tmpdir:
        if args.output_path is None:
            model_path = Path(tmpdir) / "tiny_model.np"

        model = NeuralProphet(
            n_changepoints=0,
            n_forecasts=1,
            n_lags=0,
            epochs=args.epochs,
            batch_size=min(args.batch_size, len(df)),
            learning_rate=args.learning_rate,
            collect_metrics=False,
            accelerator="cpu",
        )
        model.fit(
            df,
            freq="D",
            minimal=True,
            progress=None,
            checkpointing=False,
            deterministic=True,
            trainer_config={"default_root_dir": tmpdir},
        )

        future = model.make_future_dataframe(df, periods=args.periods)
        forecast_before = model.predict(future)
        remove_no_progress_restore_conflict(model)

        save(model, model_path)
        loaded = load(model_path, map_location="cpu")
        forecast_after = loaded.predict(future)

        cols = yhat_columns(forecast_after.columns)
        if not cols:
            print("No yhat* columns found after load/predict.", file=sys.stderr)
            return 1

        pd.testing.assert_frame_equal(
            forecast_before[cols].reset_index(drop=True),
            forecast_after[cols].reset_index(drop=True),
            check_exact=False,
            rtol=1e-6,
            atol=1e-6,
        )

        print(f"neuralprophet_version={__version__}")
        print(f"rows={len(df)} periods={args.periods} epochs={args.epochs}")
        print("yhat_columns=" + ",".join(cols))
        if args.output_path is not None:
            print(f"saved_model={model_path}")
        else:
            print("saved_model=temporary")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NeuralProphet CPU save/load smoke test")
    parser.add_argument("--n-rows", type=int, default=48, help="number of generated daily observations")
    parser.add_argument("--periods", type=int, default=3, help="future periods to predict after fit")
    parser.add_argument("--epochs", type=int, default=2, help="training epochs for the tiny fit")
    parser.add_argument("--batch-size", type=int, default=16, help="training batch size")
    parser.add_argument("--learning-rate", type=float, default=0.1, help="explicit learning rate to avoid LR search")
    parser.add_argument("--seed", type=int, default=42, help="random seed applied immediately before fit")
    parser.add_argument(
        "--log-level",
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="NeuralProphet log level for the smoke run",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="optional persistent .np save path; omitted means temporary file only",
    )
    parser.add_argument("--overwrite", action="store_true", help="allow overwriting --output-path if it exists")
    args = parser.parse_args()
    if args.n_rows < 12:
        parser.error("--n-rows must be at least 12 for a meaningful tiny fit")
    if args.periods < 1:
        parser.error("--periods must be at least 1")
    if args.epochs < 1:
        parser.error("--epochs must be at least 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.learning_rate <= 0:
        parser.error("--learning-rate must be positive")
    return args


def main() -> int:
    return run_smoke(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
