#!/usr/bin/env python3
"""Bounded deterministic GeneticAlgorithm smoke check."""

from __future__ import annotations

import argparse
import json
import os
import string
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
from mlfromscratch.unsupervised_learning import GeneticAlgorithm

ALPHABET = " " + string.ascii_letters


def candidate_loss(candidate: str, target: str) -> int:
    return sum(abs(ALPHABET.index(c) - ALPHABET.index(t)) for c, t in zip(candidate, target))


def run(args: argparse.Namespace) -> dict[str, Any]:
    np.random.seed(args.seed)
    ga = GeneticAlgorithm(
        target_string=args.target,
        population_size=args.population_size,
        mutation_rate=args.mutation_rate,
    )
    print(
        json.dumps(
            {
                "event": "starting_genetic_algorithm_smoke",
                "target": args.target,
                "population_size": args.population_size,
                "mutation_rate": args.mutation_rate,
                "iterations": args.iterations,
                "seed": args.seed,
            },
            sort_keys=True,
        )
    )
    ga.run(iterations=args.iterations)

    final_population = list(getattr(ga, "population", []))
    best = min(final_population, key=lambda candidate: candidate_loss(candidate, args.target)) if final_population else None
    return {
        "event": "completed_genetic_algorithm_smoke",
        "target": args.target,
        "final_population_size": len(final_population),
        "best_candidate_after_run": best,
        "best_loss_after_run": candidate_loss(best, args.target) if best is not None else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a short deterministic ML-From-Scratch GeneticAlgorithm smoke check."
    )
    parser.add_argument("--target", default="AI", help="Small target string using only space and ASCII letters.")
    parser.add_argument("--population-size", type=int, default=12, help="Even population size used by pairwise reproduction.")
    parser.add_argument("--mutation-rate", type=float, default=0.2, help="Mutation probability in [0, 1].")
    parser.add_argument("--iterations", type=int, default=5, help="Bounded number of GA iterations to print.")
    parser.add_argument("--seed", type=int, default=3, help="NumPy seed for deterministic population initialization.")
    args = parser.parse_args()

    unsupported = sorted({char for char in args.target if char not in ALPHABET})
    if unsupported:
        parser.error(f"--target contains unsupported characters: {unsupported}; allowed alphabet is space plus ASCII letters")
    if len(args.target) < 1 or len(args.target) > 32:
        parser.error("--target length must be in [1, 32] for this bounded smoke")
    if args.population_size < 4 or args.population_size > 200 or args.population_size % 2 != 0:
        parser.error("--population-size must be an even integer in [4, 200]")
    if not 0 <= args.mutation_rate <= 1:
        parser.error("--mutation-rate must be in [0, 1]")
    if args.iterations < 1 or args.iterations > 50:
        parser.error("--iterations must be in [1, 50]")
    return args


def main() -> int:
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
