#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Iterable


def mse(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        raise ValueError("cannot compute MSE over an empty sequence")
    return sum(value * value for value in items) / len(items)


def predict_epsilon(noised_latent: list[float], weight: float, bias: float) -> list[float]:
    return [weight * value + bias for value in noised_latent]


def compute_loss(noised_latent: list[float], noise: list[float], weight: float, bias: float) -> float:
    if len(noised_latent) != len(noise):
        raise ValueError("noised_latent and noise lengths must match")
    prediction = predict_epsilon(noised_latent, weight, bias)
    return mse([target - pred for target, pred in zip(noise, prediction)])


def run_reduced_step(latent: list[float], noise: list[float], alpha: float, sigma: float, weight: float, bias: float, learning_rate: float) -> dict:
    if len(latent) != len(noise):
        raise ValueError("latent and noise lengths must match")
    noised_latent = [alpha * z + sigma * eps for z, eps in zip(latent, noise)]
    loss_before = compute_loss(noised_latent, noise, weight, bias)
    prediction = predict_epsilon(noised_latent, weight, bias)
    errors = [pred - target for pred, target in zip(prediction, noise)]
    grad_weight = 2.0 * sum(err * value for err, value in zip(errors, noised_latent)) / len(errors)
    grad_bias = 2.0 * sum(errors) / len(errors)
    new_weight = weight - learning_rate * grad_weight
    new_bias = bias - learning_rate * grad_bias
    loss_after = compute_loss(noised_latent, noise, new_weight, new_bias)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": {"weight": weight, "bias": bias},
        "params_after": {"weight": new_weight, "bias": new_bias},
        "parameters_before": {"weight": weight, "bias": bias},
        "parameters_after": {"weight": new_weight, "bias": new_bias},
        "noised_latent": noised_latent,
        "target_noise": noise,
        "alpha": alpha,
        "sigma": sigma,
        "learning_rate": learning_rate,
        "mechanism_checks": {
            "latent_noising_executed": True,
            "epsilon_prediction_loss_computed": True,
            "reduced_training_executed": True,
            "optimizer_step_executed": {"weight": weight, "bias": bias} != {"weight": new_weight, "bias": new_bias},
            "training_step_executed": False,
            "qwen3_model_loaded": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--latent", default="1.0,0.5,-0.5")
    parser.add_argument("--noise", default="0.25,-0.1,0.4")
    parser.add_argument("--alpha", type=float, default=0.8)
    parser.add_argument("--sigma", type=float, default=0.6)
    parser.add_argument("--weight", type=float, default=0.0)
    parser.add_argument("--bias", type=float, default=0.0)
    parser.add_argument("--learning-rate", type=float, default=0.5)
    args = parser.parse_args()
    latent = [float(item) for item in args.latent.split(",") if item]
    noise = [float(item) for item in args.noise.split(",") if item]
    trace = run_reduced_step(latent, noise, args.alpha, args.sigma, args.weight, args.bias, args.learning_rate)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(trace, handle, indent=2)
        handle.write("\n")
    print(json.dumps(trace, indent=2))
    return 0 if trace["loss_after"] < trace["loss_before"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
