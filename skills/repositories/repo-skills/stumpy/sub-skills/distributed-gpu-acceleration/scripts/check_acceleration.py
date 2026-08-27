#!/usr/bin/env python3
"""Check STUMPY acceleration backends safely.

The Dask check creates and closes a tiny LocalCluster and runs one synthetic
`stumpy.stumped` smoke. The CUDA check reports Numba CUDA availability and
visible device count without running native GPU tests. CUDA absence is non-fatal
unless --require-cuda is supplied.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from importlib import metadata


def _package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def check_dask(args: argparse.Namespace) -> bool:
    """Create/close a small Dask LocalCluster and run a tiny STUMPY smoke."""

    print("[dask] checking imports")
    try:
        import numpy as np
        import stumpy
        from dask.distributed import Client, LocalCluster
    except Exception as exc:  # ImportError plus occasional optional import failures
        print(f"[dask] FAILED import: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return False

    print(f"[dask] stumpy distribution version: {_package_version('stumpy')}")
    print(f"[dask] dask version: {_package_version('dask')}")
    print(f"[dask] distributed version: {_package_version('distributed')}")

    cluster = None
    try:
        cluster = LocalCluster(
            n_workers=args.workers,
            threads_per_worker=args.threads_per_worker,
            processes=args.processes,
            dashboard_address=None,
            worker_dashboard_address=None,
            scheduler_port=0,
        )
        with Client(cluster, set_as_default=False) as client:
            client.wait_for_workers(args.workers, timeout=args.timeout)
            T = np.array(
                [0.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 2.0], dtype=np.float64
            )
            m = 3
            mp = stumpy.stumped(client, T, m=m)
            if hasattr(mp, "P_"):
                profile = np.asarray(mp.P_, dtype=np.float64)
                indices = np.asarray(mp.I_)
            else:  # defensive fallback for array-like results
                profile = np.asarray(mp[:, 0], dtype=np.float64)
                indices = np.asarray(mp[:, 1])
            expected_len = T.shape[0] - m + 1
            if profile.shape[0] != expected_len:
                raise RuntimeError(
                    f"unexpected profile length {profile.shape[0]} != {expected_len}"
                )
            if indices.shape[0] != expected_len:
                raise RuntimeError(
                    f"unexpected index length {indices.shape[0]} != {expected_len}"
                )
            if not np.isfinite(profile).any():
                raise RuntimeError("profile contains no finite values")
            print(
                "[dask] OK LocalCluster "
                f"workers={args.workers} threads_per_worker={args.threads_per_worker} "
                f"processes={args.processes} profile_shape={profile.shape}"
            )
        return True
    except Exception as exc:
        print(f"[dask] FAILED smoke: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return False
    finally:
        if cluster is not None:
            try:
                cluster.close(timeout=args.timeout)
                print("[dask] closed LocalCluster")
            except Exception as exc:  # pragma: no cover - cleanup best effort
                print(
                    f"[dask] WARNING cluster close failed: {exc.__class__.__name__}: {exc}",
                    file=sys.stderr,
                )


def check_cuda(args: argparse.Namespace) -> bool:
    """Report Numba CUDA availability without running STUMPY GPU kernels."""

    print("[cuda] checking numba.cuda")
    try:
        import numba
        from numba import cuda
    except Exception as exc:
        print(f"[cuda] numba import failed: {exc.__class__.__name__}: {exc}")
        return not args.require_cuda

    print(f"[cuda] numba version: {getattr(numba, '__version__', 'unknown')}")
    try:
        available = bool(cuda.is_available())
    except Exception as exc:
        print(f"[cuda] cuda.is_available() raised: {exc.__class__.__name__}: {exc}")
        available = False

    device_count = None
    device_ids: list[int] = []
    try:
        devices = list(cuda.list_devices())
        device_count = len(devices)
        for idx, device in enumerate(devices):
            device_ids.append(int(getattr(device, "id", idx)))
    except Exception as exc:
        print(f"[cuda] cuda.list_devices() raised: {exc.__class__.__name__}: {exc}")

    print(f"[cuda] numba.cuda.is_available: {available}")
    print(f"[cuda] visible device count: {device_count if device_count is not None else 'unknown'}")
    if device_ids:
        print(f"[cuda] visible device ids: {device_ids}")
    print("[cuda] native GPU STUMPY tests were not run by this script")

    if args.require_cuda and not available:
        print("[cuda] FAILED: --require-cuda was set but Numba CUDA is unavailable", file=sys.stderr)
        return False
    if args.require_cuda and device_count == 0:
        print("[cuda] FAILED: --require-cuda was set but no visible devices were listed", file=sys.stderr)
        return False
    if available:
        print("[cuda] OK CUDA appears available to Numba; run an explicit tiny GPU job only if required")
    else:
        print("[cuda] OK CUDA unavailable but optional")
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check STUMPY Dask and optional CUDA acceleration backends safely."
    )
    parser.add_argument(
        "--check",
        choices=("dask", "cuda", "all"),
        default="all",
        help="Backend check to run. Default: all.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Return a non-zero exit code when Numba CUDA is unavailable.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of LocalCluster workers for the Dask smoke. Default: 2.",
    )
    parser.add_argument(
        "--threads-per-worker",
        type=int,
        default=1,
        help="Dask LocalCluster threads per worker. Default: 1.",
    )
    parser.add_argument(
        "--processes",
        action="store_true",
        help="Use process workers for Dask. Default uses thread workers for safer smoke checks.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Dask wait/close timeout in seconds. Default: 60.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print tracebacks for failed checks.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ok = True
    if args.check in {"dask", "all"}:
        ok = check_dask(args) and ok
    if args.check in {"cuda", "all"}:
        ok = check_cuda(args) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
