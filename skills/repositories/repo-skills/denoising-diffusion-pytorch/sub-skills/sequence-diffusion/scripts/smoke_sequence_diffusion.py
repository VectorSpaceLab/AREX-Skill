#!/usr/bin/env python3
"""Smoke-test 1D sequence diffusion without training.

Validates a tiny Unet1D/GaussianDiffusion1D pair, finite loss, sample shape,
and optional channel-last handling through a safe adapter.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version
from typing import Optional

RUNTIME_IMPORT_ERROR = None
try:
    import torch
    from torch import nn
except ModuleNotFoundError as exc:
    RUNTIME_IMPORT_ERROR = exc
    torch = None  # type: ignore[assignment]
    class _DummyNN:
        Module = object
    nn = _DummyNN()  # type: ignore[assignment]
else:
    try:
        from denoising_diffusion_pytorch import Dataset1D, GaussianDiffusion1D, Trainer1D, Unet1D
    except ModuleNotFoundError as exc:
        RUNTIME_IMPORT_ERROR = exc
        Dataset1D = GaussianDiffusion1D = Trainer1D = Unet1D = None  # type: ignore[assignment]


class ChannelLastUnet1D(nn.Module):
    """Adapt public channel-first Unet1D to a channel-last diffusion wrapper."""

    def __init__(self, inner):
        super().__init__()
        self.inner = inner
        self.channels = inner.channels
        self.self_condition = inner.self_condition

    def forward(self, x, time, x_self_cond: Optional[object] = None, self_cond: Optional[object] = None):
        cond = x_self_cond if x_self_cond is not None else self_cond
        x_cf = x.transpose(1, 2).contiguous()
        cond_cf = None if cond is None else cond.transpose(1, 2).contiguous()
        out_cf = self.inner(x_cf, time, x_self_cond=cond_cf)
        return out_cf.transpose(1, 2).contiguous()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a deterministic no-training smoke test for 1D sequence diffusion.")
    parser.add_argument("--quick", action="store_true", help="Skip optional interpolation check.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--seq-length", type=int, default=8)
    parser.add_argument("--channels", type=int, default=2)
    parser.add_argument("--timesteps", type=int, default=8)
    parser.add_argument("--sampling-timesteps", type=int, default=4)
    parser.add_argument("--channel-last", action="store_true", help="Also test (batch, seq_length, channels) via adapter.")
    args = parser.parse_args()
    for name in ("seq_length", "channels", "timesteps", "sampling_timesteps"):
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if args.sampling_timesteps > args.timesteps:
        parser.error("--sampling-timesteps must be <= --timesteps")
    return args


def choose_device(requested: str):
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("--device cuda requested, but torch.cuda.is_available() is False")
        return torch.device("cuda")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device("cpu")


def package_version() -> str:
    try:
        return version("denoising-diffusion-pytorch")
    except PackageNotFoundError:
        return "unknown"


def make_diffusion(args, channel_first: bool, device):
    inner = Unet1D(dim=8, dim_mults=(1,), channels=args.channels)
    model = inner if channel_first else ChannelLastUnet1D(inner)
    diffusion = GaussianDiffusion1D(model, seq_length=args.seq_length, timesteps=args.timesteps,
                                    sampling_timesteps=args.sampling_timesteps,
                                    objective="pred_noise", beta_schedule="cosine",
                                    channel_first=channel_first)
    return diffusion.to(device).eval()


def run_case(args, channel_first: bool, device) -> None:
    label = "channel_first" if channel_first else "channel_last"
    batch = 2
    shape = (batch, args.channels, args.seq_length) if channel_first else (batch, args.seq_length, args.channels)
    x = torch.rand(shape, device=device)
    ds = Dataset1D(x.detach().cpu())
    assert len(ds) == batch
    diffusion = make_diffusion(args, channel_first, device)
    with torch.no_grad():
        loss = diffusion(x)
        if not torch.isfinite(loss).item():
            raise SystemExit(f"{label} loss is not finite")
        sample = diffusion.sample(batch_size=batch)
        if tuple(sample.shape) != shape:
            raise SystemExit(f"{label} sample shape mismatch: got {tuple(sample.shape)}, expected {shape}")
        if not torch.isfinite(sample).all().item():
            raise SystemExit(f"{label} sample contains non-finite values")
        if not args.quick:
            interp = diffusion.interpolate(x, 1.0 - x, t=min(2, args.timesteps - 1), lam=0.25)
            if tuple(interp.shape) != shape:
                raise SystemExit(f"{label} interpolate shape mismatch")
    print(f"[{label}] finite_loss={loss.item():.6f} sample_shape={tuple(sample.shape)}")


def main() -> None:
    args = parse_args()
    if RUNTIME_IMPORT_ERROR is not None or torch is None:
        missing = getattr(RUNTIME_IMPORT_ERROR, "name", None) or str(RUNTIME_IMPORT_ERROR)
        raise SystemExit("Import failed. Install with `python -m pip install denoising-diffusion-pytorch`. Missing: " + missing)
    torch.manual_seed(0)
    torch.set_num_threads(1)
    device = choose_device(args.device)
    print(f"denoising-diffusion-pytorch={package_version()} torch={torch.__version__} device={device}")
    print(f"Trainer1D import ok: {Trainer1D.__name__}; no training will be run")
    run_case(args, True, device)
    if args.channel_last:
        run_case(args, False, device)
    print("smoke ok")


if __name__ == "__main__":
    main()
