#!/usr/bin/env python3
"""Reduced continuous-time denoising score matching utilities."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable, List, Tuple


def vp_marginal(data: Iterable[float], t: float, beta_min: float = 0.1, beta_max: float = 20.0) -> Tuple[List[float], float]:
    log_mean_coeff = -0.25 * t * t * (beta_max - beta_min) - 0.5 * t * beta_min
    coeff = math.exp(log_mean_coeff)
    std = math.sqrt(max(1.0 - math.exp(2.0 * log_mean_coeff), 1e-30))
    return [coeff * float(x) for x in data], std


def build_perturbation(data: Iterable[float], t: float, noise: Iterable[float]) -> dict:
    data_values = [float(x) for x in data]
    noise_values = [float(z) for z in noise]
    if len(data_values) != len(noise_values):
        raise ValueError("data and noise must have the same length")
    mean, std = vp_marginal(data_values, t)
    perturbed = [m + std * z for m, z in zip(mean, noise_values)]
    target = [-z / std for z in noise_values]
    return {"mean": mean, "std": std, "perturbed": perturbed, "target_score": target, "time": t, "noise": noise_values}


def linear_scores(perturbed: Iterable[float], t: float, params: dict) -> List[float]:
    weight = float(params.get("weight", 0.0))
    time_weight = float(params.get("time_weight", 0.0))
    bias = float(params.get("bias", 0.0))
    return [weight * float(x) + time_weight * t + bias for x in perturbed]


def loss_and_grads(data: Iterable[float], t: float, noise: Iterable[float], params: dict) -> tuple[float, dict, dict]:
    item = build_perturbation(data, t, noise)
    perturbed = item["perturbed"]
    target = item["target_score"]
    preds = linear_scores(perturbed, t, params)
    n = float(len(preds))
    residuals = [p - y for p, y in zip(preds, target)]
    loss = sum(r * r for r in residuals) / n
    grads = {
        "weight": 2.0 * sum(r * x for r, x in zip(residuals, perturbed)) / n,
        "time_weight": 2.0 * sum(r * t for r in residuals) / n,
        "bias": 2.0 * sum(residuals) / n,
    }
    item["predicted_score"] = preds
    item["loss"] = loss
    return loss, grads, item


def optimizer_step(data: Iterable[float], t: float, noise: Iterable[float], params: dict, lr: float = 0.05) -> dict:
    params_before = {k: float(v) for k, v in params.items()}
    loss_before, grads, item_before = loss_and_grads(data, t, noise, params_before)
    params_after = {k: params_before[k] - lr * grads[k] for k in params_before}
    loss_after, _, item_after = loss_and_grads(data, t, noise, params_after)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "loss_delta": loss_before - loss_after,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "grads": grads,
        "optimizer_step_executed": any(abs(params_after[k] - params_before[k]) > 1e-12 for k in params_before),
        "perturbation_before": item_before,
        "perturbation_after": item_after,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=float, nargs="+", required=True)
    parser.add_argument("--noise", type=float, nargs="+", required=True)
    parser.add_argument("--t", type=float, required=True)
    parser.add_argument("--lr", type=float, default=0.05)
    args = parser.parse_args()
    result = optimizer_step(args.data, args.t, args.noise, {"weight": 0.0, "time_weight": 0.0, "bias": 0.0}, args.lr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
