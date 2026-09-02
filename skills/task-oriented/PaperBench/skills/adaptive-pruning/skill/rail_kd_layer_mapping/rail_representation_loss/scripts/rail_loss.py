#!/usr/bin/env python3
"""Pure-Python RAIL-KD representation loss utilities."""
from __future__ import annotations

import argparse
import json
import math
from typing import List, Sequence, Tuple

Vector = List[float]
Matrix = List[List[float]]
Layer = List[Vector]


def mean_pool(layer: Layer) -> Vector:
    if not layer or not layer[0]:
        raise ValueError("layer must contain at least one token and one feature")
    dim = len(layer[0])
    if any(len(tok) != dim for tok in layer):
        raise ValueError("all tokens in a layer must share a feature dimension")
    return [sum(tok[j] for tok in layer) / len(layer) for j in range(dim)]


def matvec(matrix: Matrix, vector: Sequence[float]) -> Vector:
    if not matrix:
        raise ValueError("projection matrix must not be empty")
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("projection row width must match vector length")
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def l2_normalize(vector: Sequence[float], eps: float = 1e-12) -> Vector:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm < eps:
        raise ValueError("cannot normalize a near-zero vector")
    return [v / norm for v in vector]


def squared_distance(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("distance vectors must have same length")
    return sum((x - y) ** 2 for x, y in zip(a, b))


def layerwise_loss(teacher_layers: List[Layer], student_layers: List[Layer], teacher_proj: Matrix, student_proj: Matrix, alphas: Sequence[float] | None = None) -> Tuple[float, dict]:
    if len(teacher_layers) != len(student_layers) or not teacher_layers:
        raise ValueError("teacher and student selected layer counts must match and be non-empty")
    if alphas is None:
        alphas = [1.0] * len(teacher_layers)
    if len(alphas) != len(teacher_layers):
        raise ValueError("alpha count must match selected layer count")
    distances = []
    total = 0.0
    for i, (tl, sl, alpha) in enumerate(zip(teacher_layers, student_layers, alphas)):
        tp = mean_pool(tl)
        sp = mean_pool(sl)
        tn = l2_normalize(matvec(teacher_proj, tp))
        sn = l2_normalize(matvec(student_proj, sp))
        dist = squared_distance(tn, sn)
        distances.append({"layer": i, "alpha": alpha, "distance": dist})
        total += alpha * dist
    return total, {"variant": "layerwise", "per_layer": distances, "mean_pooling_used": True, "l2_normalization_used": True}


def concatenated_loss(teacher_layers: List[Layer], student_layers: List[Layer], teacher_proj: Matrix, student_proj: Matrix) -> Tuple[float, dict]:
    if len(teacher_layers) != len(student_layers) or not teacher_layers:
        raise ValueError("teacher and student selected layer counts must match and be non-empty")
    tv = []
    sv = []
    for tl, sl in zip(teacher_layers, student_layers):
        tv.extend(mean_pool(tl))
        sv.extend(mean_pool(sl))
    tn = l2_normalize(matvec(teacher_proj, tv))
    sn = l2_normalize(matvec(student_proj, sv))
    dist = squared_distance(tn, sn)
    return dist, {"variant": "concatenated", "distance": dist, "mean_pooling_used": True, "l2_normalization_used": True}


def demo() -> dict:
    teacher = [[[1.0, 2.0], [3.0, 4.0]], [[2.0, 0.0], [4.0, 2.0]]]
    student = [[[1.0, 1.5], [2.5, 4.0]], [[1.5, 0.0], [3.5, 2.5]]]
    ident = [[1.0, 0.0], [0.0, 1.0]]
    cat = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]
    l_loss, l_diag = layerwise_loss(teacher, student, ident, ident)
    c_loss, c_diag = concatenated_loss(teacher, student, cat, cat)
    return {"layerwise_loss": l_loss, "layerwise_diag": l_diag, "concatenated_loss": c_loss, "concatenated_diag": c_diag}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        print(json.dumps(demo(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
