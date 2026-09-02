#!/usr/bin/env python3
"""LoRA-guided importance utilities for LoRAPrune."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

Matrix = list[list[float]]


def shape(m: Matrix) -> tuple[int, int]:
    if not isinstance(m, list) or not m or not all(isinstance(r, list) and r for r in m):
        raise ValueError("matrix must be a non-empty list of non-empty rows")
    cols = len(m[0])
    if any(len(r) != cols for r in m):
        raise ValueError("matrix rows must have equal length")
    return len(m), cols


def matmul(a: Matrix, b: Matrix) -> Matrix:
    ar, ac = shape(a)
    br, bc = shape(b)
    if ac != br:
        raise ValueError(f"matmul shape mismatch: {(ar, ac)} x {(br, bc)}")
    return [[sum(a[i][t] * b[t][j] for t in range(ac)) for j in range(bc)] for i in range(ar)]


def add(a: Matrix, b: Matrix) -> Matrix:
    if shape(a) != shape(b):
        raise ValueError("add shape mismatch")
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def sub(a: Matrix, b: Matrix) -> Matrix:
    if shape(a) != shape(b):
        raise ValueError("sub shape mismatch")
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def lora_guided_importance(w0: Matrix, b: Matrix, a: Matrix, grad_b: Matrix, grad_a: Matrix) -> dict:
    """Compute Eq. 10 style LoRA-guided element importance without grad_W0."""
    d, k = shape(w0)
    db, r = shape(b)
    ra, ka = shape(a)
    if (db, ka) != (d, k) or r != ra:
        raise ValueError("W0, B, and A shapes are incompatible")
    if shape(grad_b) != (d, r) or shape(grad_a) != (r, k):
        raise ValueError("gradient shapes are incompatible")
    ba = matmul(b, a)
    grad_approx = sub(add(matmul(grad_b, a), matmul(b, grad_a)), matmul(grad_b, grad_a))
    merged = add(w0, ba)
    importance = [[(grad_approx[i][j] * merged[i][j]) ** 2 for j in range(k)] for i in range(d)]
    return {
        "importance": importance,
        "diagnostics": {
            "shape": [d, k],
            "rank": r,
            "uses_base_gradients": False,
            "formula": "((grad_B@A + B@grad_A - grad_B@grad_A) * (W0 + B@A))^2",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    result = lora_guided_importance(data["W0"], data["B"], data["A"], data["grad_B"], data["grad_A"])
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
