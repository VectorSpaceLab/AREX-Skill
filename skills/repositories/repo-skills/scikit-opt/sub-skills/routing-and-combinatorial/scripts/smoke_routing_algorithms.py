#!/usr/bin/env python3
"""Deterministic smoke test for scikit-opt route solvers.

The script generates a tiny coordinate fixture in-memory, builds a route-cost
function, runs one or all supported TSP solvers, and validates that the result
is a permutation with a finite positive distance.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

import numpy as np
from scipy import spatial
from sko.ACA import ACA_TSP
from sko.GA import GA_TSP
from sko.IA import IA_TSP
from sko.SA import SA_TSP

CITY_PRESETS = {
    "small": 8,
    "medium": 10,
    "large": 12,
}

SOLVER_ORDER = ("ga-tsp", "sa-tsp", "aca-tsp", "ia-tsp")
SOLVER_SEEDS = {
    "ga-tsp": 101,
    "sa-tsp": 202,
    "aca-tsp": 303,
    "ia-tsp": 404,
}


@dataclass(frozen=True)
class RouteProblem:
    name: str
    n_internal: int
    cost_distance_matrix: np.ndarray
    solver_distance_matrix: np.ndarray
    route_cost: Callable[[np.ndarray], float]
    render_route: Callable[[np.ndarray], np.ndarray]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test scikit-opt TSP and route solvers on a deterministic fixture.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--algorithm",
        choices=(*SOLVER_ORDER, "all"),
        default="all",
        help="Solver to run.",
    )
    parser.add_argument(
        "--cities",
        choices=tuple(CITY_PRESETS),
        default="small",
        help="Fixture size preset.",
    )
    parser.add_argument(
        "--fixed-endpoints",
        action="store_true",
        help="Keep a start and end city outside the optimized permutation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Base seed used for deterministic fixture generation.",
    )
    return parser.parse_args()


def validate_distance_matrix(distance_matrix: np.ndarray) -> None:
    matrix = np.asarray(distance_matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"distance matrix must be square, got shape {matrix.shape}")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("distance matrix must be finite")
    if not np.allclose(np.diag(matrix), 0.0):
        raise ValueError("distance matrix diagonal must be zero")


def validate_permutation(route: Iterable[int], n_cities: int) -> np.ndarray:
    route = np.asarray(route, dtype=int).reshape(-1)
    if route.shape != (n_cities,):
        raise ValueError(f"expected {n_cities} cities, got shape {route.shape}")
    if not np.array_equal(np.sort(route), np.arange(n_cities)):
        raise ValueError("route must contain each city exactly once")
    return route


def path_length(route: np.ndarray, distance_matrix: np.ndarray) -> float:
    total = 0.0
    for i in range(route.size - 1):
        total += distance_matrix[route[i], route[i + 1]]
    return float(total)


def cycle_length(route: np.ndarray, distance_matrix: np.ndarray) -> float:
    total = 0.0
    n_cities = route.size
    for i in range(n_cities):
        total += distance_matrix[route[i], route[(i + 1) % n_cities]]
    return float(total)


def build_problem(cities_preset: str, fixed_endpoints: bool, seed: int) -> RouteProblem:
    n_internal = CITY_PRESETS[cities_preset]
    rng = np.random.default_rng(seed)

    if fixed_endpoints:
        movable_points = rng.uniform(0.05, 0.95, size=(n_internal, 2))
        start_point = np.array([[0.0, 0.0]])
        end_point = np.array([[1.0, 1.0]])
        full_points = np.concatenate([movable_points, start_point, end_point], axis=0)
        full_distance_matrix = spatial.distance.cdist(full_points, full_points, metric="euclidean")
        solver_distance_matrix = spatial.distance.cdist(movable_points, movable_points, metric="euclidean")
        start_idx = n_internal
        end_idx = n_internal + 1

        validate_distance_matrix(full_distance_matrix)
        validate_distance_matrix(solver_distance_matrix)

        def route_cost(route: np.ndarray) -> float:
            route = validate_permutation(route, n_internal)
            full_route = np.concatenate([[start_idx], route, [end_idx]])
            return path_length(full_route, full_distance_matrix)

        def render_route(route: np.ndarray) -> np.ndarray:
            route = validate_permutation(route, n_internal)
            return np.concatenate([[start_idx], route, [end_idx]])

        name = f"fixed-endpoints:{cities_preset}"
    else:
        points_coordinate = rng.uniform(0.0, 1.0, size=(n_internal, 2))
        distance_matrix = spatial.distance.cdist(points_coordinate, points_coordinate, metric="euclidean")
        validate_distance_matrix(distance_matrix)

        def route_cost(route: np.ndarray) -> float:
            route = validate_permutation(route, n_internal)
            return cycle_length(route, distance_matrix)

        def render_route(route: np.ndarray) -> np.ndarray:
            return validate_permutation(route, n_internal)

        full_distance_matrix = distance_matrix
        solver_distance_matrix = distance_matrix
        name = f"cycle:{cities_preset}"

    return RouteProblem(
        name=name,
        n_internal=n_internal,
        cost_distance_matrix=full_distance_matrix,
        solver_distance_matrix=solver_distance_matrix,
        route_cost=route_cost,
        render_route=render_route,
    )


def scalarize_distance(value: object) -> float:
    distance = float(np.asarray(value, dtype=float).reshape(-1)[0])
    if not np.isfinite(distance) or distance <= 0:
        raise ValueError(f"invalid distance {distance}")
    return distance


def validate_result(route: np.ndarray, distance: object, n_cities: int) -> Tuple[np.ndarray, float]:
    route = validate_permutation(route, n_cities)
    distance = scalarize_distance(distance)
    return route, distance


def solve_ga_tsp(problem: RouteProblem, seed: int) -> Tuple[np.ndarray, float]:
    np.random.seed(seed)
    solver = GA_TSP(
        func=problem.route_cost,
        n_dim=problem.n_internal,
        size_pop=20,
        max_iter=20,
        prob_mut=1.0,
    )
    return solver.run()


def solve_sa_tsp(problem: RouteProblem, seed: int) -> Tuple[np.ndarray, float]:
    np.random.seed(seed)
    solver = SA_TSP(
        func=problem.route_cost,
        x0=np.arange(problem.n_internal),
        T_max=1.5,
        T_min=0.7,
        L=max(12, 2 * problem.n_internal),
        max_stay_counter=4,
    )
    return solver.run()


def solve_aca_tsp(problem: RouteProblem, seed: int) -> Tuple[np.ndarray, float]:
    np.random.seed(seed)
    solver = ACA_TSP(
        func=problem.route_cost,
        n_dim=problem.n_internal,
        size_pop=10,
        max_iter=12,
        distance_matrix=problem.solver_distance_matrix,
        alpha=1,
        beta=2,
        rho=0.1,
    )
    return solver.run()


def solve_ia_tsp(problem: RouteProblem, seed: int) -> Tuple[np.ndarray, float]:
    np.random.seed(seed)
    solver = IA_TSP(
        func=problem.route_cost,
        n_dim=problem.n_internal,
        size_pop=20,
        max_iter=20,
        prob_mut=0.2,
        T=0.7,
        alpha=0.95,
    )
    return solver.run()


SOLVERS = {
    "ga-tsp": solve_ga_tsp,
    "sa-tsp": solve_sa_tsp,
    "aca-tsp": solve_aca_tsp,
    "ia-tsp": solve_ia_tsp,
}


def run_solver(name: str, problem: RouteProblem, seed: int) -> None:
    route, distance = SOLVERS[name](problem, seed)
    route, distance = validate_result(route, distance, problem.n_internal)
    rendered_route = problem.render_route(route)
    print(f"{name}: distance={distance:.8f} route={rendered_route.tolist()}")


def main() -> int:
    args = parse_args()
    problem = build_problem(args.cities, args.fixed_endpoints, args.seed)

    print(
        f"fixture={problem.name} optimized_cities={problem.n_internal} "
        f"algorithm={args.algorithm}"
    )

    if args.algorithm == "all":
        for index, name in enumerate(SOLVER_ORDER):
            run_solver(name, problem, args.seed + SOLVER_SEEDS[name] + index)
    else:
        run_solver(args.algorithm, problem, args.seed + SOLVER_SEEDS[args.algorithm])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
