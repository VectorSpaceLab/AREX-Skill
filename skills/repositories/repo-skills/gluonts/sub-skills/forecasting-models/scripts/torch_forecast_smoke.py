#!/usr/bin/env python3
"""Bounded GluonTS PyTorch estimator construction/train smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

SKIP = 77


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny PandasDataset and construct a bounded GluonTS "
            "PyTorch estimator. By default this is construction-only; pass "
            "--train for a one-epoch train/predict smoke."
        )
    )
    parser.add_argument(
        "--estimator",
        choices=["deepar", "simple-feedforward"],
        default="deepar",
        help="Estimator to construct (default: deepar).",
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Run a tiny one-epoch train/predict smoke instead of construction only.",
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Frequency string for the synthetic PandasDataset (default: D).",
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=2,
        help="Forecast horizon (default: 2).",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=4,
        help="Context length for tiny estimators (default: 4).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Training/prediction batch size (default: 2).",
    )
    parser.add_argument(
        "--num-batches-per-epoch",
        type=int,
        default=1,
        help="Number of training batches per epoch (default: 1).",
    )
    parser.add_argument(
        "--accelerator",
        choices=["cpu", "gpu", "auto"],
        default="cpu",
        help="Lightning accelerator setting (default: cpu).",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=5,
        help="Number of forecast samples to request after --train (default: 5).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional dataset and forecast details.",
    )
    return parser


def make_dataset(freq: str):
    from gluonts.dataset.pandas import PandasDataset

    periods = 48
    index = pd.date_range("2024-01-01", periods=periods, freq=freq)
    frames = {}
    for item, offset in [("item_0", 0.0), ("item_1", 3.0)]:
        steps = np.arange(periods, dtype=np.float32)
        target = 10.0 + offset + np.sin(steps / 4.0) + 0.05 * steps
        frames[item] = pd.DataFrame({"target": target.astype(np.float32)}, index=index)
    return PandasDataset(frames, target="target", freq=freq)


def trainer_kwargs(args: argparse.Namespace, tmpdir: str | None, training: bool) -> dict:
    kwargs = {
        "max_epochs": 1,
        "logger": False,
        "enable_model_summary": False,
        "accelerator": args.accelerator,
        "devices": 1,
        "num_sanity_val_steps": 0,
    }
    if training:
        # GluonTS' PyTorch estimator internals add a ModelCheckpoint callback.
        # Keep any checkpoint files temporary rather than passing
        # enable_checkpointing=False, which conflicts with that callback.
        if tmpdir is not None:
            kwargs["default_root_dir"] = tmpdir
    else:
        # Construction-only checks can prove a disabled-checkpointing trainer
        # config without instantiating GluonTS' internal checkpoint callback.
        kwargs["enable_checkpointing"] = False
    return kwargs


def make_estimator(args: argparse.Namespace, tmpdir: str | None, training: bool):
    from gluonts.torch import DeepAREstimator, SimpleFeedForwardEstimator

    common = {
        "prediction_length": args.prediction_length,
        "context_length": args.context_length,
        "batch_size": args.batch_size,
        "num_batches_per_epoch": args.num_batches_per_epoch,
        "trainer_kwargs": trainer_kwargs(args, tmpdir, training=training),
    }
    if args.estimator == "deepar":
        return DeepAREstimator(freq=args.freq, **common)
    if args.estimator == "simple-feedforward":
        return SimpleFeedForwardEstimator(**common)
    raise AssertionError(f"unhandled estimator {args.estimator}")


def validate_args(args: argparse.Namespace) -> int | None:
    for name in ["prediction_length", "context_length", "batch_size", "num_batches_per_epoch", "num_samples"]:
        if getattr(args, name.replace("-", "_"), None) is not None and getattr(args, name.replace("-", "_")) <= 0:
            print(f"ERROR: --{name} must be positive", file=sys.stderr)
            return 2
    if args.context_length < args.prediction_length:
        print(
            "ERROR: --context-length should be at least --prediction-length for this smoke",
            file=sys.stderr,
        )
        return 2
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validation_error = validate_args(args)
    if validation_error is not None:
        return validation_error

    try:
        import torch
        import lightning.pytorch as pl
        from gluonts.torch import DeepAREstimator as _DeepAREstimator  # noqa: F401
    except ImportError as exc:
        print(f"SKIP: GluonTS PyTorch/Lightning extra is unavailable: {exc}", file=sys.stderr)
        return SKIP

    if args.accelerator == "gpu" and not torch.cuda.is_available():
        print("SKIP: --accelerator gpu requested but torch.cuda.is_available() is false", file=sys.stderr)
        return SKIP

    torch.manual_seed(7)
    try:
        pl.seed_everything(7, workers=True, verbose=False)
    except TypeError:
        pl.seed_everything(7, workers=True)

    dataset = make_dataset(args.freq)
    first_entry = next(iter(dataset))

    if not args.train:
        estimator = make_estimator(args, tmpdir=None, training=False)
        result = {
            "status": "ok",
            "mode": "construction-only",
            "estimator": type(estimator).__name__,
            "prediction_length": args.prediction_length,
            "context_length": args.context_length,
            "trainer_kwargs": estimator.trainer_kwargs,
            "first_target_length": int(len(first_entry["target"])),
        }
        if args.verbose:
            result["first_start"] = str(first_entry["start"])
            result["torch_version"] = torch.__version__
            result["cuda_available"] = bool(torch.cuda.is_available())
        print(json.dumps(result, sort_keys=True, default=str))
        return 0

    with TemporaryDirectory(prefix="gluonts-torch-smoke-") as tmp:
        estimator = make_estimator(args, tmpdir=tmp, training=True)
        try:
            predictor = estimator.train(dataset)
            forecasts = list(predictor.predict(dataset, num_samples=args.num_samples))
        except Exception as exc:  # noqa: BLE001 - report smoke failure clearly.
            print(f"ERROR: tiny PyTorch train/predict smoke failed: {exc}", file=sys.stderr)
            return 2

        if not forecasts:
            print("ERROR: predictor emitted no forecasts", file=sys.stderr)
            return 2

        means = [np.asarray(f.mean, dtype=float) for f in forecasts]
        for idx, mean in enumerate(means):
            if mean.shape[0] != args.prediction_length:
                print(
                    f"ERROR: forecast {idx} mean shape {mean.shape} does not match prediction length",
                    file=sys.stderr,
                )
                return 2
            if not np.isfinite(mean).all():
                print(f"ERROR: forecast {idx} mean contains non-finite values", file=sys.stderr)
                return 2

        result = {
            "status": "ok",
            "mode": "train-predict",
            "estimator": type(estimator).__name__,
            "predictor": type(predictor).__name__,
            "num_forecasts": len(forecasts),
            "prediction_length": args.prediction_length,
            "forecast_mean_shapes": [list(mean.shape) for mean in means],
            "accelerator": args.accelerator,
        }
        if args.verbose:
            result["forecast_means"] = [mean.tolist() for mean in means]
            result["temporary_training_root_name"] = Path(tmp).name
            result["cuda_available"] = bool(torch.cuda.is_available())

    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
