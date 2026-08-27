#!/usr/bin/env python3
"""Check LeRobot version, core imports, optional modules, and torch device state.

Read-only and network-free by default. Run with ``python check_environment.py``
from any directory after installing the desired LeRobot extras.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import sys
from typing import Any


def probe_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # optional modules may fail without their extra
        return {"module": name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return {"module": name, "status": "ok", "file": getattr(module, "__file__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only LeRobot environment checks.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--probe", action="append", default=[], help="Additional import name; repeatable.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "distribution": None,
        "core_import": None,
        "torch": None,
        "optional_imports": [],
    }
    try:
        result["distribution"] = importlib.metadata.version("lerobot")
    except importlib.metadata.PackageNotFoundError:
        result["distribution"] = "not-installed"

    try:
        import lerobot

        result["core_import"] = {"status": "ok", "version": getattr(lerobot, "__version__", None)}
    except Exception as exc:
        result["core_import"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    try:
        import torch

        torch_info: dict[str, Any] = {
            "version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            torch_info["device_name"] = torch.cuda.get_device_name(0)
            torch_info["device_capability"] = list(torch.cuda.get_device_capability(0))
            probe = torch.ones((2, 2), device="cuda") @ torch.ones((2, 2), device="cuda")
            torch_info["cuda_probe"] = float(probe[0, 0].item())
        result["torch"] = torch_info
    except Exception as exc:
        result["torch"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    names = [
        "lerobot.datasets.lerobot_dataset",
        "lerobot.configs.train",
        "lerobot.configs.eval",
        "lerobot.processor.pipeline",
        "datasets",
        "transformers",
        "av",
        "torchcodec",
    ] + args.probe
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            result["optional_imports"].append(probe_module(name))
            seen.add(name)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"lerobot={result['distribution']} python={result['python']}")
        print(f"core_import={result['core_import']}")
        print(f"torch={result['torch']}")
        for item in result["optional_imports"]:
            print(f"{item['module']}: {item['status']}{(' - ' + item['error']) if 'error' in item else ''}")

    core_ok = result["distribution"] != "not-installed" and result["core_import"].get("status") == "ok"
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
