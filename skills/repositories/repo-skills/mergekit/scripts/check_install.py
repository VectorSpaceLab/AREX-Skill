#!/usr/bin/env python3
"""Read-only mergekit installation check.

Run from any directory with the target environment's Python. This helper does
not download models, inspect a checkout, or modify the filesystem.
"""
from __future__ import annotations

import argparse
import importlib.util
from importlib.metadata import PackageNotFoundError, version


def main() -> int:
    parser = argparse.ArgumentParser(description="Check core mergekit imports and optional extras")
    parser.add_argument("--cuda", action="store_true", help="require a CUDA device allocation")
    args = parser.parse_args()
    try:
        import mergekit
        import torch
        import transformers
        from mergekit.merge_methods.registry import REGISTERED_MERGE_METHODS
    except Exception as exc:
        print(f"FAIL import: {type(exc).__name__}: {exc}")
        return 2
    print(f"mergekit={version('mergekit')} module={mergekit.__name__}")
    print(f"torch={torch.__version__} cuda_build={torch.version.cuda}")
    print(f"transformers={transformers.__version__}")
    print("methods=" + ",".join(sorted(REGISTERED_MERGE_METHODS)))
    cuda_ok = bool(torch.cuda.is_available())
    print(f"cuda_available={cuda_ok} devices={torch.cuda.device_count()}")
    if args.cuda:
        if not cuda_ok:
            print("FAIL CUDA unavailable")
            return 3
        try:
            torch.empty((1,), device="cuda")
        except Exception as exc:
            print(f"FAIL CUDA allocation: {type(exc).__name__}: {exc}")
            return 3
        print("cuda_allocation=passed")
    extras = {name: bool(importlib.util.find_spec(name)) for name in ("ray", "cma", "lm_eval", "wandb", "vllm")}
    print("optional=" + ",".join(f"{name}:{present}" for name, present in extras.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
