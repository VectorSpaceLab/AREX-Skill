#!/usr/bin/env python3
"""Check a Janus runtime environment without downloading model weights.

This script verifies package metadata, required imports, optional JanusFlow
imports, and optionally a tiny CUDA tensor allocation. It is safe to run from
any working directory.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any, Dict, List


def check_distribution(name: str) -> Dict[str, Any]:
    try:
        return {"name": name, "status": "ok", "version": metadata.version(name)}
    except metadata.PackageNotFoundError as exc:
        return {"name": name, "status": "missing", "error": str(exc)}


def check_import(module: str, show_origin: bool = False) -> Dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        result: Dict[str, Any] = {"module": module, "status": "ok"}
        if show_origin:
            result["origin"] = getattr(imported, "__file__", None)
        return result
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all import failures.
        return {"module": module, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def check_cuda() -> Dict[str, Any]:
    try:
        import torch

        result: Dict[str, Any] = {
            "status": "ok",
            "torch": getattr(torch, "__version__", "unknown"),
            "torch_cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            result["device0"] = torch.cuda.get_device_name(0)
            result["device0_capability"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            result["tiny_tensor"] = "allocated"
        return result
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Janus imports and optional CUDA support.")
    parser.add_argument("--check-janusflow", action="store_true", help="Also import JanusFlow modules and diffusers.")
    parser.add_argument("--check-cuda", action="store_true", help="Run a tiny torch CUDA allocation if CUDA is visible.")
    parser.add_argument("--show-origins", action="store_true", help="Include module __file__ origins in output for debugging.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    args = parser.parse_args(argv)

    modules = [
        "janus",
        "janus.models",
        "janus.utils.io",
        "torch",
        "transformers",
        "timm",
        "sentencepiece",
    ]
    if args.check_janusflow:
        modules.extend(["diffusers", "janus.janusflow.models"])

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": [check_distribution("janus")],
        "imports": [check_import(module, args.show_origins) for module in modules],
    }
    if args.check_cuda:
        report["cuda"] = check_cuda()

    failed = [item for item in report["imports"] if item["status"] != "ok"]
    if report["distributions"][0]["status"] != "ok":
        failed.append(report["distributions"][0])
    if args.check_cuda and report.get("cuda", {}).get("status") == "failed":
        failed.append(report["cuda"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for dist in report["distributions"]:
            print(f"distribution {dist['name']}: {dist['status']} {dist.get('version', dist.get('error', ''))}")
        for item in report["imports"]:
            detail = item.get("origin") or item.get("error") or ""
            print(f"import {item['module']}: {item['status']} {detail}")
        if "cuda" in report:
            print("cuda:", json.dumps(report["cuda"], sort_keys=True))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
