#!/usr/bin/env python3
"""Deterministic POT Gromov-Wasserstein smoke checks.

This helper verifies tiny NumPy-only GW and FGW paths without plotting,
network access, optional graph libraries, optional GNN dependencies, or access to
an original source checkout.

Examples
--------
python scripts/gromov_smoke.py --help
python scripts/gromov_smoke.py --mode all
python scripts/gromov_smoke.py --mode fgw --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Tuple


def _import_dependencies():
    """Import required runtime dependencies with user-facing errors."""
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Missing required dependency 'numpy'. Install NumPy in the Python "
            "environment that will run POT Gromov-Wasserstein workflows."
        ) from exc

    try:
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Missing required dependency 'POT' (import name 'ot'). Install POT "
            "before running this smoke check."
        ) from exc

    return np, ot


def _normalize_cost(matrix, np):
    """Return a finite floating cost matrix scaled by its maximum when possible."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError(f"expected a 2D cost matrix, got shape {matrix.shape}")
    if not np.isfinite(matrix).all():
        raise ValueError("cost matrix contains NaN or infinite values")
    max_value = float(matrix.max())
    if max_value > 0.0:
        matrix = matrix / max_value
    return matrix


def _fixture(np, ot):
    """Create tiny structures and features with an unambiguous FGW alignment."""
    nodes = np.arange(4.0)[:, None]
    structure = _normalize_cost(np.abs(nodes - nodes.T), np)

    # Same structure but reversed feature labels. Pure GW is structurally valid;
    # FGW should prefer the anti-diagonal feature-respecting coupling.
    C1 = structure
    C2 = structure.copy()
    F1 = np.array([[0.0], [0.0], [1.0], [1.0]], dtype=float)
    F2 = F1[::-1].copy()
    M = _normalize_cost(ot.dist(F1, F2), np)
    p = ot.unif(C1.shape[0])
    q = ot.unif(C2.shape[0])
    return C1, C2, M, p, q


def _validate_balanced_plan(name: str, T, p, q, np, tol: float) -> Dict[str, float]:
    """Validate balanced GW/FGW coupling constraints."""
    T = np.asarray(T, dtype=float)
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    if T.shape != (p.shape[0], q.shape[0]):
        raise AssertionError(
            f"{name}: expected plan shape {(p.shape[0], q.shape[0])}, got {T.shape}"
        )
    if not np.isfinite(T).all():
        raise AssertionError(f"{name}: plan contains NaN or infinite values")
    if float(T.min()) < -tol:
        raise AssertionError(f"{name}: plan has negative entry {float(T.min())}")
    row_error = float(np.linalg.norm(T.sum(axis=1) - p, ord=1))
    col_error = float(np.linalg.norm(T.sum(axis=0) - q, ord=1))
    mass_error = float(abs(T.sum() - min(p.sum(), q.sum())))
    if row_error > 10 * tol or col_error > 10 * tol or mass_error > 10 * tol:
        raise AssertionError(
            f"{name}: marginal errors too large: "
            f"row={row_error:.3g}, col={col_error:.3g}, mass={mass_error:.3g}, tol={tol:.3g}"
        )
    return {"row_l1_error": row_error, "col_l1_error": col_error, "mass_error": mass_error}


def run_gw(np, ot, max_iter: int, tol: float) -> Dict[str, Any]:
    """Run unified and classical balanced GW on the tiny fixture."""
    C1, C2, _M, p, q = _fixture(np, ot)
    result = ot.solve_gromov(
        C1,
        C2,
        a=p,
        b=q,
        loss="L2",
        symmetric=True,
        max_iter=max_iter,
        tol=tol,
    )
    errors = _validate_balanced_plan("ot.solve_gromov GW", result.plan, p, q, np, tol)

    gw_value, log = ot.gromov.gromov_wasserstein2(
        C1,
        C2,
        p,
        q,
        loss_fun="square_loss",
        symmetric=True,
        log=True,
        max_iter=max_iter,
        tol_rel=tol,
        tol_abs=tol,
    )
    classical_plan = log["T"]
    classical_errors = _validate_balanced_plan(
        "ot.gromov.gromov_wasserstein2", classical_plan, p, q, np, tol
    )

    return {
        "mode": "gw",
        "unified_value": float(result.value),
        "unified_value_quad": None if result.value_quad is None else float(result.value_quad),
        "classical_value": float(gw_value),
        "plan_shape": list(np.asarray(result.plan).shape),
        "errors": errors,
        "classical_errors": classical_errors,
    }


