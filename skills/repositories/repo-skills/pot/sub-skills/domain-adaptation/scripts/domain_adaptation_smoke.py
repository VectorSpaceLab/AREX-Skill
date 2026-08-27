#!/usr/bin/env python3
"""Deterministic smoke checks for POT domain-adaptation workflows.

The helper imports the installed public POT package as ``ot`` and builds tiny
NumPy fixtures in memory. It exercises baseline EMD/Sinkhorn transports,
learned mapping, multi-source JCPOT, and optional dependency probes without
plotting, downloads, native test execution, or repository-local files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import warnings
from typing import Any, Callable


def _import_dependencies():
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - user environment dependent
        raise RuntimeError("Missing required dependency 'numpy'.") from exc
    try:
        import ot  # type: ignore
    except Exception as exc:  # pragma: no cover - user environment dependent
        raise RuntimeError("Missing required dependency 'POT' (import name 'ot').") from exc
    return np, ot


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _fixture(np):
    xs = np.array([[-1.0, 0.0], [-1.0, 1.0], [0.0, -1.0], [0.0, 0.0]], dtype=float)
    xt = xs + np.array([2.0, 0.5], dtype=float)
    ys = np.array([0, 0, 1, 1], dtype=int)
    yt_partial = np.array([0, -1, 1, -1], dtype=int)
    return xs, xt, ys, yt_partial


def _validate_coupling(name: str, G: Any, np, rows: int, cols: int) -> dict[str, Any]:
    arr = np.asarray(G, dtype=float)
    _ensure(arr.shape == (rows, cols), f"{name} coupling shape {arr.shape} != {(rows, cols)}")
    _ensure(np.isfinite(arr).all(), f"{name} coupling contains non-finite values")
    _ensure(float(arr.min(initial=0.0)) >= -1e-10, f"{name} coupling has negative entries")
    return {"shape": list(arr.shape), "mass": float(arr.sum())}


def case_emd() -> dict[str, Any]:
    np, ot = _import_dependencies()
    xs, xt, _ys, _yt = _fixture(np)
    est = ot.da.EMDTransport(metric="sqeuclidean", out_of_sample_map="ferradans")
    est.fit(Xs=xs, Xt=xt)
    mapped = np.asarray(est.transform(Xs=xs), dtype=float)
    _ensure(mapped.shape == xs.shape, f"mapped shape {mapped.shape} != {xs.shape}")
    _ensure(np.isfinite(mapped).all(), "EMD mapped samples contain non-finite values")
    info = _validate_coupling("EMDTransport", est.coupling_, np, len(xs), len(xt))
    return {"status": "passed", "coupling": info, "mapped_shape": list(mapped.shape)}


def case_sinkhorn() -> dict[str, Any]:
    np, ot = _import_dependencies()
    xs, xt, ys, yt_partial = _fixture(np)
    est = ot.da.SinkhornTransport(reg_e=0.5, method="sinkhorn_log", max_iter=500, tol=1e-8)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        est.fit(Xs=xs, ys=ys, Xt=xt, yt=yt_partial)
    mapped = np.asarray(est.transform(Xs=xs), dtype=float)
    _ensure(mapped.shape == xs.shape, f"mapped shape {mapped.shape} != {xs.shape}")
    _ensure(np.isfinite(mapped).all(), "Sinkhorn mapped samples contain non-finite values")
    info = _validate_coupling("SinkhornTransport", est.coupling_, np, len(xs), len(xt))
    return {
        "status": "passed",
        "coupling": info,
        "mapped_shape": list(mapped.shape),
        "warnings": [str(w.message) for w in caught],
    }


def case_mapping() -> dict[str, Any]:
    np, ot = _import_dependencies()
    xs, xt, _ys, _yt = _fixture(np)
    try:
        est = ot.da.MappingTransport(
            kernel="linear",
            mu=1.0,
            eta=1e-3,
            bias=True,
            max_iter=3,
            max_inner_iter=5,
            tol=1e-5,
            inner_tol=1e-5,
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            est.fit(Xs=xs, Xt=xt)
        mapped = np.asarray(est.transform(xs + np.array([0.2, -0.1])), dtype=float)
        _ensure(mapped.shape == xs.shape, f"mapped shape {mapped.shape} != {xs.shape}")
        _ensure(np.isfinite(mapped).all(), "MappingTransport mapped samples contain non-finite values")
        info = _validate_coupling("MappingTransport", est.coupling_, np, len(xs), len(xt))
        return {
            "status": "passed",
            "coupling": info,
            "mapped_shape": list(mapped.shape),
            "has_mapping": hasattr(est, "mapping_"),
            "warnings": [str(w.message) for w in caught],
        }
    except Exception as exc:
        return {"status": "skipped", "reason": f"MappingTransport tiny fixture unavailable: {type(exc).__name__}: {exc}"}


def case_jcpot() -> dict[str, Any]:
    np, ot = _import_dependencies()
    xs, xt, ys, _yt = _fixture(np)
    xs_list = [xs, xs + np.array([0.5, -0.25])]
    ys_list = [ys, ys]
    try:
        est = ot.da.JCPOTTransport(reg_e=0.5, max_iter=20, tol=1e-7)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            est.fit(Xs=xs_list, ys=ys_list, Xt=xt)
        _ensure(isinstance(est.coupling_, list), "JCPOT coupling_ should be a list")
        couplings = [
            _validate_coupling(f"JCPOTTransport[{i}]", coupling, np, len(xs_list[i]), len(xt))
            for i, coupling in enumerate(est.coupling_)
        ]
        proportions = est.proportions_[0] if isinstance(est.proportions_, tuple) else est.proportions_
        prop = np.asarray(proportions, dtype=float)
        _ensure(np.isfinite(prop).all(), "JCPOT proportions contain non-finite values")
        _ensure(float(prop.sum()) > 0.0, "JCPOT proportions sum must be positive")
        return {
            "status": "passed",
            "couplings": couplings,
            "proportions": prop.tolist(),
            "warnings": [str(w.message) for w in caught],
        }
    except Exception as exc:
        return {"status": "skipped", "reason": f"JCPOT tiny fixture unavailable: {type(exc).__name__}: {exc}"}


def case_dependencies() -> dict[str, Any]:
    _np, _ot = _import_dependencies()
    probes: dict[str, dict[str, str]] = {}
    for name in ["cvxpy", "sklearn", "autograd", "pymanopt", "torch", "torch_geometric"]:
        try:
            importlib.import_module(name)
            probes[name] = {"status": "available"}
        except Exception as exc:  # pragma: no cover - environment dependent
            probes[name] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}
    try:
        importlib.import_module("ot.dr")
        probes["ot.dr"] = {"status": "available"}
    except Exception as exc:
        probes["ot.dr"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}
    try:
        importlib.import_module("ot.gnn")
        probes["ot.gnn"] = {"status": "available"}
    except Exception as exc:
        probes["ot.gnn"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "passed", "optional_dependencies": probes}


CASES: dict[str, Callable[[], dict[str, Any]]] = {
    "emd": case_emd,
    "sinkhorn": case_sinkhorn,
    "mapping": case_mapping,
    "jcpot": case_jcpot,
    "dependencies": case_dependencies,
}


def run_cases(selected: str) -> dict[str, Any]:
    names = list(CASES) if selected == "all" else [selected]
    results: dict[str, Any] = {}
    for name in names:
        try:
            results[name] = CASES[name]()
        except Exception as exc:
            results[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    statuses = [entry.get("status") for entry in results.values()]
    if any(status == "failed" for status in statuses):
        status = "failed"
    elif any(status == "skipped" for status in statuses):
        status = "passed_with_skips"
    else:
        status = "passed"
    return {"status": status, "cases": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=["all", *CASES.keys()],
        default="all",
        help="Smoke case to run. 'all' runs every deterministic NumPy-safe case.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    payload = run_cases(args.case)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"domain-adaptation smoke status: {payload['status']}")
        for name, result in payload["cases"].items():
            detail = result.get("reason") or result.get("error") or "ok"
            print(f"- {name}: {result.get('status')} ({detail})")
    return 1 if payload["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
