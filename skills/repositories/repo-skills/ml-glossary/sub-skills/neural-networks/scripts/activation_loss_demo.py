#!/usr/bin/env python3
"""Self-contained activation and loss calculations for ML Glossary.

This pure-Python helper demonstrates small values for ReLU, LeakyReLU, sigmoid,
tanh, softmax, MSE, MAE, and binary cross-entropy. It avoids framework and
original-checkout dependencies.

Example:
    python activation_loss_demo.py
"""

from __future__ import annotations

import argparse
import math
from typing import Sequence


def relu(z: float) -> float:
    return max(0.0, z)


def leaky_relu(z: float, alpha: float = 0.01) -> float:
    return z if z >= 0 else alpha * z


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def tanh(z: float) -> float:
    return math.tanh(z)


def softmax(values: Sequence[float]) -> list[float]:
    max_v = max(values)
    exps = [math.exp(v - max_v) for v in values]
    total = sum(exps)
    return [v / total for v in exps]


def mse(predictions: Sequence[float], targets: Sequence[float]) -> float:
    return sum((p - y) ** 2 for p, y in zip(predictions, targets)) / len(predictions)


def mae(predictions: Sequence[float], targets: Sequence[float]) -> float:
    return sum(abs(p - y) for p, y in zip(predictions, targets)) / len(predictions)


def binary_cross_entropy(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    eps = 1e-12
    total = 0.0
    for p, y in zip(probabilities, labels):
        p = min(max(p, eps), 1.0 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(probabilities)


def main() -> int:
    parser = argparse.ArgumentParser(description="Show ML Glossary activation and loss toy calculations.")
    parser.add_argument("--values", nargs="*", type=float, default=[-2.0, -0.5, 0.0, 0.5, 2.0])
    args = parser.parse_args()

    values = args.values
    print("Activations")
    print(f"input        = {values}")
    print(f"relu         = {[round(relu(v), 4) for v in values]}")
    print(f"leaky_relu   = {[round(leaky_relu(v), 4) for v in values]}")
    print(f"sigmoid      = {[round(sigmoid(v), 4) for v in values]}")
    print(f"tanh         = {[round(tanh(v), 4) for v in values]}")
    print(f"softmax      = {[round(v, 4) for v in softmax(values)]}")

    predictions = [0.9, 0.2, 0.4]
    targets = [1.0, 0.0, 1.0]
    probabilities = [0.9, 0.2, 0.4]
    labels = [1, 0, 1]
    print("\nLosses")
    print(f"predictions  = {predictions}")
    print(f"targets      = {targets}")
    print(f"mse          = {mse(predictions, targets):.4f}")
    print(f"mae          = {mae(predictions, targets):.4f}")
    print(f"binary_ce    = {binary_cross_entropy(probabilities, labels):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
