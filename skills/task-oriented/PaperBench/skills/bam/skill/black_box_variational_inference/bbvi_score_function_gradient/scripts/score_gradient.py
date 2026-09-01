#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _as_matrix(score):
    if not isinstance(score, list) or not score:
        raise ValueError("score must be a non-empty list")
    if isinstance(score[0], list):
        matrix = [[float(value) for value in row] for row in score]
    else:
        matrix = [[float(value)] for value in score]
    width = len(matrix[0])
    if width == 0 or any(len(row) != width for row in matrix):
        raise ValueError("score rows must have consistent non-zero width")
    return matrix


def _check_finite(values, name):
    for value in values:
        if isinstance(value, list):
            _check_finite(value, name)
        elif not math.isfinite(float(value)):
            raise ValueError(f"{name} contains non-finite value")


def estimate_score_gradient(logp, logq, score):
    logp = [float(value) for value in logp]
    logq = [float(value) for value in logq]
    score_matrix = _as_matrix(score)
    if len(logp) != len(logq) or len(logp) != len(score_matrix):
        raise ValueError("logp, logq, and score must share the same sample count")
    if len(logp) == 0:
        raise ValueError("at least one sample is required")
    _check_finite(logp, "logp")
    _check_finite(logq, "logq")
    _check_finite(score_matrix, "score")
    learning_signal = [lp - lq for lp, lq in zip(logp, logq)]
    gradient_terms = [
        [score_value * signal for score_value in row]
        for row, signal in zip(score_matrix, learning_signal)
    ]
    sample_count = len(gradient_terms)
    param_dim = len(gradient_terms[0])
    gradient_estimate = [
        sum(row[col] for row in gradient_terms) / sample_count
        for col in range(param_dim)
    ]
    return {
        "learning_signal": learning_signal,
        "gradient_terms": gradient_terms,
        "gradient_estimate": gradient_estimate,
        "diagnostics": {
            "sample_count": sample_count,
            "param_dim": param_dim,
            "finite": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input_json).read_text())
    result = estimate_score_gradient(payload["logp"], payload["logq"], payload["score"])
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
