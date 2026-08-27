#!/usr/bin/env python3
"""Safe LTX-Video component diagnostics.

This script performs no checkpoint download and no image/video generation. It only
checks importable component APIs, RectifiedFlowScheduler math/shape behavior, and
CausalVideoAutoencoder demo-config downscale factors.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: dict[str, Any]
    error: str | None = None


def _result(name: str, ok: bool, details: dict[str, Any] | None = None, error: Exception | str | None = None) -> CheckResult:
    return CheckResult(
        name=name,
        ok=ok,
        details=details or {},
        error=None if error is None else str(error),
    )


def check_scheduler(sampler: str, device: str | None, num_steps: int) -> CheckResult:
    try:
        import torch
        from ltx_video.schedulers.rf import RectifiedFlowScheduler

        if device is None:
            device = "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("--device cuda requested but torch.cuda.is_available() is False")

        scheduler = RectifiedFlowScheduler(sampler=sampler)
        latents = torch.randn(2, 16, 8, device=device)
        noise_pred = torch.randn_like(latents)
        scheduler.set_timesteps(num_inference_steps=num_steps, samples_shape=latents.shape, device=latents.device)
        timestep = scheduler.timesteps[0]
        out = scheduler.step(noise_pred, timestep, latents, return_dict=False)[0]

        if out.shape != latents.shape:
            raise AssertionError(f"shape changed: expected {tuple(latents.shape)}, got {tuple(out.shape)}")

        next_t = scheduler.timesteps[1] if len(scheduler.timesteps) > 1 else torch.tensor(0.0, device=latents.device)
        expected = latents - (timestep - next_t) * noise_pred
        if not torch.allclose(out, expected, atol=1e-6):
            max_abs = (out - expected).abs().max().item()
            raise AssertionError(f"deterministic scheduler step mismatch; max_abs={max_abs}")

        return _result(
            "scheduler",
            True,
            {
                "sampler": sampler,
                "device": str(latents.device),
                "num_steps": int(num_steps),
                "latents_shape": list(latents.shape),
                "first_timestep": float(timestep.detach().cpu()),
                "shape_preserved": True,
                "deterministic_step_matches_expected": True,
            },
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _result("scheduler", False, {"sampler": sampler, "device": device, "num_steps": num_steps}, exc)


def check_vae_config(latent_channels: int) -> CheckResult:
    try:
        from ltx_video.models.autoencoders.causal_video_autoencoder import (
            CausalVideoAutoencoder,
            create_video_autoencoder_demo_config,
        )

        config = create_video_autoencoder_demo_config(latent_channels=latent_channels)
        vae = CausalVideoAutoencoder.from_config(config)
        spatial = int(vae.spatial_downscale_factor)
        temporal = int(vae.temporal_downscale_factor)
        is_video_supported = bool(vae.is_video_supported)

        if spatial != 32:
            raise AssertionError(f"demo VAE spatial_downscale_factor expected 32, got {spatial}")
        if temporal != 8:
            raise AssertionError(f"demo VAE temporal_downscale_factor expected 8, got {temporal}")
        if not is_video_supported:
            raise AssertionError("demo VAE should support video inputs")

        return _result(
            "vae_config",
            True,
            {
                "latent_channels": latent_channels,
                "spatial_downscale_factor": spatial,
                "temporal_downscale_factor": temporal,
                "is_video_supported": is_video_supported,
                "no_checkpoint_loaded": True,
            },
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _result("vae_config", False, {"latent_channels": latent_channels}, exc)


def check_cuda_smoke() -> CheckResult:
    try:
        import torch

        available = bool(torch.cuda.is_available())
        details: dict[str, Any] = {
            "torch_version": torch.__version__,
            "cuda_available": available,
            "cuda_version": torch.version.cuda,
        }
        if not available:
            return _result("cuda_smoke", False, details, "CUDA is not available to torch")

        device_count = torch.cuda.device_count()
        current = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(current)
        tensor = torch.ones((2, 2), device="cuda")
        details.update(
            {
                "device_count": device_count,
                "current_device": current,
                "device_name": props.name,
                "capability": list(props.major_minor) if hasattr(props, "major_minor") else [props.major, props.minor],
                "tiny_allocation_sum": float(tensor.sum().detach().cpu()),
            }
        )
        return _result("cuda_smoke", True, details)
    except Exception as exc:  # pylint: disable=broad-except
        return _result("cuda_smoke", False, {}, exc)


def print_text(results: list[CheckResult]) -> None:
    print("LTX-Video component diagnostics (no downloads, no generation)")
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        print(f"[{status}] {item.name}")
        for key, value in item.details.items():
            print(f"  - {key}: {value}")
        if item.error:
            print(f"  - error: {item.error}")
    if results:
        print("Reminder: these component checks do not verify full checkpoint inference or output quality.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe LTX-Video component diagnostics without downloading checkpoints "
            "or generating media. If no check flag is supplied, runs --scheduler and --vae-config."
        )
    )
    parser.add_argument("--scheduler", action="store_true", help="check RectifiedFlowScheduler setup and deterministic step math")
    parser.add_argument("--vae-config", action="store_true", help="instantiate the demo CausalVideoAutoencoder config and validate downscale factors")
    parser.add_argument("--cuda-smoke", action="store_true", help="check torch CUDA availability and a tiny CUDA allocation")
    parser.add_argument("--sampler", choices=["Uniform", "LinearQuadratic"], default="LinearQuadratic", help="scheduler sampler to test")
    parser.add_argument("--num-steps", type=int, default=4, help="number of scheduler inference steps for the smoke")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="device for the scheduler smoke; defaults to cpu")
    parser.add_argument("--latent-channels", type=int, default=16, help="latent channel count for the lightweight demo VAE config smoke")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.num_steps < 1:
        print("--num-steps must be >= 1", file=sys.stderr)
        return 2
    if args.latent_channels < 1:
        print("--latent-channels must be >= 1", file=sys.stderr)
        return 2

    selected_any = args.scheduler or args.vae_config or args.cuda_smoke
    run_scheduler = args.scheduler or not selected_any
    run_vae = args.vae_config or not selected_any

    results: list[CheckResult] = []
    if run_scheduler:
        results.append(check_scheduler(args.sampler, args.device, args.num_steps))
    if run_vae:
        results.append(check_vae_config(args.latent_channels))
    if args.cuda_smoke:
        results.append(check_cuda_smoke())

    if args.json:
        print(json.dumps([asdict(item) for item in results], indent=2, sort_keys=True))
    else:
        print_text(results)

    return 0 if all(item.ok for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
