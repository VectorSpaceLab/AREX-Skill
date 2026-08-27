#!/usr/bin/env python3
"""Tiny PyTorch Forecasting v1 model smoke test.

Default behavior builds deterministic pandas data, creates a target-only
TimeSeriesDataSet, and runs Baseline prediction on CPU. It intentionally does
not train by default. Optional --model nbeats instantiates a very small NBeats
model and predicts one batch; add --train-nbeats for a one-epoch/limited-batch
CPU fit.
"""

from __future__ import annotations

import argparse
import math
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build tiny synthetic time-series data and run a PyTorch Forecasting "
            "v1 Baseline prediction by default."
        )
    )
    parser.add_argument(
        "--model",
        choices=["baseline", "nbeats"],
        default="baseline",
        help="Model smoke to run. Default: baseline (no training).",
    )
    parser.add_argument("--series", type=int, default=4, help="Number of series.")
    parser.add_argument(
        "--timesteps", type=int, default=28, help="Timesteps per series."
    )
    parser.add_argument(
        "--encoder-length", type=int, default=8, help="Fixed encoder length."
    )
    parser.add_argument(
        "--prediction-length", type=int, default=3, help="Fixed prediction length."
    )
    parser.add_argument("--batch-size", type=int, default=4, help="Dataloader batch size.")
    parser.add_argument(
        "--num-workers", type=int, default=0, help="Dataloader worker count."
    )
    parser.add_argument(
        "--train-nbeats",
        action="store_true",
        help=(
            "For --model nbeats only: run a bounded one-epoch CPU fit before "
            "prediction. Off by default."
        ),
    )
    parser.add_argument(
        "--limit-train-batches",
        type=int,
        default=1,
        help="Maximum training batches for --train-nbeats.",
    )
    parser.add_argument("--seed", type=int, default=13, help="Torch random seed.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.series < 1:
        raise SystemExit("--series must be >= 1")
    if args.encoder_length < 1:
        raise SystemExit("--encoder-length must be >= 1")
    if args.prediction_length < 1:
        raise SystemExit("--prediction-length must be >= 1")
    minimum = args.encoder_length + 2 * args.prediction_length + 2
    if args.timesteps < minimum:
        raise SystemExit(
            "--timesteps is too small for the requested windows; need at least "
            f"{minimum}"
        )
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")
    if args.num_workers < 0:
        raise SystemExit("--num-workers must be >= 0")
    if args.limit_train_batches < 1:
        raise SystemExit("--limit-train-batches must be >= 1")
    if args.train_nbeats and args.model != "nbeats":
        raise SystemExit("--train-nbeats is only valid with --model nbeats")


def make_frame(args: argparse.Namespace) -> Any:
    import pandas as pd

    rows: list[dict[str, Any]] = []
    for series_idx in range(args.series):
        for time_idx in range(args.timesteps):
            seasonal = math.sin(2.0 * math.pi * time_idx / 7.0)
            trend = 0.05 * time_idx
            offset = float(series_idx)
            rows.append(
                {
                    "series": f"s{series_idx}",
                    "time_idx": time_idx,
                    "value": offset + trend + seasonal,
                }
            )
    return pd.DataFrame(rows)


def make_datasets(args: argparse.Namespace, data: Any) -> tuple[Any, Any, Any, Any]:
    from pytorch_forecasting import TimeSeriesDataSet
    from pytorch_forecasting.data import NaNLabelEncoder

    training_cutoff = int(data["time_idx"].max()) - args.prediction_length
    training = TimeSeriesDataSet(
        data[data.time_idx <= training_cutoff],
        time_idx="time_idx",
        target="value",
        group_ids=["series"],
        categorical_encoders={"series": NaNLabelEncoder().fit(data.series)},
        min_encoder_length=args.encoder_length,
        max_encoder_length=args.encoder_length,
        min_prediction_length=args.prediction_length,
        max_prediction_length=args.prediction_length,
        time_varying_unknown_reals=["value"],
        randomize_length=None,
        add_relative_time_idx=False,
        add_target_scales=False,
    )
    validation = TimeSeriesDataSet.from_dataset(
        training,
        data,
        min_prediction_idx=training_cutoff + 1,
        stop_randomization=True,
    )
    train_loader = training.to_dataloader(
        train=True,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    val_loader = validation.to_dataloader(
        train=False,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    return training, validation, train_loader, val_loader


def summarize_prediction(result: Any) -> None:
    output = getattr(result, "output", result)
    shape = getattr(output, "shape", None)
    if shape is not None:
        print(f"prediction_shape={tuple(shape)}")
    elif isinstance(output, (list, tuple)):
        print("prediction_shapes=" + repr([getattr(x, "shape", None) for x in output]))
    else:
        print(f"prediction_type={type(output).__name__}")

    index = getattr(result, "index", None)
    if index is not None:
        print(f"index_rows={len(index)}")
        print(index.head().to_string(index=False))

    decoder_lengths = getattr(result, "decoder_lengths", None)
    if decoder_lengths is not None:
        print(f"decoder_lengths={decoder_lengths.tolist()}")


def run_baseline(args: argparse.Namespace, val_loader: Any) -> None:
    from pytorch_forecasting import Baseline

    model = Baseline()
    result = model.predict(
        val_loader,
        fast_dev_run=True,
        return_index=True,
        return_decoder_lengths=True,
        trainer_kwargs={"accelerator": "cpu", "devices": 1},
    )
    print("model=baseline")
    summarize_prediction(result)


def run_nbeats(args: argparse.Namespace, training: Any, train_loader: Any, val_loader: Any) -> None:
    from pytorch_forecasting import NBeats

    model = NBeats.from_dataset(
        training,
        learning_rate=3e-2,
        stack_types=["generic"],
        num_blocks=[1],
        num_block_layers=[1],
        widths=[8],
        sharing=[False],
        expansion_coefficient_lengths=[4],
        dropout=0.0,
        log_interval=-1,
        log_val_interval=-1,
        reduce_on_plateau_patience=1000,
    )
    print("model=nbeats")
    print(f"parameters={model.size()}")

    if args.train_nbeats:
        import lightning.pytorch as pl

        trainer = pl.Trainer(
            max_epochs=1,
            accelerator="cpu",
            devices=1,
            gradient_clip_val=0.1,
            limit_train_batches=args.limit_train_batches,
            limit_val_batches=1,
            num_sanity_val_steps=0,
            enable_checkpointing=False,
            logger=False,
            enable_model_summary=False,
            enable_progress_bar=False,
        )
        trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
        print("trained_nbeats=true")
    else:
        print("trained_nbeats=false")

    result = model.predict(
        val_loader,
        fast_dev_run=True,
        return_index=True,
        return_decoder_lengths=True,
        trainer_kwargs={
            "accelerator": "cpu",
            "devices": 1,
            "logger": False,
            "enable_checkpointing": False,
            "enable_progress_bar": False,
        },
    )
    summarize_prediction(result)


def main() -> None:
    args = parse_args()
    validate_args(args)

    try:
        data = make_frame(args)
        training, _validation, train_loader, val_loader = make_datasets(args, data)

        import torch

        torch.manual_seed(args.seed)
        print(
            "data="
            f"rows:{len(data)} series:{args.series} timesteps:{args.timesteps} "
            f"encoder:{args.encoder_length} prediction:{args.prediction_length}"
        )

        if args.model == "baseline":
            run_baseline(args, val_loader)
        elif args.model == "nbeats":
            run_nbeats(args, training, train_loader, val_loader)
        else:  # argparse prevents this branch
            raise SystemExit(f"unknown model: {args.model}")
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        raise SystemExit(
            "Missing runtime dependency "
            f"{missing!r}. Run this smoke in an environment with "
            "pytorch-forecasting 1.8.0, torch, lightning, pandas, and "
            "scikit-learn installed."
        ) from exc


if __name__ == "__main__":
    main()
