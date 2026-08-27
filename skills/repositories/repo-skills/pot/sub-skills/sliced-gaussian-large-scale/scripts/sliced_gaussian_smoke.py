#!/usr/bin/env python3
"""Deterministic smoke checks for POT sliced, Gaussian, GMM, and low-rank APIs.

This helper is self-contained and uses tiny NumPy fixtures. It does not read the
POT source checkout, download data, or require plotting. It is intended for a
local Python environment where POT is installed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Callable


def _import_dependencies():
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        raise SystemExit(
            "Missing required dependency 'numpy'. Install NumPy before running "
            "this POT smoke check."
        ) from exc

    try:
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        raise SystemExit(
            "Missing required package 'POT' (import root 'ot'). Install POT in "
            "the active Python environment before running this smoke check."
        ) from exc

    return np, ot


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _finite_scalar(value: Any, name: str) -> float:
    value_float = float(value)
    _assert(math.isfinite(value_float), f"{name} is not finite: {value!r}")
    return value_float


def check_sliced(seed: int) -> dict[str, Any]:
    np, ot = _import_dependencies()
    rng = np.random.RandomState(seed)
    n = 8
    X = rng.normal(size=(n, 2))
    Y = X + np.array([0.5, -0.25])
    a = ot.unif(n)
    b = ot.unif(n)

    same = ot.sliced.sliced_wasserstein_distance(
        X, X, a=a, b=a, n_projections=16, seed=seed
    )
    _assert(abs(float(same)) < 1e-12, "sliced distance for identical clouds is not zero")

    swd, log = ot.sliced.sliced_wasserstein_distance(
        X, Y, a=a, b=b, n_projections=16, seed=seed, log=True
    )
    swd = _finite_scalar(swd, "sliced_wasserstein_distance")
    _assert(swd > 0.0, "sliced distance between shifted clouds should be positive")
    _assert(log["projections"].shape == (2, 16), "unexpected projection log shape")
    _assert(len(log["projected_emds"]) == 16, "unexpected projected EMD count")

    projections = ot.sliced.get_random_projections(2, 16, seed=seed)
    swd_from_proj = ot.sliced.sliced_wasserstein_distance(X, Y, a=a, b=b, projections=projections)
    _assert(np.isclose(swd, swd_from_proj), "fixed projections did not reproduce SWD")

    plan_min, cost_min = ot.sliced.min_sliced_transport_plan(
        X, Y, a=a, b=b, projections=projections, dense=True
    )
    plan_exp, cost_exp = ot.sliced.expected_sliced_plan(
        X, Y, a=a, b=b, projections=projections, beta=0.0, dense=True
    )
    for label, plan in {"min_plan": plan_min, "expected_plan": plan_exp}.items():
        _assert(plan.shape == (n, n), f"{label} has unexpected shape {plan.shape}")
        _assert(np.allclose(plan.sum(axis=1), a), f"{label} source marginals mismatch")
        _assert(np.allclose(plan.sum(axis=0), b), f"{label} target marginals mismatch")

    return {
        "swd": swd,
        "min_cost": _finite_scalar(cost_min, "min_sliced_cost"),
        "expected_cost": _finite_scalar(cost_exp, "expected_sliced_cost"),
    }


def check_gaussian(seed: int) -> dict[str, Any]:
    np, ot = _import_dependencies()
    _ = seed
    ms = np.array([0.0, 0.0])
    mt = np.array([1.0, -2.0])
    Cs = np.eye(2)
    Ct = np.eye(2)

    W = ot.gaussian.bures_wasserstein_distance(ms, mt, Cs, Ct)
    expected = np.linalg.norm(mt - ms)
    _assert(np.isclose(W, expected), "Bures distance with equal covariance should equal mean distance")

    A, b = ot.gaussian.bures_wasserstein_mapping(ms, mt, Cs, Ct)
    mapped_mean = ms @ A + b
    _assert(A.shape == (2, 2), f"Gaussian map A has unexpected shape {A.shape}")
    _assert(b.shape[-1] == 2, f"Gaussian map bias has unexpected shape {b.shape}")
    _assert(np.allclose(mapped_mean, mt), "Gaussian map does not send source mean to target mean")

    means = np.array([[0.0, 0.0], [2.0, 0.0]])
    covs = np.stack([np.eye(2), 2.0 * np.eye(2)])
    weights = np.array([0.25, 0.75])
    mb, Cb = ot.gaussian.bures_wasserstein_barycenter(
        means, covs, weights=weights, num_iter=100, eps=1e-9
    )
    _assert(mb.shape == (2,), "Gaussian barycenter mean has unexpected shape")
    _assert(Cb.shape == (2, 2), "Gaussian barycenter covariance has unexpected shape")
    _assert(np.all(np.linalg.eigvalsh(0.5 * (Cb + Cb.T)) >= -1e-8), "barycenter covariance is not PSD")

    return {"bures_distance": _finite_scalar(W, "bures_distance"), "barycenter_trace": float(np.trace(Cb))}


def check_gmm(seed: int) -> dict[str, Any]:
    np, ot = _import_dependencies()
    m_s = np.array([[0.0], [2.0]])
    m_t = np.array([[1.0], [3.0], [4.0]])
    C_s = np.array([[[0.2]], [[0.3]]])
    C_t = np.array([[[0.2]], [[0.25]], [[0.4]]])
    w_s = np.array([0.4, 0.6])
    w_t = np.array([0.3, 0.3, 0.4])

    plan = ot.gmm.gmm_ot_plan(m_s, m_t, C_s, C_t, w_s, w_t)
    _assert(plan.shape == (2, 3), f"GMM plan has unexpected shape {plan.shape}")
    _assert(np.allclose(plan.sum(axis=1), w_s), "GMM plan source marginals mismatch")
    _assert(np.allclose(plan.sum(axis=0), w_t), "GMM plan target marginals mismatch")

    loss = ot.gmm.gmm_ot_loss(m_s, m_t, C_s, C_t, w_s, w_t)
    _assert(float(loss) >= 0.0, "GMM loss should be nonnegative")

    x = np.linspace(-1.0, 3.0, 7)[:, None]
    mapped_bary = ot.gmm.gmm_ot_apply_map(x, m_s, m_t, C_s, C_t, w_s, w_t, plan=plan, method="bary")
    mapped_rand = ot.gmm.gmm_ot_apply_map(
        x, m_s, m_t, C_s, C_t, w_s, w_t, plan=plan, method="rand", seed=seed
    )
    _assert(mapped_bary.shape == x.shape, "GMM barycentric map shape mismatch")
    _assert(mapped_rand.shape == x.shape, "GMM random map shape mismatch")

    return {"loss": _finite_scalar(loss, "gmm_ot_loss"), "plan_mass": float(plan.sum())}


def check_lowrank(seed: int, lowrank_init: str) -> dict[str, Any]:
    np, ot = _import_dependencies()
    n = 12
    X_s = np.linspace(0.0, 1.0, n)[:, None]
    X_t = np.linspace(0.1, 1.1, n)[:, None]
    a = ot.unif(n)
    b = ot.unif(n)

    try:
        Q, R, g, log = ot.lowrank.lowrank_sinkhorn(
            X_s,
            X_t,
            a=a,
            b=b,
            reg=0.1,
            rank=4,
            init=lowrank_init,
            seed_init=seed,
            rescale_cost=False,
            warn=False,
            log=True,
            numItermax=800,
            stopThr=1e-8,
        )
    except ImportError as exc:
        if lowrank_init == "kmeans":
            raise SystemExit(
                "lowrank init='kmeans' requires optional scikit-learn. Re-run with "
                "--lowrank-init deterministic or install scikit-learn in this environment."
            ) from exc
        raise

    _assert(Q.shape == (n, 4), f"Q has unexpected shape {Q.shape}")
    _assert(R.shape == (n, 4), f"R has unexpected shape {R.shape}")
    _assert(g.shape == (4,), f"g has unexpected shape {g.shape}")
    P = log["lazy_plan"][:]
    _assert(P.shape == (n, n), f"low-rank lazy plan has unexpected shape {P.shape}")
    _assert(np.allclose(P.sum(axis=1), a, atol=1e-5), "low-rank plan source marginals mismatch")
    _assert(np.allclose(P.sum(axis=0), b, atol=1e-5), "low-rank plan target marginals mismatch")

    K1, K2 = ot.lowrank.kernel_nystroem(X_s, X_t, anchors=8, sigma=1.0, random_state=seed)
    _assert(K1.shape[0] == n and K2.shape[0] == n, "Nystroem factors have wrong leading dimension")
    _assert(np.isfinite(K1).all() and np.isfinite(K2).all(), "Nystroem factors contain nonfinite values")

    return {"rank": 4, "value_linear": _finite_scalar(log["value_linear"], "lowrank value_linear")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic tiny POT smoke checks for sliced, Gaussian, GMM, and low-rank APIs.",
    )
    parser.add_argument(
        "--mode",
        choices=["all", "sliced", "gaussian", "gmm", "lowrank"],
        default="all",
        help="Which smoke check to run. Default: all.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic fixtures. Default: 0.")
    parser.add_argument(
        "--lowrank-init",
        choices=["random", "deterministic", "kmeans"],
        default="deterministic",
        help="Initialization for lowrank_sinkhorn. 'kmeans' requires optional scikit-learn.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary instead of a compact text summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    checks: dict[str, Callable[[], dict[str, Any]]] = {
        "sliced": lambda: check_sliced(args.seed),
        "gaussian": lambda: check_gaussian(args.seed),
        "gmm": lambda: check_gmm(args.seed),
        "lowrank": lambda: check_lowrank(args.seed, args.lowrank_init),
    }
    selected = list(checks) if args.mode == "all" else [args.mode]

    results: dict[str, Any] = {}
    try:
        for name in selected:
            results[name] = checks[name]()
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "ok", "checks": results}, indent=2, sort_keys=True))
    else:
        completed = ", ".join(selected)
        print(f"OK: completed POT smoke checks: {completed}")
        for name in selected:
            print(f"  - {name}: {results[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
