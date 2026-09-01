#!/usr/bin/env python3
"""Small Score SDE kernel utilities for reduced recovery experiments."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


Number = float | int
Vector = list[float]
ScoreFn = Callable[[Vector, float], Vector]


def as_vector(value: Number | Sequence[Number]) -> Vector:
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(item) for item in value]


def scalar_or_vector(values: Vector) -> float | Vector:
    return values[0] if len(values) == 1 else values


def _mul_scalar(values: Sequence[Number], scalar: Number) -> Vector:
    return [float(scalar) * float(value) for value in values]


def _sub(a: Sequence[Number], b: Sequence[Number]) -> Vector:
    return [float(x) - float(y) for x, y in zip(a, b)]


@dataclass(frozen=True)
class SDEKernel:
    """VE, VP, or sub-VP kernel with closed-form marginal helpers."""

    family: str
    sigma_min: float = 0.01
    sigma_max: float = 50.0
    beta_min: float = 0.1
    beta_max: float = 20.0

    def __post_init__(self) -> None:
        family = self.family.lower()
        if family not in {"ve", "vp", "subvp"}:
            raise ValueError("family must be one of: ve, vp, subvp")
        if self.sigma_min <= 0 or self.sigma_max <= self.sigma_min:
            raise ValueError("VE schedule requires 0 < sigma_min < sigma_max")
        if self.beta_min <= 0 or self.beta_max < self.beta_min:
            raise ValueError("VP schedule requires 0 < beta_min <= beta_max")
        object.__setattr__(self, "family", family)

    @property
    def T(self) -> float:
        return 1.0

    def beta(self, t: float) -> float:
        return self.beta_min + float(t) * (self.beta_max - self.beta_min)

    def sigma(self, t: float) -> float:
        return self.sigma_min * (self.sigma_max / self.sigma_min) ** float(t)

    def log_mean_coeff(self, t: float) -> float:
        t = float(t)
        return -0.25 * t * t * (self.beta_max - self.beta_min) - 0.5 * t * self.beta_min

    def sde(self, x: Number | Sequence[Number], t: float) -> tuple[float | Vector, float]:
        values = as_vector(x)
        if self.family == "ve":
            drift = [0.0 for _ in values]
            diffusion = self.sigma(t) * math.sqrt(2.0 * (math.log(self.sigma_max) - math.log(self.sigma_min)))
        elif self.family == "vp":
            beta_t = self.beta(t)
            drift = _mul_scalar(values, -0.5 * beta_t)
            diffusion = math.sqrt(beta_t)
        else:
            beta_t = self.beta(t)
            drift = _mul_scalar(values, -0.5 * beta_t)
            discount = 1.0 - math.exp(-2.0 * self.beta_min * float(t) - (self.beta_max - self.beta_min) * float(t) ** 2)
            diffusion = math.sqrt(max(beta_t * discount, 0.0))
        return scalar_or_vector(drift), diffusion

    def marginal_prob(self, x0: Number | Sequence[Number], t: float) -> tuple[float | Vector, float]:
        values = as_vector(x0)
        if self.family == "ve":
            return scalar_or_vector(values), self.sigma(t)
        coeff = math.exp(self.log_mean_coeff(t))
        mean = _mul_scalar(values, coeff)
        if self.family == "vp":
            std = math.sqrt(max(1.0 - math.exp(2.0 * self.log_mean_coeff(t)), 0.0))
        else:
            std = max(1.0 - math.exp(2.0 * self.log_mean_coeff(t)), 0.0)
        return scalar_or_vector(mean), std

    def prior_sample(self, shape: int, seed: int = 0) -> Vector:
        rng = random.Random(seed)
        scale = self.sigma_max if self.family == "ve" else 1.0
        return [rng.gauss(0.0, scale) for _ in range(int(shape))]

    def prior_logp(self, z: Number | Sequence[Number]) -> float:
        values = as_vector(z)
        variance = self.sigma_max ** 2 if self.family == "ve" else 1.0
        dim = len(values)
        return -0.5 * dim * math.log(2.0 * math.pi * variance) - sum(v * v for v in values) / (2.0 * variance)

    def reverse_drift(
        self,
        x: Number | Sequence[Number],
        t: float,
        score_fn: ScoreFn,
        probability_flow: bool = False,
    ) -> float | Vector:
        values = as_vector(x)
        drift_raw, diffusion = self.sde(values, t)
        drift = as_vector(drift_raw)
        score = as_vector(score_fn(values, float(t)))
        factor = 0.5 if probability_flow else 1.0
        correction = _mul_scalar(score, factor * diffusion * diffusion)
        return scalar_or_vector(_sub(drift, correction))


def perturb(kernel: SDEKernel, x0: Number | Sequence[Number], t: float, noise: Number | Sequence[Number]) -> float | Vector:
    mean_raw, std = kernel.marginal_prob(x0, t)
    mean = as_vector(mean_raw)
    z = as_vector(noise)
    if len(z) == 1 and len(mean) > 1:
        z = z * len(mean)
    return scalar_or_vector([m + std * zi for m, zi in zip(mean, z)])


def self_test() -> dict:
    vp = SDEKernel("vp", beta_min=0.1, beta_max=2.0)
    subvp = SDEKernel("subvp", beta_min=0.1, beta_max=2.0)
    _, vp_std = vp.marginal_prob(1.0, 0.7)
    _, subvp_std = subvp.marginal_prob(1.0, 0.7)
    score = lambda x, t: [-0.25 * item for item in x]
    rev = vp.reverse_drift([1.0], 0.5, score, probability_flow=False)
    ode = vp.reverse_drift([1.0], 0.5, score, probability_flow=True)
    drift, diffusion = vp.sde([1.0], 0.5)
    expected_ode = as_vector(drift)[0] - 0.5 * diffusion * diffusion * score([1.0], 0.5)[0]
    return {
        "ok": subvp_std <= vp_std and abs(as_vector(ode)[0] - expected_ode) < 1e-12 and as_vector(rev)[0] != as_vector(ode)[0],
        "vp_std": vp_std,
        "subvp_std": subvp_std,
        "reverse_drift": rev,
        "probability_flow_drift": ode,
    }


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
