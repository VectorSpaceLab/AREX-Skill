#!/usr/bin/env python3
"""Read-only nano-vLLM environment probe.

This script checks imports and CUDA visibility without constructing an LLM or
loading model weights. It is safe to run before a generation or benchmark run.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata


def package_version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, object]:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    # Do not expose local site-packages or checkout paths in the generated
    # skill's diagnostic output; importing is enough for this public probe.
    return {"ok": True, "module": module}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check nano-vLLM imports and CUDA visibility without loading weights.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit nonzero if PyTorch cannot see CUDA.")
    args = parser.parse_args(argv)

    modules = ["torch", "triton", "transformers", "flash_attn", "nanovllm"]
    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "distributions": {
            "nano-vllm": package_version("nano-vllm"),
            "torch": package_version("torch"),
            "triton": package_version("triton"),
            "transformers": package_version("transformers"),
            "flash-attn": package_version("flash-attn"),
            "xxhash": package_version("xxhash"),
        },
        "imports": {module: import_status(module) for module in modules},
        "cuda": {"available": False, "device_count": 0, "devices": []},
    }

    torch_info = result["imports"].get("torch", {})  # type: ignore[index]
    if isinstance(torch_info, dict) and torch_info.get("ok"):
        import torch

        devices = []
        if torch.cuda.is_available():
            for idx in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(idx)
                devices.append({
                    "index": idx,
                    "name": props.name,
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                    "capability": f"{props.major}.{props.minor}",
                })
        result["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "torch_cuda": getattr(torch.version, "cuda", None),
            "device_count": torch.cuda.device_count(),
            "devices": devices,
        }

    ok = all(isinstance(v, dict) and v.get("ok") for v in result["imports"].values())  # type: ignore[union-attr]
    cuda_available = bool(result["cuda"].get("available"))  # type: ignore[union-attr]
    if args.require_cuda and not cuda_available:
        ok = False

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("nano-vLLM environment check")
        print(f"Python: {result['python']}")
        print("Distributions:")
        for name, version in result["distributions"].items():  # type: ignore[union-attr]
            print(f"  {name}: {version or 'not installed'}")
        print("Imports:")
        for module, status in result["imports"].items():  # type: ignore[union-attr]
            if status["ok"]:
                print(f"  OK  {module}")
            else:
                print(f"  ERR {module}: {status['error']}")
        cuda = result["cuda"]  # type: ignore[assignment]
        print(f"CUDA available: {cuda['available']} (devices: {cuda['device_count']})")
        for device in cuda.get("devices", []):
            print(f"  cuda:{device['index']} {device['name']} {device['total_memory_gb']}GB sm_{device['capability']}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
