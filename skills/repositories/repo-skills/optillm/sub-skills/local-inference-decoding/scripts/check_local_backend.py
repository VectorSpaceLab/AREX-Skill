#!/usr/bin/env python3
"""Probe OptiLLM local inference backend imports without downloading models."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform


def try_import(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"imported": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:
        return {"imported": False, "error": f"{type(exc).__name__}: {exc}"}


def probe() -> dict:
    result = {
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "env_present": {
            name: bool(os.environ.get(name))
            for name in ["OPTILLM_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_HUB_TOKEN", "CUDA_VISIBLE_DEVICES"]
        },
        "imports": {},
    }
    for name in ["optillm", "torch", "transformers", "peft", "bitsandbytes", "mlx", "mlx_lm"]:
        result["imports"][name] = try_import(name)
    torch_info = result["imports"].get("torch", {})
    if torch_info.get("imported"):
        import torch
        result["torch_backend"] = {
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "mps_available": bool(
                getattr(getattr(torch, "backends", None), "mps", None)
                and torch.backends.mps.is_available()
            ),
        }
        if torch.cuda.is_available():
            result["torch_backend"]["device_0_name"] = torch.cuda.get_device_name(0)
            result["torch_backend"]["device_0_capability"] = torch.cuda.get_device_capability(0)
            try:
                tensor = torch.empty((1,), device="cuda")
                result["torch_backend"]["tiny_cuda_allocation"] = str(tensor.device)
            except Exception as exc:
                result["torch_backend"]["tiny_cuda_allocation_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe local inference backend imports without model downloads")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    result = probe()
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Platform: {result['platform']}")
        print("Environment variables present:")
        for key, value in result["env_present"].items():
            print(f"  {key}: {value}")
        print("Imports:")
        for key, value in result["imports"].items():
            status = "ok" if value.get("imported") else "missing"
            detail = value.get("version") or value.get("error")
            print(f"  {key}: {status} {detail}")
        if "torch_backend" in result:
            print("Torch backend:")
            for key, value in result["torch_backend"].items():
                print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
