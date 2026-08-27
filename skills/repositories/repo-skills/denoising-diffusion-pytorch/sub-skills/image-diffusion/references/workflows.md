# Image Diffusion Workflows

These workflows are safe operating patterns for `denoising-diffusion-pytorch` 2D image tasks. They use public package imports and bundled skill scripts.

## Install and import

```bash
python -m pip install denoising-diffusion-pytorch
python - <<'PYCODE'
from importlib.metadata import version
from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Trainer
print(version('denoising-diffusion-pytorch'))
PYCODE
```

## Tiny smoke before real training

From the generated skill root:

```bash
python sub-skills/image-diffusion/scripts/smoke_image_diffusion.py --quick --device cpu
```

Equivalent minimal code:

```python
import torch
from denoising_diffusion_pytorch import Unet, GaussianDiffusion

torch.manual_seed(0)
model = Unet(dim=8, dim_mults=(1,), channels=1, flash_attn=False)
diffusion = GaussianDiffusion(model, image_size=8, timesteps=8,
                              sampling_timesteps=4, beta_schedule='sigmoid')
images = torch.rand(1, 1, 8, 8)
loss = diffusion(images)
assert torch.isfinite(loss).item()
samples = diffusion.sample(batch_size=1)
assert samples.shape == (1, 1, 8, 8)
```

Why these defaults: `dim_mults=(1,)` avoids downsample divisibility surprises, `timesteps=8` with `sampling_timesteps=4` checks DDIM sampling, and `'sigmoid'` avoids a known tiny linear-schedule NaN edge.

## Adapt the public image tensor recipe

```python
import torch
from denoising_diffusion_pytorch import Unet, GaussianDiffusion

model = Unet(dim=64, dim_mults=(1, 2, 4, 8), channels=3, flash_attn=False)
diffusion = GaussianDiffusion(model, image_size=128, timesteps=1000,
                              sampling_timesteps=250, beta_schedule='sigmoid')
training_images = torch.rand(8, 3, 128, 128)  # values in [0, 1]
loss = diffusion(training_images)
loss.backward()

# after real training, not as a quality check from random weights
sampled_images = diffusion.sample(batch_size=4)
assert sampled_images.shape == (4, 3, 128, 128)
```

Do not judge quality from an untrained model; immediate samples only validate shape and runtime.

## Choose DDPM vs DDIM

`sample()` chooses its loop from `sampling_timesteps`:

- `None` or equal to `timesteps`: full DDPM ancestral sampling.
- Smaller than `timesteps`: DDIM sampling.

`ddim_sampling_eta=0.0` removes DDIM noise in the denoising transition, but model initialization and starting noise still affect output unless seeds are controlled.

## Image folder training

```python
from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Trainer

model = Unet(dim=64, dim_mults=(1, 2, 4, 8), channels=3, flash_attn=False)
diffusion = GaussianDiffusion(model, image_size=128, timesteps=1000,
                              sampling_timesteps=250)
trainer = Trainer(diffusion, 'data/images', train_batch_size=16,
                  gradient_accumulate_every=1, train_lr=8e-5,
                  train_num_steps=700000, ema_decay=0.995,
                  amp=False, calculate_fid=False, results_folder='./results')
trainer.train()
```

Before constructing `Trainer`, verify at least 100 matching image files, effective batch size at least 16, square `num_samples`, consistent image mode/channels, and an explicit decision about FID.

For multi-GPU training, place the code in a script and use the public Accelerate workflow:

```bash
accelerate config
accelerate launch train.py
```

## FID workflow

Keep FID off for smoke tests. When enabling it, prefer DDIM sampling and budget for generated samples:

```python
trainer = Trainer(diffusion, 'data/images', train_batch_size=32,
                  calculate_fid=True, num_fid_samples=50000,
                  inception_block_idx=2048, save_best_and_latest_only=True)
```

`save_best_and_latest_only=True` requires `calculate_fid=True` because FID is the metric used for best/latest selection.

## RePaint inpainting

```python
import torch
from denoising_diffusion_pytorch.repaint import Unet, GaussianDiffusion

model = Unet(dim=64, dim_mults=(1, 2, 4, 8), channels=3)
diffusion = GaussianDiffusion(model, image_size=128, timesteps=1000)
gt = torch.rand(2, 3, 128, 128, device=diffusion.device)
mask = torch.zeros(2, 1, 128, 128, device=diffusion.device)
mask[:, :, :, :64] = 1.0
out = diffusion.sample(gt=gt, mask=mask, resample=True,
                       resample_iter=10, resample_jump=10, resample_every=50)
assert out.shape == gt.shape
```

Use mask value `1` where ground truth should be preserved and `0` where the model should regenerate. For a quick validation set `resample=False`; for quality use resampling and budget for extra runtime.
