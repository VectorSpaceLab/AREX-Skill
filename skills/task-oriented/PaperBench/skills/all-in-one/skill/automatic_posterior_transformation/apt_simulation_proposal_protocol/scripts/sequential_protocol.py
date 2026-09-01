#!/usr/bin/env python3
"""Sequential simulator/proposal helpers for reduced APT recovery."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Gaussian1D:
    name: str
    mean: float
    variance: float
    support_low: float | None = None
    support_high: float | None = None

    def sample(self, rng: random.Random) -> float:
        for _ in range(1000):
            value = rng.gauss(self.mean, math.sqrt(self.variance))
            if self.contains(value):
                return value
        raise RuntimeError("failed to draw a supported sample")

    def contains(self, value: float) -> bool:
        if self.support_low is not None and value < self.support_low:
            return False
        if self.support_high is not None and value > self.support_high:
            return False
        return True

    def log_prob(self, value: float) -> float:
        if not self.contains(value):
            return float("-inf")
        return -0.5 * (math.log(2.0 * math.pi * self.variance) + ((value - self.mean) ** 2) / self.variance)


def scalar_simulator(theta: float, rng: random.Random, noise_variance: float = 0.25) -> float:
    return theta + rng.gauss(0.0, math.sqrt(noise_variance))


def posterior_from_gaussian_observation(
    prior: Gaussian1D,
    observation: float,
    noise_variance: float,
    name: str = "posterior_analytic",
) -> Gaussian1D:
    prior_precision = 1.0 / prior.variance
    likelihood_precision = 1.0 / noise_variance
    variance = 1.0 / (prior_precision + likelihood_precision)
    mean = variance * (prior_precision * prior.mean + likelihood_precision * observation)
    return Gaussian1D(name=name, mean=mean, variance=variance, support_low=prior.support_low, support_high=prior.support_high)


def run_two_round_protocol(
    seed: int = 123,
    simulations_per_round: int = 8,
    observation: float = 0.7,
    noise_variance: float = 0.25,
) -> dict:
    rng = random.Random(seed)
    prior = Gaussian1D("prior", mean=0.0, variance=4.0, support_low=-6.0, support_high=6.0)
    posterior = posterior_from_gaussian_observation(prior, observation, noise_variance)
    proposals = [prior, posterior]
    records = []
    updates = [
        {
            "round_index": 1,
            "previous_proposal": asdict(prior),
            "posterior_at_observation": asdict(posterior),
            "next_proposal": asdict(posterior),
            "update_rule": "proposal_{r+1} = q_F(x_o, phi); analytic posterior used for reduced recovery",
        }
    ]
    for round_index, proposal in enumerate(proposals, start=1):
        for item_index in range(simulations_per_round):
            item_seed = seed * 1000 + round_index * 100 + item_index
            item_rng = random.Random(item_seed)
            theta = proposal.sample(item_rng)
            x_value = scalar_simulator(theta, item_rng, noise_variance=noise_variance)
            records.append(
                {
                    "round_index": round_index,
                    "item_index": item_index,
                    "seed": item_seed,
                    "theta": theta,
                    "x": x_value,
                    "proposal_name": proposal.name,
                    "proposal_parameters": asdict(proposal),
                    "proposal_log_prob": proposal.log_prob(theta),
                    "within_prior_support": prior.contains(theta),
                }
            )
    return {
        "schema_version": 1,
        "seed": seed,
        "observed_x": observation,
        "noise_variance": noise_variance,
        "prior": asdict(prior),
        "round_count": len(proposals),
        "simulations_per_round": simulations_per_round,
        "records": records,
        "proposal_updates": updates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--simulations-per-round", type=int, default=8)
    parser.add_argument("--observation", type=float, default=0.7)
    args = parser.parse_args(argv)
    result = run_two_round_protocol(
        seed=args.seed,
        simulations_per_round=args.simulations_per_round,
        observation=args.observation,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "record_count": len(result["records"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
