#!/usr/bin/env python3
"""Read-only PointLLM environment and CUDA diagnostic.

This helper checks importability, package versions, and a tiny CUDA allocation.
It does not load model weights, access datasets, call APIs, or start services.
"""
from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import sys


def version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    print(f"python={sys.version.split()[0]}")
    for distribution in ("pointllm", "torch", "torchvision", "transformers", "tokenizers", "timm", "open3d", "deepspeed", "flash-attn", "openai"):
        print(f"{distribution}={version(distribution)}")
    try:
        import torch
    except Exception as exc:
        print(f"torch_import=FAIL {type(exc).__name__}: {exc}")
        return 1
    try:
        import pointllm
        print(f"pointllm_import=OK {pointllm.__file__}")
    except Exception as exc:
        print(f"pointllm_import=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(f"cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"cuda_version={torch.version.cuda}")
        print(f"cuda_device={torch.cuda.get_device_name(0)}")
        print(f"cuda_capability={torch.cuda.get_device_capability(0)}")
        try:
            tensor = torch.zeros((1,), device="cuda")
            print(f"cuda_allocation=OK device={tensor.device}")
        except Exception as exc:
            print(f"cuda_allocation=FAIL {type(exc).__name__}: {exc}")
            return 1
    for module in ("pointllm", "transformers", "tokenizers", "timm", "open3d", "deepspeed", "flash_attn"):
        print(f"module_{module}={bool(importlib.util.find_spec(module))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
