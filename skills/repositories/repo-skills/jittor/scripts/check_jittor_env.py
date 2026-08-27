#!/usr/bin/env python3
"""Inspect a Jittor installation from the active Python environment.

Safe by default:
- imports jittor and jittor_utils
- runs a tiny CPU smoke
- only tries CUDA when --use-cuda is requested and Jittor already reports it
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether the current Python environment can run Jittor.")
    parser.add_argument("--use-cuda", action="store_true", help="Try a CUDA smoke if Jittor already reports CUDA support.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--skip-smoke", action="store_true", help="Only import and report metadata; skip the tiny tensor smoke.")
    parser.add_argument("--verbose-jittor-logs", action="store_true", help="Allow Jittor logs instead of silencing them.")
    return parser.parse_args()


def configure_environment(args: argparse.Namespace) -> None:
    if not args.verbose_jittor_logs:
        os.environ.setdefault("log_silent", "1")
    if not args.use_cuda:
        os.environ.setdefault("nvcc_path", "")


def cpu_smoke(jt: Any) -> Dict[str, Any]:
    x = jt.float32([1, 2, 3])
    y = (x * x).sum()
    data = y.data
    return {
        "status": "passed",
        "sum_squares": float(data.reshape(-1)[0]),
    }


def cuda_smoke(jt: Any) -> Dict[str, Any]:
    if not bool(getattr(jt, "has_cuda", False)):
        return {"status": "skipped", "reason": "Jittor does not report CUDA support"}
    jt.flags.use_cuda = 1
    x = jt.float32([1, 2, 3])
    y = (x * x).sum()
    data = y.data
    return {
        "status": "passed",
        "sum_squares": float(data.reshape(-1)[0]),
    }


def main() -> int:
    args = parse_args()
    configure_environment(args)

    try:
        import jittor as jt
        import jittor_utils
    except Exception as exc:  # pragma: no cover - CLI path
        result = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print(result["error"], file=sys.stderr)
        return 1

    result: Dict[str, Any] = {
        "status": "passed",
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "jittor_version": getattr(jt, "__version__", None),
        "has_cuda": bool(getattr(jt, "has_cuda", False)),
        "cc_type": getattr(getattr(jt, "flags", object()), "cc_type", None),
        "cache_path": getattr(getattr(jt, "flags", object()), "cache_path", None),
        "cpu_smoke": None,
        "cuda_smoke": None,
    }

    try:
        if not args.skip_smoke:
            result["cpu_smoke"] = cpu_smoke(jt)
        if args.use_cuda:
            result["cuda_smoke"] = cuda_smoke(jt)
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print(result["error"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"jittor_version: {result['jittor_version']}")
        print(f"has_cuda: {result['has_cuda']}")
        print(f"cc_type: {result['cc_type']}")
        print(f"sum_squares: {result['cpu_smoke']['sum_squares'] if result['cpu_smoke'] else 'skipped'}")
        if result.get("cuda_smoke"):
            print(f"cuda_sum_squares: {result['cuda_smoke']['sum_squares']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
