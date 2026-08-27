#!/usr/bin/env python3
"""Safe deterministic smoke checks for core bayesian-optimization workflows."""

from __future__ import annotations

import argparse
import io
import math
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

from bayes_opt import BayesianOptimization
from bayes_opt.exception import NotUniqueError

try:
    from importlib.metadata import version
except ImportError:  # pragma: no cover - Python 3.9+ normally has this
    version = None  # type: ignore[assignment]


def objective(x: float, y: float) -> float:
    """Small deterministic function with maximum near x=0.25, y=-0.5."""
    return float(1.0 - (x - 0.25) ** 2 - (y + 0.5) ** 2)


def assert_in_bounds(params: dict[str, float], pbounds: dict[str, tuple[float, float]]) -> None:
    for key, value in params.items():
        low, high = pbounds[key]
        if not (low <= float(value) <= high):
            raise AssertionError(f"parameter {key}={value!r} outside bounds {(low, high)!r}")


def assert_best_structure(best: dict | None, pbounds: dict[str, tuple[float, float]]) -> None:
    if best is None:
        raise AssertionError("optimizer.max is None after observations")
    if set(best) < {"target", "params"}:
        raise AssertionError(f"optimizer.max has unexpected keys: {best!r}")
    if set(best["params"]) != set(pbounds):
        raise AssertionError(f"best params keys do not match pbounds: {best!r}")
    if not math.isfinite(float(best["target"])):
        raise AssertionError(f"best target is not finite: {best!r}")
    assert_in_bounds(best["params"], pbounds)


def exercise_persistence(
    optimizer: BayesianOptimization,
    pbounds: dict[str, tuple[float, float]],
    seed: int,
    output_dir: Path | None,
) -> None:
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="bo-core-smoke-") as tmp:
            state_path = Path(tmp) / "optimizer_state.json"
            _save_load_check(optimizer, pbounds, seed, state_path)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        state_path = output_dir / f"bo_core_state_{os.getpid()}.json"
        _save_load_check(optimizer, pbounds, seed, state_path)


def _save_load_check(
    optimizer: BayesianOptimization,
    pbounds: dict[str, tuple[float, float]],
    seed: int,
    state_path: Path,
) -> None:
    optimizer.save_state(state_path)
    if not state_path.exists() or state_path.stat().st_size == 0:
        raise AssertionError("state file was not written")

    restored = BayesianOptimization(f=objective, pbounds=pbounds, random_state=seed, verbose=0)
    restored.load_state(state_path)

    if len(restored.res) != len(optimizer.res):
        raise AssertionError("loaded state observation count differs")
    assert_best_structure(restored.max, pbounds)
    if not np.isclose(float(restored.max["target"]), float(optimizer.max["target"])):
        raise AssertionError("loaded best target differs from original best target")


