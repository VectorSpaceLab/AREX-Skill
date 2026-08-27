#!/usr/bin/env python3
"""Deterministic smoke checks for POT backend discovery and batch solvers.

The checks use tiny in-memory fixtures only. They do not run repository tests,
examples, plotting code, network calls, downloads, or external datasets. Optional
backend libraries are reported when available, but NumPy is the only backend
required by the default checks.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from typing import Any, Callable

OPTIONAL_BACKENDS: dict[str, dict[str, str]] = {
    "torch": {
        "module": "torch",
        "backend": "torch",
        "disable_env": "POT_BACKEND_DISABLE_PYTORCH",
        "install": 'install PyTorch or use `pip install "POT[backend-torch]"`',
    },
    "jax": {
        "module": "jax",
        "backend": "jax",
        "disable_env": "POT_BACKEND_DISABLE_JAX",
        "install": 'install JAX/JAXlib or use `pip install "POT[backend-jax]"`',
    },
    "tensorflow": {
        "module": "tensorflow",
        "backend": "tensorflow",
        "disable_env": "POT_BACKEND_DISABLE_TENSORFLOW",
        "install": 'install TensorFlow or use `pip install "POT[backend-tf]"`',
    },
    "cupy": {
        "module": "cupy",
        "backend": "cupy",
        "disable_env": "POT_BACKEND_DISABLE_CUPY",
        "install": "install a CUDA-compatible CuPy package, such as a conda-forge CuPy build or the matching cupy-cudaXX wheel",
    },
}


def require_numpy():
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover - POT normally requires NumPy
        raise RuntimeError(
            "NumPy is not importable. POT backend and batch smoke checks require NumPy arrays."
        ) from exc
    return np


def require_pot():
    try:
        import ot  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "POT is not importable. Install it with `pip install POT` or "
            "`conda install -c conda-forge pot`. If an optional backend import "
            "is broken, set the matching POT_BACKEND_DISABLE_* environment "
            "variable before importing POT."
        ) from exc
    return ot


def _as_float_list(x: Any) -> list[float]:
    np = require_numpy()
    return [float(v) for v in np.asarray(x).reshape(-1)]


def _allclose(label: str, actual: Any, expected: Any, *, atol: float, rtol: float = 1e-7) -> None:
    np = require_numpy()
    actual_arr = np.asarray(actual)
    expected_arr = np.asarray(expected)
    if not np.allclose(actual_arr, expected_arr, atol=atol, rtol=rtol):
        raise RuntimeError(
            f"{label} mismatch:\nactual={actual_arr}\nexpected={expected_arr}\natol={atol} rtol={rtol}"
        )


def _validate_plan(label: str, plan: Any, a: Any, b: Any, *, atol: float) -> None:
    np = require_numpy()
    P = np.asarray(plan)
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    expected_shape = (a_arr.shape[0], a_arr.shape[1], b_arr.shape[1])
    if P.shape != expected_shape:
        raise RuntimeError(f"{label} plan shape {P.shape} != expected {expected_shape}.")
    if not np.isfinite(P).all():
        raise RuntimeError(f"{label} plan contains NaN or infinite entries.")
    if P.min() < -atol:
        raise RuntimeError(f"{label} plan contains entries below {-atol}.")
    _allclose(f"{label} row marginals", P.sum(axis=2), a_arr, atol=atol)
    _allclose(f"{label} column marginals", P.sum(axis=1), b_arr, atol=atol)


def _sample_fixture():
    np = require_numpy()
    X = np.array(
        [
            [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
            [[0.0, 0.0], [0.5, 0.8], [1.0, 0.2]],
            [[0.2, 0.1], [0.9, 0.1], [0.4, 0.9]],
        ],
        dtype=float,
    )
    Y = np.array(
        [
            [[0.1, 0.0], [1.0, 0.2], [0.1, 1.0]],
            [[0.0, 0.1], [0.6, 0.7], [0.9, 0.3]],
            [[0.3, 0.1], [0.8, 0.2], [0.5, 0.8]],
        ],
        dtype=float,
    )
    a = np.tile(np.array([0.2, 0.5, 0.3], dtype=float), (X.shape[0], 1))
    b = np.tile(np.array([0.4, 0.35, 0.25], dtype=float), (X.shape[0], 1))
    return X, Y, a, b


def _cost_fixture():
    ot = require_pot()
    X, Y, a, b = _sample_fixture()
    M = ot.dist_batch(X, Y, metric="sqeuclidean")
    return ot, X, Y, a, b, M


def _implementation_public_name(implementation: Any) -> str:
    """Return POT's backend name for a backend implementation class."""
    # Backend classes define a public __name__ class attribute such as "numpy",
    # but Python's class __name__ descriptor reports "NumpyBackend". Inspecting
    # the class dictionary avoids instantiating optional GPU backends just to get
    # their POT-level names.
    class_dict = getattr(implementation, "__dict__", {})
    return str(class_dict.get("__name__", getattr(implementation, "__name__", implementation)))


