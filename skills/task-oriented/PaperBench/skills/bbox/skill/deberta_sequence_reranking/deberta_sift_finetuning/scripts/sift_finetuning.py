#!/usr/bin/env python3
"""Small deterministic SiFT-style fine-tuning helpers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def normalize_vector(values: list[float], epsilon: float = 1e-12) -> list[float]:
    norm = math.sqrt(sum(float(value) ** 2 for value in values))
    if norm < epsilon:
        return [0.0 for _ in values]
    return [float(value) / norm for value in values]


def perturb_normalized(values: list[float], scale: float = 0.05) -> list[float]:
    normalized = normalize_vector(values)
    signs = [1.0 if index % 2 == 0 else -1.0 for index, _ in enumerate(normalized)]
    return [value + scale * sign for value, sign in zip(normalized, signs)]


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def logistic_loss(score: float, target: float) -> float:
    probability = min(max(sigmoid(score), 1e-12), 1.0 - 1e-12)
    return -(target * math.log(probability) + (1.0 - target) * math.log(1.0 - probability))


def train_step(
    features: list[float],
    params: dict[str, float],
    target: float = 1.0,
    learning_rate: float = 0.1,
    perturbation_scale: float = 0.05,
) -> dict:
    clean = normalize_vector(features)
    perturbed = perturb_normalized(features, perturbation_scale)
    weights = [float(params.get(f"w{i}", 0.0)) for i in range(len(clean))]
    bias = float(params.get("bias", 0.0))
    score_before = sum(weight * value for weight, value in zip(weights, perturbed)) + bias
    loss_before = logistic_loss(score_before, target)
    probability = sigmoid(score_before)
    error = probability - target
    updated = dict(params)
    for i, value in enumerate(perturbed):
        key = f"w{i}"
        updated[key] = float(params.get(key, 0.0)) - learning_rate * error * value
    updated["bias"] = bias - learning_rate * error
    updated_weights = [float(updated.get(f"w{i}", 0.0)) for i in range(len(clean))]
    score_after = sum(weight * value for weight, value in zip(updated_weights, perturbed)) + updated["bias"]
    loss_after = logistic_loss(score_after, target)
    return {
        "normalized_features": clean,
        "perturbed_features": perturbed,
        "score_before": score_before,
        "score_after": score_after,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": dict(params),
        "params_after": updated,
        "optimizer_state_changed": dict(params) != updated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-json", required=True)
    parser.add_argument("--params-json", required=True)
    parser.add_argument("--target", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--perturbation-scale", type=float, default=0.05)
    args = parser.parse_args()
    features = json.loads(Path(args.features_json).read_text(encoding="utf-8"))
    params = json.loads(Path(args.params_json).read_text(encoding="utf-8"))
    result = train_step(features, params, args.target, args.learning_rate, args.perturbation_scale)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
