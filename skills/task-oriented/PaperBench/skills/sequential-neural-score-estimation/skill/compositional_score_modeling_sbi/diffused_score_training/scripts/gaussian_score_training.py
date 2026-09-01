#!/usr/bin/env python3
"""Reduced Gaussian score-training utilities for F-NPSE recovery."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def single_observation_posterior(x: float, prior_var: float = 1.0, likelihood_var: float = 0.25) -> tuple[float, float]:
    precision = 1.0 / prior_var + 1.0 / likelihood_var
    variance = 1.0 / precision
    mean = variance * x / likelihood_var
    return mean, variance


def exact_score(theta: float, x: float, prior_var: float = 1.0, likelihood_var: float = 0.25) -> float:
    mean, variance = single_observation_posterior(x, prior_var, likelihood_var)
    return -(theta - mean) / variance


def predict_score(params: dict[str, float], theta: float, x: float) -> float:
    return params["a"] * theta + params["b"] * x + params["c"]


def mse_loss(params: dict[str, float], examples: list[dict[str, float]]) -> float:
    errors = []
    for item in examples:
        pred = predict_score(params, item["theta"], item["x"])
        errors.append((pred - item["target_score"]) ** 2)
    return sum(errors) / len(errors)


def gradient_step(params: dict[str, float], examples: list[dict[str, float]], learning_rate: float) -> dict[str, float]:
    grads = {"a": 0.0, "b": 0.0, "c": 0.0}
    for item in examples:
        pred = predict_score(params, item["theta"], item["x"])
        error = pred - item["target_score"]
        grads["a"] += 2.0 * error * item["theta"] / len(examples)
        grads["b"] += 2.0 * error * item["x"] / len(examples)
        grads["c"] += 2.0 * error / len(examples)
    return {key: params[key] - learning_rate * grads[key] for key in params}


def build_training_trace(observations: list[float], theta_grid: list[float], learning_rate: float = 0.01) -> dict:
    examples = []
    for x in observations:
        for theta in theta_grid:
            examples.append({"theta": theta, "x": x, "target_score": exact_score(theta, x)})
    params_before = {"a": -0.5, "b": 0.5, "c": 0.0}
    loss_before = mse_loss(params_before, examples)
    params_after = gradient_step(params_before, examples, learning_rate)
    loss_after = mse_loss(params_after, examples)
    return {
        "schema_version": 1,
        "training_type": "reduced_affine_gaussian_score_surrogate",
        "examples": examples,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "optimizer_state_changed": params_before != params_after,
        "full_score_network_trained": False,
        "reduced_training_executed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", nargs="+", type=float, required=True)
    parser.add_argument("--theta-grid", nargs="+", type=float, default=[-1.0, 0.0, 1.0])
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    trace = build_training_trace(args.observations, args.theta_grid, args.learning_rate)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": math.isfinite(trace["loss_after"]), "output": args.output, "loss_after": trace["loss_after"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