def _registered_backend_names(ot_module: Any) -> list[str]:
    backend_module = ot_module.backend
    if hasattr(backend_module, "get_available_backend_implementations"):
        implementations = backend_module.get_available_backend_implementations()
        return [_implementation_public_name(impl) for impl in implementations]
    # Fallback for older POT-like versions. Avoid relying on this unless needed.
    return [str(backend) for backend in backend_module.get_backend_list()]


def _optional_status(ot_module: Any) -> dict[str, dict[str, Any]]:
    registered = set(_registered_backend_names(ot_module))
    status: dict[str, dict[str, Any]] = {}
    for name, meta in OPTIONAL_BACKENDS.items():
        module_found = importlib.util.find_spec(meta["module"]) is not None
        env_value = os.environ.get(meta["disable_env"])
        backend_registered = meta["backend"] in registered
        status[name] = {
            "module_found": module_found,
            "backend_registered": backend_registered,
            "disable_env": meta["disable_env"],
            "disable_env_set": bool(env_value),
            "install_hint": meta["install"],
        }
    return status


def _enforce_required_optional(ot_module: Any, required: list[str]) -> None:
    if not required:
        return
    status = _optional_status(ot_module)
    missing: list[str] = []
    for name in required:
        item = status[name]
        if not item["module_found"] or not item["backend_registered"]:
            reason = []
            if not item["module_found"]:
                reason.append("module import spec not found")
            if not item["backend_registered"]:
                reason.append("POT backend not registered")
            if item["disable_env_set"]:
                reason.append(f"{item['disable_env']} is set")
            missing.append(f"{name}: {', '.join(reason)}; {item['install_hint']}")
    if missing:
        raise RuntimeError("Required optional backend(s) unavailable: " + " | ".join(missing))


