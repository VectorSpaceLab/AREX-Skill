#!/usr/bin/env python3
"""Diagonal Fisher helpers for EWC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def diagonal_fisher(gradients: list[list[float]]) -> list[float]:
    if not gradients:
        raise ValueError("at least one gradient vector is required")
    width = len(gradients[0])
    if width == 0:
        raise ValueError("gradient vectors must be non-empty")
    accum = [0.0] * width
    for grad in gradients:
        if len(grad) != width:
            raise ValueError("all gradient vectors must have the same dimension")
        for index, value in enumerate(grad):
            accum[index] += float(value) * float(value)
    return [value / len(gradients) for value in accum]


def trace_normalize(fisher: list[float]) -> list[float]:
    if any(value < 0 for value in fisher):
        raise ValueError("fisher entries must be nonnegative")
    total = sum(fisher)
    if total == 0:
        return [0.0 for _ in fisher]
    return [value / total for value in fisher]


def fisher_overlap(first: list[float], second: list[float]) -> float:
    if len(first) != len(second):
        raise ValueError("fisher vectors must have the same dimension")
    norm_first = trace_normalize(first)
    norm_second = trace_normalize(second)
    return sum(min(left, right) for left, right in zip(norm_first, norm_second))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file containing {'gradients': [[...]]}")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    fisher = diagonal_fisher(data["gradients"])
    result = {"schema_version": 1, "fisher": fisher, "normalized_fisher": trace_normalize(fisher)}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
