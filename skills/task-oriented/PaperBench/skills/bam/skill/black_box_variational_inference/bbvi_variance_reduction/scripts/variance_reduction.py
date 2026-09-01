#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _as_matrix(values):
    if not isinstance(values, list) or not values:
        raise ValueError("score must be a non-empty list")
    if isinstance(values[0], list):
        matrix = [[float(value) for value in row] for row in values]
    else:
        matrix = [[float(value)] for value in values]
    width = len(matrix[0])
    if width == 0 or any(len(row) != width for row in matrix):
        raise ValueError("score rows must have consistent width")
    return matrix


def _mean(values):
    return sum(values) / len(values)


def _sample_variance(values):
    if len(values) < 2:
        return 0.0
    center = _mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def _term_norms(terms):
    return [sum(value * value for value in row) ** 0.5 for row in terms]


def _terms(score, signal):
    return [[score_value * signal_value for score_value in row] for row, signal_value in zip(score, signal)]


def reduce_variance(score, local_signal, full_signal=None):
    score_matrix = _as_matrix(score)
    local_signal = [float(value) for value in local_signal]
    if len(score_matrix) != len(local_signal):
        raise ValueError("score and local_signal must share the same sample count")
    if full_signal is not None:
        full_signal = [float(value) for value in full_signal]
        if len(full_signal) != len(local_signal):
            raise ValueError("full_signal must share the same sample count")
    for row in score_matrix:
        for value in row:
            if not math.isfinite(value):
                raise ValueError("score contains non-finite value")
    if any(not math.isfinite(value) for value in local_signal):
        raise ValueError("local_signal contains non-finite value")
    rb_terms = _terms(score_matrix, local_signal)
    sample_count = len(rb_terms)
    param_dim = len(rb_terms[0])
    score_means = [_mean([row[col] for row in score_matrix]) for col in range(param_dim)]
    term_means = [_mean([row[col] for row in rb_terms]) for col in range(param_dim)]
    covariance_sum = 0.0
    score_variance_sum = 0.0
    for col in range(param_dim):
        covariance_sum += sum(
            (rb_terms[row][col] - term_means[col]) * (score_matrix[row][col] - score_means[col])
            for row in range(sample_count)
        )
        score_variance_sum += sum(
            (score_matrix[row][col] - score_means[col]) ** 2
            for row in range(sample_count)
        )
    scale = covariance_sum / score_variance_sum if score_variance_sum > 0 else 0.0
    cv_terms = [
        [rb_terms[row][col] - scale * score_matrix[row][col] for col in range(param_dim)]
        for row in range(sample_count)
    ]
    rb_estimate = [_mean([row[col] for row in rb_terms]) for col in range(param_dim)]
    cv_estimate = [_mean([row[col] for row in cv_terms]) for col in range(param_dim)]
    naive_terms = _terms(score_matrix, full_signal) if full_signal is not None else None
    naive_variance = _sample_variance(_term_norms(naive_terms)) if naive_terms is not None else None
    rb_variance = _sample_variance(_term_norms(rb_terms))
    cv_variance = _sample_variance(_term_norms(cv_terms))
    ratio = None
    if naive_variance is not None:
        ratio = naive_variance / max(cv_variance, 1e-12)
    return {
        "rao_blackwell_terms": rb_terms,
        "rao_blackwell_estimate": rb_estimate,
        "control_variate_scale": scale,
        "control_variate_terms": cv_terms,
        "control_variate_estimate": cv_estimate,
        "variance": {
            "naive": naive_variance,
            "rao_blackwell": rb_variance,
            "control_variate": cv_variance,
        },
        "variance_reduction_ratio": ratio,
        "diagnostics": {"sample_count": sample_count, "param_dim": param_dim, "finite": True},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input_json).read_text())
    result = reduce_variance(payload["score"], payload["local_signal"], payload.get("full_signal"))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
