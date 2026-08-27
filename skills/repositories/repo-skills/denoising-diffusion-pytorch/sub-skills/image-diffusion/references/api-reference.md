# Image Diffusion API Reference

This reference covers 2D image diffusion APIs in `denoising-diffusion-pytorch` version 2.3.1. Use public install/import names: install distribution `denoising-diffusion-pytorch`, import package `denoising_diffusion_pytorch`.

## Public imports

```python
from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Trainer
from denoising_diffusion_pytorch.denoising_diffusion_pytorch import Dataset
```

`Dataset` is defined in the main image module but is not re-exported by the package root in the inspected version. Import it from `denoising_diffusion_pytorch.denoising_diffusion_pytorch` when needed.

RePaint is a separate image module:

```python
from denoising_diffusion_pytorch.repaint import Unet as RePaintUnet, GaussianDiffusion as RePaintGaussianDiffusion
```

## `Unet`: base 2D model

Constructor summary:

```python
Unet(dim, init_dim=None, out_dim=None, dim_mults=(1, 2, 4, 8), channels=3,
     self_condition=False, learned_variance=False, learned_sinusoidal_cond=False,
     random_fourier_features=False, learned_sinusoidal_dim=16,
     sinusoidal_pos_emb_theta=10000, dropout=0.0, attn_dim_head=32,
     attn_heads=4, full_attn=None, flash_attn=False)
```

Important constraints:

- Input tensors are channel-first images: `(batch, channels, height, width)`.
- `channels` must match the input tensor and generated samples.
- The downsample factor is `2 ** (len(dim_mults) - 1)`. Height and width should be divisible by this factor.
- Base `GaussianDiffusion` rejects `learned_sinusoidal_cond=True` or `random_fourier_features=True`; route continuous-time wrappers to `advanced-variants`.
- `learned_variance=True` changes output channels and belongs with `LearnedGaussianDiffusion` in `advanced-variants`.
- Keep `flash_attn=False` until PyTorch/CUDA SDPA compatibility is verified.

## `GaussianDiffusion`: DDPM/DDIM wrapper

Constructor summary:

```python
GaussianDiffusion(model, *, image_size, timesteps=1000, sampling_timesteps=None,
                  objective='pred_v', beta_schedule='sigmoid', schedule_fn_kwargs=dict(),
                  ddim_sampling_eta=0.0, auto_normalize=True, offset_noise_strength=0.0,
                  min_snr_loss_weight=False, min_snr_gamma=5, immiscible=False)
```

| Parameter | Contract / effect |
| --- | --- |
| `model` | Compatible image `Unet`; for the base class, `model.channels == model.out_dim` and random/learned sinusoidal conditioning is disabled. |
| `image_size` | Integer square size or `(height, width)` tuple/list. Loss asserts inputs match it. |
| `timesteps` | Number of training diffusion steps. Avoid extremely tiny values with the linear schedule. |
| `sampling_timesteps` | Defaults to `timesteps`; must be `<= timesteps`. Smaller values select DDIM sampling. |
| `objective` | `'pred_noise'`, `'pred_x0'`, or `'pred_v'`. |
| `beta_schedule` | `'linear'`, `'cosine'`, or `'sigmoid'`. Safe tiny smoke default is `'sigmoid'`. |
| `auto_normalize` | If true, `forward()` maps input images `[0, 1]` to `[-1, 1]` and `sample()` returns `[0, 1]`-scaled samples. |

Common methods:

```python
loss = diffusion(images)                         # images: BCHW in [0, 1]
loss = diffusion(images, times=times)            # integer times shape (batch,)
samples = diffusion.sample(batch_size=4)
all_steps = diffusion.sample(batch_size=4, return_all_timesteps=True)
mixed = diffusion.interpolate(x1, x2, t=None, lam=0.5)
```

## `Dataset` and `Trainer`

```python
Dataset(folder, image_size, exts=['jpg', 'jpeg', 'png', 'tiff'],
        augment_horizontal_flip=False, convert_image_to=None)
```

`Dataset` recursively scans image files, resizes/crops to `image_size`, converts mode when requested, and returns tensors in `[0, 1]`.

```python
Trainer(diffusion_model, folder, train_batch_size=16, gradient_accumulate_every=1,
        augment_horizontal_flip=True, train_lr=1e-4, train_num_steps=100000,
        ema_update_every=10, ema_decay=0.995, save_and_sample_every=1000,
        num_samples=25, results_folder='./results', amp=False,
        mixed_precision_type='fp16', split_batches=True, convert_image_to=None,
        calculate_fid=True, inception_block_idx=2048, max_grad_norm=1.0,
        num_fid_samples=50000, save_best_and_latest_only=False)
```

Hard gates enforced by `Trainer`:

- `num_samples` must have an integer square root.
- `train_batch_size * gradient_accumulate_every >= 16`.
- Folder must contain at least 100 matching images.
- `save_best_and_latest_only=True` requires `calculate_fid=True`.

## FID and RePaint notes

`FIDEvaluation` depends on `pytorch-fid`, can be slow, caches real dataset statistics as `dataset_stats.npz`, and repeats one-channel images to 3 channels before Inception features.

RePaint uses similarly named classes in `denoising_diffusion_pytorch.repaint`. Its `sample(batch_size, gt=None, mask=None, resample=True, resample_iter=10, resample_jump=10, resample_every=50)` keeps `mask == 1` regions from `gt` and regenerates `mask == 0` regions. `gt` should be BCHW in `[0, 1]`; a `(batch, 1, H, W)` mask broadcasts across channels.
