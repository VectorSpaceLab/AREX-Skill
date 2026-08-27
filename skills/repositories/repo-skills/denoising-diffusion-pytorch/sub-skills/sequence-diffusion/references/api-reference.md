# 1D Sequence API Reference

Use this reference to choose public 1D APIs, tensor layouts, diffusion hyperparameters, and method calls for `denoising-diffusion-pytorch` 2.3.1.

## Public imports

```python
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D, Dataset1D, Trainer1D
```

## Tensor layout contract

| Setting | Data shape expected by `GaussianDiffusion1D.forward` | Sample shape | Practical model requirement |
| --- | --- | --- | --- |
| `channel_first=True` (default) | `(batch, channels, seq_length)` | `(batch, channels, seq_length)` | Matches public `Unet1D`, which uses `Conv1d`. |
| `channel_first=False` | `(batch, seq_length, channels)` | `(batch, seq_length, channels)` | Requires a model wrapper or custom model that accepts and returns channel-last tensors. |

`GaussianDiffusion1D` checks sequence length at `img.shape[-1]` when `channel_first=True`, and at `img.shape[-2]` when `channel_first=False`.

## `Unet1D`

```python
Unet1D(dim, init_dim=None, out_dim=None, dim_mults=(1, 2, 4, 8), channels=3,
       dropout=0.0, self_condition=False, learned_variance=False,
       learned_sinusoidal_cond=False, random_fourier_features=False,
       learned_sinusoidal_dim=16, sinusoidal_pos_emb_theta=10000,
       attn_dim_head=32, attn_heads=4)
```

Forward call: `model(x, time, x_self_cond=None)`.

- `channels` is the number of sequence feature channels, not the sequence length.
- The default `out_dim` is `channels`, or `channels * 2` if `learned_variance=True`.
- In version 2.3.1, some self-conditioning paths use the keyword `self_cond`, while public `Unet1D.forward` accepts `x_self_cond`. Prefer `self_condition=False` with the public `Unet1D`, or wrap the model to accept both names.

## `GaussianDiffusion1D`

```python
GaussianDiffusion1D(model, *, seq_length, timesteps=1000, sampling_timesteps=None,
                    objective='pred_noise', beta_schedule='cosine', ddim_sampling_eta=0.0,
                    auto_normalize=True, channels=None, self_condition=None,
                    channel_first=True)
```

| Parameter | Valid values / behavior |
| --- | --- |
| `seq_length` | Required integer; asserted against each input batch. Pad/crop/bucket variable-length data outside this wrapper. |
| `objective` | `'pred_noise'`, `'pred_x0'`, or `'pred_v'`. |
| `beta_schedule` | `'cosine'` or `'linear'`. |
| `sampling_timesteps` | Defaults to `timesteps`; must be `<= timesteps`; smaller values use DDIM-style sampling. |
| `auto_normalize` | Maps inputs from `[0, 1]` to `[-1, 1]` for loss and maps samples back toward `[0, 1]`. |

Common methods:

```python
loss = diffusion(x, times=None, loss_reduction='mean')
per_sample = diffusion(x, loss_reduction='none')
times = diffusion.random_times(batch_size)
sample = diffusion.sample(batch_size=16, return_noise=False)
sample, start_noise = diffusion.sample(batch_size=16, return_noise=True)
interp = diffusion.interpolate(x1, x2, t=None, lam=0.5)
```

## `Dataset1D` and `Trainer1D`

`Dataset1D(tensor)` clones the input tensor and returns cloned items. It does not load files, normalize, resample, or compute metrics.

`Trainer1D(diffusion_model, dataset, train_batch_size=16, gradient_accumulate_every=1, train_lr=1e-4, train_num_steps=100000, ema_update_every=10, ema_decay=0.995, adam_betas=(0.9, 0.99), save_and_sample_every=1000, num_samples=25, results_folder='./results', amp=False, mixed_precision_type='fp16', split_batches=True, max_grad_norm=1.0)` uses Accelerate internally. `num_samples` must have an integer square root. It saves checkpoints and tensor samples but does not compute FID or any sequence metric.
