#!/usr/bin/env python3
"""Construct stochastic-interpolant samples for scalar/vector lists."""

from __future__ import annotations

import argparse
import json
from typing import Iterable


def _as_float_list(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values]


def _broadcast_times(times: list[float], n_items: int) -> list[float]:
    if len(times) == 1:
        return times * n_items
    if len(times) != n_items:
        raise ValueError("times must have length 1 or match endpoint length")
    return times


def gamma_quadratic(t: float) -> float:
    return 2.0 * t * (1.0 - t)


def gamma_dot_quadratic(t: float) -> float:
    return 2.0 - 4.0 * t


def construct_interpolant(x0: Iterable[float], x1: Iterable[float], times: Iterable[float], noise: Iterable[float]) -> dict:
    x0_values = _as_float_list(x0)
    x1_values = _as_float_list(x1)
    noise_values = _as_float_list(noise)
    if len(x0_values) != len(x1_values) or len(x0_values) != len(noise_values):
        raise ValueError("x0, x1, and noise must have matching lengths")
    time_values = _broadcast_times(_as_float_list(times), len(x0_values))
    if any(t < 0.0 or t > 1.0 for t in time_values):
        raise ValueError("all time values must be in [0, 1]")

    gamma_values = [gamma_quadratic(t) for t in time_values]
    gamma_dot_values = [gamma_dot_quadratic(t) for t in time_values]
    xt = []
    dot_xt = []
    for x0_item, x1_item, t, noise_item, gamma, gamma_dot in zip(x0_values, x1_values, time_values, noise_values, gamma_values, gamma_dot_values):
        xt.append((1.0 - t) * x0_item + t * x1_item + gamma * noise_item)
        dot_xt.append(x1_item - x0_item + gamma_dot * noise_item)
    return {
        "schedule": "linear_quadratic_gamma",
        "x_t": xt,
        "dot_x_t": dot_xt,
        "gamma": gamma_values,
        "gamma_dot": gamma_dot_values,
        "endpoint_constraints": {
            "gamma_0": gamma_quadratic(0.0),
            "gamma_1": gamma_quadratic(1.0),
            "linear_I_0_is_x0": True,
            "linear_I_1_is_x1": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x0", nargs="*", type=float, default=[0.0, 1.0])
    parser.add_argument("--x1", nargs="*", type=float, default=[2.0, 3.0])
    parser.add_argument("--times", nargs="*", type=float, default=[0.5])
    parser.add_argument("--noise", nargs="*", type=float, default=[1.0, -1.0])
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    print(json.dumps(construct_interpolant(args.x0, args.x1, args.times, args.noise), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
