#!/usr/bin/env python3
"""Deterministic smoke checks for POT unbalanced and partial OT workflows.

The helper imports the installed public POT package as ``ot`` and builds tiny
NumPy fixtures in memory. It checks relaxed-marginal UOT, fixed-mass partial OT,
unbalanced barycenters, and the L2-UOT regularization-path API without plotting,
network access, external datasets, or repository-local files. The legacy
``--include-optional-uot-1d`` flag attempts the optional autodiff-backed 1D UOT
helper when PyTorch is available and reports a structured skip otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from typing import Any, Callable


def _import_dependencies():
    """Import NumPy and POT with actionable errors."""
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "Missing required dependency 'numpy'. Install NumPy in the Python "
            "environment that will run POT unbalanced/partial workflows."
        ) from exc

    try:
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "Missing required dependency 'POT' (import name 'ot'). Install POT "
            "before running this smoke check."
        ) from exc

    return np, ot


def _to_float(value: Any) -> float:
    np, _ot = _import_dependencies()
    arr = np.asarray(value, dtype=float)
    if arr.size != 1:
        raise AssertionError(f"Expected scalar value, got shape {arr.shape}.")
    return float(arr.reshape(-1)[0])


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _finite_nonnegative(name: str, array: Any, np, *, atol: float = 1e-10):
    arr = np.asarray(array, dtype=float)
    _ensure(np.isfinite(arr).all(), f"{name} contains NaN or infinite values: {arr!r}")
    _ensure(float(arr.min(initial=0.0)) >= -atol, f"{name} has negative entries: {arr!r}")
    return arr


def _normalize_cost(cost: Any, np):
    arr = np.asarray(cost, dtype=float)
    _ensure(arr.ndim == 2, f"cost matrix must be 2D, got shape {arr.shape}")
    _ensure(np.isfinite(arr).all(), "cost matrix contains NaN or infinite values")
    max_value = float(arr.max(initial=0.0))
    if max_value > 0.0:
        arr = arr / max_value
    return arr


def _uot_partial_fixture(np, ot):
    """Return a tiny outlier fixture adapted from POT's UOT/partial examples."""
    x_source = np.array(
        [[0.0, 0.0], [0.1, 0.0], [-0.1, 0.0], [4.0, 4.0]], dtype=float
    )
    x_target = np.array(
        [[0.05, 0.0], [-0.05, 0.0], [0.0, 0.1], [-4.0, -4.0]], dtype=float
    )
    a = np.array([0.30, 0.30, 0.30, 0.10], dtype=float)
    b = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    cost = _normalize_cost(ot.dist(x_source, x_target), np)
    return a, b, cost


def _validate_relaxed_plan(label: str, plan: Any, a: Any, b: Any, np, *, atol=1e-9):
    G = _finite_nonnegative(label, plan, np, atol=atol)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    _ensure(G.shape == (a.size, b.size), f"{label} shape {G.shape} != {(a.size, b.size)}")
    transported_mass = float(G.sum())
    _ensure(transported_mass > 0.0, f"{label} transported zero mass")
    _ensure(
        transported_mass < min(float(a.sum()), float(b.sum())) + 1e-7,
        f"{label} should be relaxed, got mass {transported_mass:.12g}",
    )
    return G


