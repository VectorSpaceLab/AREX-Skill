#!/usr/bin/env python3
"""Tiny self-contained DIN smoke for behavior-history sequence inputs."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Tuple

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny in-memory DeepCTR-Torch DIN training/prediction smoke "
            "with target item/category features, hist_* behavior sequences, "
            "shared embedding_name settings, and a seq_length column."
        )
    )
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs for the smoke run; default: 1.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size; default uses all 4 rows.")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, or auto; default: cpu.")
    parser.add_argument("--att-activation", default="Dice", help="DIN attention activation; default: Dice.")
    parser.add_argument(
        "--att-weight-normalization",
        dest="att_weight_normalization",
        action="store_true",
        default=True,
        help="Enable softmax normalization over valid history timesteps; enabled by default.",
    )
    parser.add_argument(
        "--no-att-weight-normalization",
        dest="att_weight_normalization",
        action="store_false",
        help="Disable attention weight normalization.",
    )
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


def make_tiny_din_data() -> Tuple[Dict[str, np.ndarray], np.ndarray, list, list]:
    from deepctr_torch.inputs import DenseFeat, SparseFeat, VarLenSparseFeat, get_feature_names

    maxlen = 4
    feature_columns = [
        SparseFeat("user_id", vocabulary_size=4, embedding_dim=4),
        SparseFeat("gender", vocabulary_size=3, embedding_dim=2),
        SparseFeat("item_id", vocabulary_size=5, embedding_dim=8),
        SparseFeat("cate_id", vocabulary_size=4, embedding_dim=4),
        DenseFeat("pay_score", 1),
        VarLenSparseFeat(
            SparseFeat("hist_item_id", vocabulary_size=5, embedding_dim=8, embedding_name="item_id"),
            maxlen=maxlen,
            length_name="seq_length",
        ),
        VarLenSparseFeat(
            SparseFeat("hist_cate_id", vocabulary_size=4, embedding_dim=4, embedding_name="cate_id"),
            maxlen=maxlen,
            length_name="seq_length",
        ),
    ]
    behavior_feature_list = ["item_id", "cate_id"]

    arrays: Dict[str, np.ndarray] = {
        "user_id": np.array([0, 1, 2, 3], dtype="int64"),
        "gender": np.array([0, 1, 2, 1], dtype="int64"),
        "item_id": np.array([1, 2, 3, 4], dtype="int64"),
        "cate_id": np.array([1, 2, 3, 1], dtype="int64"),
        "pay_score": np.array([0.1, 0.4, 0.2, 0.8], dtype="float32"),
        "hist_item_id": np.array(
            [
                [1, 2, 3, 0],
                [2, 1, 0, 0],
                [3, 4, 1, 2],
                [4, 3, 0, 0],
            ],
            dtype="int64",
        ),
        "hist_cate_id": np.array(
            [
                [1, 2, 3, 0],
                [2, 1, 0, 0],
                [3, 1, 2, 3],
                [1, 3, 0, 0],
            ],
            dtype="int64",
        ),
        "seq_length": np.array([3, 2, 4, 2], dtype="int64"),
    }
    labels = np.array([1, 0, 1, 0], dtype="float32")

    feature_names = get_feature_names(feature_columns)
    model_input = {name: arrays[name] for name in feature_names}
    return model_input, labels, feature_columns, behavior_feature_list


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
        from deepctr_torch.models import DIN
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "ERROR: cannot import deepctr_torch.models. Install deepctr-torch in the active Python environment."
        ) from exc

    torch.set_num_threads(args.torch_threads)
    device = resolve_device(args.device)
    model_input, labels, feature_columns, behavior_feature_list = make_tiny_din_data()

    model = DIN(
        feature_columns,
        behavior_feature_list,
        dnn_hidden_units=(16, 8),
        att_hidden_size=(8, 4),
        att_activation=args.att_activation,
        att_weight_normalization=args.att_weight_normalization,
        device=device,
    )
    model.compile("adagrad", "binary_crossentropy", metrics=["binary_crossentropy"])

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

    print("DIN sequence smoke passed")
    print(f"device={device} rows={labels.shape[0]} pred_shape={pred.shape} pred_mean={float(pred.mean()):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
