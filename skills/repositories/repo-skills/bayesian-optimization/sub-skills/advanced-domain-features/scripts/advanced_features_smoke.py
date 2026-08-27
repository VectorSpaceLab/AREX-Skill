#!/usr/bin/env python3
"""Deterministic smoke checks for BayesianOptimization advanced domain features.

The checks are intentionally tiny: no network, no plots, no downloads, and no
writes. They validate constrained TargetSpace behavior, typed/custom parameter
conversion, and sequential domain reduction limits.

Examples:
    python advanced_features_smoke.py --help
    python advanced_features_smoke.py --check all
    python advanced_features_smoke.py --check constraints
"""

from __future__ import annotations

import argparse
import sys
import warnings
from typing import Callable


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_exception(func: Callable[[], object], exc_type: type[BaseException], fragment: str | None = None) -> BaseException:
    try:
        func()
    except exc_type as exc:  # noqa: PERF203 - clarity matters for diagnostics
        if fragment is not None and fragment not in str(exc):
            raise AssertionError(f"Expected exception containing {fragment!r}, got: {exc}") from exc
        return exc
    except Exception as exc:  # noqa: BLE001 - report wrong exception type clearly
        raise AssertionError(f"Expected {exc_type.__name__}, got {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"Expected {exc_type.__name__} but no exception was raised")


def check_constraints() -> None:
    import numpy as np
    from scipy.optimize import NonlinearConstraint

    from bayes_opt import BayesianOptimization, ConstraintModel, acquisition

    def objective(x: float, y: float) -> float:
        return x + y

    def constraint_function(x: float, y: float) -> float:
        return x - y

    constraint = NonlinearConstraint(constraint_function, -1.0, 1.0)
    optimizer = BayesianOptimization(
        f=objective,
        pbounds={"x": (-2.0, 2.0), "y": (-2.0, 2.0)},
        constraint=constraint,
        random_state=1,
        verbose=0,
    )

    _assert(isinstance(optimizer.constraint, ConstraintModel), "constraint was not wrapped as ConstraintModel")
    _assert(
        isinstance(optimizer.acquisition_function, acquisition.ExpectedImprovement),
        "constrained optimizer did not default to ExpectedImprovement",
    )

    optimizer.register(params={"x": 0.0, "y": 0.0}, target=0.0, constraint_value=0.0)
    optimizer.register(params={"x": 2.0, "y": 0.0}, target=2.0, constraint_value=2.0)
    results = optimizer.res
    _assert(bool(results[0]["allowed"]), "feasible registered point was not marked allowed")
    _assert(not bool(results[1]["allowed"]), "infeasible registered point was not rejected")
    _assert(optimizer.max is not None and optimizer.max["target"] == 0.0, "max did not mask infeasible target")

    multi = ConstraintModel(
        fun=lambda x, y: np.array([x + y, x - y]),
        lb=np.array([-1.0, -1.0]),
        ub=np.array([1.0, 1.0]),
        random_state=1,
    )
    allowed = multi.allowed(np.array([[0.0, 0.0], [2.0, 0.0]]))
    _assert(allowed.tolist() == [True, False], "multiple-constraint allowed mask was unexpected")

    _expect_exception(
        lambda: ConstraintModel(lambda x: x, lb=1.0, ub=1.0),
        ValueError,
        "Lower bounds must be less than upper bounds",
    )

    bad_constraint = NonlinearConstraint(lambda a, b: a - b, -1.0, 1.0)
    bad_optimizer = BayesianOptimization(
        f=objective,
        pbounds={"x": (-1.0, 1.0), "y": (-1.0, 1.0)},
        constraint=bad_constraint,
        random_state=1,
        verbose=0,
    )
    _expect_exception(
        lambda: bad_optimizer.probe({"x": 0.0, "y": 0.0}, lazy=False),
        TypeError,
        "same keyword arguments as the target function",
    )

    print("PASS constraints")


def check_typed_parameters() -> None:
    import numpy as np

    from bayes_opt.parameter import BayesParameter, CategoricalParameter, IntParameter
    from bayes_opt.target_space import TargetSpace
    from bayes_opt.util import ensure_rng

    def target(lr: float, depth: int, kernel: str) -> float:
        return lr + depth + (1.0 if kernel == "rbf" else 0.0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        space = TargetSpace(
            target,
            {
                "lr": (0.0, 1.0),
                "depth": (1, 5, int),
                "kernel": ("rbf", "poly"),
            },
            random_state=1,
        )

    _assert(
        any("Non-float parameters are experimental" in str(item.message) for item in caught),
        "non-float parameter warning was not emitted",
    )
    _assert(space.keys == ["lr", "depth", "kernel"], "TargetSpace key order changed unexpectedly")
    _assert(space.dim == 4, "float + int + two-category categorical should expand to 4 dimensions")
    _assert(isinstance(space.params_config["depth"], IntParameter), "integer bound did not create IntParameter")
    _assert(
        isinstance(space.params_config["kernel"], CategoricalParameter),
        "categorical bound did not create CategoricalParameter",
    )

    arr = space.params_to_array({"kernel": "rbf", "depth": 3, "lr": 0.25})
    _assert(np.allclose(arr, np.array([0.25, 3.0, 1.0, 0.0])), "params_to_array conversion mismatch")
    back = space.array_to_params(np.array([0.25, 2.7, 0.2, 0.8]))
    _assert(back["depth"] == 3, "array_to_params did not round integer dimension")
    _assert(back["kernel"] == "poly", "array_to_params did not decode categorical argmax")

    transformed = space.kernel_transform(np.array([0.25, 2.7, 0.2, 0.8]))
    _assert(np.allclose(transformed, np.array([[0.25, 3.0, 0.0, 1.0]])), "kernel transform mismatch")

    _expect_exception(lambda: space.params_to_array({"lr": 0.1, "depth": 2}), ValueError, "do not match")
    _expect_exception(lambda: space.array_to_params(np.array([0.1, 2.0, 1.0])), ValueError, "expected number")
    _expect_exception(lambda: CategoricalParameter("bad", ("same", "same")), ValueError, "unique")
    _expect_exception(lambda: CategoricalParameter("bad", ("only",)), ValueError, "At least two")

    class SumOnePairParameter(BayesParameter):
        def __init__(self, name: str) -> None:
            super().__init__(name, np.array([[0.0, 1.0], [0.0, 1.0]]))

        @property
        def is_continuous(self) -> bool:
            return True

        def random_sample(self, n_samples: int, random_state):
            rng = ensure_rng(random_state)
            first = rng.uniform(0.0, 1.0, n_samples)
            return np.column_stack([first, 1.0 - first])

        def to_float(self, value):
            return np.asarray(value, dtype=float)

        def to_param(self, value):
            value = np.asarray(value, dtype=float)
            total = float(np.sum(value))
            if total == 0.0:
                return np.array([0.5, 0.5])
            return value / total

        def kernel_transform(self, value):
            value = np.atleast_2d(np.asarray(value, dtype=float))
            total = np.sum(value, axis=-1, keepdims=True)
            total[total == 0.0] = 1.0
            return value / total

        @property
        def dim(self) -> int:
            return 2

    custom = SumOnePairParameter("pair")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        custom_space = TargetSpace(lambda pair: float(pair[0]), {"pair": custom}, random_state=1)
    custom_arr = custom_space.params_to_array({"pair": np.array([0.2, 0.8])})
    _assert(custom_arr.shape == (2,), "custom parameter did not occupy two dimensions")
    custom_back = custom_space.array_to_params(np.array([2.0, 1.0]))["pair"]
    _assert(np.allclose(custom_back.sum(), 1.0), "custom to_param did not normalize canonical value")
    custom_kernel = custom_space.kernel_transform(np.array([2.0, 1.0]))
    _assert(np.allclose(custom_kernel.sum(axis=1), np.array([1.0])), "custom kernel transform did not normalize")

    print("PASS typed-parameters")


def check_domain_reduction() -> None:
    import numpy as np

    from bayes_opt import SequentialDomainReductionTransformer
    from bayes_opt.domain_reduction import DomainTransformer
    from bayes_opt.target_space import TargetSpace

    def objective(x: float, y: float) -> float:
        return -(x**2) - (y - 1.0) ** 2 + 1.0

    space = TargetSpace(objective, {"x": (-5.0, 5.0), "y": (-5.0, 5.0)}, random_state=1)
    space.register({"x": 0.0, "y": 1.0}, objective(0.0, 1.0))
    space.register({"x": 4.0, "y": -4.0}, objective(4.0, -4.0))

    transformer = SequentialDomainReductionTransformer(minimum_window={"y": 1.0, "x": 1.0})
    _assert(isinstance(transformer, DomainTransformer), "transformer is not a DomainTransformer")
    transformer.initialize(space)
    new_bounds = transformer.transform(space)

    _assert(set(new_bounds) == {"x", "y"}, "domain reduction did not return bounds for each key")
    latest = np.array([new_bounds[key] for key in space.keys])
    _assert(np.all(latest[:, 0] >= np.array([-5.0, -5.0])), "reduced lower bounds escaped global bounds")
    _assert(np.all(latest[:, 1] <= np.array([5.0, 5.0])), "reduced upper bounds escaped global bounds")
    _assert(np.all(np.diff(latest, axis=1).ravel() >= np.array([1.0, 1.0])), "minimum_window was not preserved")
    _assert(len(transformer.bounds) == 2, "transformer did not record original and transformed bounds")

    _expect_exception(
        lambda: SequentialDomainReductionTransformer(minimum_window=[1.0]).initialize(space),
        ValueError,
        "Length of minimum_window",
    )
    _expect_exception(
        lambda: SequentialDomainReductionTransformer(minimum_window=11.0).initialize(space),
        ValueError,
        "Global bounds are not compatible",
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        typed_space = TargetSpace(None, {"x": (-1.0, 1.0), "depth": (1, 3, int)}, random_state=1)
    _expect_exception(
        lambda: SequentialDomainReductionTransformer().initialize(typed_space),
        ValueError,
        "all-FloatParameter",
    )

    print("PASS domain-reduction")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic checks for bayesian-optimization advanced domain features.",
    )
    parser.add_argument(
        "--check",
        choices=("all", "constraints", "typed", "domain-reduction"),
        default="all",
        help="Subset to validate. Default: all.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    checks: list[tuple[str, Callable[[], None]]] = [
        ("constraints", check_constraints),
        ("typed", check_typed_parameters),
        ("domain-reduction", check_domain_reduction),
    ]
    for name, check in checks:
        if args.check in {"all", name}:
            check()

    print("PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ImportError as exc:
        print(f"IMPORT ERROR: {exc}", file=sys.stderr)
        print("Install bayesian-optimization with its runtime dependencies in the active Python environment.", file=sys.stderr)
        raise SystemExit(2) from exc
