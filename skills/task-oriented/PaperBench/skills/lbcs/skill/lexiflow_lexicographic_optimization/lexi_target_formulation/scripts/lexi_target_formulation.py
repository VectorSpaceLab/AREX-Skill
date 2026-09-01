#!/usr/bin/env python3
"""Historical lexi-target computation for LexiFlow-style minimization objectives."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable, Sequence


def _validate(history: Sequence[Sequence[float]], goals: Sequence[float | None], tolerances: Sequence[float]) -> int:
    if not history:
        raise ValueError("history must be non-empty")
    dim = len(history[0])
    if dim == 0:
        raise ValueError("objective vectors must be non-empty")
    if len(goals) != dim or len(tolerances) != dim:
        raise ValueError("goals and tolerances must match objective dimension")
    for row in history:
        if len(row) != dim:
            raise ValueError("all objective vectors must have equal dimension")
    if any(t < 0 for t in tolerances):
        raise ValueError("tolerances must be non-negative")
    return dim


def vanilla_lexicographic_key(vector: Sequence[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in vector)


def compute_historical_targets(
    history: Sequence[Sequence[float]],
    goals: Sequence[float | None],
    tolerances: Sequence[float],
) -> dict:
    """Compute Eq. 8 historical targets and nested frontier indices."""
    dim = _validate(history, goals, tolerances)
    frontier = list(range(len(history)))
    frontiers: list[list[int]] = []
    targets: list[float] = []
    best_values: list[float] = []
    for priority in range(dim):
        best_value = min(float(history[index][priority]) for index in frontier)
        goal = goals[priority]
        target = best_value + float(tolerances[priority])
        if goal is not None and not (isinstance(goal, float) and math.isinf(goal) and goal < 0):
            target = max(float(goal), target)
        frontier = [index for index in frontier if float(history[index][priority]) <= target]
        best_values.append(best_value)
        targets.append(target)
        frontiers.append(list(frontier))
    best_index = min(frontier, key=lambda index: vanilla_lexicographic_key(history[index]))
    return {
        "targets": targets,
        "best_values": best_values,
        "frontiers": frontiers,
        "best_index": best_index,
        "best_objectives": list(map(float, history[best_index])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", default="", help="JSON objective matrix")
    parser.add_argument("--goals", default="", help="JSON goals; null means no goal")
    parser.add_argument("--tolerances", default="", help="JSON tolerances")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = compute_historical_targets([[0.10, 10], [0.12, 2], [0.20, 1]], [None, None], [0.03, 0.0])
        assert result["targets"] == [0.13, 2.0]
        assert result["frontiers"][-1] == [1]
        print(json.dumps({"ok": True, "result": result}, indent=2))
        return 0
    result = compute_historical_targets(json.loads(args.history), json.loads(args.goals), json.loads(args.tolerances))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