def run_backends(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    from ot.backend import get_backend, to_numpy

    names = _registered_backend_names(ot)
    _enforce_required_optional(ot, args.require_optional or [])

    # Exercise the required NumPy backend and conversion path.
    arr = np.array([0.25, 0.75], dtype=float)
    nx = get_backend(arr)
    if nx.__name__ != "numpy":
        raise RuntimeError(f"Expected NumPy backend for a NumPy array, got {nx.__name__}.")
    arr_np = to_numpy(arr)
    if not isinstance(arr_np, np.ndarray):
        raise RuntimeError(f"to_numpy should return a NumPy ndarray, got {type(arr_np)}.")

    instantiated: list[str] | None = None
    if args.instantiate_backends:
        instantiated = [backend.__name__ for backend in ot.backend.get_backend_list()]

    return {
        "pot_version": getattr(ot, "__version__", "unknown"),
        "registered_backend_implementations": names,
        "instantiated_backends": instantiated,
        "optional_status": _optional_status(ot),
        "numpy_get_backend": nx.__name__,
        "numpy_to_numpy_dtype": str(arr_np.dtype),
    }


def run_batch_linear(args: argparse.Namespace) -> dict[str, Any]:
    ot, X, Y, a, b, M = _cost_fixture()
    np = require_numpy()
    tol = float(args.tol)
    max_iter = int(args.max_iter)
    compare_atol = max(5e-4, tol * 50)

    M_loop = np.stack([ot.dist(X[i], Y[i], metric="sqeuclidean") for i in range(X.shape[0])])
    _allclose("dist_batch vs looped ot.dist", M, M_loop, atol=1e-12)

    loop_exact = []
    for i in range(M.shape[0]):
        res_i = ot.solve(M[i], a[i], b[i], max_iter=max_iter, tol=tol)
        loop_exact.append(float(np.asarray(res_i.value_linear)))

    res_exact = ot.solve_batch(
        M,
        a=a,
        b=b,
        method="auto",
        max_iter=max_iter,
        tol=tol,
        grad="detach",
        inner_reg=float(args.inner_reg),
    )
    _validate_plan("solve_batch exact/proximal", res_exact.plan, a, b, atol=compare_atol)
    _allclose("solve_batch exact values", res_exact.value_linear, loop_exact, atol=compare_atol)

    reg = float(args.reg)
    loop_reg = []
    for i in range(M.shape[0]):
        res_i = ot.solve(
            M[i],
            a[i],
            b[i],
            reg=reg,
            reg_type="entropy",
            max_iter=max_iter,
            tol=tol,
            grad="detach",
        )
        loop_reg.append(float(np.asarray(res_i.value_linear)))

    res_reg = ot.solve_batch(
        M,
        reg=reg,
        a=a,
        b=b,
        method="log_sinkhorn",
        reg_type="entropy",
        max_iter=max_iter,
        tol=tol,
        grad="detach",
    )
    _validate_plan("solve_batch entropic", res_reg.plan, a, b, atol=max(1e-5, tol * 20))
    _allclose("solve_batch regularized values", res_reg.value_linear, loop_reg, atol=max(1e-5, tol * 20))

    loss_recomputed = ot.batch.loss_linear_batch(M, res_reg.plan)
    _allclose("loss_linear_batch recomputation", loss_recomputed, res_reg.value_linear, atol=max(1e-8, tol * 10))

    return {
        "batch_shape": list(M.shape),
        "exact_value_linear": _as_float_list(res_exact.value_linear),
        "regularized_value_linear": _as_float_list(res_reg.value_linear),
        "loop_regularized_value_linear": loop_reg,
    }


def run_sample_batch(args: argparse.Namespace) -> dict[str, Any]:
    ot, X, Y, a, b, M = _cost_fixture()
    tol = float(args.tol)
    reg = float(args.reg)

    res_sample = ot.solve_sample_batch(
        X,
        Y,
        reg=reg,
        a=a,
        b=b,
        metric="sqeuclidean",
        method="log_sinkhorn",
        reg_type="entropy",
        max_iter=int(args.max_iter),
        tol=tol,
        grad="detach",
    )
    res_matrix = ot.solve_batch(
        M,
        reg=reg,
        a=a,
        b=b,
        method="log_sinkhorn",
        reg_type="entropy",
        max_iter=int(args.max_iter),
        tol=tol,
        grad="detach",
    )
    _validate_plan("solve_sample_batch", res_sample.plan, a, b, atol=max(1e-5, tol * 20))
    _allclose(
        "solve_sample_batch value_linear vs solve_batch(dist_batch)",
        res_sample.value_linear,
        res_matrix.value_linear,
        atol=max(1e-7, tol * 20),
    )
    sample_loss = ot.batch.loss_linear_samples_batch(X, Y, res_sample.plan, metric="sqeuclidean")
    _allclose("loss_linear_samples_batch recomputation", sample_loss, res_sample.value_linear, atol=max(1e-7, tol * 20))

    return {
        "sample_shape_source": list(X.shape),
        "sample_shape_target": list(Y.shape),
        "plan_shape": list(require_numpy().asarray(res_sample.plan).shape),
        "value_linear": _as_float_list(res_sample.value_linear),
    }


def run_gromov_batch(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    X = np.array(
        [
            [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
            [[0.0, 0.0], [0.8, 0.2], [0.2, 0.9]],
        ],
        dtype=float,
    )
    Y = np.array(
        [
            [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]],
            [[0.05, 0.0], [0.25, 0.85], [0.75, 0.25]],
        ],
        dtype=float,
    )
    Ca = ot.dist_batch(X, X)
    Cb = ot.dist_batch(Y, Y)
    B, n, m = Ca.shape[0], Ca.shape[1], Cb.shape[1]
    a = np.full((B, n), 1.0 / n)
    b = np.full((B, m), 1.0 / m)

    res = ot.solve_gromov_batch(
        Ca,
        Cb,
        reg=max(float(args.reg), 0.2),
        a=a,
        b=b,
        symmetric=True,
        max_iter=min(int(args.max_iter), 40),
        tol=max(float(args.tol), 1e-7),
        max_iter_inner=200,
        tol_inner=max(float(args.tol), 1e-7),
        grad="detach",
    )
    _validate_plan("solve_gromov_batch", res.plan, a, b, atol=max(1e-3, float(args.tol) * 100))
    if not np.isfinite(np.asarray(res.value)).all():
        raise RuntimeError("solve_gromov_batch returned non-finite values.")

    return {
        "Ca_shape": list(Ca.shape),
        "Cb_shape": list(Cb.shape),
        "plan_shape": list(np.asarray(res.plan).shape),
        "value": _as_float_list(res.value),
        "value_quad": _as_float_list(res.value_quad),
    }


def run_mixed_backend(args: argparse.Namespace) -> dict[str, Any]:
    ot = require_pot()
    np = require_numpy()
    from ot.backend import get_backend

    status = _optional_status(ot).get("torch", {})
    if not status.get("module_found") or not status.get("backend_registered"):
        return {
            "skipped": True,
            "reason": "Torch is not installed/registered; NumPy-only recovery guidance still applies.",
            "diagnostic": "Run with --require-optional torch in a Torch environment to turn this into a hard check.",
        }

    try:
        import torch  # type: ignore
    except ImportError as exc:  # pragma: no cover - guarded above
        raise RuntimeError(
            "Torch appeared available but could not be imported. Repair the Torch install or set POT_BACKEND_DISABLE_PYTORCH=1 before importing POT."
        ) from exc

    a_np = np.array([0.5, 0.5], dtype=float)
    b_torch = torch.tensor([0.5, 0.5], dtype=torch.float64)
    M_np = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=float)
    try:
        get_backend(a_np, b_torch, M_np)
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover - would indicate a POT contract change
        raise RuntimeError("Expected get_backend to reject mixed NumPy/Torch arrays, but it did not.")

    b_np = np.asarray([0.5, 0.5], dtype=float)
    nx = get_backend(a_np, b_np, M_np)
    res = ot.solve(M_np, a_np, b_np, n_threads=1)
    _allclose("mixed-backend NumPy recovery row marginals", res.plan.sum(axis=1), a_np, atol=1e-12)
    _allclose("mixed-backend NumPy recovery column marginals", res.plan.sum(axis=0), b_np, atol=1e-12)

    return {
        "mixed_error_contains": message,
        "recovered_backend": nx.__name__,
        "recovered_value": float(np.asarray(res.value)),
    }


RUNNERS: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
    "backends": run_backends,
    "batch-linear": run_batch_linear,
    "sample-batch": run_sample_batch,
    "gromov-batch": run_gromov_batch,
    "mixed-backend": run_mixed_backend,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny POT backend and batch-solver smoke checks. Defaults require "
            "only POT and NumPy; optional backends are reported but not required."
        )
    )
    parser.add_argument(
        "--case",
        choices=["all", *RUNNERS.keys()],
        default="all",
        help="Subset of checks to run. Default: all.",
    )
    parser.add_argument(
        "--reg",
        type=float,
        default=0.5,
        help="Positive entropic/proximal regularization for regularized checks. Default: 0.5.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=10000,
        help="Maximum iterations for linear batch solvers. Default: 10000.",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=1e-5,
        help="Stopping tolerance used by iterative batch solvers. Default: 1e-5.",
    )
    parser.add_argument(
        "--inner-reg",
        type=float,
        default=1e-3,
        help="Inner regularization for the proximal batch solver. Default: 1e-3.",
    )
    parser.add_argument(
        "--instantiate-backends",
        action="store_true",
        help=(
            "Also call ot.backend.get_backend_list(). This instantiates available backend "
            "objects and may initialize optional GPU libraries."
        ),
    )
    parser.add_argument(
        "--require-optional",
        choices=sorted(OPTIONAL_BACKENDS),
        action="append",
        default=[],
        help=(
            "Require an optional backend to be installed and registered by POT. "
            "May be repeated. Default: do not require optional backends."
        ),
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
    if args.reg <= 0:
        print("ERROR: --reg must be positive for regularized batch checks.", file=sys.stderr)
        return 2
    if args.max_iter <= 0:
        print("ERROR: --max-iter must be positive.", file=sys.stderr)
        return 2
    if args.tol <= 0:
        print("ERROR: --tol must be positive.", file=sys.stderr)
        return 2
    if args.inner_reg <= 0:
        print("ERROR: --inner-reg must be positive.", file=sys.stderr)
        return 2

    selected = list(RUNNERS) if args.case == "all" else [args.case]
    try:
        results = {name: RUNNERS[name](args) for name in selected}
    except Exception as exc:  # deliberate explicit CLI error path
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print("POT backend and batch smoke checks passed:")
        for name, result in results.items():
            print(f"- {name}: {result}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
