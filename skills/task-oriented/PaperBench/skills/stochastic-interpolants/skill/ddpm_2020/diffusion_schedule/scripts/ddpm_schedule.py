#!/usr/bin/env python3
"""DDPM schedule and forward marginal helpers."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable


def _as_list(values):
    if isinstance(values, (int, float)):
        return [float(values)]
    return [float(value) for value in values]


def linear_beta_schedule(timesteps: int, beta_start: float, beta_end: float) -> dict:
    if timesteps <= 0:
        raise ValueError("timesteps must be positive")
    if not (0.0 < beta_start <= beta_end < 1.0):
        raise ValueError("require 0 < beta_start <= beta_end < 1")
    if timesteps == 1:
        betas = [float(beta_start)]
    else:
        step = (beta_end - beta_start) / float(timesteps - 1)
        betas = [float(beta_start + step * i) for i in range(timesteps)]
    alphas = [1.0 - beta for beta in betas]
    alpha_bars = []
    product = 1.0
    for alpha in alphas:
        product *= alpha
        alpha_bars.append(product)
    posterior_variances = []
    previous_alpha_bar = 1.0
    for beta, alpha_bar in zip(betas, alpha_bars):
        if alpha_bar >= 1.0:
            posterior_variances.append(0.0)
        else:
            posterior_variances.append(((1.0 - previous_alpha_bar) / (1.0 - alpha_bar)) * beta)
        previous_alpha_bar = alpha_bar
    return {
        "timesteps": timesteps,
        "betas": betas,
        "alphas": alphas,
        "alpha_bars": alpha_bars,
        "posterior_variances": posterior_variances,
        "valid": all(0.0 < beta < 1.0 for beta in betas) and all(0.0 < alpha <= 1.0 for alpha in alphas),
        "alpha_bar_monotone_nonincreasing": all(alpha_bars[i] <= alpha_bars[i - 1] for i in range(1, len(alpha_bars))),
    }


def coefficient_at(schedule: dict, t: int) -> dict:
    if t < 1 or t > int(schedule["timesteps"]):
        raise ValueError("timestep is out of range")
    idx = t - 1
    return {
        "t": t,
        "beta": float(schedule["betas"][idx]),
        "alpha": float(schedule["alphas"][idx]),
        "alpha_bar": float(schedule["alpha_bars"][idx]),
        "posterior_variance": float(schedule["posterior_variances"][idx]),
    }


def forward_sample(schedule: dict, x0, epsilon, t: int):
    x0_values = _as_list(x0)
    eps_values = _as_list(epsilon)
    if len(x0_values) != len(eps_values):
        raise ValueError("x0 and epsilon must have the same length")
    alpha_bar = coefficient_at(schedule, t)["alpha_bar"]
    signal = math.sqrt(alpha_bar)
    noise = math.sqrt(1.0 - alpha_bar)
    values = [signal * x + noise * eps for x, eps in zip(x0_values, eps_values)]
    return values[0] if isinstance(x0, (int, float)) and isinstance(epsilon, (int, float)) else values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--timesteps", type=int, required=True)
    build.add_argument("--beta-start", type=float, required=True)
    build.add_argument("--beta-end", type=float, required=True)
    sample = sub.add_parser("sample")
    sample.add_argument("--schedule-json", required=True)
    sample.add_argument("--x0", required=True, help="JSON scalar or list")
    sample.add_argument("--epsilon", required=True, help="JSON scalar or list")
    sample.add_argument("--t", type=int, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = linear_beta_schedule(args.timesteps, args.beta_start, args.beta_end)
    else:
        result = {"x_t": forward_sample(json.loads(args.schedule_json), json.loads(args.x0), json.loads(args.epsilon), args.t)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
