#!/usr/bin/env python3
"""Run a read-only XrayGLM environment and optional CUDA preflight."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys


DISTRIBUTIONS = (
    "torch",
    "torchvision",
    "transformers",
    "SwissArmyTransformer",
    "gradio",
)
IMPORTS = ("torch", "torchvision", "transformers", "sat", "PIL")
OPTIONAL_IMPORTS = ("bitsandbytes", "deepspeed", "cpm_kernels")


def version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check XrayGLM dependencies and optionally allocate one CUDA tensor; no weights are loaded."
    )
    parser.add_argument("--cuda", action="store_true", help="require and smoke-test CUDA")
    args = parser.parse_args()

    print(f"python={sys.version.split()[0]}")
    for name in DISTRIBUTIONS:
        print(f"distribution.{name}={version(name)}")

    failed = False
    for name in IMPORTS:
        try:
            module = importlib.import_module(name)
            print(f"import.{name}=ok ({getattr(module, '__version__', 'loaded')})")
        except Exception as exc:
            print(f"import.{name}=FAIL: {type(exc).__name__}: {exc}")
            failed = True
    for name in OPTIONAL_IMPORTS:
        try:
            importlib.import_module(name)
            print(f"optional.{name}=ok")
        except Exception as exc:
            print(f"optional.{name}=warning: {type(exc).__name__}: {exc}")

    try:
        import torch

        available = bool(torch.cuda.is_available())
        print(f"cuda.available={available}")
        print(f"cuda.count={torch.cuda.device_count()}")
        if available:
            print(f"cuda.device={torch.cuda.get_device_name(0)}")
            print(f"cuda.capability={torch.cuda.get_device_capability(0)}")
            if args.cuda:
                torch.empty((1,), device="cuda")
                print("cuda.allocation=ok")
        elif args.cuda:
            print("cuda.allocation=FAIL: CUDA is unavailable")
            failed = True
    except Exception as exc:
        print(f"cuda=FAIL: {type(exc).__name__}: {exc}")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
