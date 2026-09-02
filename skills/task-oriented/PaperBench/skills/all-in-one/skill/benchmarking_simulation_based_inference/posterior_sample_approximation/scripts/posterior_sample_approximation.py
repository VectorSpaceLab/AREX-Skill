#!/usr/bin/env python3
"""Fit a tiny affine posterior approximation from simulator pairs."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, data: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def predict(params: dict, x: list[float]) -> list[float]:
    weights = params["weights"]
    bias = params["bias"]
    return [dot(row, x) + b for row, b in zip(weights, bias)]


def mse(params: dict, xs: list[list[float]], thetas: list[list[float]]) -> float:
    total = 0.0
    count = 0
    for x, theta in zip(xs, thetas):
        pred = predict(params, x)
        for p, t in zip(pred, theta):
            total += (p - t) ** 2
            count += 1
    return total / max(count, 1)


def fit_affine_posterior(
    simulations: dict,
    observation: list[float],
    learning_rate: float,
    steps: int,
    sample_count: int,
    sample_variance: float,
    seed: int,
) -> dict:
    xs = [[float(v) for v in row] for row in simulations["x"]]
    thetas = [[float(v) for v in row] for row in simulations["theta"]]
    if not xs or not thetas:
        raise ValueError("simulation pairs must be non-empty")
    dim_x = len(xs[0])
    dim_theta = len(thetas[0])
    if len(observation) != dim_x:
        raise ValueError("observation dimension does not match simulation x dimension")
    if any(len(row) != dim_x for row in xs) or any(len(row) != dim_theta for row in thetas):
        raise ValueError("simulation dimensions are inconsistent")
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if sample_variance <= 0.0:
        raise ValueError("sample_variance must be positive")

    params = {
        "weights": [[0.0 for _ in range(dim_x)] for _ in range(dim_theta)],
        "bias": [0.0 for _ in range(dim_theta)],
    }
    params_before = json.loads(json.dumps(params))
    loss_before = mse(params, xs, thetas)
    n = float(len(xs))
    for _ in range(int(steps)):
        grad_w = [[0.0 for _ in range(dim_x)] for _ in range(dim_theta)]
        grad_b = [0.0 for _ in range(dim_theta)]
        for x, theta in zip(xs, thetas):
            pred = predict(params, x)
            for j in range(dim_theta):
                err = pred[j] - theta[j]
                grad_b[j] += 2.0 * err / n
                for k in range(dim_x):
                    grad_w[j][k] += 2.0 * err * x[k] / n
        for j in range(dim_theta):
            params["bias"][j] -= learning_rate * grad_b[j]
            for k in range(dim_x):
                params["weights"][j][k] -= learning_rate * grad_w[j][k]
    loss_after = mse(params, xs, thetas)
    rng = random.Random(seed)
    mean = predict(params, [float(v) for v in observation])
    std = math.sqrt(sample_variance)
    samples = [[rng.gauss(mu, std) for mu in mean] for _ in range(sample_count)]
    trace = {
        "schema_version": 1,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": params,
        "parameters_before": params_before,
        "parameters_after": params,
        "optimizer_state_changed": params_before != params,
        "learning_rate": learning_rate,
        "steps": int(steps),
        "sample_variance": sample_variance,
        "conditioned_mean": mean,
    }
    return {
        "schema_version": 1,
        "seed": int(seed),
        "sample_count": sample_count,
        "observation": [float(v) for v in observation],
        "samples": samples,
        "trace": trace,
    }


def self_test() -> dict:
    simulations = {"theta": [], "x": []}
    for i in range(-8, 9):
        x = [i / 10.0]
        theta = [0.8 * x[0] - 0.1]
        simulations["x"].append(x)
        simulations["theta"].append(theta)
    result = fit_affine_posterior(
        simulations=simulations,
        observation=[0.5],
        learning_rate=0.1,
        steps=80,
        sample_count=10,
        sample_variance=0.04,
        seed=5,
    )
    trace = result["trace"]
    return {
        "ok": trace["loss_after"] < trace["loss_before"] and trace["optimizer_state_changed"],
        "loss_before": trace["loss_before"],
        "loss_after": trace["loss_after"],
        "sample_count": len(result["samples"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--simulations", required=True)
    fit.add_argument("--observation", required=True)
    fit.add_argument("--learning-rate", type=float, default=0.05)
    fit.add_argument("--steps", type=int, default=100)
    fit.add_argument("--sample-count", type=int, default=200)
    fit.add_argument("--sample-variance", type=float, default=0.05)
    fit.add_argument("--seed", type=int, default=0)
    fit.add_argument("--samples-output", required=True)
    fit.add_argument("--trace-output", required=True)
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "fit":
        result = fit_affine_posterior(
            simulations=read_json(args.simulations),
            observation=[float(v) for v in json.loads(args.observation)],
            learning_rate=args.learning_rate,
            steps=args.steps,
            sample_count=args.sample_count,
            sample_variance=args.sample_variance,
            seed=args.seed,
        )
        write_json(args.samples_output, {key: value for key, value in result.items() if key != "trace"})
        write_json(args.trace_output, result["trace"])
    elif args.command == "self-test":
        print(json.dumps(self_test(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
