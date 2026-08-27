# 1D Sequence Workflows

Use these workflows to build, validate, sample from, interpolate with, and train standard 1D sequence diffusion models using the public `denoising_diffusion_pytorch` API.

## Install and import check

```bash
python -m pip install denoising-diffusion-pytorch
python - <<'PYCODE'
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D, Dataset1D, Trainer1D
print('1D sequence diffusion imports ok')
PYCODE
```

From the generated skill root, run:

```bash
python sub-skills/sequence-diffusion/scripts/smoke_sequence_diffusion.py --quick --device cpu
python sub-skills/sequence-diffusion/scripts/smoke_sequence_diffusion.py --quick --device cpu --channel-last
```

## Tiny loss and sampling workflow

```python
import torch
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D

channels = 2
seq_length = 8
model = Unet1D(dim=8, dim_mults=(1,), channels=channels)
diffusion = GaussianDiffusion1D(model, seq_length=seq_length, timesteps=8,
                                sampling_timesteps=4, objective='pred_noise',
                                beta_schedule='cosine')
x = torch.rand(2, channels, seq_length)
loss = diffusion(x)
sample = diffusion.sample(batch_size=2)
assert sample.shape == (2, channels, seq_length)
```

For real training, increase `dim`, `dim_mults`, `timesteps`, dataset size, and `train_num_steps` only after the small check passes.

## Channel-first versus channel-last data

Recommended path: convert user data to channel-first before calling the public `Unet1D`.

```python
x_channel_last = torch.rand(4, 128, 32)
x_channel_first = x_channel_last.transpose(1, 2).contiguous()
model = Unet1D(dim=64, dim_mults=(1, 2, 4, 8), channels=32)
diffusion = GaussianDiffusion1D(model, seq_length=128, channel_first=True)
loss = diffusion(x_channel_first)
```

If the pipeline must keep `(batch, seq_length, channels)`, pass `channel_first=False` and wrap the model so it transposes internally. The bundled smoke script includes this adapter. Do not set `channel_first=False` with a bare public `Unet1D`; `Conv1d` will interpret the length axis as channels.

## Objective and schedule choices

- `objective='pred_noise'` is the constructor default.
- `objective='pred_v'` follows the public 1D example and v-parameterization experiments.
- `objective='pred_x0'` predicts the denoised sequence directly.
- `beta_schedule='cosine'` is the default; use `'linear'` only when matching a trained configuration.
- Keep `sampling_timesteps <= timesteps`; lower values select DDIM-style sampling.

## `Dataset1D` and `Trainer1D` recipe

```python
import torch
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D, Dataset1D, Trainer1D

training_seq = torch.rand(64, 32, 128)
dataset = Dataset1D(training_seq)
model = Unet1D(dim=64, dim_mults=(1, 2, 4, 8), channels=32)
diffusion = GaussianDiffusion1D(model, seq_length=128, timesteps=1000, objective='pred_v')
trainer = Trainer1D(diffusion, dataset=dataset, train_batch_size=32,
                    train_lr=8e-5, train_num_steps=700000,
                    gradient_accumulate_every=2, ema_decay=0.995,
                    amp=True, num_samples=25, results_folder='./results-sequence')
# trainer.train()  # run only when the user explicitly wants training
```

For multi-GPU or mixed-precision launches, place training code in a script and run `accelerate config` then `accelerate launch train_sequence.py`. `Trainer1D` has no built-in sequence metric; add task-specific evaluation outside the trainer loop.
