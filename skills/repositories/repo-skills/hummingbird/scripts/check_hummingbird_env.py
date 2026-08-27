#!/usr/bin/env python3
"""Check the active Python environment for Hummingbird repo-skill workflows.

This helper performs read-only imports and backend probes. It does not install
packages, download data, start Spark, run TVM compilation, or require CUDA.

Examples:
  python scripts/check_hummingbird_env.py
  python scripts/check_hummingbird_env.py --json
  python scripts/check_hummingbird_env.py --cuda-smoke
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
import warnings
from typing import Any, Dict


OPTIONAL_MODULES = [
    "torch",
    "sklearn",
    "onnx",
    "onnxruntime",
    "onnxmltools",
    "skl2onnx",
    "lightgbm",
    "xgboost",
    "prophet",
    "pyspark",
    "pandas",
    "tvm",
]


def module_status(name: str) -> Dict[str, Any]:
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            module = importlib.import_module(name)
    except Exception as exc:  # Import errors from compiled optional deps are useful status.
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(name)
        except Exception:
            version = None
    status = {"available": True, "version": version}
    if caught:
        status["warnings"] = [str(w.message) for w in caught]
    return status


def build_report(cuda_smoke: bool = False) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "hummingbird": {"available": False},
        "backend_aliases": [],
        "modules": {},
        "torch_cuda": None,
    }

    try:
        import hummingbird
        import hummingbird.ml as hb

        try:
            dist_version = metadata.version("hummingbird-ml")
        except Exception:
            dist_version = getattr(hummingbird, "__version__", None)
        report["hummingbird"] = {
            "available": True,
            "version": getattr(hummingbird, "__version__", None),
            "distribution_version": dist_version,
            "convert": str(hb.convert),
            "convert_batch": str(hb.convert_batch),
        }
        report["backend_aliases"] = sorted(k for k, v in hb.backends.items() if v is not None)
    except Exception as exc:
        report["hummingbird"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    for name in OPTIONAL_MODULES:
        report["modules"][name] = module_status(name)

    torch_info = report["modules"].get("torch", {})
    if torch_info.get("available"):
        try:
            import torch

            info: Dict[str, Any] = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
            }
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                info["device_name_0"] = torch.cuda.get_device_name(0)
                info["device_capability_0"] = list(torch.cuda.get_device_capability(0))
                if cuda_smoke:
                    torch.empty((1,), device="cuda")
                    info["cuda_smoke"] = "passed"
            elif cuda_smoke:
                info["cuda_smoke"] = "blocked: torch.cuda.is_available() is false"
            report["torch_cuda"] = info
        except Exception as exc:
            report["torch_cuda"] = {"error": f"{type(exc).__name__}: {exc}"}

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Hummingbird environment probe.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="If CUDA is available, allocate a tiny CUDA tensor. This still does not run model conversion.",
    )
    args = parser.parse_args()

    report = build_report(cuda_smoke=args.cuda_smoke)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        hb = report["hummingbird"]
        print(f"Python: {report['python']}")
        if hb.get("available"):
            print(f"Hummingbird: {hb.get('version')} (dist {hb.get('distribution_version')})")
            print("Backend aliases: " + (", ".join(report["backend_aliases"]) or "none"))
        else:
            print("Hummingbird: unavailable - " + hb.get("error", "unknown error"))
        print("\nModules:")
        for name, info in report["modules"].items():
            if info.get("available"):
                print(f"  {name}: yes {info.get('version') or ''}".rstrip())
            else:
                print(f"  {name}: no ({info.get('error', 'not importable')})")
        print("\nTorch CUDA:")
        print(json.dumps(report["torch_cuda"], indent=2, sort_keys=True))

    return 0 if report["hummingbird"].get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
