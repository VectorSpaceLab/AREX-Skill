#!/usr/bin/env python3
"""Tiny, safe Jittor custom-op smoke check.

Default behavior compiles a tiny CPU custom op. Use --skip-compile for an
import/API-only check, and --try-cuda only when CUDA verification is
intentionally desired and available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict


HEADER = """
#pragma once
#include "op.h"

namespace jittor {

struct CustomOp : Op {
    Var* output;
    CustomOp(NanoVector shape, NanoString dtype=ns_float32);

    const char* name() const override { return "custom"; }
    DECLARE_jit_run;
};

} // jittor
"""

SRC = """
#include "var.h"
#include "custom_op.h"

namespace jittor {
#ifndef JIT
CustomOp::CustomOp(NanoVector shape, NanoString dtype) {
    flags.set(NodeFlags::_cuda, 1);
    flags.set(NodeFlags::_cpu, 1);
    output = create_output(shape, dtype);
}

void CustomOp::jit_prepare(JK& jk) {
    add_jit_define(jk, "T", output->dtype());
}

#else // JIT
#ifdef JIT_cpu
void CustomOp::jit_run() {
    index_t num = output->num;
    auto* __restrict__ x = output->ptr<T>();
    for (index_t i=0; i<num; i++)
        x[i] = (T)i;
}
#else
__global__ void kernel(index_t n, T *x) {
    int index = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;
    for (int i = index; i < n; i += stride)
        x[i] = (T)-i;
}

void CustomOp::jit_run() {
    index_t num = output->num;
    auto* __restrict__ x = output->ptr<T>();
    int blockSize = 256;
    int numBlocks = (num + blockSize - 1) / blockSize;
    kernel<<<numBlocks, blockSize>>>(num, x);
}
#endif // JIT_cpu
#endif // JIT

} // jittor
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded Jittor custom-op smoke check."
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Import Jittor and check public extension callables without compiling a custom op.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=8,
        help="Number of elements for the tiny CPU/CUDA smoke arrays (default: 8).",
    )
    parser.add_argument(
        "--try-cuda",
        action="store_true",
        help="Optionally try a CUDA custom-op smoke; skips cleanly if CUDA is unavailable.",
    )
    parser.add_argument(
        "--verbose-jittor-logs",
        action="store_true",
        help="Allow Jittor import/compile logs. Default suppresses Jittor logs when supported.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON result instead of a concise text summary.",
    )
    return parser.parse_args()


def configure_environment(args: argparse.Namespace) -> None:
    if not args.verbose_jittor_logs:
        os.environ.setdefault("log_silent", "1")
    if not args.try_cuda:
        os.environ.setdefault("nvcc_path", "")


def import_runtime() -> tuple[Any, Any]:
    import numpy as np  # type: ignore
    import jittor as jt  # type: ignore

    return jt, np


def public_api_status(jt: Any) -> Dict[str, Any]:
    names = ["compile_custom_op", "compile_custom_ops", "code"]
    return {name: callable(getattr(jt, name, None)) for name in names}


def run_cpu_custom_op_smoke(jt: Any, np: Any, size: int) -> Dict[str, Any]:
    if size <= 0:
        raise ValueError("--size must be positive")
    old_use_cuda = getattr(jt.flags, "use_cuda", 0)
    try:
        jt.flags.use_cuda = 0
        my_op = jt.compile_custom_op(HEADER, SRC, "custom", warp=False)
        got = my_op([size], "float").fetch_sync()
        expected = np.arange(size, dtype=np.float32)
        if not np.allclose(got.flatten(), expected):
            raise AssertionError(f"CPU custom-op mismatch: got {got!r}, expected {expected!r}")
        return {"status": "passed", "backend": "cpu", "values": got.flatten().tolist()}
    finally:
        try:
            jt.flags.use_cuda = old_use_cuda
        except Exception:
            pass


def run_cuda_custom_op_smoke(jt: Any, np: Any, size: int) -> Dict[str, Any]:
    has_cuda = bool(getattr(jt, "has_cuda", False) or getattr(jt.compiler, "has_cuda", False))
    if not has_cuda:
        return {"status": "skipped", "backend": "cuda", "reason": "CUDA not reported by Jittor"}

    old_use_cuda = getattr(jt.flags, "use_cuda", 0)
    try:
        jt.flags.use_cuda = 1
        my_op = jt.compile_custom_op(HEADER, SRC, "custom", warp=False)
        got = my_op([size], "float").fetch_sync()
        expected = -np.arange(size, dtype=np.float32)
        if not np.allclose(got.flatten(), expected):
            raise AssertionError(f"CUDA custom-op mismatch: got {got!r}, expected {expected!r}")
        return {"status": "passed", "backend": "cuda", "values": got.flatten().tolist()}
    finally:
        try:
            jt.flags.use_cuda = old_use_cuda
        except Exception:
            pass


def render(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, sort_keys=True))
        return

    print(f"Jittor custom-op smoke: {result['status']}")
    print("public_api:", ", ".join(f"{k}={v}" for k, v in sorted(result["public_api"].items())))
    for check in result.get("checks", []):
        detail = check.get("reason") or check.get("values") or ""
        print(f"{check['backend']}: {check['status']} {detail}")


def main() -> int:
    args = parse_args()
    configure_environment(args)

    result: Dict[str, Any] = {"status": "passed", "public_api": {}, "checks": []}
    try:
        jt, np = import_runtime()
        result["public_api"] = public_api_status(jt)
        missing = [name for name, ok in result["public_api"].items() if not ok]
        if missing:
            raise RuntimeError("Missing public API callables: " + ", ".join(missing))
        if not args.skip_compile:
            result["checks"].append(run_cpu_custom_op_smoke(jt, np, args.size))
        if args.try_cuda:
            result["checks"].append(run_cuda_custom_op_smoke(jt, np, args.size))
    except Exception as exc:  # pragma: no cover - CLI diagnostics path
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        render(result, args.json)
        return 1

    render(result, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
