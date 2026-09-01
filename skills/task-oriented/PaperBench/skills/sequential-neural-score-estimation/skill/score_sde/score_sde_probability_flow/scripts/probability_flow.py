#!/usr/bin/env python3
"""Probability-flow ODE diagnostics for reduced Score SDE recovery."""

from __future__ import annotations

import argparse
import json
import math


def vp_beta(t: float, beta_min: float = 0.1, beta_max: float = 20.0) -> float:
    return beta_min + t * (beta_max - beta_min)


def probability_flow_step(x: float, t: float, score_coeff: float = -1.0, dt: float = -0.01) -> dict:
    beta = vp_beta(t)
    forward_drift_coeff = -0.5 * beta
    diffusion = math.sqrt(beta)
    score = score_coeff * x
    ode_drift = forward_drift_coeff * x - 0.5 * diffusion * diffusion * score
    ode_diffusion = 0.0
    drift_derivative = forward_drift_coeff - 0.5 * diffusion * diffusion * score_coeff
    x_next = x + ode_drift * dt
    log_density_delta = -drift_derivative * dt
    return {
        "x": x,
        "t": t,
        "score": score,
        "ode_drift": ode_drift,
        "ode_diffusion": ode_diffusion,
        "zero_diffusion": ode_diffusion == 0.0,
        "divergence": drift_derivative,
        "dt": dt,
        "x_next": x_next,
        "log_density_delta": log_density_delta,
        "finite": all(math.isfinite(v) for v in [ode_drift, drift_derivative, x_next, log_density_delta]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--t", type=float, required=True)
    parser.add_argument("--score-coeff", type=float, default=-1.0)
    args = parser.parse_args()
    print(json.dumps(probability_flow_step(args.x, args.t, args.score_coeff), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
