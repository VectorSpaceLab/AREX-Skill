#!/usr/bin/env python3
"""Shared safe environment checker for WeNet workflows."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from importlib import metadata
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Check installed WeNet package, public APIs, and optional backend visibility.")
    parser.add_argument("--device", choices=["cpu", "cuda", "npu"], default="cpu", help="Backend to verify at smoke level.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    result: dict[str, Any] = {"ok": True, "device": args.device, "checks": {}}
    try:
        import wenet
        from wenet import load_feature, load_model, load_tokenizer
        result["checks"]["wenet"] = {
            "ok": True,
            "version": metadata.version("wenet"),
            "module": getattr(wenet, "__name__", "wenet"),
            "signatures": {
                "load_model": str(inspect.signature(load_model)),
                "load_feature": str(inspect.signature(load_feature)),
                "load_tokenizer": str(inspect.signature(load_tokenizer)),
            },
        }
    except Exception as exc:
        result["ok"] = False
        result["checks"]["wenet"] = {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    try:
        import torch
        torch_info: dict[str, Any] = {
            "ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
        }
        if args.device == "cuda":
            available = bool(torch.cuda.is_available())
            torch_info.update({"cuda_available": available, "device_count": torch.cuda.device_count() if available else 0})
            if available:
                torch_info["device0"] = torch.cuda.get_device_name(0)
            else:
                result["ok"] = False
        elif args.device == "npu":
            has_npu = importlib.util.find_spec("torch_npu") is not None
            torch_info["torch_npu_importable"] = has_npu
            if not has_npu:
                result["ok"] = False
        else:
            tensor = torch.tensor([1, 2]).sum().item()
            torch_info["cpu_tensor_sum"] = tensor
        result["checks"]["torch"] = torch_info
    except Exception as exc:
        result["ok"] = False
        result["checks"]["torch"] = {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
