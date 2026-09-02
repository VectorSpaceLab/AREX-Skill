#!/usr/bin/env python3
"""Squared MMD and recovery-result packaging utilities."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def as_vectors(samples: list) -> list[list[float]]:
    vectors = []
    for sample in samples:
        if isinstance(sample, list):
            vectors.append([float(value) for value in sample])
        else:
            vectors.append([float(sample)])
    if not vectors:
        raise ValueError("samples must be non-empty")
    dim = len(vectors[0])
    if any(len(vector) != dim for vector in vectors):
        raise ValueError("all samples must have the same dimension")
    return vectors


def squared_distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def median_bandwidth(x: list[list[float]], y: list[list[float]]) -> float:
    values = x + y
    distances = []
    for i, first in enumerate(values):
        for second in values[i + 1 :]:
            distance = squared_distance(first, second)
            if distance > 0:
                distances.append(distance)
    if not distances:
        return 1.0
    distances.sort()
    return distances[len(distances) // 2]


def kernel(a: list[float], b: list[float], bandwidth: float) -> float:
    return math.exp(-squared_distance(a, b) / (2.0 * bandwidth))


def squared_mmd(samples, references) -> float:
    x = as_vectors(samples)
    y = as_vectors(references)
    if len(x[0]) != len(y[0]):
        raise ValueError("sample dimensions must match")
    bandwidth = median_bandwidth(x, y)
    xx = sum(kernel(a, b, bandwidth) for a in x for b in x) / (len(x) * len(x))
    yy = sum(kernel(a, b, bandwidth) for a in y for b in y) / (len(y) * len(y))
    xy = sum(kernel(a, b, bandwidth) for a in x for b in y) / (len(x) * len(y))
    return max(0.0, xx + yy - 2.0 * xy)


def build_recovery_result(paper_id: str, target: dict, samples, references, threshold: float, mechanism_checks: dict, commands: list[str], artifacts: list[str]) -> dict:
    metric = squared_mmd(samples, references)
    return {
        "schema_version": 1,
        "paper_id": paper_id,
        "experiment": target["dataset"],
        "is_proxy": bool(target.get("proxy", False)),
        "sample_count": len(samples),
        "metrics": {"squared_mmd": metric, "threshold": threshold, "passes_threshold": float(metric <= threshold)},
        "paper_target": target,
        "commands": commands,
        "artifacts": artifacts,
        "mechanism_checks": mechanism_checks,
        "notes": "Reduced proxy recovery for the F-NPSE score-composition mechanism; not a full benchmark reproduction.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-json", required=True)
    parser.add_argument("--references-json", required=True)
    parser.add_argument("--target-json", required=True)
    parser.add_argument("--mechanism-json", required=True)
    parser.add_argument("--threshold", type=float, default=0.25)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    samples = json.loads(Path(args.samples_json).read_text(encoding="utf-8"))
    references = json.loads(Path(args.references_json).read_text(encoding="utf-8"))
    target = json.loads(Path(args.target_json).read_text(encoding="utf-8"))
    mechanism = json.loads(Path(args.mechanism_json).read_text(encoding="utf-8"))
    result = build_recovery_result(args.paper_id, target, samples, references, args.threshold, mechanism, args.command, args.artifact)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "squared_mmd": result["metrics"]["squared_mmd"], "output": args.output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
