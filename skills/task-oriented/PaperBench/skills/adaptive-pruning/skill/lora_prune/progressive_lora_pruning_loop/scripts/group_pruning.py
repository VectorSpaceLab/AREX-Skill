#!/usr/bin/env python3
"""Structured group aggregation and mask creation for LoRAPrune."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

Matrix = list[list[float]]


def shape(m: Matrix) -> tuple[int, int]:
    if not m or not all(isinstance(r, list) and r for r in m):
        raise ValueError("matrix must be non-empty")
    cols = len(m[0])
    if any(len(r) != cols for r in m):
        raise ValueError("ragged matrix")
    return len(m), cols


def aggregate_groups(importance: Matrix, axis: str = "row") -> list[float]:
    rows, cols = shape(importance)
    if axis == "row":
        return [sum(importance[i][j] for j in range(cols)) for i in range(rows)]
    if axis == "column":
        return [sum(importance[i][j] for i in range(rows)) for j in range(cols)]
    raise ValueError("axis must be 'row' or 'column'")


def make_group_mask(scores: list[float], prune_count: int) -> list[int]:
    if prune_count < 0 or prune_count > len(scores):
        raise ValueError("invalid prune_count")
    order = sorted(range(len(scores)), key=lambda i: (scores[i], i))
    pruned = set(order[:prune_count])
    return [0 if i in pruned else 1 for i in range(len(scores))]


def broadcast_mask(group_mask: list[int], shape_: tuple[int, int], axis: str = "row") -> list[list[int]]:
    rows, cols = shape_
    if axis == "row":
        if len(group_mask) != rows:
            raise ValueError("row mask length mismatch")
        return [[group_mask[i] for _ in range(cols)] for i in range(rows)]
    if axis == "column":
        if len(group_mask) != cols:
            raise ValueError("column mask length mismatch")
        return [[group_mask[j] for j in range(cols)] for _ in range(rows)]
    raise ValueError("axis must be 'row' or 'column'")


def structured_pruning_mask(importance: Matrix, axis: str, prune_count: int) -> dict:
    scores = aggregate_groups(importance, axis)
    mask = make_group_mask(scores, prune_count)
    element_mask = broadcast_mask(mask, shape(importance), axis)
    return {"axis": axis, "group_scores": scores, "group_mask": mask, "element_mask": element_mask}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    result = structured_pruning_mask(data["importance"], data.get("axis", "row"), int(data["prune_count"]))
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
