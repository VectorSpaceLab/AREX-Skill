---
name: sequence-diffusion
description: "Use denoising-diffusion-pytorch for 1D sequence diffusion with
  Unet1D, GaussianDiffusion1D, Dataset1D, Trainer1D, tensor layouts, sampling,
  interpolation, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sequence Diffusion

Use this sub-skill when the task is about 1D diffusion over tensors such as audio-like features, time series, token embeddings, or other sequences using the public `denoising_diffusion_pytorch` API from `denoising-diffusion-pytorch` 2.3.1.

## Read first

- For signatures, tensor layouts, supported objectives and schedules, read [references/api-reference.md](references/api-reference.md).
- For loss, sampling, interpolation, channel-last adaptation, and `Trainer1D` recipes, read [references/workflows.md](references/workflows.md).
- For common assertion and runtime failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To check an installed package without training, run [scripts/smoke_sequence_diffusion.py](scripts/smoke_sequence_diffusion.py).

## Route here when

- The user wants `Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, or `Trainer1D`.
- Input data is shaped as `(batch, channels, sequence_length)` or needs help with `(batch, sequence_length, channels)` conversion.
- The task mentions `seq_length`, sequence channels/features, 1D sampling, 1D interpolation, `channel_first`, `sampling_timesteps`, or Accelerate-backed `Trainer1D` basics.

## Do not handle here

- 2D image folders, image `Trainer`, FID, or RePaint: route to [../image-diffusion/SKILL.md](../image-diffusion/SKILL.md).
- `XMWrapper`, classifier-free guidance, or classifier-gradient guidance layered around a sequence model: route guidance setup to [../conditioning-guidance/SKILL.md](../conditioning-guidance/SKILL.md), then return here for base 1D tensor layout.
- `KarrasUnet1D` or advanced diffusion objectives beyond standard `GaussianDiffusion1D`: route to [../advanced-variants/SKILL.md](../advanced-variants/SKILL.md).

## Minimal safe pattern

```python
import torch
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D

model = Unet1D(dim=8, dim_mults=(1,), channels=2)
diffusion = GaussianDiffusion1D(model, seq_length=8, timesteps=8,
                                sampling_timesteps=4, objective='pred_noise',
                                beta_schedule='cosine')
x = torch.rand(2, 2, 8)   # (batch, channels, seq_length), values in [0, 1]
loss = diffusion(x)
sample = diffusion.sample(batch_size=2)
assert sample.shape == (2, 2, 8)
```
