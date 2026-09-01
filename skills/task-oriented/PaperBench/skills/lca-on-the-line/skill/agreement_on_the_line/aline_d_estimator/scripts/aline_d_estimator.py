#!/usr/bin/env python3
"""ALine-D OOD accuracy estimator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import NormalDist

_NORMAL = NormalDist()


def normal_cdf(value: float) -> float:
    return _NORMAL.cdf(float(value))


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in zip(*matrix)]


def matmul(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [[sum(a * b for a, b in zip(row, col)) for col in transpose(right)] for row in left]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    aug = [list(matrix[i]) + [vector[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-10:
            raise ValueError("linear system is singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [value - factor * ref for value, ref in zip(aug[row], aug[col])]
    return [row[-1] for row in aug]


def least_squares(matrix: list[list[float]], vector: list[float]) -> list[float]:
    mt = transpose(matrix)
    mtm = matmul(mt, matrix)
    mtv = matvec(mt, vector)
    return solve_linear_system(mtm, mtv)


def estimate_aline_d(stats: dict, fit: dict) -> dict:
    models = stats["models"]
    if len(models) < 3:
        raise ValueError("ALine-D requires at least three models")
    model_index = {model: idx for idx, model in enumerate(models)}
    slope = fit["slope"]
    rows = []
    targets = []
    for key, pair in stats["pairwise"].items():
        left, right = pair["models"]
        row = [0.0] * len(models)
        row[model_index[left]] = 0.5
        row[model_index[right]] = 0.5
        pair_probit = stats["pairwise_probit"][key]
        target = pair_probit["ood_agreement"] + slope * (
            (stats["id_accuracy_probit"][left] + stats["id_accuracy_probit"][right]) / 2.0
            - pair_probit["id_agreement"]
        )
        rows.append(row)
        targets.append(target)
    solution = least_squares(rows, targets)
    predicted = {model: normal_cdf(solution[model_index[model]]) for model in models}
    residuals = [sum(a * b for a, b in zip(row, solution)) - target for row, target in zip(rows, targets)]
    simple = {
        model: normal_cdf(fit["slope"] * stats["id_accuracy_probit"][model] + fit["intercept"])
        for model in models
    }
    return {
        "models": models,
        "predicted_ood_accuracy": predicted,
        "predicted_ood_accuracy_probit": {model: solution[model_index[model]] for model in models},
        "aline_s_predicted_ood_accuracy": simple,
        "equation_count": len(rows),
        "residual_l2": sum(r * r for r in residuals) ** 0.5,
        "residual_max_abs": max(abs(r) for r in residuals),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stats")
    parser.add_argument("fit")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    stats = json.loads(Path(args.stats).read_text())
    fit = json.loads(Path(args.fit).read_text())
    result = estimate_aline_d(stats, fit)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
