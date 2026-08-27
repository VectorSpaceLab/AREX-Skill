#!/usr/bin/env python3
"""Read-only FlashVSR environment probe; never installs or downloads."""

from __future__ import annotations

import argparse
import importlib
import sys
import warnings

TARGET_PYTHON = (3, 11)
TARGET_TORCH = "2.6.0+cu124"
TARGET_CUDA = "12.4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report Python, pinned torch/CUDA compatibility, GPU capability, "
            "and block_sparse_attn import status. No private paths, downloads, "
            "or builds."
        )
    )
    return parser.parse_args()


def main() -> int:
    parse_args()
    failures = 0
    py = sys.version_info
    py_ok = (py.major, py.minor) == TARGET_PYTHON
    print(f"python: {py.major}.{py.minor}.{py.micro} ({'target' if py_ok else 'not target 3.11'})")
    if not py_ok:
        failures += 1

    try:
        # Some CUDA/PyTorch compatibility packages emit warnings containing
        # installation paths. Keep the diagnostic prose path-free.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            torch = importlib.import_module("torch")
    except Exception as exc:  # Keep the probe useful in a partially installed env.
        print(f"torch: unavailable ({type(exc).__name__})")
        print("cuda: unavailable (torch import failed)")
        print("gpu: unavailable (torch import failed)")
        print("block_sparse_attn: not checked (torch import failed)")
        return 1

    torch_version = str(getattr(torch, "__version__", "unknown"))
    cuda_version = str(getattr(getattr(torch, "version", None), "cuda", None))
    torch_ok = torch_version == TARGET_TORCH
    cuda_ok = cuda_version == TARGET_CUDA
    print(f"torch: {torch_version} ({'target' if torch_ok else 'not target 2.6.0+cu124'})")
    print(f"torch CUDA runtime: {cuda_version} ({'target' if cuda_ok else 'not target 12.4'})")
    if not torch_ok or not cuda_ok:
        failures += 1

    cuda_available = False
    try:
        cuda_available = bool(torch.cuda.is_available())
    except Exception as exc:
        print(f"cuda: probe error ({type(exc).__name__})")
    print(f"cuda available: {'yes' if cuda_available else 'no'}")
    if not cuda_available:
        failures += 1
    else:
        try:
            index = torch.cuda.current_device()
            name = torch.cuda.get_device_name(index)
            capability = torch.cuda.get_device_capability(index)
            sm = f"SM{capability[0]}{capability[1]}"
            print(f"gpu: {name}")
            print(f"gpu capability: {sm}")
            if capability != (8, 0):
                print("gpu note: target build profile is A100 SM80")
        except Exception as exc:
            print(f"gpu: probe error ({type(exc).__name__})")
            failures += 1

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            extension = importlib.import_module("block_sparse_attn")
        has_entrypoint = hasattr(extension, "block_sparse_attn_func")
        if has_entrypoint:
            print("block_sparse_attn: import OK (block_sparse_attn_func available)")
        else:
            print("block_sparse_attn: imported but entrypoint missing")
            failures += 1
    except Exception as exc:
        print(f"block_sparse_attn: unavailable ({type(exc).__name__})")
        failures += 1

    print(
        "result: target environment and LCSA gate are ready"
        if failures == 0
        else "result: unresolved environment or LCSA gate; no build/download was attempted"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
