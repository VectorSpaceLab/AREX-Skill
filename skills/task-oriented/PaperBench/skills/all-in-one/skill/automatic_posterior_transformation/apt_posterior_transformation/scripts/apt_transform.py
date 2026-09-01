#!/usr/bin/env python3
"""APT posterior transformation helpers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def gaussian_transform_1d(
    prior_mean: float,
    prior_variance: float,
    proposal_mean: float,
    proposal_variance: float,
    posterior_mean: float,
    posterior_variance: float,
) -> dict:
    prior_precision = 1.0 / prior_variance
    proposal_precision = 1.0 / proposal_variance
    posterior_precision = 1.0 / posterior_variance
    transformed_precision = posterior_precision + proposal_precision - prior_precision
    if transformed_precision <= 0.0:
        return {
            "ok": False,
            "error": "transformed precision must be positive",
            "transformed_precision": transformed_precision,
        }
    natural_mean = (
        posterior_precision * posterior_mean
        + proposal_precision * proposal_mean
        - prior_precision * prior_mean
    )
    transformed_variance = 1.0 / transformed_precision
    transformed_mean = natural_mean / transformed_precision
    return {
        "ok": True,
        "mean": transformed_mean,
        "variance": transformed_variance,
        "precision": transformed_precision,
        "natural_mean": natural_mean,
    }


def logsumexp(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return float("-inf")
    top = max(finite)
    return top + math.log(sum(math.exp(value - top) for value in finite))


def normalize_transformed_scores(log_q: list[float], log_proposal: list[float], log_prior: list[float]) -> dict:
    if not (len(log_q) == len(log_proposal) == len(log_prior)):
        raise ValueError("log_q, log_proposal, and log_prior must have the same length")
    scores = [q + proposal - prior for q, proposal, prior in zip(log_q, log_proposal, log_prior)]
    normalizer = logsumexp(scores)
    if not math.isfinite(normalizer):
        probabilities = [0.0 for _ in scores]
    else:
        probabilities = [math.exp(score - normalizer) if math.isfinite(score) else 0.0 for score in scores]
    return {
        "scores": scores,
        "log_normalizer": normalizer,
        "probabilities": probabilities,
        "probability_sum": sum(probabilities),
    }


def normal_log_prob(value: float, mean: float, variance: float) -> float:
    return -0.5 * (math.log(2.0 * math.pi * variance) + ((value - mean) ** 2) / variance)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prior-mean", type=float, default=0.0)
    parser.add_argument("--prior-variance", type=float, default=4.0)
    parser.add_argument("--proposal-mean", type=float, default=0.6)
    parser.add_argument("--proposal-variance", type=float, default=0.4)
    parser.add_argument("--posterior-mean", type=float, default=0.65)
    parser.add_argument("--posterior-variance", type=float, default=0.3)
    args = parser.parse_args(argv)
    result = gaussian_transform_1d(
        args.prior_mean,
        args.prior_variance,
        args.proposal_mean,
        args.proposal_variance,
        args.posterior_mean,
        args.posterior_variance,
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
