#!/usr/bin/env python3
"""Deterministic smoke checks for POT core optimal-transport solvers.

The checks use tiny in-memory fixtures only: exact EMD, unified OTResult
semantics, entropic and L2 regularization, sample-cloud conversion, 1D/circle
helpers, sparse EMD, and expected invalid-input failures. They do not run
repository tests, examples, plotting, network calls, or external datasets.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import Any, Callable


def require_pot():
    try:
        import ot  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "POT is not importable. Install it with `pip install POT` or "
            "`conda install -c conda-forge pot`, then rerun this smoke check."
        ) from exc
    return ot


def require_numpy():
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover - POT normally requires numpy
        raise RuntimeError(
            "NumPy is not importable. POT core solver checks require NumPy arrays."
        ) from exc
    return np


def require_scipy_sparse():
    try:
        import scipy.sparse as sp  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "SciPy sparse is not importable. Sparse EMD checks require "
            "`scipy.sparse`; install SciPy or run with `--mode` excluding sparse."
        ) from exc
    return sp


def _to_float(x: Any) -> float:
    arr = require_numpy().asarray(x)
    if arr.size != 1:
        raise RuntimeError(f"Expected a scalar value, got shape {arr.shape}.")
    return float(arr.reshape(-1)[0])


def _dense(x: Any):
    np = require_numpy()
    if hasattr(x, "toarray"):
        return np.asarray(x.toarray())
    return np.asarray(x)


def _allclose(label: str, actual: Any, expected: Any, *, rtol=1e-8, atol=1e-10) -> None:
    np = require_numpy()
    if not np.allclose(np.asarray(actual), np.asarray(expected), rtol=rtol, atol=atol):
        raise RuntimeError(
            f"{label} mismatch:\nactual={np.asarray(actual)}\nexpected={np.asarray(expected)}"
        )


def _validate_simplex(name: str, weights: Any, *, expected_len: int | None = None):
    np = require_numpy()
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1:
        raise ValueError(f"{name} must be a 1D vector, got shape {w.shape}.")
    if expected_len is not None and len(w) != expected_len:
        raise ValueError(
            f"{name} length {len(w)} does not match expected length {expected_len}."
        )
    if not np.all(np.isfinite(w)):
        raise ValueError(f"{name} contains NaN or infinite weights.")
    if np.any(w < 0):
        raise ValueError(f"{name} contains negative weights; balanced OT needs nonnegative weights.")
    total = float(w.sum())
    if total <= 0:
        raise ValueError(f"{name} has zero total mass.")
    if not np.isclose(total, 1.0):
        raise ValueError(
            f"{name} sums to {total:.12g}; normalize to the simplex or use an "
            "unbalanced/partial OT workflow if the mass difference is meaningful."
        )
    return w


def _validate_balanced_plan(label: str, plan: Any, a: Any, b: Any, *, atol=1e-8) -> None:
    np = require_numpy()
    P = _dense(plan)
    if P.shape != (len(a), len(b)):
        raise RuntimeError(f"{label} plan shape {P.shape} != {(len(a), len(b))}.")
    if np.any(P < -atol):
        raise RuntimeError(f"{label} plan has entries below {-atol}.")
    _allclose(f"{label} row marginals", P.sum(axis=1), a, atol=atol, rtol=1e-7)
    _allclose(f"{label} column marginals", P.sum(axis=0), b, atol=atol, rtol=1e-7)


def _tiny_problem():
    np = require_numpy()
    ot = require_pot()
    X_a = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=float)
    X_b = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=float)
    a = _validate_simplex("a", np.array([0.25, 0.50, 0.25], dtype=float), expected_len=3)
    b = _validate_simplex("b", np.array([0.60, 0.40], dtype=float), expected_len=2)
    M = ot.dist(X_a, X_b, metric="sqeuclidean")
    return ot, np, X_a, X_b, a, b, M


def run_exact(args: argparse.Namespace) -> dict[str, Any]:
    ot, np, _X_a, _X_b, a, b, M = _tiny_problem()
    res = ot.solve(M, a, b, n_threads=1)
    G = ot.emd(a, b, M)
    W = ot.emd2(a, b, M)

    _validate_balanced_plan("ot.solve exact", res.plan, a, b, atol=1e-10)
    _allclose("ot.solve exact plan vs ot.emd", res.plan, G, atol=1e-10)
    _allclose("ot.solve value vs ot.emd2", res.value, W, atol=1e-10)
    _allclose("exact linear recomputation", res.value, np.sum(_dense(res.plan) * M), atol=1e-10)
    if res.potentials is None or len(res.potentials) != 2:
        raise RuntimeError("Expected exact ot.solve to expose two dual potential arrays.")

    return {
        "value": _to_float(res.value),
        "plan_shape": list(_dense(res.plan).shape),
        "status": str(res.status),
    }


def run_regularized(args: argparse.Namespace) -> dict[str, Any]:
    ot, np, _X_a, _X_b, a, b, M = _tiny_problem()
    reg = float(args.reg)
    if reg <= 0:
        raise RuntimeError("--reg must be positive for regularized Sinkhorn checks.")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = ot.solve(
            M,
            a,
            b,
            reg=reg,
            reg_type="KL",
            max_iter=args.max_iter,
            tol=args.tol,
            grad="detach",
        )
        G_sink = ot.sinkhorn(
            a,
            b,
            M,
            reg=reg,
            method="sinkhorn_log",
            numItermax=args.max_iter,
            stopThr=args.tol,
            warn=True,
        )
        W_sink = ot.sinkhorn2(
            a,
            b,
            M,
            reg=reg,
            method="sinkhorn_log",
            numItermax=args.max_iter,
            stopThr=args.tol,
            warn=True,
        )

    _validate_balanced_plan("ot.solve entropic", res.plan, a, b, atol=2e-6)
    _validate_balanced_plan("ot.sinkhorn", G_sink, a, b, atol=2e-6)
    _allclose("sinkhorn2 linear value", np.sum(_dense(G_sink) * M), W_sink, atol=2e-6, rtol=2e-6)
    _allclose("unified value_linear vs sinkhorn2", res.value_linear, W_sink, atol=2e-6, rtol=2e-6)

    res_l2 = ot.solve(M, a, b, reg=1.0, reg_type="L2", max_iter=args.max_iter, tol=args.tol)
    _validate_balanced_plan("ot.solve L2", res_l2.plan, a, b, atol=2e-6)

    return {
        "reg": reg,
        "value": _to_float(res.value),
        "value_linear": _to_float(res.value_linear),
        "l2_value": _to_float(res_l2.value),
        "warnings": [str(w.message) for w in caught],
    }


def run_sample(args: argparse.Namespace) -> dict[str, Any]:
    ot, np, X_a, X_b, a, b, M = _tiny_problem()
    matrix_res = ot.solve(M, a, b, n_threads=1)
    sample_res = ot.solve_sample(X_a, X_b, a=a, b=b, metric="sqeuclidean", n_threads=1)
    sample_reg = ot.solve_sample(
        X_a,
        X_b,
        a=a,
        b=b,
        metric="sqeuclidean",
        reg=float(args.reg),
        max_iter=args.max_iter,
        tol=args.tol,
        grad="detach",
    )

    _validate_balanced_plan("ot.solve_sample exact", sample_res.plan, a, b, atol=1e-10)
    _allclose("sample value vs cost-matrix value", sample_res.value, matrix_res.value, atol=1e-10)
    _validate_balanced_plan("ot.solve_sample regularized", sample_reg.plan, a, b, atol=2e-6)

    return {
        "exact_value": _to_float(sample_res.value),
        "regularized_value_linear": _to_float(sample_reg.value_linear),
        "plan_shape": list(_dense(sample_res.plan).shape),
    }


def run_oned(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    x_a = np.array([0.0, 1.0, 3.0], dtype=float)
    x_b = np.array([0.0, 2.0], dtype=float)
    a = _validate_simplex("a_1d", np.array([0.2, 0.3, 0.5], dtype=float), expected_len=3)
    b = _validate_simplex("b_1d", np.array([0.4, 0.6], dtype=float), expected_len=2)

    G_1d, log_1d = ot.emd_1d(x_a, x_b, a, b, metric="sqeuclidean", log=True)
    W_1d = ot.emd2_1d(x_a, x_b, a, b, metric="sqeuclidean")
    M = ot.dist(x_a.reshape((-1, 1)), x_b.reshape((-1, 1)), metric="sqeuclidean")
    W_dense = ot.emd2(a, b, M)
    W1_loss = ot.wasserstein_1d(x_a, x_b, a, b, p=1)

    _validate_balanced_plan("ot.emd_1d", G_1d, a, b, atol=1e-10)
    _allclose("emd2_1d vs emd_1d log cost", W_1d, log_1d["cost"], atol=1e-12)
    _allclose("emd2_1d vs dense emd2", W_1d, W_dense, atol=1e-12)

    u = np.array([0.05, 0.25, 0.75], dtype=float)
    v = np.array([0.10, 0.50, 0.80], dtype=float)
    wu = _validate_simplex("wu_circle", np.array([0.3, 0.2, 0.5], dtype=float), expected_len=3)
    wv = _validate_simplex("wv_circle", np.array([0.3, 0.4, 0.3], dtype=float), expected_len=3)
    W_circle = ot.wasserstein_circle(u, v, wu, wv, p=1)
    if _to_float(W_circle) < -1e-12:
        raise RuntimeError("Circle Wasserstein loss should be nonnegative.")

    return {
        "emd2_1d": _to_float(W_1d),
        "wasserstein_1d_p1": _to_float(W1_loss),
        "wasserstein_circle_p1": _to_float(W_circle),
    }


def run_sparse(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    sp = require_scipy_sparse()
    coo_ctor = getattr(sp, "coo_array", sp.coo_matrix)

    n = 4
    a = _validate_simplex("a_sparse", ot.unif(n), expected_len=n)
    b = _validate_simplex("b_sparse", ot.unif(n), expected_len=n)
    rows = np.array([0, 1, 2, 3, 0, 1, 2, 3], dtype=int)
    cols = np.array([0, 1, 2, 3, 1, 2, 3, 0], dtype=int)
    data = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0], dtype=float)
    M_sparse = coo_ctor((data, (rows, cols)), shape=(n, n))

    G_sparse, log = ot.emd(a, b, M_sparse, log=True)
    W_sparse = ot.emd2(a, b, M_sparse)
    G_dense = _dense(G_sparse)
    _validate_balanced_plan("sparse ot.emd", G_dense, a, b, atol=1e-10)
    _allclose("sparse emd2 vs emd log", W_sparse, log["cost"], atol=1e-12)

    return {
        "cost": _to_float(W_sparse),
        "plan_shape": list(G_dense.shape),
        "sparse_type": type(G_sparse).__name__,
    }


def run_invalid(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    messages: dict[str, str] = {}

    try:
        _validate_simplex("bad_negative", np.array([0.5, -0.2, 0.7]))
    except ValueError as exc:
        messages["negative_weights"] = str(exc)
    else:  # pragma: no cover - indicates validation bug
        raise RuntimeError("Negative-weight validation did not trigger.")

    M2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=float)
    try:
        ot.emd(np.array([0.7, 0.3]), np.array([0.2, 0.2]), M2)
    except AssertionError as exc:
        messages["mass_mismatch"] = str(exc) or "balanced EMD rejected unequal total mass"
    else:  # pragma: no cover - indicates unexpected POT behavior
        raise RuntimeError("Expected ot.emd to reject unequal total mass.")

    try:
        ot.solve(M2, reg=1.0, reg_type="not_a_reg_type")
    except NotImplementedError as exc:
        messages["invalid_reg_type"] = str(exc) or "invalid reg_type rejected"
    else:  # pragma: no cover
        raise RuntimeError("Expected ot.solve to reject an invalid reg_type.")

    try:
        ot.solve(M2, method="not_a_method")
    except ValueError as exc:
        messages["invalid_method"] = str(exc)
    else:  # pragma: no cover
        raise RuntimeError("Expected ot.solve to reject an invalid method.")

    return messages


RUNNERS: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
    "exact": run_exact,
    "regularized": run_regularized,
    "sample": run_sample,
    "oned": run_oned,
    "sparse": run_sparse,
    "invalid": run_invalid,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny deterministic POT core-solver checks: exact EMD, "
            "regularized Sinkhorn/L2, sample-cloud OTResult conversion, "
            "1D/circle helpers, sparse EMD, and invalid-input diagnostics."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["all", *RUNNERS.keys()],
        default="all",
        help="Subset of checks to run. Default: all.",
    )
    parser.add_argument(
        "--reg",
        type=float,
        default=0.25,
        help="Positive entropic regularization used by regularized checks. Default: 0.25.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=1000,
        help="Maximum iterations for iterative regularized solvers. Default: 1000.",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=1e-8,
        help="Stopping tolerance for iterative regularized solvers. Default: 1e-8.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a text summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = list(RUNNERS) if args.mode == "all" else [args.mode]

    try:
        results = {name: RUNNERS[name](args) for name in selected}
    except Exception as exc:  # deliberate explicit CLI error path
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print("POT core solver smoke checks passed:")
        for name, result in results.items():
            print(f"- {name}: {result}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
