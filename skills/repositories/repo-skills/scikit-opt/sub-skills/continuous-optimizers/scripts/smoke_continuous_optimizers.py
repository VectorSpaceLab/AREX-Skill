#!/usr/bin/env python3
"""Tiny deterministic smoke for scikit-opt continuous optimizers.

The script uses a sphere-style objective and very small iteration counts.
It never plots and does not touch the network.
"""

from __future__ import annotations

import argparse
from typing import Iterable

import numpy as np

from sko.AFSA import AFSA
from sko.DE import DE
from sko.PSO import PSO
from sko.SA import SA, SAFast, SABoltzmann, SACauchy


def sphere(x: Iterable[float]) -> float:
    arr = np.asarray(x, dtype=float).reshape(-1)
    return float(np.dot(arr, arr))


def flatten_candidate(x: Iterable[float]) -> np.ndarray:
    arr = np.asarray(x, dtype=float).reshape(-1)
    if arr.size == 0:
        raise AssertionError("candidate is empty")
    if not np.all(np.isfinite(arr)):
        raise AssertionError("candidate contains non-finite values")
    return arr


def scalarize_y(y) -> float:
    arr = np.asarray(y, dtype=float).reshape(-1)
    if arr.size == 0:
        raise AssertionError("objective result is empty")
    value = float(arr[0])
    if not np.isfinite(value):
        raise AssertionError("objective result is not finite")
    return value


def validate_result(name: str, x, y, expected_dim: int) -> tuple[np.ndarray, float]:
    candidate = flatten_candidate(x)
    if candidate.size != expected_dim:
        raise AssertionError(f"{name}: expected dim {expected_dim}, got {candidate.size}")
    observed = scalarize_y(y)
    expected = sphere(candidate)
    if not np.isfinite(expected):
        raise AssertionError(f"{name}: recomputed objective is not finite")
    if not np.isclose(observed, expected, rtol=1e-8, atol=1e-10):
        raise AssertionError(
            f"{name}: returned y {observed} does not match recomputed {expected}"
        )
    print(f"{name}: best_x={candidate.tolist()} best_y={observed:.8f}")
    return candidate, observed


def run_de(seed: int) -> None:
    np.random.seed(seed)

    constraint_eq = (lambda x: x[0] + x[1],)
    constraint_ueq = (lambda x: x[2] - 0.75,)

    algo = DE(
        func=sphere,
        n_dim=3,
        F=0.6,
        size_pop=10,
        max_iter=5,
        prob_mut=0.2,
        lb=-1.0,
        ub=1.0,
        constraint_eq=constraint_eq,
        constraint_ueq=constraint_ueq,
        n_processes=0,
    )
    best_x, best_y = algo.run()
    validate_result("DE", best_x, best_y, 3)
    if len(algo.generation_best_X) != 5 or len(algo.generation_best_Y) != 5 or len(algo.all_history_Y) != 5:
        raise AssertionError("DE: history lengths do not match max_iter")


def run_pso(seed: int) -> None:
    np.random.seed(seed)

    constraint_ueq = (lambda x: x[0] + x[1] - 0.5,)

    algo = PSO(
        func=sphere,
        dim=3,
        pop=8,
        max_iter=6,
        lb=[-1.0, -1.0, -1.0],
        ub=[1.0, 1.0, 1.0],
        w=0.6,
        c1=0.7,
        c2=0.9,
        constraint_ueq=constraint_ueq,
        n_processes=0,
    )
    algo.record_mode = True
    best_x, best_y = algo.run()
    candidate, observed = validate_result("PSO", best_x, best_y, 3)
    if len(algo.record_value["X"]) != 6 or len(algo.record_value["V"]) != 6 or len(algo.record_value["Y"]) != 6:
        raise AssertionError("PSO: record_value lengths do not match max_iter")
    if len(algo.gbest_y_hist) != 6:
        raise AssertionError("PSO: gbest_y_hist length does not match max_iter")
    if not np.isfinite(observed) or not np.all(np.isfinite(candidate)):
        raise AssertionError("PSO: non-finite validation result")


def run_sa_family(seed: int) -> None:
    cases = [
        ("SA", SA, dict(x0=[0.5, -0.4, 0.3], T_max=1.0, T_min=0.75, L=4, max_stay_counter=2)),
        (
            "SAFast",
            SAFast,
            dict(
                x0=[0.6, -0.3, 0.2],
                T_max=1.0,
                T_min=0.5,
                L=4,
                max_stay_counter=2,
                lb=[-1.0, -1.0, -1.0],
                ub=[1.0, 1.0, 1.0],
                hop=0.4,
                m=1,
                n=1,
                quench=1.0,
            ),
        ),
        (
            "SABoltzmann",
            SABoltzmann,
            dict(
                x0=[0.4, -0.2, 0.6],
                T_max=1.0,
                T_min=0.9,
                L=4,
                max_stay_counter=2,
                lb=[-1.0, -1.0, -1.0],
                ub=[1.0, 1.0, 1.0],
                hop=0.4,
                learn_rate=0.3,
            ),
        ),
        (
            "SACauchy",
            SACauchy,
            dict(
                x0=[0.2, -0.6, 0.5],
                T_max=1.0,
                T_min=0.5,
                L=4,
                max_stay_counter=2,
                lb=[-1.0, -1.0, -1.0],
                ub=[1.0, 1.0, 1.0],
                hop=0.4,
                learn_rate=0.3,
            ),
        ),
    ]

    for offset, (name, cls, kwargs) in enumerate(cases):
        np.random.seed(seed + offset)
        algo = cls(func=sphere, **kwargs)
        best_x, best_y = algo.run()
        validate_result(name, best_x, best_y, 3)
        if len(algo.generation_best_X) != len(algo.generation_best_Y):
            raise AssertionError(f"{name}: history lengths differ")
        if len(algo.generation_best_X) < 2:
            raise AssertionError(f"{name}: expected at least one completed cycle")


def run_afsa(seed: int) -> None:
    np.random.seed(seed)

    algo = AFSA(
        func=sphere,
        n_dim=3,
        size_pop=10,
        max_iter=5,
        max_try_num=5,
        step=0.2,
        visual=0.4,
        q=0.9,
        delta=0.5,
    )
    best_x, best_y = algo.run()
    validate_result("AFSA", best_x, best_y, 3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic smoke checks for scikit-opt continuous optimizers.")
    parser.add_argument(
        "--algorithm",
        choices=("de", "pso", "sa", "afsa", "all"),
        default="all",
        help="Which optimizer family to smoke-test.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Base NumPy seed for deterministic smoke runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.algorithm in ("de", "all"):
        run_de(args.seed)
    if args.algorithm in ("pso", "all"):
        run_pso(args.seed + 100)
    if args.algorithm in ("sa", "all"):
        run_sa_family(args.seed + 200)
    if args.algorithm in ("afsa", "all"):
        run_afsa(args.seed + 300)
    print(f"Smoke check completed for {args.algorithm}.")


if __name__ == "__main__":
    main()
