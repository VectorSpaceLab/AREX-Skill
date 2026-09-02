#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def betas_for_alpha_bar(steps: int, max_beta: float = 0.999) -> list[float]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    betas = []
    for index in range(steps):
        t1 = index / steps
        t2 = (index + 1) / steps
        alpha_1 = math.cos((t1 + 0.008) / 1.008 * math.pi / 2) ** 2
        alpha_2 = math.cos((t2 + 0.008) / 1.008 * math.pi / 2) ** 2
        betas.append(min(1.0 - alpha_2 / alpha_1, max_beta))
    return betas


def make_beta_schedule(schedule: str, steps: int) -> list[float]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if schedule == "linear":
        scale = 1000.0 / steps
        start = scale * 0.0001
        end = scale * 0.02
        if steps == 1:
            return [min(end, 0.999)]
        return [min(start + (end - start) * index / (steps - 1), 0.999) for index in range(steps)]
    if schedule == "cosine":
        return betas_for_alpha_bar(steps)
    raise ValueError(f"unknown schedule: {schedule}")


def posterior_coefficients(betas: list[float]) -> dict[str, list[float]]:
    if not betas or any(beta <= 0 or beta > 1 for beta in betas):
        raise ValueError("betas must be in (0, 1]")
    alphas = [1.0 - beta for beta in betas]
    cumulative = []
    product = 1.0
    for alpha in alphas:
        product *= alpha
        cumulative.append(product)
    previous = [1.0] + cumulative[:-1]
    posterior_variance = []
    coef1 = []
    coef2 = []
    for beta, alpha, alpha_bar, alpha_bar_prev in zip(betas, alphas, cumulative, previous):
        denom = max(1.0 - alpha_bar, 1e-12)
        posterior_variance.append(beta * (1.0 - alpha_bar_prev) / denom)
        coef1.append(beta * math.sqrt(alpha_bar_prev) / denom)
        coef2.append((1.0 - alpha_bar_prev) * math.sqrt(alpha) / denom)
    return {
        "betas": betas,
        "alphas_cumprod": cumulative,
        "alphas_cumprod_prev": previous,
        "posterior_variance": posterior_variance,
        "posterior_mean_coef1": coef1,
        "posterior_mean_coef2": coef2,
    }


def build_schedule(schedule: str, steps: int) -> dict[str, object]:
    betas = make_beta_schedule(schedule, steps)
    coeffs = posterior_coefficients(betas)
    valid = all(0 < beta <= 1 for beta in betas) and all(
        later < earlier for earlier, later in zip(coeffs["alphas_cumprod"], coeffs["alphas_cumprod"][1:])
    )
    return {"schedule": schedule, "steps": steps, "valid": valid, **coeffs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", choices=["linear", "cosine"], required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build_schedule(args.schedule, args.steps)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
