---
name: image-diffusion
description: "Operate 2D image DDPM/DDIM workflows with
  denoising-diffusion-pytorch Unet, GaussianDiffusion, Dataset, Trainer, FID,
  and RePaint guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Image Diffusion

Use this sub-skill for 2D image diffusion tasks with `denoising-diffusion-pytorch` (`denoising_diffusion_pytorch` import), inspected at version 2.3.1.

## Route here for

- Building a 2D `Unet` and `GaussianDiffusion` for DDPM or DDIM image loss and sampling.
- Adapting the README-style image tensor recipe into a tiny CPU or CUDA smoke check.
- Using the folder `Dataset` and `Trainer` for image-folder training.
- Explaining `calculate_fid`, `FIDEvaluation`, and `save_best_and_latest_only` behavior.
- Using the RePaint module for mask + ground-truth image inpainting / resampling guidance.
- Debugging image shape, channel, schedule, sampling, Trainer, FID, or optional flash-attention failures.

## Route elsewhere

- 1D sequence APIs (`Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, `Trainer1D`) -> [../sequence-diffusion/SKILL.md](../sequence-diffusion/SKILL.md).
- Classifier-free guidance, external classifier guidance, and `XMWrapper` -> [../conditioning-guidance/SKILL.md](../conditioning-guidance/SKILL.md).
- Karras, continuous-time, EDM, simple diffusion, learned variance, weighted objective, and other advanced variants -> [../advanced-variants/SKILL.md](../advanced-variants/SKILL.md).

## Operating map

1. For import paths, constructor contracts, parameter constraints, and FID/RePaint API notes, read [references/api-reference.md](references/api-reference.md).
2. For safe setup, image loss/sample smoke, Trainer setup, DDPM vs DDIM sampling, interpolation, FID, and RePaint workflows, read [references/workflows.md](references/workflows.md).
3. For common failure diagnosis, read [references/troubleshooting.md](references/troubleshooting.md).
4. To verify an installed package without training or downloads, run [scripts/smoke_image_diffusion.py](scripts/smoke_image_diffusion.py) from any working directory after installing the package.

## Safe defaults

Prefer tiny smoke settings before any real training: `dim=8`, `dim_mults=(1,)`, `channels=1`, `image_size=8`, `timesteps=8`, `sampling_timesteps=4`, `beta_schedule='sigmoid'`, `flash_attn=False`, and random tensors in `[0, 1]`. These defaults exercise loss and DDIM sampling without training or dataset access.
