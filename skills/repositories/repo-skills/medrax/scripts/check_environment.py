#!/usr/bin/env python3
"""Read-only MedRAX environment preflight.

Reports package/module availability and an optional Torch CUDA probe without
constructing MedRAX tools, downloading weights, starting a server, or using
credentials. Run it from any current working directory.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
from typing import Any


MODULES = (
    "medrax",
    "medrax.agent",
    "medrax.tools",
    "langgraph",
    "langchain_openai",
    "pydicom",
    "gradio",
    "torch",
    "torchvision",
    "transformers",
    "diffusers",
    "bitsandbytes",
)
DISTRIBUTIONS = ("medrax", "torch", "torchvision", "transformers", "gradio")


def inspect_environment() -> dict[str, Any]:
    result: dict[str, Any] = {"distributions": {}, "modules": {}, "torch": {}}
    for name in DISTRIBUTIONS:
        try:
            result["distributions"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["distributions"][name] = None
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            result["modules"][name] = {"status": "ok", "version": getattr(module, "__version__", None)}
        except Exception as exc:  # optional modules can fail independently
            result["modules"][name] = {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
    try:
        torch = importlib.import_module("torch")
        result["torch"] = {
            "version": torch.__version__,
            "cuda_build": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            result["torch"]["device"] = torch.cuda.get_device_name(0)
            result["torch"]["capability"] = list(torch.cuda.get_device_capability(0))
            result["torch"]["tiny_allocation"] = float(torch.zeros(1, device="cuda").item())
    except Exception as exc:
        result["torch"] = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result = inspect_environment()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("MedRAX environment preflight")
        print("Distributions:")
        for name, version in result["distributions"].items():
            print(f"  {name}: {version or 'missing'}")
        print("Modules:")
        for name, facts in result["modules"].items():
            print(f"  {name}: {facts['status']}" + (f" ({facts.get('error')})" if facts["status"] != "ok" else ""))
        print("Torch:", json.dumps(result["torch"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
