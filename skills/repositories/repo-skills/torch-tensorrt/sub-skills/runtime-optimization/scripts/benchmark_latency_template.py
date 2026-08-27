#!/usr/bin/env python3
"""Benchmark template for eager vs compiled Torch-TensorRT modules.

This is a template, not a model loader. Replace build_model() with the user's
model code, then run in a CUDA/TensorRT environment.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from typing import Callable, Iterable, List


def build_model():  # pragma: no cover - user template
    import torch

    class Tiny(torch.nn.Module):
        def forward(self, x):
            return torch.relu(x + 1)

    return Tiny().eval().cuda()


def cuda_time_ms(fn: Callable[[], object], iters: int) -> List[float]:
    import torch

    times: List[float] = []
    for _ in range(iters):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        fn()
        end.record()
        torch.cuda.synchronize()
        times.append(float(start.elapsed_time(end)))
    return times


def summarize(values: Iterable[float]) -> dict:
    vals = list(values)
    vals_sorted = sorted(vals)
    p95 = vals_sorted[min(len(vals_sorted) - 1, int(0.95 * (len(vals_sorted) - 1)))]
    return {"mean_ms": statistics.mean(vals), "median_ms": statistics.median(vals), "p95_ms": p95, "count": len(vals)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Template benchmark for Torch-TensorRT latency.")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--features", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iters", type=int, default=50)
    parser.add_argument("--compile", action="store_true", help="compile the template model with Torch-TensorRT")
    parser.add_argument("--fp16", action="store_true", help="use float16 inputs and enabled precision")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    import torch

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available; benchmark must run on target GPU runtime")

    dtype = torch.float16 if args.fp16 else torch.float32
    model = build_model()
    x = torch.randn(args.batch, args.features, device="cuda", dtype=dtype)

    with torch.inference_mode():
        for _ in range(args.warmup):
            model(x)
        torch.cuda.synchronize()
        eager = cuda_time_ms(lambda: model(x), args.iters)

        result = {"eager": summarize(eager)}
        if args.compile:
            import torch_tensorrt

            compiled = torch_tensorrt.compile(
                model,
                ir="dynamo",
                inputs=[torch_tensorrt.Input(x.shape, dtype=dtype)],
                enabled_precisions={dtype},
                min_block_size=1,
            )
            compiled(x)  # cold build/first execution not timed
            torch.testing.assert_close(compiled(x), model(x), rtol=1e-3, atol=1e-3)
            for _ in range(args.warmup):
                compiled(x)
            torch.cuda.synchronize()
            trt = cuda_time_ms(lambda: compiled(x), args.iters)
            result["compiled"] = summarize(trt)
            result["speedup"] = result["eager"]["mean_ms"] / result["compiled"]["mean_ms"]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
