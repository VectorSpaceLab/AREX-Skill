#!/usr/bin/env python3
"""Check an RWKV-LM Python runtime for common optional capabilities."""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys


def check_import(name: str) -> bool:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "unknown")
        print(f"PASS import {name} version={version}")
        return True
    except Exception as exc:
        print(f"FAIL import {name}: {exc}")
        return False


def check_cuda() -> bool:
    try:
        import torch

        print(f"torch={torch.__version__} cuda_runtime={torch.version.cuda}")
        print(f"CUDA_HOME={os.environ.get('CUDA_HOME') or '<unset>'}")
        print(f"nvcc={shutil.which('nvcc') or '<missing>'}")
        available = torch.cuda.is_available()
        print(f"torch.cuda.is_available={available} device_count={torch.cuda.device_count()}")
        if available:
            print(f"device0={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
            print("PASS tiny CUDA allocation")
            return True
        print("WARN CUDA not available to torch")
        return False
    except Exception as exc:
        print(f"FAIL CUDA check: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cuda", action="store_true", help="Run a torch CUDA visibility/allocation check")
    parser.add_argument("--imports", nargs="*", default=["torch", "numpy", "pytorch_lightning", "deepspeed", "rwkv"], help="Modules to import")
    args = parser.parse_args()
    ok = True
    for name in args.imports:
        ok = check_import(name) and ok
    if args.check_cuda:
        ok = check_cuda() and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
