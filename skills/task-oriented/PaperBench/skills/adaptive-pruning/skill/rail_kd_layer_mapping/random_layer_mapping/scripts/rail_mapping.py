#!/usr/bin/env python3
"""RAIL-KD random teacher layer mapping utilities."""
from __future__ import annotations

import argparse
import json
import random
from typing import Dict, List


def sample_teacher_layers(teacher_layer_count: int, student_layer_count: int, seed: int | None = None, epoch: int = 0, sort_indices: bool = True) -> List[int]:
    if teacher_layer_count <= 0 or student_layer_count <= 0:
        raise ValueError("layer counts must be positive")
    if student_layer_count > teacher_layer_count:
        raise ValueError("student_layer_count must be <= teacher_layer_count")
    rng_seed = None if seed is None else int(seed) + int(epoch) * 1000003
    rng = random.Random(rng_seed)
    selected = rng.sample(range(teacher_layer_count), student_layer_count)
    return sorted(selected) if sort_indices else selected


def mapping_pairs(teacher_layer_count: int, student_layer_count: int, seed: int | None = None, epoch: int = 0, sort_indices: bool = True) -> List[Dict[str, int]]:
    selected = sample_teacher_layers(teacher_layer_count, student_layer_count, seed, epoch, sort_indices)
    return [{"student_layer": i, "teacher_layer": t} for i, t in enumerate(selected)]


def coverage_report(teacher_layer_count: int, student_layer_count: int, epochs: int, seed: int = 0) -> Dict[str, object]:
    if epochs <= 0:
        raise ValueError("epochs must be positive")
    counts = {i: 0 for i in range(teacher_layer_count)}
    mappings = []
    for epoch in range(epochs):
        selected = sample_teacher_layers(teacher_layer_count, student_layer_count, seed, epoch, True)
        mappings.append(selected)
        for idx in selected:
            counts[idx] += 1
    return {
        "teacher_layer_count": teacher_layer_count,
        "student_layer_count": student_layer_count,
        "epochs": epochs,
        "mappings": mappings,
        "coverage_counts": counts,
        "unique_layers_visited": sum(1 for v in counts.values() if v > 0),
        "complexity": "O(m) sampled mapping per epoch",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teacher-layers", type=int, required=True)
    parser.add_argument("--student-layers", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(coverage_report(args.teacher_layers, args.student_layers, args.epochs, args.seed), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
