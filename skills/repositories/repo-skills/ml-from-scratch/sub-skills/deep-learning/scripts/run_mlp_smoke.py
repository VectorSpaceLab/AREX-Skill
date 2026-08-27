#!/usr/bin/env python3
"""Tiny deterministic MLP smoke for ML-From-Scratch deep_learning.

The script validates importability, first-layer input_shape handling, one-hot
CrossEntropy labels, a one-epoch fit, and prediction shape. It performs no
plotting, network access, credential access, or destructive writes.
"""

from __future__ import annotations

import argparse
import json
import os

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.deep_learning.layers import Activation, Dense
from mlfromscratch.deep_learning.loss_functions import CrossEntropy
from mlfromscratch.deep_learning.optimizers import Adam
from mlfromscratch.utils import to_categorical


def build_model(learning_rate: float) -> NeuralNetwork:
    """Build a minimal two-class MLP with an explicit first input shape."""
    model = NeuralNetwork(optimizer=Adam(learning_rate=learning_rate), loss=CrossEntropy)
    # Keep smoke output stable; the framework normally prints a progressbar.
    model.progressbar = lambda iterable: iterable
    model.add(Dense(n_units=4, input_shape=(2,)))
    model.add(Activation("relu"))
    model.add(Dense(n_units=2))
    model.add(Activation("softmax"))
    return model


def run(args: argparse.Namespace) -> dict[str, object]:
    np.random.seed(args.seed)

    X = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ],
        dtype=float,
    )
    y_int = np.asarray([0, 1, 1, 0], dtype=int)
    y = to_categorical(y_int, n_col=2)

    model = build_model(args.learning_rate)
    if args.summary:
        model.summary(name="Tiny MLP Smoke")

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

    y_pred = np.argmax(probs, axis=1)
    accuracy = float(np.mean(y_pred == y_int))

    return {
        "smoke": "mlp",
        "ok": True,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "loss_last": round(float(train_loss[-1]), 8),
        "validation_loss_count": len(val_loss),
        "prediction_shape": list(probs.shape),
        "accuracy": round(accuracy, 8),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a one-epoch XOR-style MLP smoke for ML-From-Scratch."
    )
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to run; default: 1.")
    parser.add_argument("--batch-size", type=int, default=2, help="Mini-batch size; default: 2.")
    parser.add_argument("--learning-rate", type=float, default=0.01, help="Adam learning rate; default: 0.01.")
    parser.add_argument("--seed", type=int, default=7, help="NumPy random seed; default: 7.")
    parser.add_argument("--summary", action="store_true", help="Print the model summary before fitting.")
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    return args


def main() -> None:
    result = run(parse_args())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
