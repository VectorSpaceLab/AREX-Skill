#!/usr/bin/env python3
"""Deterministic PyGAD multi-objective GA template.

The example maximizes two conflicting objectives over a two-gene continuous
search space. It supports NSGA-II and NSGA-III parent selectors, verifies the
multi-objective fitness shape, and saves/restores state only inside a temporary
directory.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

try:
    import numpy as np
    import pygad
except ModuleNotFoundError as exc:  # pragma: no cover - used for clear runtime failure.
    raise SystemExit(
        f"Missing dependency {exc.name!r}. Install PyGAD with its core dependencies "
        "before running this multi-objective template."
    ) from exc

NSGA3_SELECTORS = {"nsga3", "tournament_nsga3"}


def fitness_func(ga_instance, solution, solution_idx):
    """Two-objective trade-off.

    Objective 1 is best near x=-2; objective 2 is best near x=+2. Both also
    prefer y close to 0. The negative squared distances convert the problem to
    PyGAD's maximization convention.
    """

    x, y = solution
    objective_left = -((x + 2.0) ** 2 + 0.25 * (y**2))
    objective_right = -((x - 2.0) ** 2 + 0.25 * (y**2))
    return [float(objective_left), float(objective_right)]


def build_ga(selector: str, nsga3_num_divisions: int) -> pygad.GA:
    kwargs = {}
    if selector in NSGA3_SELECTORS:
        if nsga3_num_divisions <= 0:
            raise ValueError("NSGA-III selectors require --nsga3-num-divisions > 0.")
        kwargs["nsga3_num_divisions"] = nsga3_num_divisions

    return pygad.GA(
        num_generations=12,
        num_parents_mating=8,
        sol_per_pop=18,
        num_genes=2,
        fitness_func=fitness_func,
        gene_space=[
            {"low": -4.0, "high": 4.0, "step": 0.25},
            {"low": -2.0, "high": 2.0, "step": 0.25},
        ],
        gene_type=[float, 2],
        parent_selection_type=selector,
        K_tournament=3,
        crossover_type="sbx",
        sbx_crossover_eta=20,
        mutation_type="polynomial",
        polynomial_mutation_eta=20,
        mutation_probability=0.25,
        random_seed=11,
        suppress_warnings=True,
        **kwargs,
    )


def run(selector: str, nsga3_num_divisions: int) -> dict:
    ga = build_ga(selector, nsga3_num_divisions)
    ga.run()

    fitness = np.asarray(ga.last_generation_fitness, dtype=float)
    if fitness.ndim != 2 or fitness.shape[1] != 2:
        raise AssertionError(f"Expected 2D two-objective fitness, got shape {fitness.shape}.")
    if not ga.run_completed:
        raise AssertionError("GA.run() did not complete cleanly.")

    solution, solution_fitness, solution_idx = ga.best_solution(ga.last_generation_fitness)
    pareto_front_count = len(ga.pareto_fronts or [])
    if pareto_front_count == 0:
        raise AssertionError("Expected non-empty Pareto fronts after a multi-objective run.")

    reference_points_shape = None
    reference_point_target = None
    if selector in NSGA3_SELECTORS:
        reference_points = getattr(ga, "nsga3_reference_points", None)
        if reference_points is None:
            raise AssertionError("NSGA-III run did not create reference points.")
        reference_points_shape = list(reference_points.shape)
        reference_point_target = math.comb(2 + nsga3_num_divisions - 1, nsga3_num_divisions)
        if reference_points.shape[0] != reference_point_target:
            raise AssertionError("Unexpected NSGA-III reference-point count.")

    with tempfile.TemporaryDirectory(prefix="pygad-moo-") as tmpdir:
        state_base = Path(tmpdir) / f"moo_{selector}"
        ga.save(str(state_base))
        restored = pygad.load(str(state_base))
        restored_fitness = np.asarray(restored.last_generation_fitness, dtype=float)
        if restored_fitness.shape != fitness.shape:
            raise AssertionError("Restored GA state changed the fitness matrix shape.")

    return {
        "selector": selector,
        "generations_completed": int(ga.generations_completed),
        "fitness_shape": list(fitness.shape),
        "best_solution": [float(value) for value in solution],
        "best_solution_fitness": [float(value) for value in solution_fitness],
        "best_solution_index": int(solution_idx),
        "pareto_front_count": int(pareto_front_count),
        "reference_points_shape": reference_points_shape,
        "reference_point_target": reference_point_target,
        "saved_and_loaded": True,
        "run_completed": bool(ga.run_completed),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--selector",
        choices=["nsga2", "tournament_nsga2", "nsga3", "tournament_nsga3"],
        default="nsga2",
        help="Multi-objective parent selector to demonstrate.",
    )
    parser.add_argument(
        "--nsga3-num-divisions",
        type=int,
        default=4,
        help="Reference-grid divisions for NSGA-III selectors.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(args.selector, args.nsga3_num_divisions)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
