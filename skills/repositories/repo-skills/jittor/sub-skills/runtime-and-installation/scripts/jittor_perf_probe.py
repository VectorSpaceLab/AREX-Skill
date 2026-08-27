#!/usr/bin/env python3
"""Bounded Jittor timing probe.

Safe defaults:
- CPU-first
- tiny matmul workload
- no network
- no dataset or pretrained downloads
- CUDA is only used when --use-cuda is requested and Jittor already reports it
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny CPU-first Jittor timing probe."
    )
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for the matmul probe.")
    parser.add_argument("--size", type=int, default=128, help="Square feature size for the matmul probe.")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations.")
    parser.add_argument("--rerun", type=int, default=5, help="Number of timed iterations.")
    parser.add_argument("--use-cuda", action="store_true", help="Try CUDA if Jittor already reports CUDA support.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--verbose-jittor-logs", action="store_true", help="Allow Jittor logs instead of silencing them.")
    return parser.parse_args()


def configure_environment(args: argparse.Namespace) -> None:
    if not args.verbose_jittor_logs:
        os.environ.setdefault("log_silent", "1")
    if not args.use_cuda:
        os.environ.setdefault("nvcc_path", "")


def timed_matmul(jt: Any, batch_size: int, size: int, warmup: int, rerun: int) -> Dict[str, Any]:
    if batch_size < 1 or size < 1 or warmup < 0 or rerun < 1:
        raise ValueError("batch-size, size, warmup, and rerun must be positive with rerun >= 1")

    x = jt.random((batch_size, size))
    w = jt.random((size, size))

    for _ in range(warmup):
        jt.matmul(x, w).sync()
    jt.sync_all(True)

    start = time.perf_counter()
    last = None
    for _ in range(rerun):
        last = jt.matmul(x, w)
        last.sync()
    jt.sync_all(True)
    elapsed = time.perf_counter() - start

    assert last is not None
    return {
        "elapsed_seconds": elapsed,
        "average_seconds": elapsed / rerun,
        "batch_size": batch_size,
        "size": size,
        "rerun": rerun,
        "warmup": warmup,
        "output_shape": list(last.shape),
        "throughput_items_per_second": (batch_size * rerun) / elapsed if elapsed > 0 else None,
    }


def main() -> int:
    args = parse_args()
    configure_environment(args)

    try:
        import jittor as jt
    except Exception as exc:  # pragma: no cover - CLI path
        print(f"failed to import jittor: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    result: Dict[str, Any] = {
        "jittor_version": getattr(jt, "__version__", None),
        "has_cuda": bool(getattr(jt, "has_cuda", False)),
        "use_cuda_requested": bool(args.use_cuda),
        "backend": "cuda" if args.use_cuda else "cpu",
    }

    try:
        if args.use_cuda:
            if not bool(getattr(jt, "has_cuda", False)):
                raise SystemExit("CUDA was requested, but Jittor does not report CUDA support on this host.")
            jt.flags.use_cuda = 1
        else:
            jt.flags.use_cuda = 0

        result.update(timed_matmul(jt, args.batch_size, args.size, args.warmup, args.rerun))
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print("Jittor timing probe failed")
            print(result["error"])
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"Jittor timing probe passed on {result['backend']}")
        print(f"version: {result['jittor_version']}")
        print(f"has_cuda: {result['has_cuda']}")
        print(f"output_shape: {result['output_shape']}")
        print(f"average_seconds: {result['average_seconds']:.6f}")
        print(f"throughput_items_per_second: {result['throughput_items_per_second']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
