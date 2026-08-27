# Advanced Variants Troubleshooting

For base image trainer/FID/RePaint issues, route to `image-diffusion`. For base 1D `Trainer1D` issues, route to `sequence-diffusion`. For guidance labels, `cond_fn`, or `XMWrapper`, route to `conditioning-guidance`.

## Continuous-time, v-param, and EDM assertions

### `assert model.random_or_learned_sinusoidal_cond`

Cause: the wrapper expects a root `Unet` configured with learned/random sinusoidal or Fourier features.

Fix:

```python
from denoising_diffusion_pytorch import Unet, ContinuousTimeGaussianDiffusion
model = Unet(dim=16, dim_mults=(1,), channels=3,
             learned_sinusoidal_cond=True, self_condition=False)
diffusion = ContinuousTimeGaussianDiffusion(model, image_size=32, channels=3)
```

Do not wrap this same model with root `GaussianDiffusion`; that class rejects random/learned sinusoidal conditioning.

### `assert not model.self_condition`

`ContinuousTimeGaussianDiffusion` and `VParamContinuousTimeGaussianDiffusion` do not support self-conditioning. Use `self_condition=False`. `ElucidatedDiffusion` can follow the wrapped net's self-conditioning path.

## Learned variance failures

`LearnedGaussianDiffusion` requires `model.out_dim == model.channels * 2` and no self-conditioning. Use `Unet(..., learned_variance=True, self_condition=False)`.

## Weighted objective failures

Weighted objective expects predicted noise, predicted `x_start`, and two weight channels, so `out_dim == channels * 2 + 2`. It also rejects self-conditioning and DDIM sampling.

```python
channels = 3
model = Unet(dim=16, dim_mults=(1,), channels=channels,
             out_dim=channels * 2 + 2, self_condition=False)
diffusion = WeightedObjectiveGaussianDiffusion(model, image_size=32,
                                              timesteps=32, sampling_timesteps=32)
```

## Simple diffusion failures

- `pred_objective` must be `'v'` or `'eps'`, not root objective strings.
- Use either shifted schedule (`noise_d`) or interpolated schedule (`noise_d_low` plus `noise_d_high`), not an ambiguous combination.
- If transform hooks are supplied to `UViT`, their composition must preserve a mock `(1, 1, 32, 32)` shape.

## Karras failures

- 2D tensors must be `(batch, channels, image_size, image_size)`.
- 1D tensors must be `(batch, channels, seq_len)`.
- If `num_classes` was provided, pass `class_labels`; if not, omit them.
- If `self_condition=False`, do not pass `self_cond`.
- Karras 3D `downsample_types` entries must be exactly `'all'`, `'frame'`, or `'image'`; selected axes must be divisible by 2 at each stage.
- Video tensors can consume memory quickly. Debug with batch 1, small channels, small `dim`, `attn_res=()`, and `num_downsamples=1`.

## Flash / SDPA issues

`flash=True` requires PyTorch >= 2.0. This package uses PyTorch scaled-dot-product attention selection, not a third-party `flash-attn` package. Keep `flash_attn=False` / `attn_flash=False` for first CPU smoke checks.
