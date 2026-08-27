#!/usr/bin/env python3
"""Self-contained KNN demo adapted for the ML Glossary runtime.

The original repository included a small KNN teaching script. This bundled
version keeps the educational behavior but is Python 3, deterministic, and free
of original-checkout dependencies.

Example:
    python knn_demo.py
"""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Callable, Iterable, Sequence


def euclidean_distance(point1: Sequence[float], point2: Sequence[float]) -> float:
    if len(point1) != len(point2):
        raise ValueError(f"points must have the same dimension, got {len(point1)} and {len(point2)}")
    return sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))


def mean(labels: Sequence[float]) -> float:
    return sum(labels) / len(labels)


def mode(labels: Sequence[int]) -> int:
    return Counter(labels).most_common(1)[0][0]


def knn(training_data: Sequence[Sequence[float]], target: Sequence[float], k: int, reducer: Callable[[Sequence], float | int]):
    """Return nearest neighbors and a reduced prediction.

    Each training row stores features followed by the label/value in the final
    position. For classification pass ``mode`` as reducer; for regression pass
    ``mean``.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(training_data):
        raise ValueError("k cannot exceed the number of training rows")
    neighbors: list[tuple[float, int]] = []
    for index, row in enumerate(training_data):
        distance = euclidean_distance(row[:-1], target)
        neighbors.append((distance, index))
    nearest = sorted(neighbors)[:k]
    labels = [training_data[index][-1] for _, index in nearest]
    return nearest, reducer(labels)


def main() -> int:
    regression_data = [
        [73.84, 241.89],
        [68.78, 162.31],
        [74.11, 212.74],
        [71.73, 220.04],
        [69.88, 206.34],
        [67.25, 152.21],
        [63.45, 156.39],
    ]
    nearest, prediction = knn(regression_data, [70.0], k=3, reducer=mean)
    print("Regression toy: predict weight from height")
    print(f"nearest={nearest}")
    print(f"predicted_weight={prediction:.2f}")

    classification_data = [
        [26, 1],
        [20, 1],
        [22, 1],
        [19, 1],
        [28, 0],
        [33, 0],
        [30, 0],
        [50, 0],
    ]
    nearest, prediction = knn(classification_data, [32], k=3, reducer=mode)
    print("\nClassification toy: predict paragliding preference from age")
    print(f"nearest={nearest}")
    print(f"predicted_class={prediction}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
