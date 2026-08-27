#!/usr/bin/env python3
"""Tiny smoke checks for denoising-diffusion-pytorch guidance APIs."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test conditioning/guidance APIs without training or data files.")
    parser.add_argument("--quick", action="store_true", help="Include tiny CFG sample check.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--candidates", type=int, default=2)
    parser.add_argument("--max-batch-size", type=int, default=None)
    parser.add_argument("--skip-cfg", action="store_true")
    return parser


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def import_runtime() -> Dict[str, Any]:
    try:
        import torch
        from denoising_diffusion_pytorch import GaussianDiffusion1D, Unet1D, XMWrapper
        from denoising_diffusion_pytorch.classifier_free_guidance import GaussianDiffusion as CFGGaussianDiffusion
        from denoising_diffusion_pytorch.classifier_free_guidance import Unet as CFGUnet
    except ModuleNotFoundError as exc:
        fail("Import failed. Install with `python -m pip install denoising-diffusion-pytorch`. Missing: " + str(exc))
    return locals()


def select_device(torch: Any, requested: str):
    if requested == "cuda":
        if not torch.cuda.is_available():
            fail("--device cuda was requested, but torch.cuda.is_available() is False")
        return torch.device("cuda")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device("cpu")


def finite_scalar(torch: Any, value: Any, name: str) -> float:
    if not torch.is_tensor(value) or value.ndim != 0 or not torch.isfinite(value.detach()).item():
        fail(f"{name} did not return a finite scalar tensor")
    return float(value.detach().cpu().item())


def run_xm(rt: Dict[str, Any], device: Any, candidates: int, max_batch_size: Optional[int]) -> Dict[str, Any]:
    torch = rt["torch"]
    model = rt["Unet1D"](dim=8, dim_mults=(1,), channels=1).to(device)
    diffusion = rt["GaussianDiffusion1D"](model, seq_length=8, timesteps=8, sampling_timesteps=4).to(device)
    xm = rt["XMWrapper"](diffusion, candidates=candidates, max_batch_size=max_batch_size).to(device)
    x = torch.rand(2, 1, 8, device=device)
    with torch.enable_grad():
        loss = xm(x)
    return {"loss": finite_scalar(torch, loss, "XMWrapper loss"), "shape": tuple(x.shape)}


def run_cfg(rt: Dict[str, Any], device: Any, quick: bool) -> Dict[str, Any]:
    torch = rt["torch"]
    model = rt["CFGUnet"](dim=8, dim_mults=(1,), channels=1, num_classes=3, cond_drop_prob=0.5).to(device)
    diffusion = rt["CFGGaussianDiffusion"](model, image_size=8, timesteps=8, sampling_timesteps=4,
                                            objective="pred_noise", beta_schedule="cosine",
                                            ddim_sampling_eta=0.0).to(device)
    images = torch.rand(2, 1, 8, 8, device=device)
    classes = torch.tensor([0, 2], dtype=torch.long, device=device)
    loss = diffusion(images, classes=classes)
    report = {"loss": finite_scalar(torch, loss, "CFG loss"), "shape": tuple(images.shape)}
    if quick:
        with torch.no_grad():
            sample = diffusion.sample(classes=classes, cond_scale=2.0, rescaled_phi=0.7)
        if tuple(sample.shape) != tuple(images.shape) or not torch.isfinite(sample).all().item():
            fail("CFG sample shape or finiteness check failed")
        report["sample_shape"] = tuple(sample.shape)
    return report


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.candidates < 1:
        fail("--candidates must be at least 1")
    if args.max_batch_size is not None and args.max_batch_size < 1:
        fail("--max-batch-size must be positive")
    rt = import_runtime()
    torch = rt["torch"]
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)
    device = select_device(torch, args.device)
    xm = run_xm(rt, device, args.candidates, args.max_batch_size)
    cfg = None if args.skip_cfg else run_cfg(rt, device, args.quick)
    print("conditioning-guidance smoke passed")
    print(f"device={device}")
    print(f"xm_loss={xm['loss']:.6f} xm_shape={xm['shape']} candidates={args.candidates} max_batch_size={args.max_batch_size}")
    if cfg is None:
        print("cfg=skipped")
    else:
        print(f"cfg_loss={cfg['loss']:.6f} cfg_shape={cfg['shape']} sample_shape={cfg.get('sample_shape')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
