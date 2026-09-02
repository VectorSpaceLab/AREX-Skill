#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math


def ensure_matrix(matrix: list[list[float]], name: str) -> tuple[int, int]:
    if not matrix or not isinstance(matrix, list) or not isinstance(matrix[0], list) or not matrix[0]:
        raise ValueError(f"{name} must be a non-empty matrix")
    width = len(matrix[0])
    for row in matrix:
        if len(row) != width:
            raise ValueError(f"{name} must be rectangular")
    return len(matrix), width


def matmul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    _, left_width = ensure_matrix(left, "left")
    right_rows, right_width = ensure_matrix(right, "right")
    if left_width != right_rows:
        raise ValueError("matrix dimensions do not align")
    return [[sum(row[k] * right[k][j] for k in range(left_width)) for j in range(right_width)] for row in left]


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    ensure_matrix(matrix, "matrix")
    return [list(col) for col in zip(*matrix)]


def softmax(row: list[float]) -> list[float]:
    maximum = max(row)
    values = [math.exp(value - maximum) for value in row]
    total = sum(values)
    return [value / total for value in values]


def cross_attention(features: list[list[float]], tokens: list[list[float]], wq: list[list[float]], wk: list[list[float]], wv: list[list[float]]) -> dict:
    ensure_matrix(features, "features")
    ensure_matrix(tokens, "tokens")
    queries = matmul(features, wq)
    keys = matmul(tokens, wk)
    values = matmul(tokens, wv)
    _, key_dim = ensure_matrix(keys, "keys")
    scores = matmul(queries, transpose(keys))
    scaled_scores = [[value / math.sqrt(key_dim) for value in row] for row in scores]
    probabilities = [softmax(row) for row in scaled_scores]
    conditioned = matmul(probabilities, values)
    return {
        "conditioned": conditioned,
        "probabilities": probabilities,
        "row_sums": [sum(row) for row in probabilities],
        "feature_rows": len(features),
        "token_rows": len(tokens),
    }


def demo() -> dict:
    features = [[1.0, 0.0], [0.0, 1.0]]
    tokens = [[1.0, 0.5], [-0.5, 1.0]]
    identity = [[1.0, 0.0], [0.0, 1.0]]
    return cross_attention(features, tokens, identity, identity, identity)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = demo()
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
