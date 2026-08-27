#!/usr/bin/env python3
"""Inspect Torch-TensorRT runtime feature availability.

This script does not compile or execute a model. It imports runtime modules and
reports which runtime helpers appear available in the current package.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any, Dict


def sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Torch-TensorRT runtime APIs without compiling.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()

    report: Dict[str, Any] = {"ok": False, "apis": {}, "features": {}}
    try:
        import torch_tensorrt  # type: ignore

        report["version"] = getattr(torch_tensorrt, "__version__", "unknown")
        features = getattr(torch_tensorrt, "ENABLED_FEATURES", None)
        if hasattr(features, "_asdict"):
            report["features"] = features._asdict()
        else:
            report["features"] = repr(features)
        runtime = importlib.import_module("torch_tensorrt.runtime")
        for name in [
            "enable_cudagraphs",
            "enable_output_allocator",
            "enable_pre_allocated_outputs",
            "weight_streaming",
            "runtime_config",
            "RuntimeSettings",
            "RuntimeCache",
            "optimization_profile",
            "set_dynamic_shapes_kernel_strategy",
        ]:
            if hasattr(runtime, name):
                report["apis"][name] = {"available": True, "signature": sig(getattr(runtime, name))}
            else:
                report["apis"][name] = {"available": False}
        report["ok"] = True
    except Exception as exc:  # pragma: no cover
        report["error"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