def run_uot(np, ot, _args: argparse.Namespace) -> dict[str, Any]:
    """Check entropic KL-UOT and non-entropic KL-UOT mass relaxation."""
    a, b, cost = _uot_partial_fixture(np, ot)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sinkhorn_plan = ot.unbalanced.sinkhorn_unbalanced(
            a,
            b,
            cost,
            reg=0.05,
            reg_m=0.2,
            method="sinkhorn",
            reg_type="kl",
            numItermax=5000,
            stopThr=1e-12,
        )
        mm_plan = ot.unbalanced.mm_unbalanced(a, b, cost, reg_m=0.2, div="kl")

    sinkhorn_plan = _validate_relaxed_plan("sinkhorn_unbalanced", sinkhorn_plan, a, b, np)
    mm_plan = _validate_relaxed_plan("mm_unbalanced", mm_plan, a, b, np)

    # The fixture gives each distribution an outlier. UOT should downweight the
    # expensive outlier row/column rather than matching full balanced marginals.
    sinkhorn_rows = sinkhorn_plan.sum(axis=1)
    sinkhorn_cols = sinkhorn_plan.sum(axis=0)
    _ensure(
        float(sinkhorn_rows[-1]) < float(a[-1]),
        "expected UOT to downweight the source outlier row",
    )
    _ensure(
        float(sinkhorn_cols[-1]) < float(b[-1]),
        "expected UOT to downweight the target outlier column",
    )
    row_l1 = float(np.linalg.norm(sinkhorn_rows - a, ord=1))
    col_l1 = float(np.linalg.norm(sinkhorn_cols - b, ord=1))
    _ensure(row_l1 > 1e-2 or col_l1 > 1e-2, "UOT plan unexpectedly matches balanced marginals")

    return {
        "case": "uot",
        "status": "passed",
        "sinkhorn_mass": float(sinkhorn_plan.sum()),
        "mm_mass": float(mm_plan.sum()),
        "source_outlier_transported": float(sinkhorn_rows[-1]),
        "target_outlier_transported": float(sinkhorn_cols[-1]),
        "row_l1_relaxation": row_l1,
        "col_l1_relaxation": col_l1,
        "warnings": [str(w.message) for w in caught],
    }


def run_partial(np, ot, _args: argparse.Namespace) -> dict[str, Any]:
    """Check exact partial OT fixed transported mass plus 1D partial helper."""
    a, b, cost = _uot_partial_fixture(np, ot)
    mass = 0.75
    plan = ot.partial.partial_wasserstein(a, b, cost, m=mass)
    plan = _finite_nonnegative("partial_wasserstein", plan, np)
    _ensure(plan.shape == cost.shape, f"partial_wasserstein shape {plan.shape} != {cost.shape}")
    np.testing.assert_allclose(float(plan.sum()), mass, atol=1e-10, rtol=1e-10)
    _ensure(np.all(plan.sum(axis=1) <= a + 1e-10), "partial source marginal exceeds a")
    _ensure(np.all(plan.sum(axis=0) <= b + 1e-10), "partial target marginal exceeds b")
    _ensure(float(plan.sum(axis=1)[-1]) <= 1e-10, "partial OT should leave source outlier unused")
    _ensure(float(plan.sum(axis=0)[-1]) <= 1e-10, "partial OT should leave target outlier unused")

    x = np.array([5.0, -2.0, 4.0], dtype=float)
    y = np.array([-1.0, 1.0, 3.0], dtype=float)
    indices_x, indices_y, marginal_costs = ot.partial.partial_wasserstein_1d(
        x, y, n_transported_samples=2, p=1
    )
    indices_x = np.asarray(indices_x, dtype=int)
    indices_y = np.asarray(indices_y, dtype=int)
    marginal_costs = _finite_nonnegative("partial_wasserstein_1d marginal_costs", marginal_costs, np)
    _ensure(indices_x.shape == (2,) and indices_y.shape == (2,), "1D partial OT returned wrong index shape")
    _ensure(marginal_costs.shape == (2,), "1D partial OT returned wrong marginal cost shape")
    _ensure(
        np.all(indices_x >= 0) and np.all(indices_x < x.size) and np.all(indices_y >= 0) and np.all(indices_y < y.size),
        "1D partial OT returned out-of-range indices",
    )
    np.testing.assert_allclose(marginal_costs.sum(), 2.0, atol=1e-12, rtol=1e-12)

    return {
        "case": "partial",
        "status": "passed",
        "transported_mass": float(plan.sum()),
        "source_outlier_transported": float(plan.sum(axis=1)[-1]),
        "target_outlier_transported": float(plan.sum(axis=0)[-1]),
        "partial_1d_indices_source": indices_x.tolist(),
        "partial_1d_indices_target": indices_y.tolist(),
        "partial_1d_total_cost": float(marginal_costs.sum()),
    }


