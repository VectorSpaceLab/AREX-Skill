#!/usr/bin/env python3
import argparse
import json
import math


def vector_correlation(left, right):
    if len(left) != len(right):
        raise ValueError("vector length mismatch")
    if not left:
        raise ValueError("vectors must not be empty")
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    centered_left = [value - mean_left for value in left]
    centered_right = [value - mean_right for value in right]
    numerator = sum(a * b for a, b in zip(centered_left, centered_right))
    denom_left = sum(a * a for a in centered_left) ** 0.5
    denom_right = sum(b * b for b in centered_right) ** 0.5
    if denom_left == 0.0 or denom_right == 0.0:
        return 1.0 if left == right else 0.0
    return numerator / (denom_left * denom_right)


def mean_abs_summary_error(observed_summary, predicted_summaries):
    if not predicted_summaries:
        return math.inf
    total = 0.0
    count = 0
    for summary in predicted_summaries:
        if len(summary) != len(observed_summary):
            raise ValueError("summary length mismatch")
        for observed, predicted in zip(observed_summary, summary):
            total += abs(observed - predicted)
            count += 1
    return total / max(1, count)


def validate_recovery(posterior_mean, true_theta, observed_summary, predicted_summaries, mechanism_flags, threshold=0.8, max_summary_error=0.75):
    correlation = vector_correlation(posterior_mean, true_theta)
    summary_error = mean_abs_summary_error(observed_summary, predicted_summaries)
    required = [
        "simulator_executed",
        "summary_conditioning_executed",
        "posterior_estimator_fit",
        "posterior_samples_generated",
        "likelihood_evaluated_false",
        "original_repo_not_used",
    ]
    missing = [name for name in required if not mechanism_flags.get(name, False)]
    accepted = correlation >= threshold and summary_error <= max_summary_error and not missing
    return {
        "posterior_mean_filter_correlation": correlation,
        "posterior_predictive_summary_error": summary_error,
        "threshold": threshold,
        "max_summary_error": max_summary_error,
        "missing_mechanism_flags": missing,
        "accepted": accepted,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = validate_recovery(payload["posterior_mean"], payload["true_theta"], payload["observed_summary"], payload["predicted_summaries"], payload["mechanism_flags"], payload.get("threshold", 0.8), payload.get("max_summary_error", 0.75))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
