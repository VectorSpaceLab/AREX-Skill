#!/usr/bin/env python3
"""Tiny deterministic CNN smoke for ML-From-Scratch deep_learning.

The script validates channels-first Conv2D input, Flatten-to-Dense shape flow,
one-hot CrossEntropy labels, a one-epoch fit, and prediction shape using a small
local sklearn digits slice. It performs no plotting, network access, credential
access, or destructive writes.
"""

from __future__ import annotations

import argparse
import json
import os

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
from sklearn import datasets

from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import Activation, Conv2D, Dense, Flatten
from mlfromscratch.deep_learning.loss_functions import CrossEntropy
from mlfromscratch.deep_learning.optimizers import Adam
from mlfromscratch.utils import to_categorical


def build_model(learning_rate: float) -> NeuralNetwork:
    """Build a minimal channels-first CNN classifier for 8x8 grayscale images."""
    model = NeuralNetwork(optimizer=Adam(learning_rate=learning_rate), loss=CrossEntropy)
    # Keep smoke output stable; the framework normally prints a progressbar.
    model.progressbar = lambda iterable: iterable
    model.add(Conv2D(n_filters=2, filter_shape=(3, 3), input_shape=(1, 8, 8), padding="same", stride=1))
    model.add(Activation("relu"))
    model.add(Flatten())
    model.add(Dense(n_units=10))
    model.add(Activation("softmax"))
    return model


def load_digits_slice(sample_count: int) -> tuple[np.ndarray, np.ndarray]:
    digits = datasets.load_digits()
    n_samples = min(sample_count, digits.data.shape[0])
    X = digits.data[:n_samples].astype(float) / 16.0
    X = X.reshape((-1, 1, 8, 8))
    y_int = digits.target[:n_samples].astype(int)
    y = to_categorical(y_int, n_col=10)
    return X, y


def run(args: argparse.Namespace) -> dict[str, object]:
    np.random.seed(args.seed)
    X, y = load_digits_slice(args.samples)

    model = build_model(args.learning_rate)
    if args.summary:
        model.summary(name="Tiny CNN Smoke")

    train_loss, val_loss = model.fit(
        X,
        y,
        n_epochs=args.epochs,
        batch_size=args.batch_size,
    )
    probs = model.predict(X)

    if probs.shape != y.shape:
        raise AssertionError(f"prediction shape {probs.shape} != target shape {y.shape}")
    if not np.all(np.isfinite(probs)):
        raise AssertionError("prediction contains non-finite values")
    if not np.allclose(probs.sum(axis=1), 1.0, atol=1e-6):
        raise AssertionError("softmax rows do not sum to one")
    if not train_loss or not np.isfinite(train_loss[-1]):
        raise AssertionError("training loss is missing or non-finite")

    return {
        "smoke": "cnn",
        "ok": True,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "samples": int(X.shape[0]),
        "loss_last": round(float(train_loss[-1]), 8),
        "validation_loss_count": len(val_loss),
        "input_shape": list(X.shape),
        "prediction_shape": list(probs.shape),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a one-epoch channels-first CNN smoke for ML-From-Scratch."
    )
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to run; default: 1.")
    parser.add_argument("--batch-size", type=int, default=5, help="Mini-batch size; default: 5.")
    parser.add_argument("--samples", type=int, default=20, help="Number of sklearn digits samples to use; default: 20.")
    parser.add_argument("--learning-rate", type=float, default=0.005, help="Adam learning rate; default: 0.005.")
    parser.add_argument("--seed", type=int, default=11, help="NumPy random seed; default: 11.")
    parser.add_argument("--summary", action="store_true", help="Print the model summary before fitting.")
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    if args.samples < 1:
        parser.error("--samples must be >= 1")
    return args


def main() -> None:
    result = run(parse_args())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
