#!/usr/bin/env python3
"""Run a safe import/backend preflight for SiamTrackers workflows.

The probe is read-only: it imports optional modules, performs no source checkout
mutation, downloads nothing, opens no GUI, and allocates only a one-element
CUDA tensor when CUDA is requested/available.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any

MODULES = {
    "torch": "core model/backend",
    "numpy": "core array API",
    "cv2": "frame decode/preprocessing",
    "yaml": "configuration parsing",
    "yacs": "NanoTrack config object",
    "Cython": "region extension rebuild",
    "PIL": "dataset/evaluation images",
    "scipy": "evaluation utilities",
    "shapely": "polygon metrics",
    "tqdm": "progress reporting",
    "colorama": "legacy console output",
    "tensorboard": "training logging",
    "thop": "optional profiling",
    "onnx": "optional graph inspection",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only SiamTrackers dependency and CUDA preflight."
    )
    parser.add_argument("--require-cuda", action="store_true", help="exit nonzero unless a one-element CUDA allocation succeeds")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {
        "python": sys.version,
        "modules": {},
        "cuda": {"available": False, "device_count": 0, "smoke": "not-run"},
        "warnings": [],
        "errors": [],
    }
    for name, purpose in MODULES.items():
        try:
            module = importlib.import_module(name)
            report["modules"][name] = {
                "status": "ok",
                "purpose": purpose,
                "version": getattr(module, "__version__", None),
            }
        except Exception as exc:  # optional modules and stale binary imports are actionable output
            report["modules"][name] = {
                "status": "missing-or-broken",
                "purpose": purpose,
                "error": f"{type(exc).__name__}: {exc}",
            }

    torch_info = report["modules"].get("torch", {})
    if torch_info.get("status") == "ok":
        import torch

        available = bool(torch.cuda.is_available())
        report["cuda"].update(
            {
                "available": available,
                "device_count": int(torch.cuda.device_count()) if available else 0,
                "torch_version": torch.__version__,
                "torch_cuda": torch.version.cuda,
            }
        )
        if available:
            try:
                report["cuda"]["device_name"] = torch.cuda.get_device_name(0)
                report["cuda"]["device_capability"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                report["cuda"]["smoke"] = "passed"
            except Exception as exc:
                report["cuda"]["smoke"] = "failed"
                report["cuda"]["error"] = f"{type(exc).__name__}: {exc}"
                if args.require_cuda:
                    report["errors"].append(
                        "CUDA is visible but the device smoke failed: "
                        + report["cuda"]["error"]
                    )
                else:
                    report["warnings"].append(
                        "CUDA is visible but the default device smoke failed; "
                        "select a free device before requiring CUDA"
                    )
        elif args.require_cuda:
            report["errors"].append("CUDA is unavailable")
    elif args.require_cuda:
        report["errors"].append("PyTorch is unavailable; cannot probe CUDA")

    missing_core = [
        name for name in ("torch", "numpy", "cv2", "yaml", "yacs")
        if report["modules"].get(name, {}).get("status") != "ok"
    ]
    if missing_core:
        report["errors"].append("missing or broken core modules: " + ", ".join(missing_core))
    for name, item in report["modules"].items():
        if item.get("status") != "ok" and name not in {"onnx", "thop"}:
            report["warnings"].append(f"{name}: {item.get('error', 'unavailable')}")

    report["status"] = "error" if report["errors"] else "ok"
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for name, item in report["modules"].items():
            print(f"{name}: {item['status']}")
        print("cuda:", report["cuda"].get("smoke"), report["cuda"].get("device_name", ""))
        for message in report["warnings"]:
            print("warning:", message)
        for message in report["errors"]:
            print("error:", message)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
