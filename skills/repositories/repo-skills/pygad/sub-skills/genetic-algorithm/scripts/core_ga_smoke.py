#!/usr/bin/env python3
"""Deterministic single-objective PyGAD smoke test.

The script optimizes a six-bit chromosome toward all ones, verifies the
best solution, and exercises GA.save()/pygad.load() using a temporary file.
It writes no persistent outputs.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

try:
    import numpy as np
    import pygad
except ModuleNotFoundError as exc:  # pragma: no cover - used for clear runtime failure.
    raise SystemExit(
        f"Missing dependency {exc.name!r}. Install PyGAD with its core dependencies "
        "before running this smoke script."
    ) from exc

TARGET = np.ones(6, dtype=int)


def fitness_func(ga_instance, solution, solution_idx):
    """Maximize the number of genes equal to one."""

    return float(np.sum(solution == TARGET))


def main() -> None:
    generation_trace = []

    def on_generation(ga_instance):
        _, best_fitness, _ = ga_instance.best_solution(ga_instance.last_generation_fitness)
        generation_trace.append(float(best_fitness))

    ga = pygad.GA(
        num_generations=30,
        num_parents_mating=4,
        sol_per_pop=10,
        num_genes=TARGET.size,
        fitness_func=fitness_func,
        gene_space=[0, 1],
        gene_type=int,
        parent_selection_type="sss",
        keep_elitism=2,
        crossover_type="single_point",
        mutation_type="random",
        mutation_probability=0.25,
        stop_criteria=f"reach_{TARGET.size}",
        random_seed=7,
        suppress_warnings=True,
        on_generation=on_generation,
    )

    ga.run()

    solution, fitness, solution_idx = ga.best_solution(ga.last_generation_fitness)
    if not ga.run_completed:
        raise AssertionError("GA.run() did not complete cleanly.")
    if int(fitness) != TARGET.size:
        raise AssertionError(f"Expected best fitness {TARGET.size}, got {fitness!r}.")
    if not np.array_equal(solution.astype(int), TARGET):
        raise AssertionError(f"Expected all-one solution, got {solution!r}.")

    with tempfile.TemporaryDirectory(prefix="pygad-core-ga-") as tmpdir:
        state_base = Path(tmpdir) / "core_ga_state"
        ga.save(str(state_base))
        state_file = state_base.with_suffix(".pkl")
        if not state_file.exists():
            raise AssertionError("GA.save() did not create the expected .pkl file.")
        loaded = pygad.load(str(state_base))
        loaded_solution, loaded_fitness, _ = loaded.best_solution(loaded.last_generation_fitness)
        if int(loaded_fitness) != TARGET.size or not np.array_equal(loaded_solution.astype(int), TARGET):
            raise AssertionError("Loaded GA state did not preserve the best solution.")

    summary = {
        "generations_completed": int(ga.generations_completed),
        "best_solution": solution.astype(int).tolist(),
        "best_fitness": float(fitness),
        "best_solution_index": int(solution_idx),
        "trace_length": len(generation_trace),
        "run_completed": bool(ga.run_completed),
        "saved_and_loaded": True,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
