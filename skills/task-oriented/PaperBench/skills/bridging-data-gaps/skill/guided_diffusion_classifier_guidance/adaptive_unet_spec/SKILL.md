---
name: adaptive_unet_spec
description: Validate paper-critical guided diffusion UNet architecture flags before claiming architecture-faithful recovery or sampling.
---

# Adaptive UNet Architecture Specification

Use this skill when checking whether a guided-diffusion configuration preserves the architecture choices emphasized in `Diffusion Models Beat GANs on Image Synthesis`. It is useful for module planning, recovery manifests, and ablation/stress checks.

## Inputs

- Resolution, base channels, residual block count, and attention resolutions.
- Flags for `use_scale_shift_norm`, `resblock_updown`, `learn_sigma`, and class conditioning.
- A declaration of whether the run is `full`, `reduced`, or `proxy`.

## Outputs

- Normalized spec dictionary.
- `ok` boolean for paper-like architecture claims.
- Warnings describing omissions that are acceptable only for declared proxies.

## Workflow

1. Normalize CLI or JSON fields into a consistent spec.
2. Require scale-shift adaptive normalization for paper-like guided diffusion.
3. Require attention metadata for ImageNet-style conditional synthesis.
4. Require residual up/downsampling and learned sigma for full high-resolution claims.
5. If a reduced proxy does not instantiate a UNet, mark the module as cross-checked instead of fully executed.

## Validation

Run `python scripts/architecture_spec.py --example paper128`. The tests check a passing paper-like spec and failing degraded specs.

## Limitations

This skill does not build neural layers or load checkpoints. It prevents architecture metadata drift and records which architecture components were omitted in bounded recovery.
