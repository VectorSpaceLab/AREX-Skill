#!/usr/bin/env python3
"""Tiny deterministic LoRAPrune progressive loop for recovery and tests."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lora_importance import lora_guided_importance, matmul
from group_pruning import structured_pruning_mask

Matrix = list[list[float]]


def transpose(m: Matrix) -> Matrix:
    return [list(row) for row in zip(*m)]


def mse_and_grads(x: Matrix, y: Matrix, w0: Matrix, b: Matrix, a: Matrix, row_mask: list[int]) -> tuple[float, Matrix, Matrix]:
    # Forward: pred = (x @ (W0 + B@A)) with output row/group mask on columns.
    ba = matmul(b, a)
    w = [[w0[i][j] + ba[i][j] for j in range(len(w0[0]))] for i in range(len(w0))]
    pred = matmul(x, w)
    n = len(x) * len(y[0])
    d_pred = []
    loss = 0.0
    for i in range(len(pred)):
        row = []
        for j in range(len(pred[0])):
            masked_pred = pred[i][j] * row_mask[j]
            diff = masked_pred - y[i][j]
            loss += diff * diff / n
            row.append(2.0 * diff * row_mask[j] / n)
        d_pred.append(row)
    d_w = matmul(transpose(x), d_pred)
    grad_b = matmul(d_w, transpose(a))
    grad_a = matmul(transpose(b), d_w)
    return loss, grad_b, grad_a


def apply_sgd(param: Matrix, grad: Matrix, lr: float) -> Matrix:
    return [[param[i][j] - lr * grad[i][j] for j in range(len(param[0]))] for i in range(len(param))]


def flatten(m: Matrix) -> list[float]:
    return [v for row in m for v in row]


def run_progressive_loop(data: dict) -> dict:
    x, y = data["x"], data["y"]
    w0, b, a = data["W0"], data["B"], data["A"]
    iterations = int(data.get("iterations", 4))
    lr = float(data.get("lr", 0.05))
    target_prune_count = int(data.get("target_prune_count", 1))
    lam = float(data.get("moving_average_lambda", 0.5))
    group_count = len(w0[0])
    row_mask = [1] * group_count
    moving = [0.0] * group_count
    trace = []
    params_before = {"B": b, "A": a}
    for t in range(1, iterations + 1):
        loss_before, grad_b, grad_a = mse_and_grads(x, y, w0, b, a, row_mask)
        importance = lora_guided_importance(w0, b, a, grad_b, grad_a)["importance"]
        # Output groups correspond to columns.
        scores = structured_pruning_mask(importance, "column", 0)["group_scores"]
        moving = [lam * moving[i] + (1.0 - lam) * scores[i] for i in range(group_count)]
        b = apply_sgd(b, grad_b, lr)
        a = apply_sgd(a, grad_a, lr)
        prune_now = math.floor(target_prune_count * t / iterations)
        mask_info = structured_pruning_mask([moving], "column", prune_now)
        row_mask = mask_info["group_mask"]
        loss_after, _, _ = mse_and_grads(x, y, w0, b, a, row_mask)
        trace.append({
            "iteration": t,
            "loss_before": loss_before,
            "loss_after": loss_after,
            "group_scores": scores,
            "moving_average_scores": moving[:],
            "prune_count": prune_now,
            "group_mask": row_mask[:],
        })
    params_after = {"B": b, "A": a}
    changed = flatten(params_before["B"]) != flatten(params_after["B"]) or flatten(params_before["A"]) != flatten(params_after["A"])
    return {
        "training_trace": trace,
        "params_before": params_before,
        "params_after": params_after,
        "optimizer_step_executed": changed,
        "final_group_mask": row_mask,
        "final_B": b,
        "final_A": a,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_progressive_loop(json.loads(Path(args.input_json).read_text()))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
