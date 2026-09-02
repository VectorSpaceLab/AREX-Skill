#!/usr/bin/env python3
"""Quadratic objectives for stochastic-interpolant field learning."""

from __future__ import annotations

import argparse
import json
from typing import Iterable


def _floats(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values]


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot average an empty list")
    return sum(values) / len(values)


def velocity_loss(predicted_velocity: Iterable[float], target_velocity: Iterable[float]) -> float:
    pred = _floats(predicted_velocity)
    target = _floats(target_velocity)
    if len(pred) != len(target):
        raise ValueError("predicted_velocity and target_velocity lengths differ")
    return mean([0.5 * p * p - y * p for p, y in zip(pred, target)])


def denoiser_loss(predicted_eta: Iterable[float], noise: Iterable[float]) -> float:
    pred = _floats(predicted_eta)
    z = _floats(noise)
    if len(pred) != len(z):
        raise ValueError("predicted_eta and noise lengths differ")
    return mean([0.5 * p * p - n * p for p, n in zip(pred, z)])


def score_from_denoiser(predicted_eta: Iterable[float], gamma: Iterable[float], min_gamma: float = 1e-8) -> list[float | None]:
    eta = _floats(predicted_eta)
    gamma_values = _floats(gamma)
    if len(eta) != len(gamma_values):
        raise ValueError("predicted_eta and gamma lengths differ")
    scores: list[float | None] = []
    for eta_value, gamma_value in zip(eta, gamma_values):
        if abs(gamma_value) < min_gamma:
            scores.append(None)
        else:
            scores.append(-eta_value / gamma_value)
    return scores


def diagnostics(predicted_velocity: Iterable[float], target_velocity: Iterable[float], predicted_eta: Iterable[float], noise: Iterable[float], gamma: Iterable[float]) -> dict:
    return {
        "velocity_loss": velocity_loss(predicted_velocity, target_velocity),
        "denoiser_loss": denoiser_loss(predicted_eta, noise),
        "score": score_from_denoiser(predicted_eta, gamma),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    output = diagnostics([1.0, 2.0], [1.0, 3.0], [0.5, -0.5], [1.0, -1.0], [0.5, 0.25])
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
