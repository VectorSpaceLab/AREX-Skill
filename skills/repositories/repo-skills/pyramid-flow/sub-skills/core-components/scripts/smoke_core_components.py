#!/usr/bin/env python3
"""Safe smoke checks for Pyramid-Flow core components.

This script only performs import, signature, scheduler, and tiny synthetic VAE
checks. It does not download checkpoints or launch generation/training.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import inspect
import io
import sys
from pathlib import Path
from typing import Dict, Iterable


REQUIRED_PACKAGES = (
    "torch",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "tokenizers",
    "timm",
    "tensorboardX",
)

OPTIONAL_PACKAGES = (
    "huggingface_hub",
    "einops",
    "jsonlines",
    "opencv-python",
    "imageio",
    "imageio-ffmpeg",
    "sentencepiece",
    "spacy",
    "torchvision",
    "torchmetrics",
    "tiktoken",
    "ftfy",
    "contexttimer",
)


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def add_package_root(package_root: str | None) -> None:
    if not package_root:
        return
    root = Path(package_root).expanduser()
    if not root.exists():
        raise FileNotFoundError("package root does not exist")
    sys.path.insert(0, str(root))


def import_public_modules() -> Dict[str, object]:
    modules = {}
    for name in ("pyramid_dit", "video_vae", "diffusion_schedulers", "trainer_misc"):
        modules[name] = importlib.import_module(name)
    return modules


def report_versions(packages: Iterable[str], quiet: bool = False) -> Dict[str, str]:
    versions: Dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "missing"
    for package in packages:
        log(f"version {package}: {versions[package]}", quiet=quiet)
    return versions


def ensure_required_packages() -> None:
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            metadata.version(package)
        except metadata.PackageNotFoundError:
            missing.append(package)
    if missing:
        raise RuntimeError(
            "missing required runtime packages: " + ", ".join(sorted(missing))
        )


def check_public_signatures(modules: Dict[str, object], quiet: bool = False) -> None:
    from pyramid_dit import PyramidDiTForVideoGeneration
    from video_vae import CausalVideoVAE, CausalVideoVAELossWrapper
    from diffusion_schedulers import PyramidFlowMatchEulerDiscreteScheduler, DDPMCosineScheduler
    from trainer_misc import init_distributed_mode, init_sequence_parallel_group

    checks = {
        "PyramidDiTForVideoGeneration.__init__": PyramidDiTForVideoGeneration.__init__,
        "PyramidDiTForVideoGeneration.generate": PyramidDiTForVideoGeneration.generate,
        "PyramidDiTForVideoGeneration.generate_i2v": PyramidDiTForVideoGeneration.generate_i2v,
        "CausalVideoVAE.__init__": CausalVideoVAE.__init__,
        "CausalVideoVAE.encode": CausalVideoVAE.encode,
        "CausalVideoVAE.decode": CausalVideoVAE.decode,
        "CausalVideoVAELossWrapper.__init__": CausalVideoVAELossWrapper.__init__,
        "PyramidFlowMatchEulerDiscreteScheduler.__init__": PyramidFlowMatchEulerDiscreteScheduler.__init__,
        "PyramidFlowMatchEulerDiscreteScheduler.set_timesteps": PyramidFlowMatchEulerDiscreteScheduler.set_timesteps,
        "PyramidFlowMatchEulerDiscreteScheduler.step": PyramidFlowMatchEulerDiscreteScheduler.step,
        "DDPMCosineScheduler.__init__": DDPMCosineScheduler.__init__,
        "DDPMCosineScheduler.set_timesteps": DDPMCosineScheduler.set_timesteps,
        "DDPMCosineScheduler.step": DDPMCosineScheduler.step,
        "init_distributed_mode": init_distributed_mode,
        "init_sequence_parallel_group": init_sequence_parallel_group,
    }
    for name, obj in checks.items():
        inspect.signature(obj)
        log(f"signature {name}: ok", quiet=quiet)


def validate_scheduler_stage_index(stage_index: int, stages: int) -> None:
    if not 0 <= stage_index < stages:
        raise ValueError(
            f"stage_index {stage_index} is out of range for {stages} stages; "
            f"valid range is 0..{stages - 1}"
        )


def validate_vae_spatial_shape(height: int, width: int, downsample_scale: int = 8) -> None:
    if height % downsample_scale != 0 or width % downsample_scale != 0:
        raise ValueError(
            f"height={height} and width={width} must both be divisible by {downsample_scale}"
        )


def run_scheduler_smoke(quiet: bool = False) -> None:
    import torch
    from diffusion_schedulers import PyramidFlowMatchEulerDiscreteScheduler, DDPMCosineScheduler

    log("scheduler smoke: flow-match", quiet=quiet)
    flow = PyramidFlowMatchEulerDiscreteScheduler(
        num_train_timesteps=8,
        stages=3,
        stage_range=[0, 1 / 3, 2 / 3, 1],
        gamma=1 / 3,
    )
    flow.set_timesteps(num_inference_steps=4, stage_index=1, device="cpu")
    sample = torch.zeros(2, 4, 1, 4, 4)
    model_output = torch.full_like(sample, 0.25)
    out = flow.step(model_output=model_output, timestep=flow.timesteps[0], sample=sample)
    if out.prev_sample.shape != sample.shape:
        raise RuntimeError("flow scheduler changed the sample shape")
    if flow.step_index != 1:
        raise RuntimeError("flow scheduler did not advance step_index")

    log("scheduler smoke: cosine-ddpm", quiet=quiet)
    ddpm = DDPMCosineScheduler()
    ddpm.set_timesteps(num_inference_steps=4, device="cpu")
    timestep = ddpm.timesteps[0:1]
    ddpm_sample = torch.zeros(1, 4, 2, 2)
    ddpm_out = ddpm.step(
        model_output=torch.zeros_like(ddpm_sample),
        timestep=timestep,
        sample=ddpm_sample,
    )
    if ddpm_out.prev_sample.shape != ddpm_sample.shape:
        raise RuntimeError("DDPM scheduler changed the sample shape")


def run_tiny_vae_smoke(quiet: bool = False) -> None:
    import torch
    from video_vae import CausalVideoVAE

    log("vae smoke: tiny round-trip", quiet=quiet)
    stdout_context = contextlib.redirect_stdout(io.StringIO()) if quiet else contextlib.nullcontext()
    with stdout_context:
        vae = CausalVideoVAE(
            encoder_layers_per_block=(1, 1, 1, 1),
            decoder_layers_per_block=(1, 1, 1, 1),
            encoder_block_out_channels=(8, 8, 8, 8),
            decoder_block_out_channels=(8, 8, 8, 8),
            encoder_norm_num_groups=4,
            decoder_norm_num_groups=4,
            sample_size=16,
            encoder_spatial_down_sample=(True, True, True, False),
            decoder_spatial_up_sample=(True, True, True, False),
            encoder_temporal_down_sample=(False, False, False, False),
            decoder_temporal_up_sample=(False, False, False, False),
            downsample_scale=8,
            interpolate=False,
        ).eval()

    x = torch.zeros(1, 3, 1, 16, 16)
    with torch.no_grad():
        posterior = vae.encode(x)
        latent = posterior.latent_dist.mode()
        decoded = vae.decode(latent).sample
    if latent.shape != (1, 4, 1, 2, 2):
        raise RuntimeError(f"unexpected latent shape: {tuple(latent.shape)}")
    if decoded.shape != x.shape:
        raise RuntimeError(f"unexpected decoded shape: {tuple(decoded.shape)}")


def run_negative_cases(quiet: bool = False) -> None:
    log("negative case: scheduler stage index", quiet=quiet)
    try:
        validate_scheduler_stage_index(stage_index=3, stages=3)
    except ValueError as exc:
        log(f"expected scheduler rejection: {exc}", quiet=quiet)
    else:
        raise RuntimeError("expected stage index validation to fail")

    log("negative case: VAE spatial divisibility", quiet=quiet)
    try:
        validate_vae_spatial_shape(height=18, width=16, downsample_scale=8)
    except ValueError as exc:
        log(f"expected VAE rejection: {exc}", quiet=quiet)
    else:
        raise RuntimeError("expected VAE shape validation to fail")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe Pyramid-Flow core-component smoke checks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--package-root",
        default=None,
        help="Optional path to a Pyramid-Flow checkout or install root to prepend to sys.path.",
    )
    parser.add_argument(
        "--skip-tiny-vae",
        action="store_true",
        help="Skip the synthetic CausalVideoVAE round-trip smoke.",
    )
    parser.add_argument(
        "--skip-negative-cases",
        action="store_true",
        help="Skip the synthetic clear-failure checks for scheduler stage index and VAE shape.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only essential failures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_package_root(args.package_root)

    log("core-components smoke: import checks", quiet=args.quiet)
    ensure_required_packages()
    modules = import_public_modules()
    check_public_signatures(modules, quiet=args.quiet)
    report_versions(list(REQUIRED_PACKAGES) + list(OPTIONAL_PACKAGES), quiet=args.quiet)

    run_scheduler_smoke(quiet=args.quiet)
    if not args.skip_tiny_vae:
        run_tiny_vae_smoke(quiet=args.quiet)
    if not args.skip_negative_cases:
        run_negative_cases(quiet=args.quiet)

    log("core-components smoke: PASS", quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
