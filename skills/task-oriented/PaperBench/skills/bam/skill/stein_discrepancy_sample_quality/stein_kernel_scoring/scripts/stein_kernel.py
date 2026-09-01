#!/usr/bin/env python3
"""Pure-Python RBF Kernelized Stein Discrepancy scoring utilities."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable


def as_2d(values, name: str) -> list[list[float]]:
    if values is None:
        raise ValueError(f"{name} is required")
    if len(values) == 0:
        return []
    if isinstance(values[0], (int, float)):
        array = [[float(value)] for value in values]
    else:
        array = [[float(item) for item in row] for row in values]
    if not array or not array[0]:
        raise ValueError(f"{name} must be non-empty")
    width = len(array[0])
    for row in array:
        if len(row) != width:
            raise ValueError(f"{name} rows must have equal length")
        if any(not math.isfinite(value) for value in row):
            raise ValueError(f"{name} contains non-finite values")
    return array


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return 1.0
    midpoint = n // 2
    if n % 2:
        return ordered[midpoint]
    return 0.5 * (ordered[midpoint - 1] + ordered[midpoint])


def median_bandwidth(samples) -> float:
    x = as_2d(samples, "samples")
    distances = []
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            sq_dist = sum((x[i][dim] - x[j][dim]) ** 2 for dim in range(len(x[i])))
            distance = math.sqrt(sq_dist)
            if distance > 0:
                distances.append(distance)
    return median(distances)


def resolve_scores(samples: list[list[float]], scores) -> list[list[float]]:
    values = scores(samples) if callable(scores) else scores
    score_array = as_2d(values, "scores")
    if len(score_array) != len(samples) or len(score_array[0]) != len(samples[0]):
        raise ValueError("scores shape does not match samples shape")
    return score_array


def rbf_stein_kernel_matrix(samples, scores, bandwidth: float | None = None) -> list[list[float]]:
    x = as_2d(samples, "samples")
    if len(x) < 1:
        raise ValueError("at least one sample is required")
    score_values = resolve_scores(x, scores)
    h = median_bandwidth(x) if bandwidth is None else float(bandwidth)
    if not math.isfinite(h) or h <= 0:
        raise ValueError("bandwidth must be positive and finite")
    dim = len(x[0])
    matrix = []
    for i, xi in enumerate(x):
        row = []
        for j, xj in enumerate(x):
            diff = [xi[k] - xj[k] for k in range(dim)]
            sq_dist = sum(value * value for value in diff)
            kernel = math.exp(-sq_dist / (2.0 * h * h))
            score_dot = sum(score_values[i][k] * score_values[j][k] for k in range(dim))
            sx_grad_y = sum(score_values[i][k] * diff[k] for k in range(dim)) / (h * h)
            grad_x_sy = sum((-diff[k]) * score_values[j][k] for k in range(dim)) / (h * h)
            trace_term = dim / (h * h) - sq_dist / (h ** 4)
            row.append(kernel * (score_dot + sx_grad_y + grad_x_sy + trace_term))
        matrix.append(row)
    return matrix


def validate_square_matrix(stein_matrix) -> list[list[float]]:
    matrix = as_2d(stein_matrix, "stein_matrix")
    if any(len(row) != len(matrix) for row in matrix):
        raise ValueError("stein_matrix must be square")
    return matrix


def ksd_u_statistic(stein_matrix) -> float:
    matrix = validate_square_matrix(stein_matrix)
    n = len(matrix)
    if n < 2:
        raise ValueError("at least two samples are required for a U-statistic")
    total = sum(sum(row) for row in matrix)
    diagonal = sum(matrix[i][i] for i in range(n))
    return (total - diagonal) / (n * (n - 1))


def ksd_v_statistic(stein_matrix) -> float:
    matrix = validate_square_matrix(stein_matrix)
    n = len(matrix)
    return sum(sum(row) for row in matrix) / (n * n)


def score_standard_normal(samples) -> list[list[float]]:
    return [[-value for value in row] for row in as_2d(samples, "samples")]


def summarize_ksd(samples, scores, bandwidth: float | None = None) -> dict:
    x = as_2d(samples, "samples")
    h = median_bandwidth(x) if bandwidth is None else float(bandwidth)
    matrix = rbf_stein_kernel_matrix(x, scores, h)
    max_symmetry_error = max(abs(matrix[i][j] - matrix[j][i]) for i in range(len(matrix)) for j in range(len(matrix)))
    return {
        "n": len(matrix),
        "dimension": len(x[0]),
        "bandwidth": h,
        "ksd_u": ksd_u_statistic(matrix),
        "ksd_v": ksd_v_statistic(matrix),
        "symmetry_error": max_symmetry_error,
        "finite": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="JSON with samples and scores arrays")
    parser.add_argument("--bandwidth", type=float, default=None)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = summarize_ksd(data["samples"], data["scores"], args.bandwidth)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