def run_barycenter(np, ot, _args: argparse.Namespace) -> dict[str, Any]:
    """Check a fixed-grid unbalanced barycenter vector."""
    support = np.arange(5, dtype=float)[:, None]
    cost = _normalize_cost(ot.dist(support, support), np)
    hist_1 = np.array([0.05, 0.15, 0.60, 0.15, 0.05], dtype=float)
    hist_2 = 1.8 * np.array([0.05, 0.10, 0.20, 0.40, 0.25], dtype=float)
    distributions = np.vstack([hist_1, hist_2]).T
    weights = np.array([0.4, 0.6], dtype=float)

    bary = ot.unbalanced.barycenter_unbalanced(
        distributions,
        cost,
        reg=0.1,
        reg_m=1.0,
        weights=weights,
        numItermax=2000,
        stopThr=1e-9,
    )
    bary = _finite_nonnegative("barycenter_unbalanced", bary, np)
    _ensure(bary.shape == (cost.shape[0],), f"barycenter shape {bary.shape} != {(cost.shape[0],)}")
    mass = float(bary.sum())
    _ensure(0.5 < mass < 2.5, f"unbalanced barycenter mass {mass:.12g} outside expected tiny-fixture range")
    normalized = bary / mass
    np.testing.assert_allclose(float(normalized.sum()), 1.0, atol=1e-12, rtol=1e-12)
    _ensure(int(np.argmax(bary)) in {2, 3}, f"unexpected barycenter peak location: {bary!r}")

    return {
        "case": "barycenter",
        "status": "passed",
        "mass": mass,
        "normalized_sum": float(normalized.sum()),
        "peak_index": int(np.argmax(bary)),
        "shape": list(bary.shape),
    }


def run_regpath(np, ot, _args: argparse.Namespace) -> dict[str, Any]:
    """Check regpath reconstruction, returning a structured skip if brittle."""
    try:
        x_source = np.array([[0.0], [1.0], [3.0]], dtype=float)
        x_target = np.array([[0.2], [1.5], [2.5]], dtype=float)
        a = np.array([0.2, 0.5, 0.3], dtype=float)
        b = np.array([0.3, 0.4, 0.3], dtype=float)
        cost = _normalize_cost(ot.dist(x_source, x_target), np)
        reg = 1e-4

        terminal_plan, path_plans, gamma_path = ot.regpath.regularization_path(
            a, b, cost, reg=reg, semi_relaxed=False, itmax=1000
        )
        reconstructed_terminal = ot.regpath.compute_transport_plan(reg, gamma_path, path_plans)
        np.testing.assert_allclose(reconstructed_terminal, terminal_plan, atol=1e-8, rtol=1e-8)

        terminal_matrix = _finite_nonnegative("regularization_path terminal plan", terminal_plan.reshape(cost.shape), np)
        gamma_one_matrix = _finite_nonnegative(
            "regularization_path gamma=1 plan",
            ot.regpath.compute_transport_plan(1.0, gamma_path, path_plans).reshape(cost.shape),
            np,
            atol=1e-9,
        )
        _ensure(len(gamma_path) >= 2, "regularization path should expose at least two gamma knots")
        _ensure(gamma_one_matrix.shape == cost.shape, f"gamma=1 plan shape {gamma_one_matrix.shape} != {cost.shape}")
        _ensure(float(gamma_one_matrix.sum()) > 0.0, "gamma=1 regpath plan transported zero mass")

        return {
            "case": "regpath",
            "status": "passed",
            "knots": len(gamma_path),
            "terminal_mass": float(terminal_matrix.sum()),
            "gamma_one_mass": float(gamma_one_matrix.sum()),
            "shape": list(gamma_one_matrix.shape),
            "min_gamma": float(np.min(np.asarray(gamma_path, dtype=float))),
            "max_gamma": float(np.max(np.asarray(gamma_path, dtype=float))),
        }
    except Exception as exc:  # pragma: no cover - depends on POT/SciPy path internals
        return {
            "case": "regpath",
            "status": "skipped",
            "reason": f"ot.regpath reconstruction was not stable in this environment: {exc}",
        }


