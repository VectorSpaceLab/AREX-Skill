#!/usr/bin/env python3
"""Tiny PyTorch Forecasting API-v2 data smoke helper.

Creates a synthetic pandas DataFrame, builds the beta API-v2 TimeSeries D1
object, and optionally builds/sets up an API-v2 datamodule. It never trains a
model. Run with --help to inspect options without importing PyTorch Forecasting.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create synthetic API-v2 data and optionally build a PyTorch "
            "Forecasting v2 datamodule without training any model."
        )
    )
    parser.add_argument("--n-series", type=int, default=6, help="number of groups")
    parser.add_argument(
        "--n-timesteps", type=int, default=48, help="timesteps per group"
    )
    parser.add_argument(
        "--datamodule",
        choices=["none", "encoder-decoder", "tslib"],
        default="none",
        help="optional D2 datamodule to instantiate",
    )
    parser.add_argument(
        "--setup-stage",
        choices=["none", "fit", "test", "predict", "all"],
        default="none",
        help="optional datamodule setup stage; use all to run fit/test/predict setup",
    )
    parser.add_argument(
        "--max-encoder-length",
        type=int,
        default=12,
        help="encoder length for EncoderDecoderTimeSeriesDataModule",
    )
    parser.add_argument(
        "--max-prediction-length",
        type=int,
        default=4,
        help="prediction length for EncoderDecoderTimeSeriesDataModule",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=12,
        help="context length for TslibDataModule",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=4,
        help="prediction length for TslibDataModule",
    )
    parser.add_argument("--batch-size", type=int, default=2, help="D2 batch size")
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable summary JSON"
    )
    return parser


def make_dataframe(n_series: int, n_timesteps: int):
    import numpy as np
    import pandas as pd

    rows: list[dict[str, Any]] = []
    for series_id in range(n_series):
        baseline = series_id * 0.25
        for time_idx in range(n_timesteps):
            seasonal = np.sin(time_idx / 4.0)
            rows.append(
                {
                    "series_id": series_id,
                    "time_idx": time_idx,
                    "y": float(baseline + seasonal + 0.01 * time_idx),
                    "x": float(time_idx) / max(n_timesteps - 1, 1),
                    "future_known_feature": float((time_idx + 1) % 7),
                    "category": int(series_id % 3),
                    "static_feature": float(series_id),
                    "static_feature_cat": int(series_id % 2),
                }
            )
    return pd.DataFrame(rows)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "shape"):
        return {"shape": list(value.shape), "type": type(value).__name__}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def summarize_batch(batch: Any) -> Any:
    if isinstance(batch, dict):
        return {k: summarize_batch(v) for k, v in batch.items()}
    if isinstance(batch, (list, tuple)):
        return [summarize_batch(v) for v in batch]
    if hasattr(batch, "shape"):
        return {"type": type(batch).__name__, "shape": list(batch.shape)}
    return {"type": type(batch).__name__, "repr": repr(batch)[:120]}


def import_v2_objects():
    try:
        from pytorch_forecasting.data.data_module import (  # noqa: PLC0415
            EncoderDecoderTimeSeriesDataModule,
            TslibDataModule,
        )
        from pytorch_forecasting.data.timeseries import TimeSeries  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        raise RuntimeError(
            "Could not import PyTorch Forecasting API-v2 objects. Activate or "
            "install an environment with pytorch-forecasting core dependencies "
            "(including torch, lightning, pandas, and scikit-learn)."
        ) from exc
    return TimeSeries, EncoderDecoderTimeSeriesDataModule, TslibDataModule


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.n_series < 1 or args.n_timesteps < 1:
        parser.error("--n-series and --n-timesteps must be positive")

    max_required = max(
        args.max_encoder_length + args.max_prediction_length,
        args.context_length + args.prediction_length,
    )
    if args.n_timesteps < max_required:
        parser.error(
            "--n-timesteps is shorter than the requested history+horizon "
            f"window ({args.n_timesteps} < {max_required})"
        )

    try:
        TimeSeries, EncoderDecoderDM, TslibDM = import_v2_objects()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    df = make_dataframe(args.n_series, args.n_timesteps)
    dataset = TimeSeries(
        data=df,
        time="time_idx",
        target="y",
        group=["series_id"],
        num=["x", "future_known_feature", "static_feature"],
        cat=["category", "static_feature_cat"],
        known=["future_known_feature"],
        unknown=["x", "category"],
        static=["static_feature", "static_feature_cat"],
    )

    summary: dict[str, Any] = {
        "dataframe_shape": list(df.shape),
        "n_series": args.n_series,
        "n_timestamps_per_series": args.n_timesteps,
        "dataset_length": len(dataset),
        "dataset_metadata": dataset.get_metadata(),
    }

    data_module = None
    if args.datamodule == "encoder-decoder":
        data_module = EncoderDecoderDM(
            time_series_dataset=dataset,
            max_encoder_length=args.max_encoder_length,
            max_prediction_length=args.max_prediction_length,
            batch_size=args.batch_size,
            num_workers=0,
            train_val_test_split=(0.7, 0.15, 0.15),
            target_normalizer=None,
        )
    elif args.datamodule == "tslib":
        data_module = TslibDM(
            time_series_dataset=dataset,
            context_length=args.context_length,
            prediction_length=args.prediction_length,
            batch_size=args.batch_size,
            num_workers=0,
            train_val_test_split=(0.7, 0.15, 0.15),
            target_normalizer=None,
            add_relative_time_idx=True,
        )

    if data_module is not None:
        summary["datamodule_type"] = type(data_module).__name__
        summary["datamodule_metadata"] = data_module.metadata

        stages = []
        if args.setup_stage == "all":
            stages = ["fit", "test", "predict"]
        elif args.setup_stage != "none":
            stages = [args.setup_stage]

        setup_summary: dict[str, Any] = {}
        for stage in stages:
            data_module.setup(stage=stage)
            stage_info: dict[str, Any] = {}
            if stage == "fit":
                loader = data_module.train_dataloader()
                stage_info["train_batch"] = summarize_batch(next(iter(loader)))
                if getattr(data_module, "val_dataset", None) is not None:
                    stage_info["val_windows"] = len(data_module.val_dataset)
            elif stage == "test":
                loader = data_module.test_dataloader()
                stage_info["test_batch"] = summarize_batch(next(iter(loader)))
            elif stage == "predict":
                loader = data_module.predict_dataloader()
                stage_info["predict_batch"] = summarize_batch(next(iter(loader)))
            setup_summary[stage] = stage_info
        if setup_summary:
            summary["setup"] = setup_summary

    safe = json_safe(summary)
    if args.json:
        print(json.dumps(safe, indent=2, sort_keys=True))
    else:
        print("API-v2 data smoke summary")
        print(json.dumps(safe, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
