#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import List, Sequence, Tuple

Matrix = List[List[float]]


def validate_matrix(name: str, value: Sequence[Sequence[float]]) -> Matrix:
    if not value:
        raise ValueError(f"{name} must be non-empty")
    rows: Matrix = []
    width = None
    for row in value:
        if not row:
            raise ValueError(f"{name} rows must be non-empty")
        converted = [float(item) for item in row]
        if any(not math.isfinite(item) for item in converted):
            raise ValueError(f"{name} contains non-finite values")
        if width is None:
            width = len(converted)
        elif len(converted) != width:
            raise ValueError(f"{name} must be rectangular")
        rows.append(converted)
    return rows


def matmul(left: Matrix, right: Matrix) -> Matrix:
    cols = list(zip(*right))
    return [[sum(a * b for a, b in zip(row, col)) for col in cols] for row in left]


def transpose(matrix: Matrix) -> Matrix:
    return [list(col) for col in zip(*matrix)]


def normalize_rows(matrix: Matrix, eps: float = 1e-12) -> Matrix:
    normalized = []
    for row in matrix:
        norm = math.sqrt(sum(value * value for value in row))
        normalized.append([value / max(norm, eps) for value in row])
    return normalized


def identity_weights(input_dim: int, embed_dim: int) -> Matrix:
    return [[1.0 if row == col % input_dim else 0.0 for col in range(embed_dim)] for row in range(input_dim)]


def compute_logits(tau: Sequence[Sequence[float]], skills: Sequence[Sequence[float]], query_weights: Sequence[Sequence[float]], key_weights: Sequence[Sequence[float]], temperature: float = 0.5) -> Matrix:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    tau_m = validate_matrix("tau", tau)
    skills_m = validate_matrix("skills", skills)
    query_w = validate_matrix("query_weights", query_weights)
    key_w = validate_matrix("key_weights", key_weights)
    if len(tau_m) != len(skills_m) or len(tau_m) < 2:
        raise ValueError("tau and skills must share batch size of at least 2")
    if len(query_w) != len(skills_m[0]):
        raise ValueError("query_weights input dimension must match skills")
    if len(key_w) != len(tau_m[0]):
        raise ValueError("key_weights input dimension must match tau")
    query = normalize_rows(matmul(skills_m, query_w))
    key = normalize_rows(matmul(tau_m, key_w))
    return [[sum(a * b for a, b in zip(query_row, key_row)) / temperature for key_row in key] for query_row in query]


def cross_entropy_from_logits(logits: Matrix) -> float:
    losses = []
    for index, row in enumerate(logits):
        max_logit = max(row)
        denom = sum(math.exp(value - max_logit) for value in row)
        losses.append(-(row[index] - max_logit - math.log(denom)))
    return sum(losses) / len(losses)


def positive_logit_margin(logits: Matrix) -> float:
    diagonal = [row[index] for index, row in enumerate(logits)]
    off_diag = [value for i, row in enumerate(logits) for j, value in enumerate(row) if i != j]
    return sum(diagonal) / len(diagonal) - sum(off_diag) / len(off_diag)


def evaluate_cic_loss(tau: Sequence[Sequence[float]], skills: Sequence[Sequence[float]], query_weights: Sequence[Sequence[float]], key_weights: Sequence[Sequence[float]], temperature: float = 0.5) -> dict:
    logits = compute_logits(tau, skills, query_weights, key_weights, temperature)
    return {
        "loss": cross_entropy_from_logits(logits),
        "logits": logits,
        "positive_logit_margin": positive_logit_margin(logits),
    }


def _flatten(weights: Matrix) -> List[float]:
    return [value for row in weights for value in row]


def _unflatten(values: Sequence[float], rows: int, cols: int) -> Matrix:
    return [list(values[row * cols:(row + 1) * cols]) for row in range(rows)]


def finite_difference_update(tau: Sequence[Sequence[float]], skills: Sequence[Sequence[float]], query_weights: Matrix, key_weights: Matrix, temperature: float = 0.5, learning_rate: float = 0.2, epsilon: float = 1e-4) -> dict:
    q_rows, q_cols = len(query_weights), len(query_weights[0])
    k_rows, k_cols = len(key_weights), len(key_weights[0])
    flat = _flatten(query_weights) + _flatten(key_weights)

    def loss_for(values: Sequence[float]) -> float:
        query = _unflatten(values[: q_rows * q_cols], q_rows, q_cols)
        key = _unflatten(values[q_rows * q_cols :], k_rows, k_cols)
        return evaluate_cic_loss(tau, skills, query, key, temperature)["loss"]

    before = loss_for(flat)
    grads = []
    for index in range(len(flat)):
        plus = list(flat)
        minus = list(flat)
        plus[index] += epsilon
        minus[index] -= epsilon
        grads.append((loss_for(plus) - loss_for(minus)) / (2.0 * epsilon))
    updated = [value - learning_rate * grad for value, grad in zip(flat, grads)]
    query_after = _unflatten(updated[: q_rows * q_cols], q_rows, q_cols)
    key_after = _unflatten(updated[q_rows * q_cols :], k_rows, k_cols)
    after_eval = evaluate_cic_loss(tau, skills, query_after, key_after, temperature)
    before_eval = evaluate_cic_loss(tau, skills, query_weights, key_weights, temperature)
    return {
        "loss_before": before,
        "loss_after": after_eval["loss"],
        "margin_before": before_eval["positive_logit_margin"],
        "margin_after": after_eval["positive_logit_margin"],
        "params_before": {"query_weights": query_weights, "key_weights": key_weights},
        "params_after": {"query_weights": query_after, "key_weights": key_after},
        "optimizer_state_changed": updated != flat,
        "logits_before": before_eval["logits"],
        "logits_after": after_eval["logits"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a tiny CIC contrastive loss demo.")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if not args.demo:
        parser.error("Use --demo for CLI output or import functions from this module.")
    tau = [[1, 0, 1.2, 0.1], [0, 1, 0.2, 1.1], [1, 1, 1.3, 1.2]]
    skills = [[1, 0], [0, 1], [1, 1]]
    query_w = identity_weights(2, 2)
    key_w = [[1, 0], [0, 1], [1, 0], [0, 1]]
    print(json.dumps(finite_difference_update(tau, skills, query_w, key_w), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
