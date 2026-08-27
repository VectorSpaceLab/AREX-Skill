#!/usr/bin/env python3
"""Tiny numeric smoke checks for tslearn metric/backend workflows.

This helper adapts the assigned plotting/autodiff examples into deterministic,
no-download checks. It is safe to run from any current working directory as long
as tslearn is importable in the active Python environment.

Examples:
  python metrics_smoke.py --help
  python metrics_smoke.py all
  python metrics_smoke.py dtw --backend numpy
  python metrics_smoke.py dtw --backend pytorch
  python metrics_smoke.py softdtw-loss
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Callable, Dict

import numpy as np


def _torch_module():
    try:
        import torch  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PyTorch is not installed. Use --backend numpy for non-gradient "
            "metric checks or install torch before running softdtw-loss."
        ) from exc
    return torch


def _normalize_backend(name: str) -> str:
    lowered = name.lower()
    if lowered == "torch":
        return "pytorch"
    if lowered not in {"numpy", "pytorch"}:
        raise RuntimeError("backend must be 'numpy', 'pytorch', or 'torch'")
    if lowered == "pytorch":
        _torch_module()
    return lowered


def _maybe_backend_array(data: Any, backend: str, *, requires_grad: bool = False):
    arr = np.asarray(data, dtype=np.float64)
    if backend == "pytorch":
        torch = _torch_module()
        return torch.tensor(arr, dtype=torch.float64, requires_grad=requires_grad)
    return arr


def _to_numpy(value: Any) -> np.ndarray:
    try:
        torch = _torch_module()
        if torch.is_tensor(value):
            return value.detach().cpu().numpy()
    except RuntimeError:
        pass
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, np.generic):
        return np.asarray(value.item())
    return np.asarray(value)


def _float(value: Any) -> float:
    arr = _to_numpy(value)
    return float(arr.reshape(-1)[0])


def _clean(value: Any) -> Any:
    try:
        torch = _torch_module()
        if torch.is_tensor(value):
            value = value.detach().cpu().numpy()
    except RuntimeError:
        pass
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return value.item()
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return repr(value)


def _assert_close(label: str, value: Any, expected: float, *, tol: float = 1e-6) -> None:
    actual = _float(value)
    if not math.isclose(actual, expected, rel_tol=tol, abs_tol=tol):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def _assert_path(label: str, value: Any, expected: Any) -> None:
    if list(value) != list(expected):
        raise AssertionError(f"{label}: expected {expected}, got {value}")


def run_dtw(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics
    from tslearn.backend import instantiate_backend

    backend = _normalize_backend(args.backend)
    x = _maybe_backend_array([1.0, 2.0, 3.0], backend)
    y = _maybe_backend_array([1.0, 2.0, 2.0, 3.0], backend)
    y_nonzero = _maybe_backend_array([1.0, 2.0, 2.0, 3.0, 4.0], backend)

    path, dist = metrics.dtw_path(x, y, be=backend)
    _assert_path("dtw_path", path, [(0, 0), (1, 1), (1, 2), (2, 3)])
    _assert_close("dtw_path distance", dist, 0.0)
    _assert_close("dtw nonzero", metrics.dtw(x, y_nonzero, be=backend), 1.0)
    matrix = metrics.cdist_dtw([[[1.0], [2.0], [2.0], [3.0]], [[1.0], [2.0], [3.0], [4.0]]])
    return {
        "status": "ok",
        "backend": instantiate_backend(backend).backend_string,
        "path": path,
        "distance": _float(dist),
        "cdist_shape": list(np.asarray(matrix).shape),
    }


def run_subsequence(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    query = _maybe_backend_array([2.0, 3.0], backend)
    longseq = _maybe_backend_array([1.0, 2.0, 2.0, 3.0, 4.0], backend)
    path, dist = metrics.dtw_subsequence_path(query, longseq, be=backend)
    _assert_path("dtw_subsequence_path", path, [(0, 2), (1, 3)])
    _assert_close("dtw_subsequence_path distance", dist, 0.0)
    cost_matrix = metrics.subsequence_cost_matrix(query, longseq, be=backend)
    manual_path = metrics.subsequence_path(cost_matrix, 3, be=backend)
    _assert_path("subsequence_path", manual_path, [(0, 2), (1, 3)])
    return {
        "status": "ok",
        "backend": backend,
        "path": path,
        "distance": _float(dist),
        "cost_matrix_shape": list(_to_numpy(cost_matrix).shape),
    }


def run_custom_metric(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    def angular_arc(a: np.ndarray, b: np.ndarray, radius: float = 1.0) -> float:
        theta = np.mod(b[0] - a[0], 2 * np.pi)
        if theta > np.pi:
            theta -= 2 * np.pi
        return float(radius * abs(theta))

    x = np.array([[0.0], [np.pi / 2], [np.pi]])
    y = np.array([[0.0], [np.pi], [np.pi / 2]])
    path, cost = metrics.dtw_path_from_metric(x, y, metric=angular_arc)
    if not path:
        raise AssertionError("custom metric path is empty")
    return {
        "status": "ok",
        "metric": "angular_arc",
        "path": path,
        "cumulative_cost": _float(cost),
    }


def run_ctw(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    x = _maybe_backend_array([1.0, 2.0, 3.0], backend)
    y = _maybe_backend_array([1.0, 2.0, 2.0, 3.0], backend)
    path, cca, dist = metrics.ctw_path(x, y, max_iter=5, n_components=1, be=backend)
    _assert_path("ctw_path", path, [(0, 0), (1, 1), (1, 2), (2, 3)])
    _assert_close("ctw_path distance", dist, 0.0)
    return {
        "status": "ok",
        "backend": backend,
        "path": path,
        "distance": _float(dist),
        "cca_type": type(cca).__name__,
    }


def run_frechet(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    x = _maybe_backend_array([1.0, 2.0, 3.0], backend)
    y = _maybe_backend_array([1.0, 0.0, 2.0, 4.0], backend)
    path, dist = metrics.frechet_path(x, y, be=backend)
    _assert_path("frechet_path", path, [(0, 0), (0, 1), (1, 2), (2, 3)])
    _assert_close("frechet distance", dist, 1.0)
    return {"status": "ok", "backend": backend, "path": path, "distance": _float(dist)}


def run_lcss(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    x = _maybe_backend_array([1.0, 2.0, 3.0], backend)
    y = _maybe_backend_array([-2.0, 5.0, 7.0], backend)
    path, similarity = metrics.lcss_path(x, y, eps=3.0, be=backend)
    _assert_path("lcss_path", path, [(0, 0), (2, 1)])
    _assert_close("lcss similarity", round(float(similarity), 2), 0.67, tol=1e-2)
    return {"status": "ok", "backend": backend, "path": path, "similarity": float(similarity)}


def run_soft_dtw(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    x = _maybe_backend_array([1.0, 2.0, 3.0], backend)
    y = _maybe_backend_array([1.0, 2.0, 2.0, 3.0, 4.0], backend)
    dist_sq_dtw = metrics.soft_dtw(x, y, gamma=0.0, be=backend)
    _assert_close("soft_dtw gamma=0 squared DTW", dist_sq_dtw, 1.0)
    normalized_self = metrics.soft_dtw_normalized(x, x, gamma=0.5, be=backend)
    _assert_close("soft_dtw_normalized self", normalized_self, 0.0)
    alignment, dist = metrics.soft_dtw_alignment(x, y, gamma=1.0, be=backend)
    return {
        "status": "ok",
        "backend": backend,
        "gamma0_squared_dtw": _float(dist_sq_dtw),
        "normalized_self": _float(normalized_self),
        "alignment_shape": list(_to_numpy(alignment).shape),
        "alignment_distance": _float(dist),
    }


def run_gak(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn import metrics

    backend = _normalize_backend(args.backend)
    dataset = _maybe_backend_array([[1.0, 2.0, 2.0, 3.0], [1.0, 2.0, 3.0, 4.0]], backend)
    sigma = metrics.sigma_gak(dataset, n_samples=200, random_state=0, be=backend)
    _assert_close("sigma_gak", sigma, 2.0, tol=1e-5)
    value = metrics.gak(
        _maybe_backend_array([1.0, 2.0, 2.0, 3.0], backend),
        _maybe_backend_array([1.0, 2.0, 3.0, 4.0], backend),
        sigma=2.0,
        be=backend,
    )
    _assert_close("gak", value, 0.65629661, tol=1e-5)
    matrix = metrics.cdist_gak(dataset, sigma=2.0, be=backend)
    return {
        "status": "ok",
        "backend": backend,
        "sigma": _float(sigma),
        "gak": _float(value),
        "cdist": _clean(matrix),
    }


def run_barycenter(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn.barycenters import (
        dtw_barycenter_averaging,
        euclidean_barycenter,
        softdtw_barycenter,
    )

    data = [[[1.0], [2.0], [3.0], [4.0]], [[1.0], [2.0], [4.0], [5.0]]]
    euc = euclidean_barycenter(data)
    dba = dtw_barycenter_averaging(data, max_iter=2)
    soft = softdtw_barycenter(data, gamma=1.0, max_iter=1)
    _assert_close("euclidean first value", euc[0, 0], 1.0)
    return {
        "status": "ok",
        "euclidean": _clean(np.round(euc, 6)),
        "dba_shape": list(np.asarray(dba).shape),
        "softdtw_shape": list(np.asarray(soft).shape),
    }


def run_performance(args: argparse.Namespace) -> Dict[str, Any]:
    from tslearn.metrics import performance

    y_true = [[[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]]
    y_pred = [[[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]]]
    train = [[[3.0, 4.0], [5.0, 5.0], [5.0, 6.0], [6.0, 7.0], [7.0, 8.0]]]
    mae = performance.mae(y_true, y_pred)
    mse = performance.mse(y_true, y_pred)
    mase = performance.mase(y_true, y_pred, train)
    _assert_close("mae", mae, 1.0)
    _assert_close("mse", mse, 1.0)
    _assert_close("mase", mase, 1.0)
    return {"status": "ok", "mae": _float(mae), "mse": _float(mse), "mase": _float(mase)}


def run_softdtw_loss(args: argparse.Namespace) -> Dict[str, Any]:
    torch = _torch_module()
    from tslearn.metrics import SoftDTWLossPyTorch

    x = torch.zeros((2, 3, 1), dtype=torch.float64, requires_grad=True)
    y = torch.ones((2, 4, 1), dtype=torch.float64)
    criterion = SoftDTWLossPyTorch(gamma=1.0, normalize=True)
    loss_values = criterion(x, y)
    if list(loss_values.shape) != [2]:
        raise AssertionError(f"expected per-example loss shape [2], got {list(loss_values.shape)}")
    loss = loss_values.mean()
    loss.backward()
    if x.grad is None or list(x.grad.shape) != [2, 3, 1]:
        raise AssertionError("SoftDTWLossPyTorch did not populate x.grad with the expected shape")
    return {
        "status": "ok",
        "loss_values": _clean(loss_values),
        "grad_norm": float(x.grad.detach().norm().cpu()),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_used": str(x.device),
    }


def run_all(args: argparse.Namespace) -> Dict[str, Any]:
    runners: Dict[str, Callable[[argparse.Namespace], Dict[str, Any]]] = {
        "dtw": run_dtw,
        "subsequence": run_subsequence,
        "custom-metric": run_custom_metric,
        "ctw": run_ctw,
        "frechet": run_frechet,
        "lcss": run_lcss,
        "soft-dtw": run_soft_dtw,
        "gak": run_gak,
        "barycenter": run_barycenter,
        "performance": run_performance,
    }
    out: Dict[str, Any] = {}
    for name, runner in runners.items():
        out[name] = runner(argparse.Namespace(backend="numpy"))
    try:
        out["softdtw-loss"] = run_softdtw_loss(argparse.Namespace())
    except RuntimeError as exc:  # torch optional
        out["softdtw-loss"] = {"status": "skipped", "reason": str(exc)}
    return {"status": "ok", "checks": out}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.set_defaults(func=None)
    sub = parser.add_subparsers(dest="command")

    def add_backend(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--backend",
            default="numpy",
            choices=["numpy", "pytorch", "torch"],
            help="Backend for this smoke check. 'torch' is accepted as a PyTorch alias.",
        )

    for name, runner, help_text, backend in [
        ("dtw", run_dtw, "DTW path, scalar distance, and cdist smoke", True),
        ("subsequence", run_subsequence, "Subsequence-DTW path helper smoke", True),
        ("custom-metric", run_custom_metric, "DTW path with a custom angular metric", False),
        ("ctw", run_ctw, "Canonical Time Warping smoke", True),
        ("frechet", run_frechet, "Fréchet path smoke", True),
        ("lcss", run_lcss, "LCSS path smoke", True),
        ("soft-dtw", run_soft_dtw, "Soft-DTW, normalized Soft-DTW, and alignment smoke", True),
        ("gak", run_gak, "GAK bandwidth/kernel/cdist smoke", True),
        ("barycenter", run_barycenter, "Euclidean, DBA, and Soft-DTW barycenter smoke", False),
        ("performance", run_performance, "MAE, MSE, and MASE smoke", False),
        ("softdtw-loss", run_softdtw_loss, "PyTorch SoftDTWLossPyTorch gradient smoke", False),
    ]:
        p = sub.add_parser(name, help=help_text)
        if backend:
            add_backend(p)
        p.set_defaults(func=runner)

    p_all = sub.add_parser("all", help="Run all CPU-safe checks and torch loss if available")
    p_all.set_defaults(func=run_all)
    return parser


def main(argv: Any = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help()
        return 0
    try:
        result = args.func(args)
    except (AssertionError, RuntimeError, ImportError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(_clean(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
