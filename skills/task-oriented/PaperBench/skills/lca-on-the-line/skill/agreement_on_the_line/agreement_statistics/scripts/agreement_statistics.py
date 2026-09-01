#!/usr/bin/env python3
"""Agreement, accuracy, and probit statistics for ALine recovery."""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from statistics import NormalDist

_NORMAL = NormalDist()


def clip_probability(value: float, epsilon: float = 1e-4) -> float:
    return min(1.0 - epsilon, max(epsilon, float(value)))


def probit(value: float, epsilon: float = 1e-4) -> float:
    return _NORMAL.inv_cdf(clip_probability(value, epsilon))


def normal_cdf(value: float) -> float:
    return _NORMAL.cdf(float(value))


def fraction_equal(left: list, right: list) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("lists must have equal non-zero length")
    return sum(1 for a, b in zip(left, right) if a == b) / len(left)


def compute_statistics(table: dict, epsilon: float = 1e-4) -> dict:
    models = table["models"]
    id_labels = table["id_labels"]
    id_predictions = table["id_predictions"]
    ood_predictions = table["ood_predictions"]
    id_accuracy = {model: fraction_equal(id_predictions[model], id_labels) for model in models}
    pairwise = {}
    for left, right in combinations(models, 2):
        key = f"{left}::{right}"
        pairwise[key] = {
            "models": [left, right],
            "id_agreement": fraction_equal(id_predictions[left], id_predictions[right]),
            "ood_agreement": fraction_equal(ood_predictions[left], ood_predictions[right]),
        }
    return {
        "epsilon": epsilon,
        "models": models,
        "id_accuracy": id_accuracy,
        "id_accuracy_probit": {m: probit(v, epsilon) for m, v in id_accuracy.items()},
        "pairwise": pairwise,
        "pairwise_probit": {
            key: {
                "id_agreement": probit(value["id_agreement"], epsilon),
                "ood_agreement": probit(value["ood_agreement"], epsilon),
            }
            for key, value in pairwise.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    parser.add_argument("--epsilon", type=float, default=1e-4)
    args = parser.parse_args()
    table = json.loads(Path(args.input).read_text())
    stats = compute_statistics(table, args.epsilon)
    Path(args.output).write_text(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
