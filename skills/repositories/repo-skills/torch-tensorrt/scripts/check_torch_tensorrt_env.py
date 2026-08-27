#!/usr/bin/env python3
"""Safe Torch-TensorRT environment probe.

This script imports torch/torch_tensorrt, prints public version and feature data,
and optionally performs a tiny CUDA allocation. It does not compile a TensorRT
engine unless --compile-smoke is passed explicitly.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from typing import Any, Dict


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "_asdict"):
        return {k: _jsonable(v) for k, v in value._asdict().items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a Torch-TensorRT Python environment.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--no-cuda-smoke", action="store_true", help="skip tiny torch CUDA allocation")
    parser.add_argument(
        "--compile-smoke",
        action="store_true",
        help="also compile and execute a tiny CUDA model with torch_tensorrt.compile(ir='dynamo')",
    )
    args = parser.parse_args()

    report: Dict[str, Any] = {"ok": False, "imports": {}, "cuda": {}, "features": {}, "compile_smoke": {}}

    try:
        import torch  # type: ignore

        report["imports"]["torch"] = {"ok": True, "version": getattr(torch, "__version__", "unknown")}
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["imports"]["torch"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("torch import failed:", report["imports"]["torch"]["error"], file=sys.stderr)
        return 2

    try:
        import torch_tensorrt  # type: ignore

        report["imports"]["torch_tensorrt"] = {
            "ok": True,
            "version": getattr(torch_tensorrt, "__version__", "unknown"),
        }
        features = getattr(torch_tensorrt, "ENABLED_FEATURES", None)
        report["features"] = _jsonable(features)
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["imports"]["torch_tensorrt"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("torch_tensorrt import failed:", report["imports"]["torch_tensorrt"]["error"], file=sys.stderr)
        return 3

    for mod_name in ("tensorrt", "tensorrt_rtx"):
        try:
            mod = importlib.import_module(mod_name)
            report["imports"][mod_name] = {
                "ok": True,
                "version": getattr(mod, "__version__", "unknown"),
                "package_name": getattr(mod, "_package_name", "unknown"),
            }
        except Exception as exc:
            report["imports"][mod_name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report["cuda"]["available"] = bool(torch.cuda.is_available())
    report["cuda"]["device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    if torch.cuda.is_available():
        try:
            idx = torch.cuda.current_device()
            report["cuda"]["current_device"] = int(idx)
            report["cuda"]["device_name"] = torch.cuda.get_device_name(idx)
        except Exception as exc:
            report["cuda"]["device_query_error"] = f"{type(exc).__name__}: {exc}"

    if torch.cuda.is_available() and not args.no_cuda_smoke:
        try:
            x = torch.ones(1, device="cuda")
            torch.cuda.synchronize()
            report["cuda"]["allocation_smoke"] = {"ok": True, "value": float(x.item())}
        except Exception as exc:
            report["cuda"]["allocation_smoke"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if args.compile_smoke:
        if not torch.cuda.is_available():
            report["compile_smoke"] = {"ok": False, "error": "CUDA is not available"}
        else:
            try:
                import torch_tensorrt  # type: ignore

                class Tiny(torch.nn.Module):
                    def forward(self, x):  # type: ignore[no-untyped-def]
                        return torch.relu(x + 1)

                model = Tiny().eval().cuda()
                inputs = [torch.randn(1, 4, device="cuda")]
                compiled = torch_tensorrt.compile(
                    model,
                    ir="dynamo",
                    inputs=inputs,
                    enabled_precisions={torch.float32},
                )
                torch.testing.assert_close(compiled(*inputs), model(*inputs), rtol=1e-4, atol=1e-4)
                report["compile_smoke"] = {"ok": True}
            except Exception as exc:  # pragma: no cover - depends on GPU/TRT
                report["compile_smoke"] = {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback_tail": traceback.format_exc().splitlines()[-10:],
                }

    report["ok"] = bool(
        report["imports"].get("torch", {}).get("ok")
        and report["imports"].get("torch_tensorrt", {}).get("ok")
        and (not torch.cuda.is_available() or args.no_cuda_smoke or report["cuda"].get("allocation_smoke", {}).get("ok", True))
        and (not args.compile_smoke or report["compile_smoke"].get("ok"))
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Torch:", report["imports"]["torch"])
        print("Torch-TensorRT:", report["imports"]["torch_tensorrt"])
        print("TensorRT:", report["imports"].get("tensorrt"))
        print("TensorRT-RTX:", report["imports"].get("tensorrt_rtx"))
        print("Enabled features:", report["features"])
        print("CUDA:", report["cuda"])
        if args.compile_smoke:
            print("Compile smoke:", report["compile_smoke"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
