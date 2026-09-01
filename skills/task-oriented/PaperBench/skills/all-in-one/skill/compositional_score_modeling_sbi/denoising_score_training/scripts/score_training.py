"""Small deterministic denoising score utilities for F-NPSE recovery."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


Vector = list[float]
Matrix = list[Vector]


def as_matrix(value: object) -> Matrix:
    rows = [[float(item) for item in row] for row in value]  # type: ignore[union-attr]
    if not rows or not rows[0]:
        raise ValueError("matrix must be non-empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix rows must have equal length")
    return rows


def zeros(rows: int, cols: int) -> Matrix:
    return [[0.0 for _ in range(cols)] for _ in range(rows)]


def denoising_target(theta_clean: Matrix, theta_noisy: Matrix, gamma: float) -> Matrix:
    """Return the Gaussian denoising score target used by score matching."""
    if not 0.0 < gamma < 1.0:
        raise ValueError("gamma must be in (0, 1)")
    sqrt_gamma = math.sqrt(gamma)
    denom = 1.0 - gamma
    return [
        [(sqrt_gamma * clean - noisy) / denom for clean, noisy in zip(clean_row, noisy_row)]
        for clean_row, noisy_row in zip(theta_clean, theta_noisy)
    ]


def make_noisy(theta_clean: Matrix, gamma: float, rng: random.Random) -> tuple[Matrix, Matrix]:
    sqrt_gamma = math.sqrt(gamma)
    sqrt_noise = math.sqrt(1.0 - gamma)
    epsilon: Matrix = []
    theta_noisy: Matrix = []
    for row in theta_clean:
        eps_row = [rng.gauss(0.0, 1.0) for _ in row]
        epsilon.append(eps_row)
        theta_noisy.append([sqrt_gamma * value + sqrt_noise * eps for value, eps in zip(row, eps_row)])
    return theta_noisy, epsilon


def featurize(theta_noisy: Matrix, condition: Matrix, gamma: float) -> Matrix:
    if len(theta_noisy) != len(condition):
        raise ValueError("theta_noisy and condition must have the same row count")
    features: Matrix = []
    for theta_row, cond_row in zip(theta_noisy, condition):
        if len(theta_row) != len(cond_row):
            raise ValueError("theta_noisy and condition rows must have the same width")
        features.append([*theta_row, *cond_row, float(gamma), 1.0])
    return features


def predict(features: Matrix, weights: Matrix) -> Matrix:
    outputs: Matrix = []
    for row in features:
        outputs.append([
            sum(row[i] * weights[i][j] for i in range(len(row)))
            for j in range(len(weights[0]))
        ])
    return outputs


def mse_loss(features: Matrix, targets: Matrix, weights: Matrix) -> float:
    preds = predict(features, weights)
    total = 0.0
    count = 0
    for pred_row, target_row in zip(preds, targets):
        for pred, target in zip(pred_row, target_row):
            total += (pred - target) ** 2
            count += 1
    return total / max(count, 1)


def gradient(features: Matrix, targets: Matrix, weights: Matrix) -> Matrix:
    preds = predict(features, weights)
    grad = zeros(len(weights), len(weights[0]))
    scale = 2.0 / max(len(features) * len(weights[0]), 1)
    for feature_row, pred_row, target_row in zip(features, preds, targets):
        for out_idx, (pred, target) in enumerate(zip(pred_row, target_row)):
            residual = pred - target
            for feat_idx, feat in enumerate(feature_row):
                grad[feat_idx][out_idx] += scale * feat * residual
    return grad


def matrix_subtract_scaled(weights: Matrix, grad: Matrix, scale: float) -> Matrix:
    return [
        [value - scale * grad_value for value, grad_value in zip(row, grad_row)]
        for row, grad_row in zip(weights, grad)
    ]


def matrix_norm(matrix: Matrix) -> float:
    return math.sqrt(sum(value * value for row in matrix for value in row))


def matrices_differ(a: Matrix, b: Matrix) -> bool:
    return any(abs(x - y) > 1e-12 for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b))


def train_one_step(
    theta_clean: Matrix,
    condition: Matrix,
    gamma: float,
    weights: Matrix | None = None,
    learning_rate: float = 0.05,
    seed: int = 0,
) -> dict:
    theta_clean = as_matrix(theta_clean)
    condition = as_matrix(condition)
    rng = random.Random(seed)
    theta_noisy, epsilon = make_noisy(theta_clean, gamma, rng)
    targets = denoising_target(theta_clean, theta_noisy, gamma)
    features = featurize(theta_noisy, condition, gamma)
    if weights is None:
        weights = zeros(len(features[0]), len(theta_clean[0]))
    else:
        weights = as_matrix(weights)
    before = [row[:] for row in weights]
    loss_before = mse_loss(features, targets, before)
    grad = gradient(features, targets, before)
    after = matrix_subtract_scaled(before, grad, learning_rate)
    loss_after = mse_loss(features, targets, after)
    return {
        "gamma": float(gamma),
        "learning_rate": float(learning_rate),
        "loss_before": float(loss_before),
        "loss_after": float(loss_after),
        "params_before": before,
        "params_after": after,
        "gradient_norm": float(matrix_norm(grad)),
        "optimizer_state_changed": matrices_differ(before, after),
        "theta_noisy": theta_noisy,
        "epsilon": epsilon,
        "target_scores": targets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta-clean", required=True, help="JSON array of clean theta rows.")
    parser.add_argument("--condition", required=True, help="JSON array of condition rows.")
    parser.add_argument("--gamma", type=float, default=0.7)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    result = train_one_step(
        json.loads(args.theta_clean),
        json.loads(args.condition),
        gamma=args.gamma,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
