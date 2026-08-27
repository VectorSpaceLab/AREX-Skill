#!/usr/bin/env python3
"""Tiny Torch-TensorRT compile/dryrun probe.

Default mode only checks imports and prints the code path. Pass --compile to
build and execute a small TensorRT engine. Pass --dryrun to request compile
analysis instead of normal execution when supported by the installed version.
"""

from __future__ import annotations

import argparse
import json
import traceback
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Torch-TensorRT Dynamo compile probe.")
    parser.add_argument("--compile", action="store_true", help="actually compile and run a tiny CUDA model")
    parser.add_argument("--dryrun", action="store_true", help="request Torch-TensorRT dryrun analysis")
    parser.add_argument("--dtype", choices=["fp32", "fp16"], default="fp32", help="input and enabled precision")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args()

    report: Dict[str, Any] = {"ok": False, "stage": "start", "compile_requested": args.compile, "dryrun": args.dryrun}
    try:
        import torch  # type: ignore
        import torch_tensorrt  # type: ignore

        report["torch"] = getattr(torch, "__version__", "unknown")
        report["torch_tensorrt"] = getattr(torch_tensorrt, "__version__", "unknown")
        report["features"] = repr(getattr(torch_tensorrt, "ENABLED_FEATURES", "missing"))
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["stage"] = "imports"

        if not args.compile:
            report["ok"] = True
            report["message"] = "Imports passed. Re-run with --compile in a compatible CUDA/TensorRT environment to build an engine."
        else:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is not available")

            class Tiny(torch.nn.Module):
                def forward(self, x):  # type: ignore[no-untyped-def]
                    return torch.relu(x + 1)

            dtype = torch.float16 if args.dtype == "fp16" else torch.float32
            model = Tiny().eval().cuda()
            x = torch.randn(1, 4, device="cuda", dtype=dtype)
            report["stage"] = "compile"
            compiled = torch_tensorrt.compile(
                model,
                ir="dynamo",
                inputs=[torch_tensorrt.Input(x.shape, dtype=dtype)],
                enabled_precisions={dtype},
                min_block_size=1,
                dryrun=args.dryrun,
            )
            if not args.dryrun:
                report["stage"] = "execute"
                with torch.inference_mode():
                    expected = model(x)
                    actual = compiled(x)
                torch.testing.assert_close(actual, expected, rtol=1e-3, atol=1e-3)
            report["ok"] = True
            report["message"] = "Tiny Dynamo compile probe completed."
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback_tail"] = traceback.format_exc().splitlines()[-12:]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
