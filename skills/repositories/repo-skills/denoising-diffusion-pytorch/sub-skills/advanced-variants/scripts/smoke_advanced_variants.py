#!/usr/bin/env python3
"""Smoke-test advanced denoising-diffusion-pytorch variant APIs."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect advanced APIs and run tiny Karras forward checks.")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--include-3d", action="store_true")
    parser.add_argument("--skip-forward", action="store_true")
    return parser.parse_args()


def signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # noqa: BLE001
        return f"<unavailable: {exc}>"


def main() -> int:
    args = parse_args()
    try:
        import torch
        from denoising_diffusion_pytorch import (
            ContinuousTimeGaussianDiffusion,
            ElucidatedDiffusion,
            InvSqrtDecayLRSched,
            KarrasUnet,
            KarrasUnet1D,
            KarrasUnet3D,
            LearnedGaussianDiffusion,
            VParamContinuousTimeGaussianDiffusion,
            WeightedObjectiveGaussianDiffusion,
        )
        from denoising_diffusion_pytorch.attend import Attend
        from denoising_diffusion_pytorch.simple_diffusion import GaussianDiffusion as SimpleGaussianDiffusion
        from denoising_diffusion_pytorch.simple_diffusion import UViT
    except ModuleNotFoundError as exc:
        print("ERROR: install with `python -m pip install denoising-diffusion-pytorch`. Missing: " + str(exc), file=sys.stderr)
        return 1

    if args.device == "cuda":
        if not torch.cuda.is_available():
            print("ERROR: --device cuda requested but CUDA is unavailable", file=sys.stderr)
            return 1
        device = torch.device("cuda")
    elif args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device("cpu")

    if device.type == "cpu":
        torch.set_num_threads(1)
    torch.manual_seed(123)

    signatures = {name: signature_text(obj) for name, obj in {
        "KarrasUnet": KarrasUnet,
        "KarrasUnet1D": KarrasUnet1D,
        "KarrasUnet3D": KarrasUnet3D,
        "InvSqrtDecayLRSched": InvSqrtDecayLRSched,
        "ContinuousTimeGaussianDiffusion": ContinuousTimeGaussianDiffusion,
        "VParamContinuousTimeGaussianDiffusion": VParamContinuousTimeGaussianDiffusion,
        "ElucidatedDiffusion": ElucidatedDiffusion,
        "LearnedGaussianDiffusion": LearnedGaussianDiffusion,
        "WeightedObjectiveGaussianDiffusion": WeightedObjectiveGaussianDiffusion,
        "simple_diffusion.UViT": UViT,
        "simple_diffusion.GaussianDiffusion": SimpleGaussianDiffusion,
        "Attend": Attend,
    }.items()}

    forward: dict[str, Any] = {}
    if not args.skip_forward:
        model2d = KarrasUnet(image_size=16, dim=4, dim_max=8, channels=2,
                             num_downsamples=1, num_blocks_per_stage=1,
                             attn_res=(), attn_dim_head=4, attn_flash=False).to(device).eval()
        x2d = torch.randn(1, 2, 16, 16, device=device)
        with torch.no_grad():
            y2d = model2d(x2d, time=torch.ones(1, device=device))
        assert tuple(y2d.shape) == tuple(x2d.shape)
        forward["KarrasUnet"] = list(y2d.shape)

        model1d = KarrasUnet1D(seq_len=16, dim=4, dim_max=8, channels=2,
                               num_downsamples=1, num_blocks_per_stage=1,
                               attn_res=(), attn_dim_head=4, attn_flash=False).to(device).eval()
        x1d = torch.randn(1, 2, 16, device=device)
        with torch.no_grad():
            y1d = model1d(x1d, time=torch.ones(1, device=device))
        assert tuple(y1d.shape) == tuple(x1d.shape)
        forward["KarrasUnet1D"] = list(y1d.shape)

        if args.include_3d:
            model3d = KarrasUnet3D(frames=2, image_size=8, dim=2, dim_max=4, channels=1,
                                   num_downsamples=1, num_blocks_per_stage=1,
                                   downsample_types=("all",), attn_res=(), attn_dim_head=2,
                                   attn_flash=False).to(device).eval()
            x3d = torch.randn(1, 1, 2, 8, 8, device=device)
            with torch.no_grad():
                y3d = model3d(x3d, time=torch.ones(1, device=device))
            assert tuple(y3d.shape) == tuple(x3d.shape)
            forward["KarrasUnet3D"] = list(y3d.shape)

    try:
        dist_version = version("denoising-diffusion-pytorch")
    except PackageNotFoundError:
        dist_version = "unknown"
    print(json.dumps({"status": "ok", "version": dist_version, "torch": torch.__version__,
                      "device": str(device), "signatures": signatures, "forward_checks": forward}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
