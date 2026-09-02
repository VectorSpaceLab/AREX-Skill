#!/usr/bin/env python3
import argparse
import json


def _transpose(matrix):
    return [list(col) for col in zip(*matrix)]


def _rank(matrix, tol=1e-10):
    rows = [list(map(float, row)) for row in matrix]
    if not rows:
        return 0
    row_count = len(rows)
    col_count = len(rows[0])
    rank = 0
    pivot_row = 0
    for col in range(col_count):
        pivot = None
        for row in range(pivot_row, row_count):
            if abs(rows[row][col]) > tol:
                pivot = row
                break
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        pivot_value = rows[pivot_row][col]
        rows[pivot_row] = [value / pivot_value for value in rows[pivot_row]]
        for row in range(row_count):
            if row != pivot_row and abs(rows[row][col]) > tol:
                factor = rows[row][col]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[pivot_row])]
        rank += 1
        pivot_row += 1
    return rank


def compute_activation_statistics(activations, min_samples=None):
    if not isinstance(activations, list) or not activations or not isinstance(activations[0], list) or not activations[0]:
        raise ValueError("activations must be a non-empty 2D matrix")
    feature_dim = len(activations[0])
    rows = []
    for row in activations:
        if len(row) != feature_dim:
            raise ValueError("activation rows must have equal length")
        converted = [float(value) for value in row]
        if any(value != value or value in (float("inf"), float("-inf")) for value in converted):
            raise ValueError("activations must be finite")
        rows.append(converted)
    sample_count = len(rows)
    mu = [sum(row[col] for row in rows) / sample_count for col in range(feature_dim)]
    if sample_count == 1:
        sigma = [[0.0 for _ in range(feature_dim)] for _ in range(feature_dim)]
    else:
        centered = [[value - mu[col] for col, value in enumerate(row)] for row in rows]
        sigma = []
        for i in range(feature_dim):
            sigma_row = []
            for j in range(feature_dim):
                sigma_row.append(sum(row[i] * row[j] for row in centered) / (sample_count - 1))
            sigma.append(sigma_row)
    warnings = []
    threshold = feature_dim if min_samples is None else int(min_samples)
    if sample_count <= threshold:
        warnings.append("sample_count_not_greater_than_feature_dim_or_minimum")
    diagnostics = {
        "sample_count": sample_count,
        "feature_dim": feature_dim,
        "covariance_symmetric": all(abs(sigma[i][j] - sigma[j][i]) < 1e-10 for i in range(feature_dim) for j in range(feature_dim)),
        "covariance_rank": _rank(sigma),
        "warnings": warnings,
    }
    return {"mu": mu, "sigma": sigma, "diagnostics": diagnostics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(open(args.input_json, encoding="utf-8").read())
    result = compute_activation_statistics(data["activations"], data.get("min_samples"))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
