---
name: advanced-variants
description: "Advanced denoising-diffusion-pytorch variants: Karras UNets,
  continuous-time, EDM, simple diffusion, learned/weighted objectives, and
  attention backend compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Advanced Variants

Use this sub-skill when a task goes beyond common DDPM/DDIM image or 1D sequence paths and asks for Karras magnitude-preserving UNets, continuous-time or v-parameterized diffusion, EDM / elucidated diffusion, simple diffusion UViT, learned variance, weighted objectives, video-shaped Karras 3D models, or flash / SDPA attention behavior in `denoising-diffusion-pytorch` 2.3.1.

## Route elsewhere

- Common 2D image `Unet`, `GaussianDiffusion`, folder `Trainer`, FID, DDIM, or RePaint work: [../image-diffusion/SKILL.md](../image-diffusion/SKILL.md).
- Common 1D sequence `Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, or `Trainer1D` work: [../sequence-diffusion/SKILL.md](../sequence-diffusion/SKILL.md).
- Classifier-free guidance, external classifier `cond_fn`, or `XMWrapper`: [../conditioning-guidance/SKILL.md](../conditioning-guidance/SKILL.md).

## What this sub-skill covers

- Karras architectures: `KarrasUnet`, `KarrasUnet1D`, `KarrasUnet3D`, and `InvSqrtDecayLRSched`.
- Advanced diffusion wrappers: `ContinuousTimeGaussianDiffusion`, `VParamContinuousTimeGaussianDiffusion`, `ElucidatedDiffusion`, `LearnedGaussianDiffusion`, and `WeightedObjectiveGaussianDiffusion`.
- Simple diffusion APIs: `denoising_diffusion_pytorch.simple_diffusion.UViT` and its `GaussianDiffusion`.
- Attention compatibility: `Attend`, `flash_attn` constructor flags, PyTorch SDPA behavior, and CPU/CUDA expectations.
- A bundled tiny smoke helper: [scripts/smoke_advanced_variants.py](scripts/smoke_advanced_variants.py).

## Required reference order

1. Read [references/api-reference.md](references/api-reference.md) for import paths, signatures, tensor shapes, and constructor constraints.
2. Read [references/workflows.md](references/workflows.md) for safe setup recipes and cross-skill routing.
3. Read [references/compatibility.md](references/compatibility.md) before changing devices, enabling `flash_attn`, using Karras 3D downsampling, or selecting a CPU/CUDA verification plan.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when an assertion mentions sinusoidal conditioning, self-conditioning, `out_dim`, DDIM, simple diffusion noise dimensions, Karras video divisibility, or SDPA.

## Fast verification

From the generated skill root:

```bash
python sub-skills/advanced-variants/scripts/smoke_advanced_variants.py --quick --device cpu
```

Add `--include-3d` only when a tiny video-shaped Karras 3D check is desired.
