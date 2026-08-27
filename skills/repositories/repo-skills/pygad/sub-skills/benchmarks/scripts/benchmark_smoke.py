#!/usr/bin/env python3
"""Deterministic PyGAD benchmark smoke test.

This script exercises the benchmark callables and quality indicators with small
examples:
- classic: Sphere
- multi-objective: ZDT1 and DTLZ2
- combinatorial: Knapsack and TSP

It uses only temporary files for save/load round-trips and prints a compact
JSON summary. If PyGAD or NumPy is missing, it exits with a clear message.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

try:
    import numpy as np
    import pygad
    from pygad.benchmarks.classic import Sphere
    from pygad.benchmarks.dtlz import DTLZ2
    from pygad.benchmarks.knapsack import Knapsack
    from pygad.benchmarks.tsp import TSP
    from pygad.benchmarks.zdt import ZDT1
    from pygad.utils.quality_indicators import (
        generational_distance,
        hypervolume,
        inverted_generational_distance,
        spacing,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - clear runtime failure.
    raise SystemExit(
        f"Missing dependency {exc.name!r}. Install PyGAD with its core dependencies "
        "before running this smoke script."
    ) from exc


def save_and_restore(ga: pygad.GA, tmpdir: Path, stem: str) -> pygad.GA:
    """Save a GA state to a temporary file and reload it."""

    base = tmpdir / stem
    ga.save(str(base))
    state_file = base.with_suffix(".pkl")
    if not state_file.exists():
        raise AssertionError(f"Expected {state_file} to exist after ga.save().")
    restored = pygad.load(str(base))
    if restored.last_generation_fitness is None:
        raise AssertionError("Loaded GA state is missing last_generation_fitness.")
    return restored


def run_sphere_case(tmpdir: Path) -> dict:
    problem = Sphere(num_genes=4)
    initial_population = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [1.0, -1.0, 0.5, -0.5],
            [2.0, 2.0, -2.0, -2.0],
            [-1.0, 1.0, -1.0, 1.0],
        ],
        dtype=float,
    )
    ga = pygad.GA(
        num_generations=3,
        num_parents_mating=2,
        fitness_func=problem,
        initial_population=initial_population,
        keep_elitism=1,
        crossover_type=None,
        mutation_type=None,
        random_seed=7,
        suppress_warnings=True,
    )
    ga.run()

    solution, fitness, solution_idx = ga.best_solution(ga.last_generation_fitness)
    if not ga.run_completed:
        raise AssertionError("Sphere smoke run did not complete cleanly.")
    if not np.isclose(fitness, 0.0, atol=1e-12):
        raise AssertionError(f"Expected Sphere optimum fitness 0.0, got {fitness!r}.")
    if not np.allclose(solution, np.zeros(problem.num_genes)):
        raise AssertionError(f"Expected the zero vector, got {solution!r}.")

    restored = save_and_restore(ga, tmpdir, "sphere_state")
    restored_solution, restored_fitness, _ = restored.best_solution(
        restored.last_generation_fitness
    )
    if not np.isclose(restored_fitness, fitness, atol=1e-12):
        raise AssertionError("Loaded Sphere state changed the best fitness.")
    if not np.allclose(restored_solution, solution):
        raise AssertionError("Loaded Sphere state changed the best solution.")

    return {
        "best_fitness": float(fitness),
        "best_solution_index": int(solution_idx),
        "generations_completed": int(ga.generations_completed),
        "run_completed": bool(ga.run_completed),
        "saved_and_loaded": True,
    }


def run_zdt1_case(tmpdir: Path) -> dict:
    problem = ZDT1(num_genes=10)
    initial_population = np.array(
        [
            [0.0] + [0.0] * 9,
            [0.25] + [0.0] * 9,
            [0.50] + [0.0] * 9,
            [0.75] + [0.0] * 9,
        ],
        dtype=float,
    )
    ga = pygad.GA(
        num_generations=5,
        num_parents_mating=4,
        fitness_func=problem,
        initial_population=initial_population,
        parent_selection_type="nsga2",
        crossover_type="sbx",
        sbx_crossover_eta=30,
        mutation_type="polynomial",
        polynomial_mutation_eta=20,
        keep_elitism=1,
        random_seed=9,
        suppress_warnings=True,
    )
    ga.run()

    front = np.asarray(ga.last_generation_fitness, dtype=float)
    if front.shape != (4, 2):
        raise AssertionError(f"Expected a 4x2 ZDT1 front, got shape {front.shape}.")
    pareto_fronts = getattr(ga, "pareto_fronts", None)
    if pareto_fronts is None or len(pareto_fronts) == 0:
        raise AssertionError("Expected Pareto fronts after the ZDT1 NSGA-II run.")

    expected_first = np.array([0.0, -1.0])
    actual_first = np.asarray(problem(None, initial_population[0], 0), dtype=float)
    if not np.allclose(actual_first, expected_first):
        raise AssertionError(
            f"Expected the first seeded ZDT1 fitness to be {expected_first!r}, got {actual_first!r}."
        )

    true_front = problem.pareto_front(num_points=33)
    igd = inverted_generational_distance(front, true_front)
    gd = generational_distance(front, true_front)
    hv = hypervolume(front, front.min(axis=0) - 0.1)
    spread = spacing(front)

    restored = save_and_restore(ga, tmpdir, "zdt1_state")
    restored_front = np.asarray(restored.last_generation_fitness, dtype=float)
    if restored_front.shape != front.shape:
        raise AssertionError("Loaded ZDT1 state changed the fitness matrix shape.")

    return {
        "front_shape": list(front.shape),
        "igd": float(igd),
        "gd": float(gd),
        "hypervolume": float(hv),
        "spacing": float(spread),
        "true_front_points": int(true_front.shape[0]),
        "run_completed": bool(ga.run_completed),
        "saved_and_loaded": True,
    }


def run_dtlz2_case() -> dict:
    problem = DTLZ2(num_objectives=3, num_distance_vars=4)
    nsga3_num_divisions = 2
    expected_reference_points = math.comb(
        problem.num_objectives + nsga3_num_divisions - 1,
        nsga3_num_divisions,
    )
    initial_population = np.array(
        [
            [0.25, 0.75, 0.50, 0.50, 0.50, 0.50],
            [0.10, 0.90, 0.10, 0.20, 0.30, 0.40],
            [0.90, 0.10, 0.20, 0.30, 0.40, 0.50],
            [0.60, 0.40, 0.70, 0.60, 0.50, 0.40],
            [0.20, 0.80, 0.40, 0.30, 0.20, 0.10],
            [0.80, 0.20, 0.30, 0.40, 0.50, 0.60],
        ],
        dtype=float,
    )
    ga = pygad.GA(
        num_generations=1,
        num_parents_mating=3,
        fitness_func=problem,
        initial_population=initial_population,
        parent_selection_type="nsga3",
        nsga3_num_divisions=nsga3_num_divisions,
        keep_elitism=1,
        crossover_type=None,
        mutation_type=None,
        random_seed=11,
        suppress_warnings=True,
    )
    ga.run()

    front = np.asarray(ga.last_generation_fitness, dtype=float)
    if front.shape != (6, 3):
        raise AssertionError(f"Expected a 6x3 DTLZ2 front, got shape {front.shape}.")
    if getattr(ga, "nsga3_reference_points", None) is None:
        raise AssertionError("Expected NSGA-III reference points to be created.")
    if ga.nsga3_reference_points.shape[0] != expected_reference_points:
        raise AssertionError("Unexpected NSGA-III reference-point count.")

    front_solution = np.asarray(problem(None, initial_population[0], 0), dtype=float)
    if not np.isclose(np.sum(front_solution**2), 1.0, atol=1e-9):
        raise AssertionError("Expected the seeded DTLZ2 point to sit on the unit sphere.")

    return {
        "front_shape": list(front.shape),
        "reference_points": int(ga.nsga3_reference_points.shape[0]),
        "expected_reference_points": int(expected_reference_points),
        "unit_sphere_check": True,
        "run_completed": bool(ga.run_completed),
    }


def run_knapsack_case() -> dict:
    problem = Knapsack(weights=[2, 3, 4, 5], values=[3, 4, 5, 6], capacity=5)
    initial_population = np.array(
        [
            [1, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
        ],
        dtype=int,
    )
    ga = pygad.GA(
        num_generations=2,
        num_parents_mating=2,
        fitness_func=problem,
        initial_population=initial_population,
        gene_space=problem.gene_space,
        gene_type=problem.gene_type,
        keep_elitism=1,
        crossover_type=None,
        mutation_type=None,
        random_seed=13,
        suppress_warnings=True,
    )
    ga.run()

    solution, fitness, solution_idx = ga.best_solution(ga.last_generation_fitness)
    expected_solution = np.array([1, 1, 0, 0])
    if not np.array_equal(solution.astype(int), expected_solution):
        raise AssertionError(f"Expected the optimal knapsack subset {expected_solution!r}, got {solution!r}.")
    if not np.isclose(fitness, 7.0, atol=1e-12):
        raise AssertionError(f"Expected knapsack fitness 7.0, got {fitness!r}.")

    overweight_penalty = problem(None, np.array([1, 1, 1, 0]), 0)
    if not np.isclose(overweight_penalty, -4.0, atol=1e-12):
        raise AssertionError("Knapsack overweight penalty does not match the expected value.")

    return {
        "best_fitness": float(fitness),
        "best_solution_index": int(solution_idx),
        "overweight_penalty": float(overweight_penalty),
        "run_completed": bool(ga.run_completed),
    }


def run_tsp_case() -> dict:
    problem = TSP(
        coordinates=[
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
        ]
    )
    initial_population = np.array(
        [
            [0, 1, 2, 3],
            [0, 2, 1, 3],
            [0, 1, 3, 2],
            [0, 3, 2, 1],
        ],
        dtype=int,
    )
    ga = pygad.GA(
        num_generations=2,
        num_parents_mating=2,
        fitness_func=problem,
        initial_population=initial_population,
        gene_space=problem.gene_space,
        gene_type=problem.gene_type,
        allow_duplicate_genes=problem.allow_duplicate_genes,
        keep_elitism=1,
        crossover_type=None,
        mutation_type=None,
        random_seed=17,
        suppress_warnings=True,
    )
    ga.run()

    solution, fitness, solution_idx = ga.best_solution(ga.last_generation_fitness)
    tour_length = problem.tour_length(solution)
    if not np.isclose(fitness, -4.0, atol=1e-12):
        raise AssertionError(f"Expected TSP fitness -4.0, got {fitness!r}.")
    if not np.isclose(tour_length, 4.0, atol=1e-12):
        raise AssertionError(f"Expected TSP tour length 4.0, got {tour_length!r}.")

    invalid_fitness = problem(None, np.array([0, 1, 2, 0]), 0)
    if invalid_fitness >= -problem.distance_matrix.sum():
        raise AssertionError("Expected an invalid TSP tour to receive a stronger penalty.")

    return {
        "best_fitness": float(fitness),
        "best_solution_index": int(solution_idx),
        "tour_length": float(tour_length),
        "invalid_penalty": float(invalid_fitness),
        "run_completed": bool(ga.run_completed),
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pygad-benchmark-smoke-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        summary = {
            "sphere": run_sphere_case(tmpdir),
            "zdt1": run_zdt1_case(tmpdir),
            "dtlz2": run_dtlz2_case(),
            "knapsack": run_knapsack_case(),
            "tsp": run_tsp_case(),
        }

    summary["all_cases_passed"] = True
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
