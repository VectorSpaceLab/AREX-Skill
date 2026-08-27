#!/usr/bin/env python3
"""Check the denoising-diffusion-pytorch environment.

Purpose:
    Verify package metadata, representative public imports, a tiny CPU tensor
    operation, and optional CUDA visibility without training or downloading.

Example:
    python scripts/check_env.py --device auto
    python scripts/check_env.py --device cpu
"""

from __future__ import annotations

import argparse
import inspect
import sys
from importlib.metadata import PackageNotFoundError, version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the denoising-diffusion-pytorch environment.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--show-signatures", action="store_true", help="Print inspected constructor signatures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import torch
        import denoising_diffusion_pytorch  # noqa: F401
        from denoising_diffusion_pytorch import (
            GaussianDiffusion,
            GaussianDiffusion1D,
            KarrasUnet,
            KarrasUnet1D,
            Unet,
            Unet1D,
            XMWrapper,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to import runtime package or torch: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        dist_version = version("denoising-diffusion-pytorch")
    except PackageNotFoundError:
        dist_version = "unknown"

    print(f"distribution={dist_version}")
    print("module_import=ok")
    print(f"torch={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")

    x = torch.tensor([1.0, 2.0, 3.0])
    print(f"cpu_tensor_sum={x.sum().item():.1f}")

    if args.device == "cuda":
        if not torch.cuda.is_available():
            print("ERROR: --device cuda requested but torch.cuda.is_available() is False", file=sys.stderr)
            return 1
        y = torch.empty((1,), device="cuda")
        print(f"cuda_device={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)} alloc={tuple(y.shape)}")
    elif args.device == "auto" and torch.cuda.is_available():
        y = torch.empty((1,), device="cuda")
        print(f"cuda_device={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)} alloc={tuple(y.shape)}")

    if args.show_signatures:
        for obj in [Unet, GaussianDiffusion, Unet1D, GaussianDiffusion1D, KarrasUnet, KarrasUnet1D, XMWrapper]:
            try:
                sig = inspect.signature(obj)
            except Exception as exc:  # noqa: BLE001
                sig = f"<unavailable: {exc}>"
            print(f"{obj.__name__} {sig}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
