#!/usr/bin/env python3
"""Probability-flow drift and likelihood accounting helpers."""

from __future__ import annotations

import argparse
import json
import math
from typing import Callable, Sequence


Number = float | int
Vector = list[float]


def as_vector(value: Number | Sequence[Number]) -> Vector:
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(v) for v in value]


def probability_flow_drift(
    x: Number | Sequence[Number],
    t: float,
    drift_fn: Callable[[Vector, float], Vector],
    diffusion_fn: Callable[[float], float],
    score_fn: Callable[[Vector, float], Vector],
) -> Vector:
    values = as_vector(x)
    drift = as_vector(drift_fn(values, float(t)))
    diffusion = float(diffusion_fn(float(t)))
    score = as_vector(score_fn(values, float(t)))
    return [d - 0.5 * diffusion * diffusion * s for d, s in zip(drift, score)]


def finite_difference_divergence(
    fn: Callable[[Vector, float], Vector],
    x: Number | Sequence[Number],
    t: float,
    eps: float = 1e-5,
) -> float:
    values = as_vector(x)
    total = 0.0
    for i in range(len(values)):
        plus = list(values)
        minus = list(values)
        plus[i] += eps
        minus[i] -= eps
        f_plus = as_vector(fn(plus, t))[i]
        f_minus = as_vector(fn(minus, t))[i]
        total += (f_plus - f_minus) / (2.0 * eps)
    return total


def gaussian_prior_logp(z: Number | Sequence[Number], std: float = 1.0) -> float:
    values = as_vector(z)
    variance = std * std
    return -0.5 * len(values) * math.log(2.0 * math.pi * variance) - sum(v * v for v in values) / (2.0 * variance)


def likelihood_summary(
    terminal_z: Number | Sequence[Number],
    divergence_values: Sequence[Number],
    dt: float,
    prior_std: float = 1.0,
    data_dim: int | None = None,
    dequantization_offset_bits: float = 0.0,
) -> dict:
    delta_logp = sum(float(v) * float(dt) for v in divergence_values)
    prior_logp = gaussian_prior_logp(terminal_z, std=prior_std)
    logp = prior_logp + delta_logp
    result = {"prior_logp": prior_logp, "delta_logp": delta_logp, "logp": logp, "negative_log_likelihood": -logp}
    if data_dim:
        result["bits_per_dim"] = -logp / (math.log(2.0) * int(data_dim)) + dequantization_offset_bits
    return result


def self_test() -> dict:
    drift_fn = lambda x, t: [-0.5 * item for item in x]
    diffusion_fn = lambda t: 0.2
    score_fn = lambda x, t: [-item for item in x]
    pf = probability_flow_drift([1.0], 0.5, drift_fn, diffusion_fn, score_fn)[0]
    div = finite_difference_divergence(lambda x, t: probability_flow_drift(x, t, drift_fn, diffusion_fn, score_fn), [1.0], 0.5)
    like = likelihood_summary([0.0], [div], dt=0.1, data_dim=1)
    return {"ok": abs(pf + 0.48) < 1e-12 and like["bits_per_dim"] > 0.0, "drift": pf, "divergence": div, "likelihood": like}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