def run_core_smoke(args: argparse.Namespace) -> None:
    pbounds = {"x": (-2.0, 2.0), "y": (-2.0, 2.0)}
    optimizer = BayesianOptimization(
        f=objective,
        pbounds=pbounds,
        random_state=args.seed,
        verbose=args.verbose,
    )

    # suggest() returns a random valid point before any observations exist.
    first_suggestion = optimizer.suggest()
    assert_in_bounds(first_suggestion, pbounds)
    if len(optimizer.res) != 0:
        raise AssertionError("suggest() should not register an observation")

    # random_sample() returns a list of parameter dictionaries.
    samples = optimizer.random_sample(2)
    if len(samples) != 2:
        raise AssertionError("random_sample(2) did not return two samples")
    for sample in samples:
        assert_in_bounds(sample, pbounds)

    # register() records known targets and rejects accidental duplicates.
    known = {"x": 0.0, "y": -0.5}
    optimizer.register(params=known, target=objective(**known))
    try:
        optimizer.register(params=known, target=objective(**known))
    except NotUniqueError:
        pass
    else:
        raise AssertionError("duplicate register did not raise NotUniqueError")

    # set_gp_params() and set_bounds() should be safe before continuing.
    optimizer.set_gp_params(alpha=1e-3, n_restarts_optimizer=1)
    optimizer.set_bounds({"x": (-1.5, 1.5), "unused": (0.0, 1.0)})
    active_pbounds = {"x": (-1.5, 1.5), "y": (-2.0, 2.0)}

    # probe(lazy=True) queues a known point for maximize() to evaluate.
    queued = {"x": 0.25, "y": -0.5}
    before = len(optimizer.res)
    optimizer.probe(params=queued, lazy=True)
    if len(optimizer.res) != before:
        raise AssertionError("lazy probe unexpectedly registered immediately")

    optimizer.maximize(init_points=args.init_points, n_iter=args.n_iter)
    expected_min = 1 + 1 + args.init_points + args.n_iter
    if len(optimizer.res) < expected_min:
        raise AssertionError(f"too few observations: {len(optimizer.res)} < {expected_min}")
    assert_best_structure(optimizer.max, active_pbounds)

    # predict() after observations; fit_gp=True refits on current observations.
    mean, std = optimizer.predict(optimizer.max["params"], return_std=True, fit_gp=True)
    if not math.isfinite(float(np.asarray(mean))):
        raise AssertionError("predict mean is not finite")
    if float(np.asarray(std)) < 0:
        raise AssertionError("predict std is negative")

    means, cov = optimizer.predict(
        [optimizer.max["params"], {"x": 0.0, "y": 0.0}],
        return_cov=True,
        fit_gp=False,
    )
    if np.asarray(means).shape != (2,) or np.asarray(cov).shape != (2, 2):
        raise AssertionError("predict return_cov shapes are wrong")

    # f=None manual ask-tell loop: suggest externally, then register target.
    manual_bounds = {"z": (-1.0, 1.0)}
    manual = BayesianOptimization(f=None, pbounds=manual_bounds, random_state=args.seed, verbose=0)
    manual_point = manual.suggest()
    assert_in_bounds(manual_point, manual_bounds)
    manual.register(params=manual_point, target=float(1.0 - (manual_point["z"] - 0.2) ** 2))
    if len(manual.res) != 1 or manual.max is None:
        raise AssertionError("manual ask-tell register failed")
    try:
        manual.probe({"z": 0.0}, lazy=False)
    except ValueError as exc:
        if "No target function" not in str(exc):
            raise
    else:
        raise AssertionError("eager probe with f=None should fail")

    # Intentional duplicate/noisy observation behavior.
    noisy = BayesianOptimization(
        f=None,
        pbounds=manual_bounds,
        random_state=args.seed,
        verbose=0,
        allow_duplicate_points=True,
    )
    noisy.register({"z": 0.0}, target=0.1)
    with redirect_stdout(io.StringIO()):
        noisy.register({"z": 0.0}, target=0.2)
    if len(noisy.res) != 2:
        raise AssertionError("allow_duplicate_points=True did not keep duplicate observations")

    if not args.no_state:
        exercise_persistence(optimizer, active_pbounds, args.seed, args.output_dir)

    package_version = version("bayesian-optimization") if version else "unknown"
    print(
        "PASS bo_core_smoke "
        f"version={package_version} observations={len(optimizer.res)} "
        f"best_target={float(optimizer.max['target']):.6f} state_checked={not args.no_state}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic core BayesianOptimization smoke checks without network or destructive I/O.",
    )
    parser.add_argument("--seed", type=int, default=13, help="Random seed for reproducible suggestions.")
    parser.add_argument("--init-points", type=int, default=2, help="Random initialization points for maximize().")
    parser.add_argument("--n-iter", type=int, default=2, help="Acquisition-driven iterations for maximize().")
    parser.add_argument("--verbose", type=int, default=0, choices=[0, 1, 2], help="Optimizer verbosity.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for a non-overwriting JSON state file; defaults to a temporary directory.",
    )
    parser.add_argument("--no-state", action="store_true", help="Skip save_state/load_state persistence check.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.init_points < 0 or args.n_iter < 0:
        raise SystemExit("--init-points and --n-iter must be non-negative")
    run_core_smoke(args)


if __name__ == "__main__":
    main()
