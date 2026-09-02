---
name: diffusion_sampler_proxy
description: Run a tiny reverse-diffusion-like sampler that exercises classifier-free guided score calls at each step.
---

# Diffusion Sampler Proxy

Use this skill for bounded recovery of classifier-free guidance when full image diffusion models are unavailable. It consumes conditional and unconditional predictions and calls the guided score formula every step.

## Inputs
- Initial scalar noise values.
- Condition/class target prototype.
- Guidance strength list and step count.
- Callable guided-score implementation.

## Outputs
- Generated scalar proxy samples.
- Per-step trace containing conditional prediction, unconditional prediction, and guided prediction.

## Workflow
1. Initialize samples from deterministic noise.
2. At every step estimate conditional and unconditional residuals toward class and global means.
3. Combine estimates with classifier-free guidance.
4. Update the sample and retain trace records.

## Validation
Tests verify that stronger guidance moves samples closer to the class prototype and that trace records include both denoiser evaluations.

## Limitations
This is a reduced mechanism check, not a photographic diffusion sampler.