def run_fgw(np, ot, max_iter: int, tol: float) -> Dict[str, Any]:
    """Run unified and classical balanced FGW on the tiny feature fixture."""
    C1, C2, M, p, q = _fixture(np, ot)
    alpha = 0.5
    result = ot.solve_gromov(
        C1,
        C2,
        M=M,
        a=p,
        b=q,
        loss="L2",
        symmetric=True,
        alpha=alpha,
        max_iter=max_iter,
        tol=tol,
    )
    errors = _validate_balanced_plan("ot.solve_gromov FGW", result.plan, p, q, np, tol)

    T, log = ot.gromov.fused_gromov_wasserstein(
        M,
        C1,
        C2,
        p,
        q,
        loss_fun="square_loss",
        symmetric=True,
        alpha=alpha,
        log=True,
        max_iter=max_iter,
        tol_rel=tol,
        tol_abs=tol,
    )
    classical_errors = _validate_balanced_plan(
        "ot.gromov.fused_gromov_wasserstein", T, p, q, np, tol
    )

    reverse_identity = np.fliplr(np.eye(len(p)))
    reverse_mass = float(np.sum(np.asarray(result.plan) * reverse_identity))
    if reverse_mass < 0.90:
        raise AssertionError(
            "ot.solve_gromov FGW: expected the tiny feature fixture to put most "
            f"mass on the anti-diagonal, observed mass={reverse_mass:.3f}"
        )

    return {
        "mode": "fgw",
        "alpha": alpha,
        "unified_value": float(result.value),
        "unified_value_linear": None
        if result.value_linear is None
        else float(result.value_linear),
        "unified_value_quad": None if result.value_quad is None else float(result.value_quad),
        "classical_value": float(log.get("fgw_dist", float("nan"))),
        "feature_respecting_antidiagonal_mass": reverse_mass,
        "plan_shape": list(np.asarray(result.plan).shape),
        "errors": errors,
        "classical_errors": classical_errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny deterministic POT Gromov-Wasserstein and Fused "
            "Gromov-Wasserstein smoke checks."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("gw", "fgw", "all"),
        default="all",
        help="Which smoke check to run. Default: all.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=200,
        help="Maximum GW/FGW iterations for tiny fixtures. Default: 200.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-7,
        help="Validation tolerance for marginal and mass checks. Default: 1e-7.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a short text report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        np, ot = _import_dependencies()
        if args.max_iter <= 0:
            raise ValueError("--max-iter must be positive")
        if args.tolerance <= 0:
            raise ValueError("--tolerance must be positive")

        results = []
        if args.mode in ("gw", "all"):
            results.append(run_gw(np, ot, args.max_iter, args.tolerance))
        if args.mode in ("fgw", "all"):
            results.append(run_fgw(np, ot, args.max_iter, args.tolerance))

        payload = {"status": "passed", "checks": results}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("POT GW/FGW smoke passed")
            for item in results:
                pieces = [
                    f"mode={item['mode']}",
                    f"value={item['unified_value']:.12g}",
                    f"row_l1={item['errors']['row_l1_error']:.3g}",
                    f"col_l1={item['errors']['col_l1_error']:.3g}",
                ]
                if item["mode"] == "fgw":
                    pieces.append(
                        "anti_diag_mass="
                        f"{item['feature_respecting_antidiagonal_mass']:.3g}"
                    )
                print("- " + ", ".join(pieces))
        return 0
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
