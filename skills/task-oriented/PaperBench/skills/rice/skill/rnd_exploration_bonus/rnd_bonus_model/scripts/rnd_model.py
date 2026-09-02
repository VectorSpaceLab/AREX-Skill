#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random


def make_matrix(rows: int, cols: int, seed: int, scale: float = 0.2) -> list[list[float]]:
    rng = random.Random(seed)
    return [[rng.uniform(-scale, scale) for _ in range(cols)] for _ in range(rows)]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(weight * value for weight, value in zip(row, vector)) for row in matrix]


def mse_errors(target: list[list[float]], predictor: list[list[float]], observations: list[list[float]]) -> list[float]:
    errors = []
    for obs in observations:
        t = matvec(target, obs)
        p = matvec(predictor, obs)
        errors.append(sum((pv - tv) ** 2 for pv, tv in zip(p, t)) / len(t))
    return errors


def mean_loss(target: list[list[float]], predictor: list[list[float]], observations: list[list[float]]) -> float:
    errors = mse_errors(target, predictor, observations)
    return sum(errors) / len(errors)


def train_predictor(target: list[list[float]], predictor: list[list[float]], observations: list[list[float]], lr: float = 0.05, steps: int = 100) -> dict:
    before_predictor = [row[:] for row in predictor]
    before_target = [row[:] for row in target]
    loss_before = mean_loss(target, predictor, observations)
    out_dim = len(target)
    for _ in range(steps):
        grads = [[0.0 for _ in row] for row in predictor]
        for obs in observations:
            t = matvec(target, obs)
            p = matvec(predictor, obs)
            for i in range(out_dim):
                coeff = 2.0 * (p[i] - t[i]) / (len(observations) * out_dim)
                for j, value in enumerate(obs):
                    grads[i][j] += coeff * value
        for i in range(len(predictor)):
            for j in range(len(predictor[i])):
                predictor[i][j] -= lr * grads[i][j]
    loss_after = mean_loss(target, predictor, observations)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": before_predictor,
        "params_after": [row[:] for row in predictor],
        "target_before": before_target,
        "target_after": [row[:] for row in target],
        "target_unchanged": before_target == target,
        "predictor_changed": before_predictor != predictor,
    }


def _self_test() -> None:
    observations = [[1.0, 0.0], [1.0, 0.2], [0.9, 0.1]]
    target = make_matrix(3, 2, seed=7)
    predictor = make_matrix(3, 2, seed=11)
    trace = train_predictor(target, predictor, observations, lr=0.2, steps=80)
    assert trace["loss_after"] < trace["loss_before"]
    assert trace["target_unchanged"] is True
    assert trace["predictor_changed"] is True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    payload = json.load(__import__("sys").stdin)
    target = payload.get("target") or make_matrix(payload["out_dim"], len(payload["observations"][0]), payload.get("target_seed", 7))
    predictor = payload.get("predictor") or make_matrix(len(target), len(payload["observations"][0]), payload.get("predictor_seed", 11))
    trace = train_predictor(target, predictor, payload["observations"], payload.get("lr", 0.05), payload.get("steps", 100))
    trace["errors_after"] = mse_errors(target, predictor, payload["observations"])
    print(json.dumps(trace, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
