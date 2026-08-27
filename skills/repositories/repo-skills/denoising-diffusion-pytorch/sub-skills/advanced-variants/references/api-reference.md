# Advanced Variants API Reference

This reference summarizes advanced APIs inspected for `denoising-diffusion-pytorch` 2.3.1. Use public package import names only.

## Import map

```python
from denoising_diffusion_pytorch import (
    KarrasUnet, KarrasUnet1D, KarrasUnet3D, InvSqrtDecayLRSched,
    ContinuousTimeGaussianDiffusion, VParamContinuousTimeGaussianDiffusion,
    ElucidatedDiffusion, LearnedGaussianDiffusion, WeightedObjectiveGaussianDiffusion,
    Unet,
)
from denoising_diffusion_pytorch.attend import Attend
from denoising_diffusion_pytorch.simple_diffusion import UViT, GaussianDiffusion as SimpleGaussianDiffusion
```

## Karras magnitude-preserving UNets

| API | Constructor essentials | Forward contract | Constraints |
| --- | --- | --- | --- |
| `KarrasUnet` | keyword-only `image_size`, optional `dim=192`, `dim_max=768`, `num_classes=None`, `channels=4`, `num_downsamples=3`, `num_blocks_per_stage=4`, `attn_res=(16, 8)`, `attn_flash=False`, `self_condition=False` | `model(x, time, self_cond=None, class_labels=None)` with `(batch, channels, image_size, image_size)` | If `num_classes` is set, pass integer or one-hot `class_labels`; otherwise omit them. |
| `KarrasUnet1D` | keyword-only `seq_len`, same major options | `(batch, channels, seq_len)` | Use for Karras-style architecture, not common `GaussianDiffusion1D` training. |
| `KarrasUnet3D` | keyword-only `image_size`, `frames`, optional `downsample_types`, `factorize_space_time_attn` | `(batch, channels, frames, image_size, image_size)` | `downsample_types` entries are `all`, `frame`, or `image`; selected axes must be divisible by 2 per stage. |
| `InvSqrtDecayLRSched` | `InvSqrtDecayLRSched(optimizer, t_ref=70000, sigma_ref=0.01)` | Returns PyTorch `LambdaLR` | Multiplier is `sigma_ref / sqrt(max(step / t_ref, 1.0))`. |

## Continuous-time and EDM wrappers

| API | Constructor essentials | Model requirements |
| --- | --- | --- |
| `ContinuousTimeGaussianDiffusion` | `model, image_size, channels=3, noise_schedule='linear', num_sample_steps=500` | Root `Unet` must have `learned_sinusoidal_cond=True` or `random_fourier_features=True`; `self_condition=False`. |
| `VParamContinuousTimeGaussianDiffusion` | `model, image_size, channels=3, num_sample_steps=500` | Same conditioning requirement; no self-conditioning. |
| `ElucidatedDiffusion` | `net, image_size, channels=3, num_sample_steps=32, sigma_min=0.002, sigma_max=80, sigma_data=0.5, rho=7` | Requires learned/random sinusoidal conditioning; can follow the net's self-conditioning setting. |

Root `GaussianDiffusion` rejects models with random/learned sinusoidal conditioning; use these wrappers instead for continuous log-SNR or EDM conditioning.

## Learned variance and weighted objective

| API | Required model output | Disallowed settings |
| --- | --- | --- |
| `LearnedGaussianDiffusion(model, vb_loss_weight=0.001, *args, **kwargs)` | `model.out_dim == model.channels * 2` (`Unet(learned_variance=True)` sets this) | `model.self_condition` must be false. |
| `WeightedObjectiveGaussianDiffusion(model, *args, pred_noise_loss_weight=0.1, pred_x_start_loss_weight=0.1, **kwargs)` | `model.out_dim == channels * 2 + 2` | no self-conditioning; no DDIM (`sampling_timesteps` must equal `timesteps`). |

## Simple diffusion UViT

`simple_diffusion.UViT` is an independent U-ViT image model. Its `SimpleGaussianDiffusion` uses `pred_objective='v'` or `'eps'`, and shifted/interpolated noise schedules via `noise_d` or `noise_d_low` plus `noise_d_high`.

## Attention API

`Attend(dropout=0.0, flash=False, scale=None)` accepts q/k/v tensors shaped like `(batch, heads, sequence, dim_head)`. `flash=True` requires PyTorch >= 2.0 and uses PyTorch scaled-dot-product attention backend selection; it is not a separate `flash-attn` dependency.
