#!/usr/bin/env python3
"""Check a STUMPY runtime environment without reading any repository checkout.

Examples:
  python scripts/stumpy_check_env.py --check import
  python scripts/stumpy_check_env.py --check dask
  python scripts/stumpy_check_env.py --check cuda --require-cuda
  python scripts/stumpy_check_env.py --check all
"""

from __future__ import annotations

import argparse
import json
import sys


def check_import() -> tuple[bool, dict[str, object]]:
    info: dict[str, object] = {"check": "import"}
    try:
        from importlib.metadata import version
        import inspect
        import numpy as np
        import stumpy
    except Exception as exc:  # pragma: no cover - depends on caller env
        info["error"] = f"{type(exc).__name__}: {exc}"
        return False, info
    info["stumpy_distribution_version"] = version("stumpy")
    info["module_version"] = getattr(stumpy, "__version__", None)
    info["stump_signature"] = str(inspect.signature(stumpy.stump))
    T = np.array([0.0, 1.0, 0.0, -1.0, -1.0, 0.0, 1.0, 0.0], dtype=np.float64)
    mp = stumpy.stump(T, 3)
    info["tiny_stump_shape"] = list(mp.shape)
    info["tiny_stump_finite_distances"] = int(np.isfinite(mp[:, 0].astype(float)).sum())
    return True, info


def check_dask() -> tuple[bool, dict[str, object]]:
    info: dict[str, object] = {"check": "dask"}
    try:
        from dask.distributed import Client, LocalCluster
    except Exception as exc:  # pragma: no cover
        info["error"] = f"missing dask/distributed: {type(exc).__name__}: {exc}"
        return False, info
    try:
        cluster = LocalCluster(n_workers=1, threads_per_worker=1, processes=False, dashboard_address=None)
        client = Client(cluster)
        try:
            info["workers"] = len(client.scheduler_info().get("workers", {}))
        finally:
            client.close(); cluster.close()
    except Exception as exc:  # pragma: no cover
        info["error"] = f"LocalCluster smoke failed: {type(exc).__name__}: {exc}"
        return False, info
    return True, info


def check_cuda(require_cuda: bool) -> tuple[bool, dict[str, object]]:
    info: dict[str, object] = {"check": "cuda", "required": require_cuda}
    try:
        import numba
        from numba import cuda
    except Exception as exc:  # pragma: no cover
        info["error"] = f"missing numba.cuda: {type(exc).__name__}: {exc}"
        return (False if require_cuda else True), info
    info["numba_version"] = getattr(numba, "__version__", None)
    try:
        available = bool(cuda.is_available())
        info["cuda_available"] = available
        try:
            devices = list(cuda.gpus)
            info["device_count"] = len(devices)
            info["device_ids"] = [int(getattr(d, "id", i)) for i, d in enumerate(devices)]
        except Exception as dev_exc:
            info["device_probe_error"] = f"{type(dev_exc).__name__}: {dev_exc}"
        if available:
            with cuda.gpus[0]:
                arr = cuda.device_array(1)
                arr.copy_to_host()
            info["tiny_allocation"] = "passed"
            return True, info
        info["message"] = "CUDA unavailable to Numba; GPU APIs must be treated as unverified unless this is fixed."
        return (False if require_cuda else True), info
    except Exception as exc:  # pragma: no cover
        info["error"] = f"CUDA probe failed: {type(exc).__name__}: {exc}"
        return (False if require_cuda else True), info


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check STUMPY imports and optional Dask/CUDA backends.")
    parser.add_argument("--check", choices=["import", "dask", "cuda", "all"], default="all")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero if CUDA is unavailable.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    checks = [args.check] if args.check != "all" else ["import", "dask", "cuda"]
    results = []
    ok = True
    for name in checks:
        if name == "import":
            passed, info = check_import()
        elif name == "dask":
            passed, info = check_dask()
        else:
            passed, info = check_cuda(args.require_cuda)
        info["passed"] = passed
        results.append(info)
        ok = ok and passed
    print(json.dumps({"ok": ok, "results": results}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
