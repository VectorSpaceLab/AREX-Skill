#!/usr/bin/env python3
"""Quick PyGAD installation and API smoke check.

The script verifies core imports, runs a tiny deterministic GA, and reports
whether optional visualization/report/deep-learning dependencies are available.
It writes no persistent outputs.
"""

from __future__ import annotations

import importlib.util
import json

try:
    import numpy as np
    import pygad
except ModuleNotFoundError as exc:  # pragma: no cover - clear runtime failure.
    raise SystemExit(
        f"Missing dependency {exc.name!r}. Install PyGAD in this environment first."
    ) from exc


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_core_ga() -> dict:
    target = np.array([1, 1, 1, 1], dtype=int)

    def fitness_func(ga_instance, solution, solution_idx):
        return float(np.sum(solution.astype(int) == target))

    ga = pygad.GA(
        num_generations=20,
        num_parents_mating=3,
        sol_per_pop=8,
        num_genes=target.size,
        fitness_func=fitness_func,
        gene_space=[0, 1],
        gene_type=int,
        stop_criteria=f"reach_{target.size}",
        random_seed=3,
        suppress_warnings=True,
    )
    ga.run()
    solution, fitness, index = ga.best_solution(ga.last_generation_fitness)
    if not ga.run_completed:
        raise AssertionError("GA.run() did not complete cleanly")
    if int(fitness) != target.size:
        raise AssertionError(f"Expected all bits matched, got fitness={fitness!r}")
    return {
        "generations_completed": int(ga.generations_completed),
        "best_solution": solution.astype(int).tolist(),
        "best_fitness": float(fitness),
        "best_solution_index": int(index),
    }


def main() -> None:
    summary = {
        "pygad_version": pygad.__version__,
        "core_ga": run_core_ga(),
        "optional_modules": {
            "matplotlib": module_available("matplotlib"),
            "reportlab": module_available("reportlab"),
            "tensorflow": module_available("tensorflow"),
            "keras": module_available("keras"),
            "torch": module_available("torch"),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
