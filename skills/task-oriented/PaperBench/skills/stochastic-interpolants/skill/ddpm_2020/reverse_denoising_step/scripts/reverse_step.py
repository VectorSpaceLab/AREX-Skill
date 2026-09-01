#!/usr/bin/env python3
"""DDPM reverse denoising step helpers."""

from __future__ import annotations

import argparse
import json
import math


def _as_list(values):
    if isinstance(values, (int, float)):
        return [float(values)]
    return [float(value) for value in values]


def _scalar_inputs(*values) -> bool:
    return all(isinstance(value, (int, float)) for value in values if value is not None)


def coefficients(schedule: dict, t: int) -> dict:
    if t < 1 or t > int(schedule["timesteps"]):
        raise ValueError("timestep is out of range")
    idx = t - 1
    beta = float(schedule["betas"][idx])
    alpha = float(schedule["alphas"][idx])
    alpha_bar = float(schedule["alpha_bars"][idx])
    if not (0.0 < alpha <= 1.0 and 0.0 < alpha_bar < 1.0):
        raise ValueError("invalid schedule coefficients for reverse mean")
    return {"t": t, "beta": beta, "alpha": alpha, "alpha_bar": alpha_bar, "posterior_variance": float(schedule.get("posterior_variances", [0.0] * int(schedule["timesteps"]))[idx])}


def reverse_mean(schedule: dict, x_t, predicted_epsilon, t: int):
    x_values = _as_list(x_t)
    eps_values = _as_list(predicted_epsilon)
    if len(x_values) != len(eps_values):
        raise ValueError("x_t and predicted_epsilon must have the same length")
    coeff = coefficients(schedule, t)
    denom = math.sqrt(1.0 - coeff["alpha_bar"])
    alpha_sqrt = math.sqrt(coeff["alpha"])
    values = [(x - coeff["beta"] * eps / denom) / alpha_sqrt for x, eps in zip(x_values, eps_values)]
    return values[0] if isinstance(x_t, (int, float)) and isinstance(predicted_epsilon, (int, float)) else values


def reverse_sample(schedule: dict, x_t, predicted_epsilon, t: int, z=None, variance_mode: str = "posterior") -> dict:
    mean = reverse_mean(schedule, x_t, predicted_epsilon, t)
    coeff = coefficients(schedule, t)
    if variance_mode == "posterior":
        sigma_sq = max(0.0, coeff["posterior_variance"])
    elif variance_mode == "beta":
        sigma_sq = coeff["beta"]
    elif variance_mode == "zero":
        sigma_sq = 0.0
    else:
        raise ValueError("variance_mode must be posterior, beta, or zero")
    z_values = _as_list(0.0 if z is None else z)
    mean_values = _as_list(mean)
    if len(z_values) == 1 and len(mean_values) > 1:
        z_values = z_values * len(mean_values)
    if len(z_values) != len(mean_values):
        raise ValueError("reverse noise must be scalar or match x_t length")
    sigma = math.sqrt(sigma_sq)
    sample = [m + sigma * noise for m, noise in zip(mean_values, z_values)]
    scalar = isinstance(mean, (int, float)) and (z is None or isinstance(z, (int, float)))
    return {"mean": mean, "sample": sample[0] if scalar else sample, "sigma": sigma, "coefficients": coeff}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule-json", required=True)
    parser.add_argument("--x-t", required=True)
    parser.add_argument("--pred", required=True)
    parser.add_argument("--t", type=int, required=True)
    parser.add_argument("--z", default="0.0")
    parser.add_argument("--variance-mode", default="posterior")
    args = parser.parse_args()
    result = reverse_sample(json.loads(args.schedule_json), json.loads(args.x_t), json.loads(args.pred), args.t, json.loads(args.z), args.variance_mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
