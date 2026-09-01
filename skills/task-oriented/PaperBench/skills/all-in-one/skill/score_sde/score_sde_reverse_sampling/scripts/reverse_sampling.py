#!/usr/bin/env python3
"""Reduced reverse SDE and predictor-corrector sampling helpers."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence


Number = float | int
Vector = list[float]


def as_vector(value: Number | Sequence[Number]) -> Vector:
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(item) for item in value]


def l2_norm(values: Sequence[Number]) -> float:
    return math.sqrt(sum(float(v) * float(v) for v in values))


@dataclass
class SamplerConfig:
    times: list[float]
    dt: float
    probability_flow: bool = False
    corrector_steps: int = 0
    corrector_step_size: float = 0.01
    corrector_noise: float = 0.0
    seed: int = 0


def reverse_drift(
    x: Sequence[Number],
    t: float,
    drift_fn: Callable[[Vector, float], Vector],
    diffusion_fn: Callable[[float], float],
    score_fn: Callable[[Vector, float], Vector],
    probability_flow: bool = False,
) -> Vector:
    drift = as_vector(drift_fn(as_vector(x), float(t)))
    diffusion = float(diffusion_fn(float(t)))
    score = as_vector(score_fn(as_vector(x), float(t)))
    factor = 0.5 if probability_flow else 1.0
    return [d - factor * diffusion * diffusion * s for d, s in zip(drift, score)]


def langevin_corrector_step(
    x: Sequence[Number],
    t: float,
    score_fn: Callable[[Vector, float], Vector],
    step_size: float,
    rng: random.Random,
    noise_scale: float = 0.0,
) -> tuple[Vector, dict]:
    current = as_vector(x)
    score = as_vector(score_fn(current, float(t)))
    noise = [rng.gauss(0.0, 1.0) for _ in current]
    updated = [v + step_size * s + noise_scale * math.sqrt(max(2.0 * step_size, 0.0)) * n for v, s, n in zip(current, score, noise)]
    return updated, {"score_norm": l2_norm(score), "noise_norm": l2_norm(noise), "step_size": step_size}


def predictor_step(
    x: Sequence[Number],
    t: float,
    dt: float,
    drift_fn: Callable[[Vector, float], Vector],
    diffusion_fn: Callable[[float], float],
    score_fn: Callable[[Vector, float], Vector],
    rng: random.Random,
    probability_flow: bool = False,
) -> tuple[Vector, dict]:
    current = as_vector(x)
    rev = reverse_drift(current, t, drift_fn, diffusion_fn, score_fn, probability_flow)
    diffusion = 0.0 if probability_flow else float(diffusion_fn(t))
    noise = [rng.gauss(0.0, 1.0) for _ in current]
    # Times are descending; dt should be negative for reverse integration.
    updated = [v + r * dt + diffusion * math.sqrt(abs(dt)) * n for v, r, n in zip(current, rev, noise)]
    return updated, {"reverse_drift": rev, "diffusion": diffusion, "noise_norm": l2_norm(noise)}


def run_sampler(
    initial: Sequence[Number],
    config: SamplerConfig,
    drift_fn: Callable[[Vector, float], Vector],
    diffusion_fn: Callable[[float], float],
    score_fn: Callable[[Vector, float], Vector],
) -> dict:
    rng = random.Random(config.seed)
    x = as_vector(initial)
    trajectory = [{"time": config.times[0] if config.times else 1.0, "state": list(x), "event": "initial"}]
    score_evaluations = 0
    for t in config.times:
        for _ in range(config.corrector_steps):
            x, diag = langevin_corrector_step(
                x,
                t,
                score_fn,
                config.corrector_step_size,
                rng,
                noise_scale=config.corrector_noise,
            )
            score_evaluations += 1
            trajectory.append({"time": t, "state": list(x), "event": "corrector", "diagnostics": diag})
        x, diag = predictor_step(
            x,
            t,
            config.dt,
            drift_fn,
            diffusion_fn,
            score_fn,
            rng,
            probability_flow=config.probability_flow,
        )
        score_evaluations += 1
        trajectory.append({"time": t, "state": list(x), "event": "predictor", "diagnostics": diag})
    return {
        "final_state": x,
        "trajectory": trajectory,
        "score_evaluations": score_evaluations,
        "probability_flow": config.probability_flow,
        "corrector_steps": config.corrector_steps,
    }


def self_test() -> dict:
    drift_fn = lambda x, t: [-0.5 * item for item in x]
    diffusion_fn = lambda t: 0.2
    score_fn = lambda x, t: [-item for item in x]
    result = run_sampler(
        [1.0],
        SamplerConfig(times=[1.0, 0.5], dt=-0.1, probability_flow=True, corrector_steps=1, corrector_step_size=0.01),
        drift_fn,
        diffusion_fn,
        score_fn,
    )
    return {"ok": len(result["trajectory"]) == 5 and result["score_evaluations"] == 4, "result": result}


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
