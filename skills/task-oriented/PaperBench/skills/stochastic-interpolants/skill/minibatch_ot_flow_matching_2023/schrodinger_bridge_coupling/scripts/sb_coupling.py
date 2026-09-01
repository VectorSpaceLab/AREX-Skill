from __future__ import annotations

import json
import math
from typing import Sequence


def squared_distance(a: Sequence[float], b: Sequence[float]) -> float:
    return sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))


def row_normalized_gibbs(source: Sequence[Sequence[float]], target: Sequence[Sequence[float]], epsilon: float) -> dict:
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    costs = [[squared_distance(a, b) for b in target] for a in source]
    weights = []
    for row in costs:
        minimum = min(row)
        raw = [math.exp(-(c - minimum) / epsilon) for c in row]
        total = sum(raw)
        weights.append([v / total for v in raw])
    return {"cost_matrix": costs, "row_coupling": weights, "epsilon": epsilon}


def bridge_std(t: float, sigma: float) -> float:
    if t < 0.0 or t > 1.0:
        raise ValueError("t must lie in [0, 1]")
    if sigma < 0.0:
        raise ValueError("sigma must be non-negative")
    return sigma * math.sqrt(t * (1.0 - t))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    args = parser.parse_args()
    payload = json.load(open(args.input_json, "r", encoding="utf-8"))
    result = row_normalized_gibbs(payload["source"], payload["target"], payload["epsilon"])
    result["bridge_std"] = bridge_std(payload.get("t", 0.5), payload.get("sigma", 1.0))
    print(json.dumps(result, indent=2))
