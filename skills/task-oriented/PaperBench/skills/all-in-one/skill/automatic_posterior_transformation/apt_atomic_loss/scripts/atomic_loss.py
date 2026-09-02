#!/usr/bin/env python3
"""Atomic APT equation-6 loss helpers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def logsumexp(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return float("-inf")
    top = max(finite)
    return top + math.log(sum(math.exp(value - top) for value in finite))


def atomic_probabilities(log_q_values: list[float], log_prior_values: list[float]) -> dict:
    if len(log_q_values) != len(log_prior_values):
        raise ValueError("log_q_values and log_prior_values must have the same length")
    if not log_q_values:
        raise ValueError("atom set must be non-empty")
    scores = []
    for q_value, prior_value in zip(log_q_values, log_prior_values):
        if prior_value == float("-inf"):
            scores.append(float("-inf"))
        else:
            scores.append(q_value - prior_value)
    normalizer = logsumexp(scores)
    probabilities = [math.exp(score - normalizer) if math.isfinite(score) else 0.0 for score in scores]
    return {
        "scores": scores,
        "log_normalizer": normalizer,
        "probabilities": probabilities,
        "probability_sum": sum(probabilities),
    }


def atomic_loss(log_q_values: list[float], log_prior_values: list[float], true_index: int) -> dict:
    if true_index < 0 or true_index >= len(log_q_values):
        raise IndexError("true_index is outside the atom set")
    if not math.isfinite(log_prior_values[true_index]):
        raise ValueError("true atom must be inside prior support")
    result = atomic_probabilities(log_q_values, log_prior_values)
    probability = result["probabilities"][true_index]
    loss = float("inf") if probability <= 0.0 else -math.log(probability)
    result.update({"true_index": true_index, "true_probability": probability, "loss": loss})
    return result


def ratio_diagnostic(log_q_values: list[float], log_prior_values: list[float], i: int, j: int) -> dict:
    result = atomic_probabilities(log_q_values, log_prior_values)
    probabilities = result["probabilities"]
    log_probability_ratio = math.log(probabilities[i] / probabilities[j])
    expected = (log_q_values[i] - log_prior_values[i]) - (log_q_values[j] - log_prior_values[j])
    return {
        "i": i,
        "j": j,
        "log_probability_ratio": log_probability_ratio,
        "expected_log_ratio": expected,
        "abs_error": abs(log_probability_ratio - expected),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-q", required=True, help="JSON list of log q values")
    parser.add_argument("--log-prior", required=True, help="JSON list of log prior values")
    parser.add_argument("--true-index", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = atomic_loss(json.loads(args.log_q), json.loads(args.log_prior), args.true_index)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
