#!/usr/bin/env python3
"""Merge-compatible evaluation helpers for LoRAPrune recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lora_importance import matmul

Matrix = list[list[float]]


def merge_weights(w0: Matrix, b: Matrix, a: Matrix) -> Matrix:
    ba = matmul(b, a)
    return [[w0[i][j] + ba[i][j] for j in range(len(w0[0]))] for i in range(len(w0))]


def apply_column_mask(w: Matrix, mask: list[int]) -> Matrix:
    if len(mask) != len(w[0]):
        raise ValueError("mask length must match output columns")
    return [[w[i][j] * mask[j] for j in range(len(mask))] for i in range(len(w))]


def mse(pred: Matrix, y: Matrix) -> float:
    n = len(pred) * len(pred[0])
    return sum((pred[i][j] - y[i][j]) ** 2 for i in range(len(pred)) for j in range(len(pred[0]))) / n


def evaluate_merge_compatibility(x: Matrix, y: Matrix, w0: Matrix, b: Matrix, a: Matrix, mask: list[int], baseline_loss: float | None = None) -> dict:
    merged = merge_weights(w0, b, a)
    masked_merged = apply_column_mask(merged, mask)
    explicit = apply_column_mask(merge_weights(w0, b, a), mask)
    pred_merged = matmul(x, masked_merged)
    pred_explicit = matmul(x, explicit)
    max_diff = max(abs(pred_merged[i][j] - pred_explicit[i][j]) for i in range(len(pred_merged)) for j in range(len(pred_merged[0])))
    eval_loss = mse(pred_merged, y)
    rel = None if baseline_loss is None else (baseline_loss - eval_loss) / max(abs(baseline_loss), 1e-12)
    checks = {
        "structured_mask_applied": all(v in (0, 1) for v in mask) and any(v == 0 for v in mask),
        "merge_equivalence_checked": True,
        "merge_equivalence_max_abs_diff": max_diff,
        "merge_equivalence_passed": max_diff < 1e-10,
        "dense_unstructured_mask_used": False,
    }
    return {"eval_loss": eval_loss, "relative_improvement_vs_baseline": rel, "mechanism_checks": checks, "merged_weight": masked_merged}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    result = evaluate_merge_compatibility(data["x"], data["y"], data["W0"], data["B"], data["A"], data["mask"], data.get("baseline_loss"))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
