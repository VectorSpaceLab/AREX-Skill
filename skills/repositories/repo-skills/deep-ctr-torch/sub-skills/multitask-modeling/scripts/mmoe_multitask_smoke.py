#!/usr/bin/env python3
"""Tiny DeepCTR-Torch MMOE multi-task smoke test.

The script builds inline feature columns and two binary labels, trains for a
small number of epochs, predicts, and asserts prediction shape (n_samples, 2).
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Tuple

import numpy as np
import torch

try:
    from deepctr_torch.inputs import DenseFeat, SparseFeat, get_feature_names
    from deepctr_torch.models import MMOE
except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
    raise SystemExit(
        "ERROR: cannot import deepctr_torch. Install deepctr-torch in the active Python environment."
    ) from exc


def build_inline_data(sample_size: int, seed: int) -> Tuple[Dict[str, np.ndarray], np.ndarray, list]:
    """Create deterministic tiny data with two binary labels."""
    if sample_size < 4:
        raise ValueError("sample_size must be at least 4 so both binary labels contain both classes")

    rng = np.random.default_rng(seed)
    user_id = np.arange(sample_size, dtype="int32") % 5
    item_id = (np.arange(sample_size, dtype="int32") * 2 + 1) % 7
    duration = np.linspace(0.05, 0.95, sample_size, dtype="float32")

    # Two related but non-identical binary tasks, similar to a finish/like setup.
    finish = ((user_id + item_id) % 2).astype("float32")
    like = ((duration > 0.45) | (item_id % 3 == 0)).astype("float32")

    # Ensure both columns contain both classes even for small sample counts.
    finish[0], finish[1] = 0.0, 1.0
    like[0], like[1] = 1.0, 0.0

    model_input = {
        "user_id": user_id,
        "item_id": item_id,
        "duration": duration,
    }
    labels = np.stack([finish, like], axis=1).astype("float32")
    feature_columns = [
        SparseFeat("user_id", vocabulary_size=5, embedding_dim=4),
        SparseFeat("item_id", vocabulary_size=7, embedding_dim=4),
        DenseFeat("duration", 1),
    ]

    # Reorder the dictionary to the exact feature order used by the model.
    feature_names = get_feature_names(feature_columns)
    model_input = {name: model_input[name] for name in feature_names}
    return model_input, labels, feature_columns


def resolve_device(requested: str) -> str:
    if requested == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"requested {requested!r}, but torch.cuda.is_available() is False")
    return requested


def run_smoke(args: argparse.Namespace) -> np.ndarray:
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = resolve_device(args.device)

    model_input, labels, feature_columns = build_inline_data(args.samples, args.seed)
    task_names = ["finish", "like"]
    task_types = ["binary", "binary"]

    assert labels.shape == (args.samples, 2), labels.shape

    model = MMOE(
        feature_columns,
        num_experts=args.num_experts,
        expert_dnn_hidden_units=(8, 4),
        gate_dnn_hidden_units=(4,),
        tower_dnn_hidden_units=(4,),
        task_types=task_types,
        task_names=task_names,
        seed=args.seed,
        device=device,
    )
    model.compile(
        args.optimizer,
        loss=["binary_crossentropy", "binary_crossentropy"],
        metrics=[] if args.no_metrics else ["binary_crossentropy"],
    )
    history = model.fit(
        model_input,
        labels,
        batch_size=args.batch_size,
        epochs=args.epochs,
        verbose=0 if args.quiet else 2,
        shuffle=False,
    )
    if "loss" not in history.history:
        raise AssertionError("training history did not contain a loss entry")

    predictions = model.predict(model_input, batch_size=args.batch_size)
    expected_shape = (args.samples, 2)
    if predictions.shape != expected_shape:
        raise AssertionError(f"expected prediction shape {expected_shape}, got {predictions.shape}")
    if not np.isfinite(predictions).all():
        raise AssertionError("predictions contain non-finite values")
    return predictions


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny DeepCTR-Torch MMOE on inline two-task binary data and "
            "assert predictions have shape (n_samples, 2)."
        )
    )
    parser.add_argument("--samples", type=int, default=12, help="number of inline rows to generate (default: 12)")
    parser.add_argument("--epochs", type=int, default=1, help="training epochs (default: 1)")
    parser.add_argument("--batch-size", type=int, default=4, help="fit/predict batch size (default: 4)")
    parser.add_argument("--num-experts", type=int, default=2, help="MMOE expert count; must be >1 (default: 2)")
    parser.add_argument("--optimizer", default="adam", choices=["adam", "adagrad", "sgd", "rmsprop"], help="optimizer string (default: adam)")
    parser.add_argument("--device", default="cpu", help="device string: cpu, cuda:0, or auto (default: cpu)")
    parser.add_argument("--seed", type=int, default=2024, help="random seed (default: 2024)")
    parser.add_argument("--no-metrics", action="store_true", help="compile without aggregate training metrics")
    parser.add_argument("--quiet", action="store_true", help="suppress epoch logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    predictions = run_smoke(args)
    print(f"OK: MMOE predictions shape={predictions.shape}; first_row={predictions[0].round(6).tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
