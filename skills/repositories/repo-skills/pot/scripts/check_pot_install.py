#!/usr/bin/env python3
"""Check that an installed POT package is usable for repo-skill workflows.

This root helper imports the public package as ``ot``, verifies compiled solver
extensions that are part of the base package, runs a tiny NumPy OT solve, and
optionally reports optional dependency availability. It does not read any source
checkout files, download data, start services, or require optional backends.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


def _record_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"status": "available", "module": module, "object": getattr(imported, "__name__", module)}
    except Exception as exc:  # pragma: no cover - depends on user environment
        return {"status": "missing", "module": module, "error": f"{type(exc).__name__}: {exc}"}


def run(include_optional: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "passed", "checks": {}}
    try:
        import numpy as np  # type: ignore
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        return {"status": "failed", "error": f"base import failed: {type(exc).__name__}: {exc}"}

    payload["checks"]["version"] = getattr(ot, "__version__", "unknown")
    payload["checks"]["backend_list"] = [str(nx) for nx in ot.backend.get_backend_list()]

    compiled = {
        name: _record_import(name)
        for name in ["ot.lp.emd_wrap", "ot.partial.partial_cython", "ot.bsp.bsp_wrap"]
    }
    payload["checks"]["compiled_extensions"] = compiled
    if any(item["status"] != "available" for item in compiled.values()):
        payload["status"] = "failed"

    try:
        n = 4
        a = ot.unif(n)
        b = ot.unif(n)
        x = np.arange(n, dtype=float)[:, None]
        M = ot.dist(x, x)
        scale = float(M.max()) or 1.0
        M = M / scale
        plan = ot.emd(a, b, M)
        sol = ot.solve(M, a, b, reg=0.1, max_iter=1000, tol=1e-9)
        if plan.shape != (n, n) or sol.plan.shape != (n, n):
            raise AssertionError("unexpected plan shape")
        if not np.isfinite(plan).all() or not np.isfinite(sol.plan).all():
            raise AssertionError("non-finite plan")
        payload["checks"]["tiny_solve"] = {
            "status": "passed",
            "emd_mass": float(plan.sum()),
            "regularized_value": float(sol.value),
        }
    except Exception as exc:
        payload["status"] = "failed"
        payload["checks"]["tiny_solve"] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}

    if include_optional:
        optional_modules = {
            "plot": "ot.plot",
            "dr": "ot.dr",
            "gnn": "ot.gnn",
            "torch": "torch",
            "jax": "jax",
            "tensorflow": "tensorflow",
            "cupy": "cupy",
            "cvxpy": "cvxpy",
            "geomloss": "geomloss",
        }
        payload["checks"]["optional"] = {
            label: _record_import(module) for label, module in optional_modules.items()
        }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-optional", action="store_true", help="Report optional backend/extra imports without requiring them.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    payload = run(include_optional=args.include_optional)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"POT install check: {payload['status']}")
        for key, value in payload.get("checks", {}).items():
            print(f"- {key}: {value}")
        if payload.get("error"):
            print(f"error: {payload['error']}", file=sys.stderr)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
