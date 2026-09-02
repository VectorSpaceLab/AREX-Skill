#!/usr/bin/env python3
"""Deterministic two-sample metrics for posterior sample comparison."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, data: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_samples(data: dict) -> list[list[float]]:
    samples = data.get("samples", data)
    if not isinstance(samples, list) or not samples:
        raise ValueError("samples must be a non-empty list")
    if samples and isinstance(samples[0], (int, float)):
        samples = [[float(item)] for item in samples]
    result = [[float(v) for v in row] for row in samples]
    dim = len(result[0])
    if dim <= 0 or any(len(row) != dim for row in result):
        raise ValueError("sample dimensions are inconsistent")
    return result


def column_stats(samples: list[list[float]]) -> tuple[list[float], list[float]]:
    dim = len(samples[0])
    means = [sum(row[j] for row in samples) / len(samples) for j in range(dim)]
    stds = []
    for j in range(dim):
        var = sum((row[j] - means[j]) ** 2 for row in samples) / max(len(samples) - 1, 1)
        stds.append(math.sqrt(var) if var > 1e-12 else 1.0)
    return means, stds


def zscore(samples: list[list[float]], means: list[float], stds: list[float]) -> list[list[float]]:
    return [[(row[j] - means[j]) / stds[j] for j in range(len(row))] for row in samples]


def mean_vector(samples: list[list[float]]) -> list[float]:
    dim = len(samples[0])
    return [sum(row[j] for row in samples) / len(samples) for j in range(dim)]


def squared_distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def nearest_centroid_accuracy(reference: list[list[float]], approximate: list[list[float]]) -> float:
    n = min(len(reference), len(approximate))
    if n < 4:
        raise ValueError("at least four samples from each distribution are required")
    reference = reference[:n]
    approximate = approximate[:n]
    folds = min(5, n)
    correct = 0
    total = 0
    for fold in range(folds):
        train_ref = [row for idx, row in enumerate(reference) if idx % folds != fold]
        train_app = [row for idx, row in enumerate(approximate) if idx % folds != fold]
        test_ref = [row for idx, row in enumerate(reference) if idx % folds == fold]
        test_app = [row for idx, row in enumerate(approximate) if idx % folds == fold]
        centroid_ref = mean_vector(train_ref)
        centroid_app = mean_vector(train_app)
        for row in test_ref:
            pred_app = squared_distance(row, centroid_app) < squared_distance(row, centroid_ref)
            correct += 0 if pred_app else 1
            total += 1
        for row in test_app:
            pred_app = squared_distance(row, centroid_app) < squared_distance(row, centroid_ref)
            correct += 1 if pred_app else 0
            total += 1
    return correct / total


def compute_metrics(reference_samples: list[list[float]], approximate_samples: list[list[float]]) -> dict:
    if len(reference_samples[0]) != len(approximate_samples[0]):
        raise ValueError("reference and approximate sample dimensions differ")
    means, stds = column_stats(reference_samples)
    ref_z = zscore(reference_samples, means, stds)
    app_z = zscore(approximate_samples, means, stds)
    accuracy = nearest_centroid_accuracy(ref_z, app_z)
    ref_mean = mean_vector(ref_z)
    app_mean = mean_vector(app_z)
    mmd2 = squared_distance(ref_mean, app_mean)
    distance_to_ideal = abs(accuracy - 0.5)
    return {
        "schema_version": 1,
        "metric": "c2st_accuracy",
        "c2st_accuracy": accuracy,
        "c2st_distance_to_ideal": distance_to_ideal,
        "mmd2": mmd2,
        "num_reference": len(reference_samples),
        "num_approximate": len(approximate_samples),
        "dimension": len(reference_samples[0]),
        "ideal_c2st_accuracy": 0.5,
        "interpretation": "closer to chance-level 0.5 is better; values farther from 0.5 indicate more distinguishable sample sets under this classifier",
    }


def self_test() -> dict:
    reference = [[-0.2], [0.0], [0.2], [0.4], [0.6], [0.8], [1.0], [1.2]]
    identical = [row[:] for row in reference]
    shifted = [[row[0] + 3.0] for row in reference]
    same = compute_metrics(reference, identical)
    different = compute_metrics(reference, shifted)
    return {
        "ok": same["c2st_accuracy"] <= 0.625 and different["c2st_accuracy"] > same["c2st_accuracy"],
        "same": same,
        "different": different,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    compute = sub.add_parser("compute")
    compute.add_argument("--reference", required=True)
    compute.add_argument("--approximate", required=True)
    compute.add_argument("--output", required=True)
    sub.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "compute":
        metrics = compute_metrics(extract_samples(read_json(args.reference)), extract_samples(read_json(args.approximate)))
        write_json(args.output, metrics)
    elif args.command == "self-test":
        print(json.dumps(self_test(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
