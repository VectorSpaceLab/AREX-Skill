#!/usr/bin/env python3
"""Run a tiny offline OFA search smoke.

Purpose: verify the search controller and accuracy predictor without public
weight downloads, lookup-table downloads, or ImageNet data.

Examples:
  python scripts/tiny_search.py
  python scripts/tiny_search.py --constraint-type note10 --constraint 25 --device cuda
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import torch


def _pick_device(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return requested


def _maybe_add_repo_root(repo_root: str) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).resolve()))


class DummyEfficiency:
    """Deterministic efficiency proxy for offline smoke checks."""

    def predict_efficiency(self, sample):
        depth_score = sum(sample["d"])
        size_score = sample["r"][0] / 100.0
        return depth_score * 10.0 + size_score


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="", help="Optional local checkout root for import fallback.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--constraint-type", choices=["flops", "note10"], default="flops")
    parser.add_argument("--constraint", type=float, default=600.0)
    parser.add_argument("--population-size", type=int, default=4)
    parser.add_argument("--time-budget", type=int, default=2)
    parser.add_argument("--parent-ratio", type=float, default=0.5)
    parser.add_argument("--mutation-ratio", type=float, default=0.5)
    parser.add_argument("--mutate-prob", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)
    device = _pick_device(args.device)
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    from ofa.tutorial import AccuracyPredictor, EvolutionFinder

    accuracy_predictor = AccuracyPredictor(pretrained=False, device=device)
    finder = EvolutionFinder(
        constraint_type=args.constraint_type,
        efficiency_constraint=args.constraint,
        efficiency_predictor=DummyEfficiency(),
        accuracy_predictor=accuracy_predictor,
        mutate_prob=args.mutate_prob,
        population_size=args.population_size,
        max_time_budget=args.time_budget,
        parent_ratio=args.parent_ratio,
        mutation_ratio=args.mutation_ratio,
    )

    best_valids, best_info = finder.run_evolution_search(verbose=False)
    print(f"device={device}")
    print(f"best_valids_len={len(best_valids)}")
    print(
        json.dumps(
            {
                "predicted_accuracy": best_info[0],
                "efficiency": best_info[2],
                "sample": best_info[1],
            },
            sort_keys=True,
        )
    )
    print("search_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
