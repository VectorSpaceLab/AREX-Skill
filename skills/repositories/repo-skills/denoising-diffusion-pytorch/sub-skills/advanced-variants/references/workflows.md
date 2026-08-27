# Advanced Variant Workflows

Use these workflows after installing `denoising-diffusion-pytorch` and importing from `denoising_diffusion_pytorch`. They avoid long training and sampling in routine checks.

## Select the right route

| User asks for | Use | Route notes |
| --- | --- | --- |
| Karras image model | `KarrasUnet` | For folder `Trainer`, DDPM/DDIM image sampling, FID, or RePaint, route to `image-diffusion`. |
| Karras 1D model | `KarrasUnet1D` | For common `Unet1D` / `GaussianDiffusion1D` / `Trainer1D`, route to `sequence-diffusion`. |
| Karras 3D / video | `KarrasUnet3D` | Verify `frames`, `image_size`, `num_downsamples`, and `downsample_types` divisibility. |
| Continuous log-SNR | `ContinuousTimeGaussianDiffusion` or `VParamContinuousTimeGaussianDiffusion` | Requires learned/random Fourier sinusoidal conditioning and no self-conditioning. |
| EDM / elucidated diffusion | `ElucidatedDiffusion` | Requires learned/random Fourier sinusoidal conditioning. |
| Learned variance | `LearnedGaussianDiffusion` | Requires `out_dim=channels*2`. |
| Weighted objective | `WeightedObjectiveGaussianDiffusion` | Requires `out_dim=channels*2+2`, no self-conditioning, no DDIM. |
| simple diffusion | `simple_diffusion.UViT` + `SimpleGaussianDiffusion` | Import from the submodule. |

## Run the bundled tiny smoke check

From the generated skill root:

```bash
python sub-skills/advanced-variants/scripts/smoke_advanced_variants.py --quick --device cpu
python sub-skills/advanced-variants/scripts/smoke_advanced_variants.py --quick --device auto --include-3d
```

The helper imports advanced classes, inspects signatures, and runs tiny Karras 2D/1D forward shape checks. `--include-3d` adds a small video-shaped check.

## Karras 2D / 1D setup

```python
import torch
from denoising_diffusion_pytorch import KarrasUnet, KarrasUnet1D

model = KarrasUnet(image_size=32, channels=3, dim=16, dim_max=32,
                   num_downsamples=1, num_blocks_per_stage=1,
                   attn_res=(), attn_dim_head=8, attn_flash=False)
x = torch.randn(2, 3, 32, 32)
y = model(x, time=torch.ones(2))
assert y.shape == x.shape

model1d = KarrasUnet1D(seq_len=32, channels=4, dim=16, dim_max=32,
                       num_downsamples=1, num_blocks_per_stage=1,
                       attn_res=(), attn_dim_head=8)
x1d = torch.randn(2, 4, 32)
y1d = model1d(x1d, time=torch.ones(2))
assert y1d.shape == x1d.shape
```

If `num_classes` is set, provide `class_labels` every forward call. For self-conditioning, construct with `self_condition=True` and pass a same-shaped `self_cond`, or omit it to use zeros.

## Karras 3D / video setup

```python
import torch
from denoising_diffusion_pytorch import KarrasUnet3D

model = KarrasUnet3D(frames=4, image_size=16, channels=2, dim=4, dim_max=8,
                     num_downsamples=1, num_blocks_per_stage=1,
                     downsample_types=("all",), attn_res=(), attn_dim_head=4)
video = torch.randn(1, 2, 4, 16, 16)
out = model(video, time=torch.ones(1))
assert out.shape == video.shape
```

Use batch 1, small `dim`, `attn_res=()`, and few downsample stages before scaling video tensors.

## Continuous-time / v-param / EDM setup

```python
import torch
from denoising_diffusion_pytorch import Unet, ContinuousTimeGaussianDiffusion, ElucidatedDiffusion

model = Unet(dim=16, dim_mults=(1,), channels=3,
             learned_sinusoidal_cond=True, self_condition=False)
continuous = ContinuousTimeGaussianDiffusion(model, image_size=32, channels=3,
                                             noise_schedule='cosine', num_sample_steps=8)
images = torch.rand(2, 3, 32, 32)
loss = continuous(images)

edm = ElucidatedDiffusion(model, image_size=32, channels=3, num_sample_steps=4)
loss_edm = edm(images)
```

A default root `Unet` will fail these wrappers because it lacks random/learned sinusoidal conditioning.

## Learned variance and weighted objective

```python
from denoising_diffusion_pytorch import Unet, LearnedGaussianDiffusion, WeightedObjectiveGaussianDiffusion

learned_model = Unet(dim=16, dim_mults=(1,), channels=3,
                     learned_variance=True, self_condition=False)
learned = LearnedGaussianDiffusion(learned_model, image_size=32, timesteps=32)

weighted_model = Unet(dim=16, dim_mults=(1,), channels=3,
                      out_dim=3 * 2 + 2, self_condition=False)
weighted = WeightedObjectiveGaussianDiffusion(weighted_model, image_size=32,
                                              timesteps=32, sampling_timesteps=32)
```

Do not set `sampling_timesteps < timesteps` for weighted objective; it rejects DDIM.

## Simple diffusion

```python
from denoising_diffusion_pytorch.simple_diffusion import UViT, GaussianDiffusion as SimpleGaussianDiffusion

model = UViT(dim=16, dim_mults=(1,), channels=3, vit_depth=1)
diffusion = SimpleGaussianDiffusion(model, image_size=32, channels=3,
                                    pred_objective='v', num_sample_steps=8)
```

Use `pred_objective='v'` or `'eps'`, not root strings like `'pred_noise'`.
