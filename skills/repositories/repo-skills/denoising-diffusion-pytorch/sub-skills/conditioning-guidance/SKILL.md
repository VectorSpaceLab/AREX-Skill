---
name: conditioning-guidance
description: "Use denoising-diffusion-pytorch conditioning and guidance APIs:
  classifier-free guidance, classifier-gradient cond_fn guidance, and XMWrapper
  multi-candidate loss."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Conditioning Guidance

Use this sub-skill for conditioning and guidance surfaces in `denoising-diffusion-pytorch`: classifier-free guidance, class-label sampling controls, external classifier-gradient `cond_fn` guidance, and `XMWrapper` multi-candidate loss selection.

## Route here when

- The task mentions classifier-free guidance, class conditioning, `num_classes`, class labels, `classes`, `cond_drop_prob`, `cond_scale`, `rescaled_phi`, or CFG++ / `use_cfg_plus_plus`.
- The task asks for an external classifier `cond_fn`, `guidance_kwargs`, classifier-gradient sampling, label-conditioned classifier logits, or guidance shape/device debugging.
- The task asks about `XMWrapper`, explorative / multi-candidate loss, `candidates`, `max_batch_size`, `random_time_method`, or `random_time_kwarg`.

## Route elsewhere for base setup

- 2D image `Unet`, `GaussianDiffusion`, image folders, `Trainer`, FID, DDIM/DDPM basics, interpolation without classes, or RePaint setup: [../image-diffusion/SKILL.md](../image-diffusion/SKILL.md).
- 1D tensors, `Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, `Trainer1D`, sequence layout, sequence sampling, or `channel_first`: [../sequence-diffusion/SKILL.md](../sequence-diffusion/SKILL.md).
- Karras models, continuous-time wrappers, learned variance, weighted objectives, simple diffusion, flash/SDPA attention, or other advanced variants: [../advanced-variants/SKILL.md](../advanced-variants/SKILL.md).

## Operating map

1. Read [references/api-reference.md](references/api-reference.md) for import paths, signatures, tensor contracts, and guidance-specific semantics.
2. Read [references/workflows.md](references/workflows.md) for safe recipes: CFG loss/sample, classifier-gradient `cond_fn`, `XMWrapper`, and candidate chunking.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for label shape errors, CFG schedule assertions, guidance strength issues, `cond_fn` gradient failures, and `XMWrapper` failures.
4. Run [scripts/smoke_conditioning_guidance.py](scripts/smoke_conditioning_guidance.py) after installing the package to verify tiny CPU or CUDA guidance checks without training, downloads, or data files.

## Safe defaults

For quick local checks, keep models tiny: `dim=8`, `dim_mults=(1,)`, `channels=1`, `image_size=8` or `seq_length=8`, `timesteps=8`, `sampling_timesteps=4`, random tensors in `[0, 1]`, `candidates=2`, and `max_batch_size` no larger than `batch * candidates`.
