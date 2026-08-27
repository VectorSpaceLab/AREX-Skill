#!/usr/bin/env python3
"""Tiny 2D image diffusion smoke test for denoising-diffusion-pytorch.

Purpose:
    Verify that an installed package can build the public image Unet +
    GaussianDiffusion stack, compute a finite loss, run a backward pass, and
    produce a tiny DDIM sample with the expected shape.

Example:
    python smoke_image_diffusion.py --quick --device cpu
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny Unet + GaussianDiffusion image smoke without training or data files.")
    parser.add_argument("--quick", action="store_true", help="Use the minimal smoke batch size.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--image-size", type=positive_int, default=8)
    parser.add_argument("--timesteps", type=positive_int, default=8)
    parser.add_argument("--sampling-timesteps", type=positive_int, default=4)
    parser.add_argument("--beta-schedule", choices=("linear", "cosine", "sigmoid"), default="sigmoid")
    parser.add_argument("--seed", type=int, default=0)
    return parser


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.sampling_timesteps > args.timesteps:
        return fail("--sampling-timesteps must be <= --timesteps")

    try:
        import torch
        from denoising_diffusion_pytorch import GaussianDiffusion, Unet
    except ModuleNotFoundError as exc:
        return fail("Import failed. Install with `python -m pip install denoising-diffusion-pytorch`. Missing: " + str(exc))

    if args.device == "cuda" and not torch.cuda.is_available():
        return fail("CUDA was requested but torch.cuda.is_available() is False; use --device cpu or install CUDA-capable PyTorch.")
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else args.device)
    if args.device == "auto" and not torch.cuda.is_available():
        device = torch.device("cpu")
    if device.type == "cpu":
        torch.set_num_threads(1)

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    batch_size = 1 if args.quick else 2
    expected_shape = (batch_size, 1, args.image_size, args.image_size)

    model = Unet(dim=8, dim_mults=(1,), channels=1, flash_attn=False).to(device)
    diffusion = GaussianDiffusion(model, image_size=args.image_size, timesteps=args.timesteps,
                                  sampling_timesteps=args.sampling_timesteps,
                                  beta_schedule=args.beta_schedule).to(device)
    images = torch.rand(expected_shape, device=device)
    loss = diffusion(images)
    if not torch.isfinite(loss).item():
        return fail("Loss is NaN or infinite. For tiny smokes use timesteps=8, sampling_timesteps=4, beta_schedule='sigmoid'.")
    loss.backward()

    with torch.inference_mode():
        sample = diffusion.sample(batch_size=batch_size)
    if tuple(sample.shape) != expected_shape:
        return fail(f"Unexpected sample shape {tuple(sample.shape)}; expected {expected_shape}.")
    if not torch.isfinite(sample).all().item():
        return fail("Sample contains NaN or infinite values.")

    try:
        pkg_version = version("denoising-diffusion-pytorch")
    except PackageNotFoundError:
        pkg_version = "unknown"
    print("image diffusion smoke passed")
    print(f"package_version={pkg_version}")
    print(f"device={device.type}")
    print(f"loss={loss.detach().cpu().item():.6f}")
    print(f"sample_shape={tuple(sample.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
