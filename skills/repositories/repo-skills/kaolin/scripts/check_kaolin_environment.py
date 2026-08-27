#!/usr/bin/env python3
"""Safe Kaolin environment diagnostic.

Example:
  python check_kaolin_environment.py --json
  python check_kaolin_environment.py --json --cuda-smoke
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Any, Dict


def import_status(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {
            "ok": True,
            "version": getattr(mod, "__version__", None),
            "file": getattr(mod, "__file__", None),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cuda_smoke() -> Dict[str, Any]:
    import torch

    if not torch.cuda.is_available():
        return {"ok": False, "reason": "torch.cuda.is_available() is false"}
    x = torch.tensor([1.0], device="cuda") + 1.0
    return {"ok": True, "value": float(x.item()), "device": torch.cuda.get_device_name(0)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Kaolin import, backend, and optional dependencies safely.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--cuda-smoke", action="store_true", help="Run a tiny torch CUDA tensor allocation.")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "imports": {
            name: import_status(name)
            for name in [
                "torch",
                "kaolin",
                "kaolin._C",
                "kaolin.io",
                "kaolin.ops",
                "kaolin.render",
                "kaolin.physics",
                "kaolin.visualize",
                "pxr",
                "nvdiffrast",
                "warp",
                "flask",
                "tornado",
                "ipycanvas",
                "ipyevents",
                "pygltflib",
                "plyfile",
            ]
        },
    }

    try:
        import torch
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
        }
    except Exception as exc:
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        import kaolin
        kaolin_file = getattr(kaolin, "__file__", "") or ""
        report["kaolin"] = {
            "version": getattr(kaolin, "__version__", None),
            "file": kaolin_file,
            "possible_source_shadowing": "/kaolin/kaolin/" in kaolin_file.replace("\\", "/"),
        }
    except Exception as exc:
        report["kaolin"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.cuda_smoke:
        try:
            report["cuda_smoke"] = cuda_smoke()
        except Exception as exc:
            report["cuda_smoke"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    ok = report["imports"]["kaolin"].get("ok", False)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, info in report["imports"].items():
            marker = "OK" if info.get("ok") else "MISSING"
            print(f"{marker:7s} {name} {info.get('version') or info.get('error') or ''}")
        if report.get("kaolin", {}).get("possible_source_shadowing"):
            print("WARNING: Kaolin appears to be imported from a source checkout; _C may be missing unless built.")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
