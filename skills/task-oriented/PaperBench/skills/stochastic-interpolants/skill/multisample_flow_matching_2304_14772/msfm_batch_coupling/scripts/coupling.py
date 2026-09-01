#!/usr/bin/env python3
import argparse
import itertools
import json
import math
from pathlib import Path


def _as_vectors(batch):
    if not isinstance(batch, list) or not batch:
        raise ValueError("batch must be a non-empty list")
    vectors = []
    dim = None
    for row in batch:
        if not isinstance(row, list) or not row:
            raise ValueError("each sample must be a non-empty numeric vector")
        vector = [float(x) for x in row]
        if dim is None:
            dim = len(vector)
        elif len(vector) != dim:
            raise ValueError("all vectors must have the same dimension")
        vectors.append(vector)
    return vectors


def squared_cost(a, b):
    if len(a) != len(b):
        raise ValueError("vector dimensions differ")
    return sum((x - y) ** 2 for x, y in zip(a, b))


def pairwise_costs(source, target):
    source = _as_vectors(source)
    target = _as_vectors(target)
    if len(source) != len(target):
        raise ValueError("source and target batches must have equal length")
    return [[squared_cost(a, b) for b in target] for a in source]


def uniform_coupling(source, target):
    costs = pairwise_costs(source, target)
    k = len(costs)
    matrix = [[1.0 / k for _ in range(k)] for _ in range(k)]
    expected_cost = sum(costs[i][j] * matrix[i][j] for i in range(k) for j in range(k))
    return {
        "method": "uniform",
        "pairs": [(i, i) for i in range(k)],
        "coupling_matrix": matrix,
        "transport_cost": expected_cost,
        "row_sums": [sum(row) for row in matrix],
        "column_sums": [sum(matrix[i][j] for i in range(k)) for j in range(k)],
    }


def batch_ot_coupling(source, target):
    costs = pairwise_costs(source, target)
    k = len(costs)
    best_perm = None
    best_cost = math.inf
    for perm in itertools.permutations(range(k)):
        cost = sum(costs[i][perm[i]] for i in range(k)) / k
        if cost < best_cost:
            best_cost = cost
            best_perm = perm
    matrix = [[0.0 for _ in range(k)] for _ in range(k)]
    for i, j in enumerate(best_perm):
        matrix[i][j] = 1.0
    return {
        "method": "batch_ot",
        "pairs": [(i, int(j)) for i, j in enumerate(best_perm)],
        "coupling_matrix": matrix,
        "transport_cost": best_cost,
        "row_sums": [sum(row) for row in matrix],
        "column_sums": [sum(matrix[i][j] for i in range(k)) for j in range(k)],
    }


def build_coupling(source, target, method):
    if method == "uniform":
        return uniform_coupling(source, target)
    if method == "batch_ot":
        return batch_ot_coupling(source, target)
    raise ValueError("method must be 'uniform' or 'batch_ot'")


def _self_test():
    source = [[0.0], [10.0]]
    target = [[9.0], [1.0]]
    uniform = build_coupling(source, target, "uniform")
    batch_ot = build_coupling(source, target, "batch_ot")
    assert batch_ot["pairs"] == [(0, 1), (1, 0)]
    assert batch_ot["transport_cost"] < uniform["transport_cost"]
    assert batch_ot["row_sums"] == [1.0, 1.0]
    assert batch_ot["column_sums"] == [1.0, 1.0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON with source, target, and method")
    parser.add_argument("--output", help="path for coupling JSON")
    parser.add_argument("--method", choices=["uniform", "batch_ot"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return
    payload = json.loads(Path(args.input).read_text())
    method = args.method or payload.get("method", "batch_ot")
    result = build_coupling(payload["source"], payload["target"], method)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
