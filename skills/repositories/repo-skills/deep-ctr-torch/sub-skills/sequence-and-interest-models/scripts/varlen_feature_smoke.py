#!/usr/bin/env python3
"""Tiny self-contained VarLenSparseFeat smoke with inline multi-value sequences."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Tuple

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny in-memory DeepCTR-Torch smoke for a pooled multi-value "
            "VarLenSparseFeat. The script does not read sample files."
        )
    )
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for the smoke run; default: 1.")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size; default: 3.")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, or auto; default: cpu.")
    parser.add_argument("--combiner", default="mean", choices=["sum", "mean", "max"], help="VarLenSparseFeat pooling combiner.")
    parser.add_argument("--skip-fit", action="store_true", help="Only compile and predict; skip the fit call.")
    parser.add_argument("--verbose", type=int, default=0, choices=[0, 1, 2], help="DeepCTR-Torch fit verbosity.")
    parser.add_argument("--torch-threads", type=int, default=1, help="Torch intra-op threads for this tiny smoke.")
    return parser


def resolve_device(requested: str) -> str:
    import torch

    if requested == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"Requested {requested!r}, but CUDA is not available.")
    return requested


def make_tiny_varlen_data(combiner: str) -> Tuple[Dict[str, np.ndarray], np.ndarray, list, list]:
    from deepctr_torch.inputs import SparseFeat, VarLenSparseFeat, get_feature_names

    maxlen = 3
    fixed_columns = [
        SparseFeat("movie_id", vocabulary_size=6, embedding_dim=4),
        SparseFeat("user_id", vocabulary_size=5, embedding_dim=4),
        SparseFeat("gender", vocabulary_size=3, embedding_dim=4),
    ]
    varlen_columns = [
        VarLenSparseFeat(
            SparseFeat("genres", vocabulary_size=7, embedding_dim=4),
            maxlen=maxlen,
            combiner=combiner,
        )
    ]
    linear_feature_columns = fixed_columns + varlen_columns
    dnn_feature_columns = fixed_columns + varlen_columns

    arrays: Dict[str, np.ndarray] = {
        "movie_id": np.array([1, 2, 3, 4, 5, 1], dtype="int64"),
        "user_id": np.array([1, 2, 1, 3, 4, 2], dtype="int64"),
        "gender": np.array([0, 1, 0, 1, 2, 1], dtype="int64"),
        # 0 is padding because this VarLenSparseFeat has no length_name.
        "genres": np.array(
            [
                [1, 2, 0],
                [3, 0, 0],
                [1, 4, 5],
                [2, 5, 6],
                [6, 0, 0],
                [1, 3, 4],
            ],
            dtype="int64",
        ),
    }
    labels = np.array([1, 0, 1, 0, 1, 0], dtype="float32")

    feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
    model_input = {name: arrays[name] for name in feature_names}
    return model_input, labels, linear_feature_columns, dnn_feature_columns


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.epochs < 0:
        raise ValueError("--epochs must be non-negative")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive")
    if args.torch_threads <= 0:
        raise ValueError("--torch-threads must be positive")

    import torch
    try:
        from deepctr_torch.models import DeepFM
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "ERROR: cannot import deepctr_torch.models. Install deepctr-torch in the active Python environment."
        ) from exc

    torch.set_num_threads(args.torch_threads)
    device = resolve_device(args.device)
    model_input, labels, linear_feature_columns, dnn_feature_columns = make_tiny_varlen_data(args.combiner)

    model = DeepFM(
        linear_feature_columns,
        dnn_feature_columns,
        dnn_hidden_units=(16, 8),
        task="binary",
        device=device,
    )
    model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])

    if not args.skip_fit and args.epochs:
        model.fit(
            model_input,
            labels,
            batch_size=args.batch_size,
            epochs=args.epochs,
            verbose=args.verbose,
            validation_split=0.0,
            shuffle=False,
        )

    pred = model.predict(model_input, batch_size=args.batch_size)
    expected_shape = (labels.shape[0], 1)
    if pred.shape != expected_shape:
        raise AssertionError(f"Expected prediction shape {expected_shape}, got {pred.shape}")

    print("VarLenSparseFeat smoke passed")
    print(
        f"device={device} combiner={args.combiner} rows={labels.shape[0]} "
        f"pred_shape={pred.shape} pred_mean={float(pred.mean()):.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
