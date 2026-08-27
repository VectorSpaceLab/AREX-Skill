#!/usr/bin/env python3
"""Tiny deterministic smoke checks for POT barycenter workflows.

The checks use only NumPy and the installed POT package (`import ot`). They do
not require plotting data, notebooks, or external repository files.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from typing import Callable

import numpy as np


def import_pot():
    """Import POT with an explicit user-facing error."""
    try:
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise SystemExit(
            "ERROR: barycenter_smoke.py requires POT installed as package 'POT' "
            "with import root 'ot'. Install POT before running this smoke check."
        ) from exc
    return ot


def assert_finite(name: str, value: np.ndarray) -> None:
    arr = np.asarray(value)
    if not np.isfinite(arr).all():
        raise AssertionError(f"{name} contains non-finite values: {arr!r}")


def assert_simplex(name: str, value: np.ndarray, atol: float = 1e-6) -> None:
    arr = np.asarray(value, dtype=float)
    assert_finite(name, arr)
    if (arr < -atol).any():
        raise AssertionError(f"{name} has negative entries beyond tolerance: {arr!r}")
    total = float(arr.sum())
    if not np.isclose(total, 1.0, atol=atol):
        raise AssertionError(f"{name} sum is {total:.12g}, expected 1.0")


def run_fixed_support(ot) -> str:
    """Check entropic, debiased, and exact LP barycenters on a 3-bin grid."""
    x = np.arange(3, dtype=float)[:, None]
    M = ot.dist(x, x)
    A = np.array(
        [
            [1.0, 0.0],
            [0.0, 0.0],
            [0.0, 1.0],
        ]
    )
    weights = np.array([0.5, 0.5])
    expected = np.array([0.0, 1.0, 0.0])

    bary_entropic = ot.bregman.barycenter(
        A,
        M,
        reg=1e-2,
        weights=weights,
        numItermax=5000,
        stopThr=1e-9,
        warn=False,
    )
    bary_debiased = ot.bregman.barycenter_debiased(
        A,
        M,
        reg=1e-2,
        weights=weights,
        numItermax=5000,
        stopThr=1e-9,
        warn=False,
    )
    bary_lp = ot.lp.barycenter(A, M, weights=weights, solver="highs-ipm")

    assert_simplex("entropic fixed-support barycenter", bary_entropic, atol=1e-6)
    assert_simplex("debiased fixed-support barycenter", bary_debiased, atol=1e-4)
    assert_simplex("LP fixed-support barycenter", bary_lp, atol=1e-8)
    np.testing.assert_allclose(bary_lp, expected, atol=1e-8)
    if int(np.argmax(bary_entropic)) != 1 or int(np.argmax(bary_debiased)) != 1:
        raise AssertionError(
            "Expected the symmetric 3-bin barycenters to peak at the middle bin; "
            f"got entropic={bary_entropic}, debiased={bary_debiased}"
        )
    return "fixed-support ok: entropic/debiased simplex and LP middle-bin check passed"


def run_free_support(ot) -> str:
    """Check exact and Sinkhorn free-support barycenters between two Diracs."""
    measures_locations = [np.array([[-1.0]]), np.array([[1.0]])]
    measures_weights = [np.array([1.0]), np.array([1.0])]
    X_init = np.array([[-12.0]])
    b = np.array([1.0])

    exact = ot.lp.free_support_barycenter(
        measures_locations,
        measures_weights,
        X_init,
        b=b,
        numItermax=20,
        stopThr=1e-12,
    )
    sinkhorn = ot.bregman.free_support_sinkhorn_barycenter(
        measures_locations,
        measures_weights,
        X_init,
        reg=1.0,
        b=b,
        numItermax=20,
        numInnerItermax=200,
        stopThr=1e-12,
    )

    assert_finite("exact free-support barycenter", exact)
    assert_finite("Sinkhorn free-support barycenter", sinkhorn)
    np.testing.assert_allclose(exact, np.array([[0.0]]), atol=1e-8)
    np.testing.assert_allclose(sinkhorn, np.array([[0.0]]), atol=1e-6)
    return "free-support ok: exact and Sinkhorn Dirac midpoint checks passed"


def _check_bary_result(name: str, res, expected_shape: tuple[int, int]) -> None:
    if getattr(res, "X", None) is None:
        raise AssertionError(f"{name} returned no barycenter support X")
    if tuple(res.X.shape) != expected_shape:
        raise AssertionError(f"{name} X shape {res.X.shape} != {expected_shape}")
    assert_finite(f"{name} support", res.X)
    assert_simplex(f"{name} barycenter weights", res.b, atol=1e-6)
    if not res.list_res or len(res.list_res) != 2:
        raise AssertionError(f"{name} expected two inner OT results, got {res.list_res!r}")
    if res.value is None or not np.isfinite(float(np.asarray(res.value))):
        raise AssertionError(f"{name} returned non-finite objective value: {res.value!r}")


def run_sample_cloud(ot) -> str:
    """Check `solve_bary_sample` on two unequal-size tiny 1D clouds."""
    x1 = np.array([[0.0], [1.0]])
    x2 = np.array([[1.0], [1.5], [2.0]])
    X_a_list = [x1, x2]
    a_list = [ot.unif(x.shape[0]) for x in X_a_list]
    w = np.array([0.5, 0.5])
    X_b_init = np.array([[0.25], [1.25]])
    b = ot.unif(2)

    with warnings.catch_warnings():
        # POT's BCD criterion starts from infinity, which can emit a benign
        # scalar-divide RuntimeWarning on tiny deterministic fixtures.
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in scalar divide",
            category=RuntimeWarning,
        )
        exact = ot.solvers.solve_bary_sample(
            X_a_list,
            n=2,
            a_list=a_list,
            w=w,
            X_b_init=X_b_init,
            b=b,
            metric="sqeuclidean",
            max_iter_bary=20,
            tol_bary=1e-8,
            stopping_criterion="bary",
        )
    _check_bary_result("exact sample-cloud barycenter", exact, (2, 1))

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="invalid value encountered in scalar divide",
            category=RuntimeWarning,
        )
        regularized = ot.solvers.solve_bary_sample(
            X_a_list,
            n=2,
            a_list=a_list,
            w=w,
            X_b_init=np.asarray(exact.X),
            b=b,
            metric="sqeuclidean",
            reg=1.0,
            reg_type="KL",
            max_iter=2000,
            tol=1e-9,
            max_iter_bary=20,
            tol_bary=1e-8,
            stopping_criterion="loss",
        )
    _check_bary_result("regularized sample-cloud barycenter", regularized, (2, 1))
    return "sample-cloud ok: exact and entropic BaryResult checks passed"


def run_convolutional(ot) -> str:
    """Check convolutional and debiased image barycenters on two tiny images."""
    A = np.array(
        [
            [[1.0, 0.01], [0.01, 0.01]],
            [[0.01, 0.01], [0.01, 1.0]],
        ],
        dtype=float,
    )
    A /= A.sum(axis=(1, 2), keepdims=True)
    weights = np.array([0.5, 0.5])

    bar = ot.bregman.convolutional_barycenter2d(
        A,
        reg=0.5,
        weights=weights,
        method="sinkhorn",
        numItermax=300,
        stopThr=1e-8,
        warn=False,
    )
    bar_debiased = ot.bregman.convolutional_barycenter2d_debiased(
        A,
        reg=0.5,
        weights=weights,
        method="sinkhorn",
        numItermax=300,
        stopThr=1e-8,
        warn=False,
    )

    if tuple(bar.shape) != (2, 2) or tuple(bar_debiased.shape) != (2, 2):
        raise AssertionError(
            f"convolutional shapes expected (2, 2), got {bar.shape} and {bar_debiased.shape}"
        )
    assert_simplex("convolutional barycenter", bar, atol=1e-4)
    assert_simplex("debiased convolutional barycenter", bar_debiased, atol=1e-4)
    return "convolutional ok: ordinary and debiased image checks passed"


CASES: dict[str, Callable[[object], str]] = {
    "fixed-support": run_fixed_support,
    "free-support": run_free_support,
    "sample-cloud": run_sample_cloud,
    "convolutional": run_convolutional,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic tiny POT barycenter smoke checks. Default 'all' "
            "covers fixed-support, free-support, sample-cloud, and convolutional workflows."
        )
    )
    parser.add_argument(
        "--case",
        choices=["all", *CASES.keys()],
        default="all",
        help="Smoke case to run. Default: all.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    ot = import_pot()
    selected = list(CASES) if args.case == "all" else [args.case]
    for case_name in selected:
        message = CASES[case_name](ot)
        print(message)
    print("all requested POT barycenter smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
