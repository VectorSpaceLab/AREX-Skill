#!/usr/bin/env python3
"""Small deterministic SDE contracts for Score SDE recovery."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable, List, Tuple


def _as_list(x: float | Iterable[float]) -> List[float]:
    if isinstance(x, (int, float)):
        return [float(x)]
    return [float(v) for v in x]


def _mul(values: Iterable[float], scalar: float) -> List[float]:
    return [float(v) * float(scalar) for v in values]


class ScoreSDE:
    def __init__(
        self,
        kind: str,
        sigma_min: float = 0.01,
        sigma_max: float = 50.0,
        beta_min: float = 0.1,
        beta_max: float = 20.0,
        num_steps: int = 1000,
    ):
        self.kind = kind
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.beta_min = beta_min
        self.beta_max = beta_max
        self.num_steps = num_steps

    @property
    def T(self) -> float:
        return 1.0

    def beta(self, t: float) -> float:
        return self.beta_min + t * (self.beta_max - self.beta_min)

    def sde(self, x: Iterable[float], t: float) -> Tuple[List[float], float]:
        values = _as_list(x)
        if self.kind == "ve":
            sigma = self.sigma_min * (self.sigma_max / self.sigma_min) ** t
            diffusion = sigma * math.sqrt(2.0 * math.log(self.sigma_max / self.sigma_min))
            return [0.0 for _ in values], diffusion
        if self.kind in {"vp", "subvp"}:
            beta_t = self.beta(t)
            drift = _mul(values, -0.5 * beta_t)
            if self.kind == "vp":
                diffusion = math.sqrt(beta_t)
            else:
                discount = 1.0 - math.exp(-2.0 * self.beta_min * t - (self.beta_max - self.beta_min) * t * t)
                diffusion = math.sqrt(max(beta_t * discount, 0.0))
            return drift, diffusion
        raise ValueError(f"unknown SDE kind: {self.kind}")

    def marginal_prob(self, x: Iterable[float], t: float) -> Tuple[List[float], float]:
        values = _as_list(x)
        if self.kind == "ve":
            std = self.sigma_min * (self.sigma_max / self.sigma_min) ** t
            return values, std
        if self.kind in {"vp", "subvp"}:
            log_mean_coeff = -0.25 * t * t * (self.beta_max - self.beta_min) - 0.5 * t * self.beta_min
            mean_coeff = math.exp(log_mean_coeff)
            mean = _mul(values, mean_coeff)
            variance = 1.0 - math.exp(2.0 * log_mean_coeff)
            std = math.sqrt(max(variance, 1e-30)) if self.kind == "vp" else max(variance, 1e-30)
            return mean, std
        raise ValueError(f"unknown SDE kind: {self.kind}")

    def prior_logp(self, z: Iterable[float]) -> float:
        values = _as_list(z)
        n_dims = len(values)
        return -0.5 * n_dims * math.log(2.0 * math.pi) - 0.5 * sum(v * v for v in values)

    def discretize(self, x: Iterable[float], t: float) -> Tuple[List[float], float]:
        drift, diffusion = self.sde(x, t)
        dt = 1.0 / float(self.num_steps)
        return _mul(drift, dt), diffusion * math.sqrt(dt)

    def reverse_drift_diffusion(
        self, x: Iterable[float], t: float, score: Iterable[float], probability_flow: bool = False
    ) -> Tuple[List[float], float]:
        values = _as_list(x)
        score_values = _as_list(score)
        if len(score_values) == 1 and len(values) > 1:
            score_values = score_values * len(values)
        drift, diffusion = self.sde(values, t)
        factor = 0.5 if probability_flow else 1.0
        reverse_drift = [d - diffusion * diffusion * s * factor for d, s in zip(drift, score_values)]
        reverse_diffusion = 0.0 if probability_flow else diffusion
        return reverse_drift, reverse_diffusion


def make_sde(kind: str, **kwargs) -> ScoreSDE:
    return ScoreSDE(kind=kind.lower(), **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sde", choices=["ve", "vp", "subvp"], required=True)
    parser.add_argument("--x", type=float, nargs="+", required=True)
    parser.add_argument("--t", type=float, required=True)
    parser.add_argument("--score", type=float, nargs="+", default=[0.0])
    args = parser.parse_args()
    sde = make_sde(args.sde)
    drift, diffusion = sde.sde(args.x, args.t)
    mean, std = sde.marginal_prob(args.x, args.t)
    rev_drift, rev_diffusion = sde.reverse_drift_diffusion(args.x, args.t, args.score)
    ode_drift, ode_diffusion = sde.reverse_drift_diffusion(args.x, args.t, args.score, probability_flow=True)
    print(json.dumps({
        "sde": args.sde,
        "drift": drift,
        "diffusion": diffusion,
        "marginal_mean": mean,
        "marginal_std": std,
        "reverse_drift": rev_drift,
        "reverse_diffusion": rev_diffusion,
        "probability_flow_drift": ode_drift,
        "probability_flow_diffusion": ode_diffusion,
        "prior_logp": sde.prior_logp(args.x),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
