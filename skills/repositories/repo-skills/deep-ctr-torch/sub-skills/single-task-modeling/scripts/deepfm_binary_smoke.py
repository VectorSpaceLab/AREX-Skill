#!/usr/bin/env python3
"""Self-contained DeepCTR-Torch DeepFM binary smoke test.

The script builds tiny inline CTR-like data, label-encodes sparse features,
scales dense features, trains one epoch by default, predicts, and reports basic
metrics. It does not read any external sample files.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def build_inline_data():
    """Return a tiny balanced CTR-like table with sparse and dense features."""
    import pandas as pd

    return pd.DataFrame(
        {
            "C1": ["u0", "u1", "u2", "u3", "u0", "u1", "u2", "u3", "u4", "u5", "u4", "u5"],
            "C2": ["ad0", "ad0", "ad1", "ad1", "ad2", "ad2", "ad3", "ad3", "ad0", "ad1", "ad2", "ad3"],
            "C3": ["morning", "evening", "morning", "evening", "night", "night", "morning", "evening", "night", "morning", "evening", "night"],
            "I1": [0.10, 0.20, 0.35, 0.70, 0.15, 0.80, 0.55, 0.25, 0.40, 0.60, 0.05, 0.95],
            "I2": [3.0, 1.0, 2.0, 4.0, 2.5, 4.5, 1.5, 3.5, 2.2, 3.8, 1.2, 4.8],
            "label": [0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1],
        }
    )


def resolve_device(requested: str, torch_module) -> str:
    if requested == "auto":
        return "cuda:0" if torch_module.cuda.is_available() else "cpu"
    if requested.startswith("cuda") and not torch_module.cuda.is_available():
        raise RuntimeError(f"Requested {requested!r}, but torch.cuda.is_available() is False")
    return requested


def parse_gpus(raw: Optional[str], device: str) -> Optional[List[int]]:
    if not raw:
        return None
    gpus = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not gpus:
        return None
    if str(gpus[0]) not in device:
        raise ValueError("gpus[0] must match device, e.g. device='cuda:0' with --gpus 0,1")
    return gpus


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny inline DeepCTR-Torch DeepFM binary classification smoke test."
    )
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs. Default: 1")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size. Default: 4")
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device string: cpu, cuda:0, or auto. Default: cpu",
    )
    parser.add_argument(
        "--gpus",
        default=None,
        help="Optional comma-separated DataParallel GPU ids; first id must match --device.",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.0,
        help="Optional fit(validation_split=...). Default 0.0 avoids tiny-split AUC issues.",
    )
    parser.add_argument(
        "--compile-auc",
        action="store_true",
        help="Include auc in model.compile metrics. Use only when every metric batch/split has both classes.",
    )
    parser.add_argument("--seed", type=int, default=2020, help="Random seed for split/model. Default: 2020")
    args = parser.parse_args()

    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    if not 0.0 <= args.validation_split < 1.0:
        parser.error("--validation-split must be in [0.0, 1.0)")

    import numpy as np
    import torch
    from sklearn.metrics import log_loss, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler

    from deepctr_torch.inputs import DenseFeat, SparseFeat, get_feature_names
    from deepctr_torch.models import DeepFM

    data = build_inline_data()
    sparse_features = ["C1", "C2", "C3"]
    dense_features = ["I1", "I2"]
    target = ["label"]

    data[sparse_features] = data[sparse_features].fillna("-1")
    data[dense_features] = data[dense_features].fillna(0.0)

    for feat in sparse_features:
        encoder = LabelEncoder()
        data[feat] = encoder.fit_transform(data[feat])

    scaler = MinMaxScaler(feature_range=(0, 1))
    data[dense_features] = scaler.fit_transform(data[dense_features])

    fixlen_feature_columns = [
        SparseFeat(feat, vocabulary_size=int(data[feat].max()) + 1, embedding_dim=4)
        for feat in sparse_features
    ] + [DenseFeat(feat, 1) for feat in dense_features]
    linear_feature_columns = fixlen_feature_columns
    dnn_feature_columns = fixlen_feature_columns
    feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)

    train, test = train_test_split(
        data,
        test_size=0.25,
        random_state=args.seed,
        stratify=data[target[0]],
    )
    train_model_input = {name: train[name].values for name in feature_names}
    test_model_input = {name: test[name].values for name in feature_names}

    device = resolve_device(args.device, torch)
    gpus = parse_gpus(args.gpus, device)

    model = DeepFM(
        linear_feature_columns=linear_feature_columns,
        dnn_feature_columns=dnn_feature_columns,
        task="binary",
        l2_reg_embedding=1e-5,
        seed=args.seed,
        device=device,
        gpus=gpus,
    )
    metrics = ["binary_crossentropy"]
    if args.compile_auc:
        metrics.append("auc")
    model.compile("adagrad", "binary_crossentropy", metrics=metrics)

    history = model.fit(
        train_model_input,
        train[target].values,
        batch_size=args.batch_size,
        epochs=args.epochs,
        verbose=0,
        validation_split=args.validation_split,
    )
    pred = model.predict(test_model_input, batch_size=args.batch_size).reshape(-1)
    y_true = test[target[0]].values.reshape(-1)

    if pred.shape[0] != y_true.shape[0]:
        raise AssertionError(f"Prediction length {pred.shape[0]} != target length {y_true.shape[0]}")

    print(f"device={device}")
    print(f"history_keys={sorted(history.history.keys())}")
    print(f"prediction_shape={(pred.shape[0], 1)}")
    print(f"test_logloss={log_loss(y_true, np.clip(pred, 1e-7, 1 - 1e-7)):.6f}")
    if np.unique(y_true).size == 2:
        print(f"test_auc={roc_auc_score(y_true, pred):.6f}")
    else:
        print("test_auc=skipped-single-class-test")
    print("deepfm_binary_smoke=passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ImportError as exc:
        print(f"ImportError: {exc}", file=sys.stderr)
        print("Install deepctr-torch runtime dependencies, including requests if deepctr_torch import fails.", file=sys.stderr)
        raise
