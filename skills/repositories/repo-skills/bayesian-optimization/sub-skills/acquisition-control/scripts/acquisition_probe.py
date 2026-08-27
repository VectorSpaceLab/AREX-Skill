#!/usr/bin/env python3
"""Deterministic acquisition-function probe for bayesian-optimization.

The script builds a tiny one-dimensional optimizer, registers seed observations,
compares UCB/EI/PI suggestions, optionally probes Constant Liar and GPHedge,
validates that every suggestion stays within bounds, and prints concise PASS
output. It performs no network access, no plotting, and no writes.

Example:
    python acquisition_probe.py --include-constant-liar --include-gphedge
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from typing import Callable, Iterable


def _import_bayes_opt():
    try:
        from bayes_opt import BayesianOptimization, acquisition
    except ImportError as exc:  # pragma: no cover - environment-specific user aid
        raise SystemExit(
            "ERROR: could not import bayes_opt with its acquisition dependencies. "
            "Install bayesian-optimization plus numpy, scipy, scikit-learn, packaging, and colorama. "
            f"Original import error: {exc}"
        ) from exc
    return BayesianOptimization, acquisition


@dataclass(frozen=True)
class SuggestionRecord:
    name: str
    params: dict[str, float]


def objective(x: float) -> float:
    """Small deterministic maximization target with a maximum near x=1.3."""
    return 1.0 - (x - 1.3) ** 2 + 0.05 * math.sin(3.0 * x)


def build_optimizer(acq, seed: int, bounds: tuple[float, float]):
    BayesianOptimization, _ = _import_bayes_opt()
    optimizer = BayesianOptimization(
        f=None,
        pbounds={"x": bounds},
        acquisition_function=acq,
        random_state=seed,
        verbose=0,
    )
    for x in (-1.5, -0.25, 0.75, 2.75):
        optimizer.register({"x": x}, target=objective(x))
    return optimizer


def as_float_params(params: dict[str, object]) -> dict[str, float]:
    return {key: float(value) for key, value in params.items()}


def assert_in_bounds(record: SuggestionRecord, bounds: tuple[float, float]) -> None:
    lo, hi = bounds
    x = record.params["x"]
    if not (lo <= x <= hi):
        raise SystemExit(
            f"ERROR: {record.name} suggested x={x:.12g}, outside expected bounds [{lo}, {hi}]."
        )


def summarize(record: SuggestionRecord) -> str:
    return f"{record.name}: x={record.params['x']:.6f}"


def suggest_with_optimizer(acq_factory: Callable[[], object], seed: int, bounds: tuple[float, float]) -> SuggestionRecord:
    acq = acq_factory()
    optimizer = build_optimizer(acq, seed=seed, bounds=bounds)
    params = as_float_params(optimizer.suggest())
    name = type(acq).__name__
    record = SuggestionRecord(name=name, params=params)
    assert_in_bounds(record, bounds)
    return record


def run_base_acquisitions(args: argparse.Namespace, bounds: tuple[float, float]) -> list[SuggestionRecord]:
    _, acquisition = _import_bayes_opt()
    factories: list[Callable[[], object]] = [
        lambda: acquisition.UpperConfidenceBound(kappa=args.kappa),
        lambda: acquisition.ExpectedImprovement(xi=args.xi),
        lambda: acquisition.ProbabilityOfImprovement(xi=args.xi),
    ]
    return [suggest_with_optimizer(factory, seed=args.seed, bounds=bounds) for factory in factories]


def run_constant_liar(args: argparse.Namespace, bounds: tuple[float, float]) -> list[SuggestionRecord]:
    _, acquisition = _import_bayes_opt()
    base = acquisition.UpperConfidenceBound(kappa=args.kappa)
    liar = acquisition.ConstantLiar(base_acquisition=base, strategy=args.liar_strategy)
    optimizer = build_optimizer(liar, seed=args.seed, bounds=bounds)

    records = []
    for idx in range(args.liar_suggestions):
        params = as_float_params(optimizer.suggest())
        record = SuggestionRecord(name=f"ConstantLiar[{idx + 1}]", params=params)
        assert_in_bounds(record, bounds)
        records.append(record)

    expected_dummies = args.liar_suggestions
    actual_dummies = len(liar.dummies)
    if actual_dummies != expected_dummies:
        raise SystemExit(
            f"ERROR: ConstantLiar stored {actual_dummies} dummies, expected {expected_dummies}."
        )
    return records


def run_gphedge(args: argparse.Namespace, bounds: tuple[float, float]) -> SuggestionRecord:
    _, acquisition = _import_bayes_opt()
    portfolio = acquisition.GPHedge(
        base_acquisitions=[
            acquisition.UpperConfidenceBound(kappa=args.kappa),
            acquisition.ExpectedImprovement(xi=args.xi),
            acquisition.ProbabilityOfImprovement(xi=args.xi),
        ]
    )
    optimizer = build_optimizer(portfolio, seed=args.seed, bounds=bounds)
    raw = portfolio.suggest(
        gp=optimizer._gp,
        target_space=optimizer.space,
        n_random=args.n_random,
        n_smart=args.n_smart,
        fit_gp=True,
        random_state=args.seed,
    )
    params = as_float_params(optimizer.space.array_to_params(raw))
    record = SuggestionRecord(name="GPHedge", params=params)
    assert_in_bounds(record, bounds)
    return record


def print_pass(records: Iterable[SuggestionRecord], detail: bool) -> None:
    records = list(records)
    print("PASS acquisition_probe " + " ".join(summarize(record) for record in records))
    if detail:
        for record in records:
            print(f"PASS_DETAIL {record.name} params={record.params}")


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be nonnegative")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe bayesian-optimization acquisition suggestions on a tiny deterministic problem.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic suggestions.")
    parser.add_argument("--lower", type=float, default=-2.0, help="Lower bound for the single x parameter.")
    parser.add_argument("--upper", type=float, default=4.0, help="Upper bound for the single x parameter.")
    parser.add_argument("--kappa", type=float, default=2.576, help="UCB kappa used by UCB and meta probes.")
    parser.add_argument("--xi", type=float, default=0.01, help="EI/PI xi used by EI, PI, and GPHedge probes.")
    parser.add_argument(
        "--n-random",
        type=nonnegative_int,
        default=384,
        help="Random search budget for the lower-level GPHedge probe.",
    )
    parser.add_argument(
        "--n-smart",
        type=nonnegative_int,
        default=6,
        help="Smart optimizer budget for the lower-level GPHedge probe.",
    )
    parser.add_argument(
        "--include-constant-liar",
        action="store_true",
        help="Also ask ConstantLiar for in-flight dummy suggestions.",
    )
    parser.add_argument(
        "--liar-suggestions",
        type=positive_int,
        default=2,
        help="Number of ConstantLiar suggestions to request when enabled.",
    )
    parser.add_argument(
        "--liar-strategy",
        default="max",
        help="ConstantLiar strategy: min, mean, max, or a numeric string accepted by the package.",
    )
    parser.add_argument("--include-gphedge", action="store_true", help="Also probe a UCB/EI/PI GPHedge portfolio.")
    parser.add_argument("--detail", action="store_true", help="Print extra PASS_DETAIL lines with raw params.")
    args = parser.parse_args(argv)

    if not args.lower < args.upper:
        parser.error("--lower must be less than --upper")
    if args.kappa < 0:
        parser.error("--kappa must be greater than or equal to 0")
    if args.xi < 0:
        parser.error("--xi must be greater than or equal to 0")
    if args.n_random == 0 and args.n_smart == 0:
        parser.error("at least one of --n-random or --n-smart must be greater than 0")
    if args.include_gphedge and args.n_random < 3 and args.n_smart < 3:
        parser.error("GPHedge with three base acquisitions needs --n-random >= 3 or --n-smart >= 3")

    try:
        args.liar_strategy = float(args.liar_strategy)
    except ValueError:
        pass
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    bounds = (args.lower, args.upper)

    records = run_base_acquisitions(args, bounds)
    print_pass(records, detail=args.detail)

    if args.include_constant_liar:
        liar_records = run_constant_liar(args, bounds)
        print_pass(liar_records, detail=args.detail)

    if args.include_gphedge:
        gphedge_record = run_gphedge(args, bounds)
        print_pass([gphedge_record], detail=args.detail)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
