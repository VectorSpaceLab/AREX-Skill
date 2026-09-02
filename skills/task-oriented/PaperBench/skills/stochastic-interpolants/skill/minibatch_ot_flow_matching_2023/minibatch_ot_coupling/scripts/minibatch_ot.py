from __future__ import annotations

import itertools
import json
from typing import Sequence


def squared_distance(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("point dimensions must match")
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))


def cost_matrix(source: Sequence[Sequence[float]], target: Sequence[Sequence[float]]) -> list[list[float]]:
    if len(source) != len(target):
        raise ValueError("source and target batch sizes must match")
    return [[squared_distance(a, b) for b in target] for a in source]


def assignment_cost(matrix: Sequence[Sequence[float]], permutation: Sequence[int]) -> float:
    return sum(float(matrix[i][j]) for i, j in enumerate(permutation))


def exact_minibatch_ot(source: Sequence[Sequence[float]], target: Sequence[Sequence[float]]) -> dict:
    matrix = cost_matrix(source, target)
    n = len(matrix)
    if n == 0:
        raise ValueError("batch must be non-empty")
    if n > 8:
        raise ValueError("exact enumerator is only intended for n <= 8")
    best_perm = None
    best_cost = None
    for perm in itertools.permutations(range(n)):
        cost = assignment_cost(matrix, perm)
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_perm = list(perm)
    pairs = [{"source_index": i, "target_index": j, "cost": matrix[i][j]} for i, j in enumerate(best_perm)]
    return {"permutation": best_perm, "transport_cost": best_cost, "cost_matrix": matrix, "pairs": pairs}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    payload = json.load(open(args.input_json, "r", encoding="utf-8"))
    print(json.dumps(exact_minibatch_ot(payload["source"], payload["target"]), indent=2))