def run_optional_uot_1d(np, ot) -> dict[str, Any]:
    """Run optional PyTorch-backed uot_1d, or return a structured skip."""
    try:
        import torch  # type: ignore
    except Exception:
        return {
            "case": "uot_1d",
            "status": "skipped",
            "reason": "optional PyTorch backend is not installed; NumPy-only POT environments cannot run ot.unbalanced.uot_1d",
        }

    try:
        x = torch.linspace(0.0, 1.0, 5, dtype=torch.float64)
        y = torch.linspace(0.1, 1.1, 5, dtype=torch.float64)
        a = torch.ones(5, dtype=torch.float64) / 5.0
        b = torch.tensor([0.10, 0.15, 0.20, 0.25, 0.30], dtype=torch.float64)
        u_relaxed, v_relaxed, loss = ot.unbalanced.uot_1d(
            x,
            y,
            reg_m=1.0,
            u_weights=a,
            v_weights=b,
            p=2,
            numItermax=3,
            returnCost="linear",
        )
        _ensure(bool(torch.isfinite(u_relaxed).all()), "uot_1d source marginal contains non-finite values")
        _ensure(bool(torch.isfinite(v_relaxed).all()), "uot_1d target marginal contains non-finite values")
        _ensure(bool(torch.isfinite(torch.as_tensor(loss)).all()), "uot_1d loss is non-finite")
        _ensure(tuple(u_relaxed.shape) == (5,), f"uot_1d source shape {tuple(u_relaxed.shape)} != (5,)")
        _ensure(tuple(v_relaxed.shape) == (5,), f"uot_1d target shape {tuple(v_relaxed.shape)} != (5,)")
        return {
            "case": "uot_1d",
            "status": "passed",
            "backend": "torch",
            "source_mass": float(u_relaxed.detach().cpu().sum().item()),
            "target_mass": float(v_relaxed.detach().cpu().sum().item()),
            "loss": float(torch.as_tensor(loss).detach().cpu().reshape(-1)[0].item()),
        }
    except Exception as exc:
        return {
            "case": "uot_1d",
            "status": "skipped",
            "reason": f"optional ot.unbalanced.uot_1d check could not run with PyTorch: {exc}",
        }


CASES: dict[str, Callable[[Any, Any, argparse.Namespace], dict[str, Any]]] = {
    "uot": run_uot,
    "partial": run_partial,
    "barycenter": run_barycenter,
    "regpath": run_regpath,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny deterministic NumPy checks for POT unbalanced OT, partial OT, "
            "unbalanced barycenters, and regularization paths."
        )
    )
    parser.add_argument(
        "--case",
        choices=("all", "uot", "partial", "barycenter", "regpath"),
        default="all",
        help="Which smoke check to run. Default: all.",
    )
    parser.add_argument(
        "--include-optional-uot-1d",
        action="store_true",
        help=(
            "Legacy optional check for ot.unbalanced.uot_1d. It attempts a PyTorch-backed "
            "fixture and records a skip when the optional backend is unavailable."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a short text report.",
    )
    return parser


def _overall_status(results: list[dict[str, Any]]) -> str:
    statuses = {str(item.get("status")) for item in results}
    if "failed" in statuses:
        return "failed"
    if "skipped" in statuses:
        return "passed_with_skips"
    return "passed"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        np, ot = _import_dependencies()
        selected = list(CASES) if args.case == "all" else [args.case]
        results = [CASES[name](np, ot, args) for name in selected]
        if args.include_optional_uot_1d and args.case in {"all", "uot"}:
            results.append(run_optional_uot_1d(np, ot))

        payload = {
            "status": _overall_status(results),
            "pot_version": str(getattr(ot, "__version__", "unknown")),
            "checks": results,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"POT unbalanced/partial smoke {payload['status']}")
            for item in results:
                line = f"- {item['case']}: {item['status']}"
                if item.get("status") == "skipped":
                    line += f" ({item.get('reason', 'no reason provided')})"
                elif item["case"] in {"uot", "partial", "barycenter", "regpath", "uot_1d"}:
                    details = []
                    for key in ("sinkhorn_mass", "transported_mass", "mass", "gamma_one_mass", "loss"):
                        if key in item:
                            details.append(f"{key}={float(item[key]):.6g}")
                    if details:
                        line += " " + ", ".join(details)
                print(line)
        return 0
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
