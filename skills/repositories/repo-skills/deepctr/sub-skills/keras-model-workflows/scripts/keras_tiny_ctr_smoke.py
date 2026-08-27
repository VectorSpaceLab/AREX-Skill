#!/usr/bin/env python3
"""Tiny synthetic DeepCTR Keras smoke test.

This script is adapted from the DeepCTR Criteo classification workflow, but it
uses generated in-memory data instead of external files. It checks the Keras
path only: feature columns, DeepFM construction, compile/fit/evaluate/predict,
and full-model save/load with deepctr.layers.custom_objects.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from typing import Dict

import numpy as np


def build_synthetic_inputs(n_samples: int, seed: int) -> tuple[dict, np.ndarray, list, list, list]:
    rng = np.random.default_rng(seed)

    from deepctr.feature_column import DenseFeat, SparseFeat, get_feature_names

    sparse_features = ["user_id", "ad_id", "site_id"]
    dense_features = ["price", "hour"]
    vocab_sizes = {"user_id": 17, "ad_id": 23, "site_id": 7}

    feature_columns = [
        SparseFeat(name, vocabulary_size=vocab_sizes[name], embedding_dim=4)
        for name in sparse_features
    ] + [DenseFeat(name, 1) for name in dense_features]

    feature_names = get_feature_names(feature_columns)

    model_input: Dict[str, np.ndarray] = {
        "user_id": rng.integers(0, vocab_sizes["user_id"], size=(n_samples, 1), dtype=np.int32),
        "ad_id": rng.integers(0, vocab_sizes["ad_id"], size=(n_samples, 1), dtype=np.int32),
        "site_id": rng.integers(0, vocab_sizes["site_id"], size=(n_samples, 1), dtype=np.int32),
        "price": rng.random((n_samples, 1), dtype=np.float32),
        "hour": rng.random((n_samples, 1), dtype=np.float32),
    }

    # Make a deterministic but non-trivial binary target from both sparse and dense signals.
    logit = (
        0.08 * model_input["user_id"].reshape(-1)
        + 0.05 * model_input["ad_id"].reshape(-1)
        - 0.03 * model_input["site_id"].reshape(-1)
        + 1.2 * model_input["price"].reshape(-1)
        - 0.7 * model_input["hour"].reshape(-1)
    )
    threshold = np.median(logit)
    y = (logit > threshold).astype("float32").reshape(-1, 1)

    missing = sorted(set(feature_names) - set(model_input))
    if missing:
        raise AssertionError(f"Missing model input keys: {missing}")
    sizes = {name: np.asarray(model_input[name]).shape[0] for name in feature_names}
    if len(set(sizes.values())) != 1:
        raise AssertionError(f"Input arrays have inconsistent row counts: {sizes}")

    return model_input, y, feature_columns, feature_columns, feature_names


def run_smoke(args: argparse.Namespace) -> None:
    # Keep the smoke script CPU-friendly. This does not forbid GPU use when TensorFlow selects it.
    if args.force_cpu:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

    import tensorflow as tf
    import deepctr
    from tensorflow.keras.models import load_model, save_model

    from deepctr.layers import custom_objects
    from deepctr.models import DeepFM

    np.random.seed(args.seed)
    try:
        tf.random.set_seed(args.seed)
    except AttributeError:
        pass

    print(f"tensorflow={tf.__version__}")
    print(f"deepctr={getattr(deepctr, '__version__', 'unknown')}")
    print(f"gpu_devices={len(tf.config.list_physical_devices('GPU')) if hasattr(tf, 'config') else 'unknown'}")

    model_input, y, linear_feature_columns, dnn_feature_columns, feature_names = build_synthetic_inputs(
        args.samples, args.seed
    )

    model = DeepFM(
        linear_feature_columns,
        dnn_feature_columns,
        dnn_hidden_units=(16, 8),
        dnn_dropout=0.0,
        task="binary",
    )
    model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])

    history = model.fit(
        model_input,
        y,
        batch_size=args.batch_size,
        epochs=args.epochs,
        verbose=args.verbose,
        validation_split=0.25,
        shuffle=False,
    )
    if "loss" not in history.history:
        raise AssertionError(f"Expected loss in history, got keys {sorted(history.history)}")

    evaluation = model.evaluate(model_input, y, batch_size=args.batch_size, verbose=0)
    predictions = model.predict(model_input, batch_size=args.batch_size, verbose=0)

    if predictions.shape != (args.samples, 1):
        raise AssertionError(f"Unexpected prediction shape: {predictions.shape}")
    if not np.all(np.isfinite(predictions)):
        raise AssertionError("Predictions contain NaN or infinity")
    if predictions.min() < -1e-6 or predictions.max() > 1.0 + 1e-6:
        raise AssertionError(
            f"Binary DeepFM predictions should be probabilities, got range "
            f"[{predictions.min()}, {predictions.max()}]"
        )

    fd, model_path = tempfile.mkstemp(prefix="deepctr_tiny_", suffix=".h5")
    os.close(fd)
    try:
        save_model(model, model_path)
        restored = load_model(model_path, custom_objects=custom_objects)
        restored_predictions = restored.predict(model_input, batch_size=args.batch_size, verbose=0)
    finally:
        try:
            os.remove(model_path)
        except OSError:
            pass

    if restored_predictions.shape != predictions.shape:
        raise AssertionError(
            f"Restored prediction shape {restored_predictions.shape} != original {predictions.shape}"
        )

    labels = model.metrics_names
    values = evaluation if isinstance(evaluation, list) else [evaluation]
    metrics = dict(zip(labels, [float(v) for v in values]))

    print(f"feature_names={feature_names}")
    print(f"history_keys={sorted(history.history)}")
    print(f"evaluation={metrics}")
    print(f"prediction_shape={predictions.shape}")
    print(f"prediction_range=({float(predictions.min()):.6f}, {float(predictions.max()):.6f})")
    print("save_load=ok")
    print("smoke=ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny synthetic DeepCTR DeepFM Keras smoke test.")
    parser.add_argument("--samples", type=int, default=32, help="Number of synthetic rows to generate.")
    parser.add_argument("--batch-size", type=int, default=8, help="Keras batch size.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of tiny training epochs.")
    parser.add_argument("--seed", type=int, default=2024, help="Random seed for NumPy and TensorFlow.")
    parser.add_argument("--verbose", type=int, default=0, choices=[0, 1, 2], help="Keras fit verbosity.")
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Hide GPUs from TensorFlow for this smoke process. CPU is sufficient for this script.",
    )
    args = parser.parse_args()
    if args.samples < 8:
        parser.error("--samples must be at least 8 so validation_split and batch checks are meaningful")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    return args


if __name__ == "__main__":
    run_smoke(parse_args())
