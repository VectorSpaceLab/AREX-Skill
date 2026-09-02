#!/usr/bin/env python3
"""Bounded randomized direct search using LexiFlow update mechanics."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Callable, Sequence

try:
    from lexi_target_formulation import compute_historical_targets
    from targeted_lexicographic_relation import update_decision, vanilla_preferred
except ImportError:  # pragma: no cover
    import sys
    here = Path(__file__).resolve()
    sibling_root = here.parents[2]
    sys.path.insert(0, str(sibling_root / "lexi_target_formulation" / "scripts"))
    sys.path.insert(0, str(sibling_root / "targeted_lexicographic_relation" / "scripts"))
    from lexi_target_formulation import compute_historical_targets
    from targeted_lexicographic_relation import update_decision, vanilla_preferred


def synthetic_objective(point: Sequence[float]) -> list[float]:
    x = float(point[0])
    return [(x - 0.25) ** 2, (x - 0.78) ** 2]


def first_objective_baseline(seed: int = 0, budget: int = 80) -> dict:
    rng = random.Random(seed)
    best_x = rng.random()
    best_obj = synthetic_objective([best_x])
    history = [{"point": [best_x], "objectives": best_obj}]
    for _ in range(budget - 1):
        x = rng.random()
        obj = synthetic_objective([x])
        history.append({"point": [x], "objectives": obj})
        if obj[0] < best_obj[0]:
            best_x, best_obj = x, obj
    return {"best_point": [best_x], "best_objectives": best_obj, "history": history}


def _project(point: Sequence[float], bounds: Sequence[Sequence[float]]) -> list[float]:
    return [min(max(float(value), float(lo)), float(hi)) for value, (lo, hi) in zip(point, bounds)]


def _unit_direction(dim: int, rng: random.Random) -> list[float]:
    values = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def run_lexiflow(
    objective: Callable[[Sequence[float]], Sequence[float]],
    bounds: Sequence[Sequence[float]],
    goals: Sequence[float | None],
    tolerances: Sequence[float],
    seed: int = 0,
    budget: int = 80,
    initial_step: float = 0.20,
) -> dict:
    rng = random.Random(seed)
    dim = len(bounds)
    incumbent = [(float(lo) + float(hi)) / 2.0 for lo, hi in bounds]
    incumbent_obj = list(map(float, objective(incumbent)))
    history_points = [incumbent]
    history_objs = [incumbent_obj]
    trace = []
    evaluations = 1
    rejected = 0
    step = float(initial_step)
    while evaluations < budget:
        targets_info = compute_historical_targets(history_objs, goals, tolerances)
        targets = targets_info["targets"]
        direction = _unit_direction(dim, rng)
        accepted = False
        candidates = []
        for sign in [1.0, -1.0]:
            if evaluations >= budget:
                break
            candidate = _project([value + sign * step * delta for value, delta in zip(incumbent, direction)], bounds)
            candidate_obj = list(map(float, objective(candidate)))
            evaluations += 1
            history_points.append(candidate)
            history_objs.append(candidate_obj)
            decision = update_decision(candidate_obj, incumbent_obj, targets)
            candidates.append({"point": candidate, "objectives": candidate_obj, "decision": decision})
            if decision["accept"]:
                incumbent, incumbent_obj = candidate, candidate_obj
                accepted = True
                rejected = 0
                break
        if not accepted:
            rejected += 1
            if rejected >= max(1, 2 * dim - 1):
                step = max(step * 0.70, 0.01)
                rejected = 0
        trace.append({"targets": targets, "step": step, "direction": direction, "candidates": candidates, "accepted": accepted})
    final_targets = compute_historical_targets(history_objs, goals, tolerances)
    best_index = final_targets["best_index"]
    return {
        "best_point": history_points[best_index],
        "best_objectives": history_objs[best_index],
        "incumbent_point": incumbent,
        "incumbent_objectives": incumbent_obj,
        "targets": final_targets["targets"],
        "history": [{"point": p, "objectives": o} for p, o in zip(history_points, history_objs)],
        "trace": trace,
        "budget": budget,
        "seed": seed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--budget", type=int, default=80)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = {
        "lexiflow": run_lexiflow(synthetic_objective, [[0.0, 1.0]], [None, None], [0.03, 0.0], args.seed, args.budget),
        "baseline": first_objective_baseline(args.seed, args.budget),
    }
    if args.self_test:
        assert result["lexiflow"]["targets"][0] >= result["lexiflow"]["best_objectives"][0]
        assert any(item["accepted"] for item in result["lexiflow"]["trace"])
    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
