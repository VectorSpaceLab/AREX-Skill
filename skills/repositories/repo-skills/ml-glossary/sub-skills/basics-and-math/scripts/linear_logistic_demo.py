#!/usr/bin/env python3
"""Self-contained linear/logistic regression toy demos for ML Glossary.

This script replaces legacy educational snippets with Python 3, no external
datasets, and no NumPy dependency. It is for explanations and smoke examples,
not for production modeling.

Examples:
    python linear_logistic_demo.py --mode linear
    python linear_logistic_demo.py --mode logistic
"""

from __future__ import annotations

import argparse
import math
from typing import Iterable, Sequence


def linear_predict(x: float, weight: float, bias: float) -> float:
    return weight * x + bias


def mse(xs: Sequence[float], ys: Sequence[float], weight: float, bias: float) -> float:
    return sum((y - linear_predict(x, weight, bias)) ** 2 for x, y in zip(xs, ys)) / len(xs)


def linear_step(xs: Sequence[float], ys: Sequence[float], weight: float, bias: float, lr: float) -> tuple[float, float]:
    n = float(len(xs))
    d_weight = sum(-2 * x * (y - linear_predict(x, weight, bias)) for x, y in zip(xs, ys)) / n
    d_bias = sum(-2 * (y - linear_predict(x, weight, bias)) for x, y in zip(xs, ys)) / n
    return weight - lr * d_weight, bias - lr * d_bias


def sigmoid(z: float) -> float:
    # Stable enough for the tiny demo values used here.
    return 1.0 / (1.0 + math.exp(-z))


def logistic_probability(features: Sequence[float], weights: Sequence[float], bias: float) -> float:
    z = sum(x * w for x, w in zip(features, weights)) + bias
    return sigmoid(z)


def log_loss(rows: Sequence[Sequence[float]], labels: Sequence[int], weights: Sequence[float], bias: float) -> float:
    eps = 1e-12
    total = 0.0
    for row, label in zip(rows, labels):
        p = logistic_probability(row, weights, bias)
        p = min(max(p, eps), 1.0 - eps)
        total += -(label * math.log(p) + (1 - label) * math.log(1 - p))
    return total / len(rows)


def logistic_step(rows: Sequence[Sequence[float]], labels: Sequence[int], weights: list[float], bias: float, lr: float) -> tuple[list[float], float]:
    n = float(len(rows))
    gradients = [0.0 for _ in weights]
    bias_grad = 0.0
    for row, label in zip(rows, labels):
        p = logistic_probability(row, weights, bias)
        error = p - label
        for j, value in enumerate(row):
            gradients[j] += error * value
        bias_grad += error
    new_weights = [w - lr * (g / n) for w, g in zip(weights, gradients)]
    return new_weights, bias - lr * (bias_grad / n)


def run_linear() -> None:
    xs = [37.8, 39.3, 45.9, 41.3]
    ys = [22.1, 10.4, 18.3, 18.5]
    weight = 0.0
    bias = 0.0
    lr = 0.0005
    print("Linear regression toy: y_hat = weight * radio + bias")
    for iteration in range(0, 51):
        if iteration in {0, 1, 10, 50}:
            print(f"iter={iteration:02d} weight={weight:.4f} bias={bias:.4f} mse={mse(xs, ys, weight, bias):.4f}")
        weight, bias = linear_step(xs, ys, weight, bias, lr)
    print(f"prediction for radio=40: {linear_predict(40.0, weight, bias):.4f}")


def run_logistic() -> None:
    # Features are [hours_studied, hours_slept]; labels are pass/fail.
    rows = [[4.85, 9.63], [8.62, 3.23], [5.43, 8.23], [9.21, 6.34]]
    labels = [1, 0, 1, 0]
    weights = [0.0, 0.0]
    bias = 0.0
    lr = 0.05
    print("Logistic regression toy: probability = sigmoid(features · weights + bias)")
    for iteration in range(0, 101):
        if iteration in {0, 1, 10, 100}:
            print(f"iter={iteration:03d} weights={[round(w, 4) for w in weights]} bias={bias:.4f} log_loss={log_loss(rows, labels, weights, bias):.4f}")
        weights, bias = logistic_step(rows, labels, weights, bias, lr)
    sample = [6.0, 8.0]
    probability = logistic_probability(sample, weights, bias)
    print(f"sample={sample} pass_probability={probability:.4f} class={int(probability >= 0.5)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run small ML Glossary regression demos.")
    parser.add_argument("--mode", choices=["linear", "logistic"], default="linear")
    args = parser.parse_args()
    if args.mode == "linear":
        run_linear()
    else:
        run_logistic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
