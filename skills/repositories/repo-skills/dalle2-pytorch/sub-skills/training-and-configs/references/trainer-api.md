# Trainer API

This page covers direct Python training APIs from `dalle2_pytorch` 1.15.6. Use it when a task is building a custom loop, loading a checkpoint manually, or diagnosing trainer state rather than launching from JSON.

## Imports

```python
from dalle2_pytorch import DecoderTrainer, DiffusionPriorTrainer
from dalle2_pytorch import Decoder, DiffusionPrior, DiffusionPriorNetwork, Unet
```

For config-driven construction:

```python
from dalle2_pytorch.train_configs import TrainDecoderConfig, TrainDiffusionPriorConfig
```

## `DecoderTrainer`

Verified constructor shape:

```python
DecoderTrainer(
    decoder,
    accelerator=None,
    dataloaders=None,
    use_ema=True,
    lr=0.0001,
    wd=0.01,
    eps=1e-8,
    warmup_steps=None,
    cosine_decay_max_steps=None,
    max_grad_norm=0.5,
    amp=False,
    group_wd_params=True,
    **kwargs,
)
```

Key behavior:

- `decoder` must be a `dalle2_pytorch.Decoder` instance.
- If `accelerator` is not supplied, a Hugging Face `Accelerator()` is created.
- One optimizer and scheduler are created per UNet. Scalar `lr`, `wd`, `eps`, `warmup_steps`, and `cosine_decay_max_steps` are broadcast across UNets; tuple/list values can tune per UNet.
- Learning rates above `1e-2` are rejected.
- `dataloaders`, when provided, should include at least `"train"` and `"val"`; those loaders are prepared by Accelerate.
- EMA modules are maintained per UNet when `use_ema=True`. `sample()` uses EMA UNets by default unless `use_non_ema=True` is passed.
- DeepSpeed with a decoder-side CLIP adapter requires float32 precision for on-the-fly CLIP embedding generation. DeepSpeed fp16 plus learned variance is blocked by the bundled decoder launcher.

### Minimal direct decoder update

```python
import torch
from dalle2_pytorch import Decoder, DecoderTrainer, Unet

unet = Unet(dim=16, image_embed_dim=32, cond_dim=16, dim_mults=(1, 2), channels=3)
decoder = Decoder(unet=unet, image_size=32, timesteps=4, learned_variance=False)
trainer = DecoderTrainer(decoder, lr=1e-4, wd=0.01, use_ema=True)

images = torch.randn(2, 3, 32, 32)
image_embed = torch.randn(2, 32)
loss = trainer(images, image_embed=image_embed, unet_number=1)
trainer.update(unet_number=1)
```

If the decoder has multiple UNets, always pass `unet_number` to `forward()`/`__call__()` and to `update()`. For gradient accumulation, pass `max_batch_size` to the forward call.

### Decoder save/load

```python
trainer.save("decoder-checkpoint.pth", overwrite=True, epoch=0)
loaded = trainer.load("decoder-checkpoint.pth", only_model=False, strict=True)
```

Checkpoint contents include the decoder model state, package version, per-UNET steps, per-UNET optimizer/scheduler states, EMA state when enabled, and any extra metadata. Loading warns when the checkpoint package version differs from the current package.

For model-only loading, use `only_model=True` to skip optimizer, scheduler, and EMA state. For config-launcher resume, use the `tracker.load` section instead of calling `load()` directly.

## `DiffusionPriorTrainer`

Verified constructor shape:

```python
DiffusionPriorTrainer(
    diffusion_prior,
    accelerator=None,
    use_ema=True,
    lr=0.0003,
    wd=0.01,
    eps=1e-6,
    max_grad_norm=None,
    group_wd_params=True,
    warmup_steps=None,
    cosine_decay_max_steps=None,
    **kwargs,
)
```

Key behavior:

- `diffusion_prior` must be a `dalle2_pytorch.DiffusionPrior` instance.
- If `accelerator` is not supplied, a Hugging Face `Accelerator()` is created.
- The trainer prepares the prior, optimizer, and scheduler with Accelerate.
- `use_ema=True` creates `ema_diffusion_prior`; `sample()` and `p_sample_loop()` use the EMA model when available.
- `max_grad_norm` enables Accelerate gradient clipping before optimizer step.
- DeepSpeed with an attached CLIP adapter asserts float32 precision for on-the-fly CLIP embedding generation.

### Minimal direct prior update with precomputed embeddings

```python
import torch
from dalle2_pytorch import DiffusionPrior, DiffusionPriorNetwork, DiffusionPriorTrainer

net = DiffusionPriorNetwork(dim=32, depth=1, num_timesteps=4, max_text_len=8)
prior = DiffusionPrior(
    net=net,
    image_embed_dim=32,
    image_size=32,
    timesteps=4,
    sample_timesteps=4,
    condition_on_text_encodings=False,
)
trainer = DiffusionPriorTrainer(prior, lr=3e-4, wd=0.01, use_ema=True)

image_embed = torch.randn(2, 32)
text_embed = torch.randn(2, 32)
loss = trainer(text_embed=text_embed, image_embed=image_embed)
trainer.update()
```

This direct API supports precomputed `text_embed` and `image_embed`. The bundled JSON prior launcher is narrower: it expects image embeddings plus caption metadata and uses a CLIP adapter to tokenize/embed text when `condition_on_text_encodings=True`.

### Prior save/load

```python
trainer.save("prior-checkpoint.pth", overwrite=True, epoch=0)
loaded = trainer.load("prior-checkpoint.pth", overwrite_lr=True, strict=True)
```

Checkpoint contents include optimizer, scheduler, optional warmup scheduler, unwrapped prior model, package version, step tensor, and EMA state when enabled. Loading prints a warning when the saved version differs from the current package version. With `overwrite_lr=True`, the trainer keeps the new constructor learning rate instead of the checkpoint learning rate.

## Tracker-Mediated Checkpointing and Resume

The config launchers use `TrackerConfig` rather than direct `save()` calls:

- `tracker.log`: `console` or `wandb` logger.
- `tracker.load`: optional `local`, `url`, or `wandb` loader.
- `tracker.save`: one saver or a list of savers: `local`, `wandb`, or `huggingface`.

Resume flow:

1. The tracker initializes logger/loader/savers.
2. If `tracker.can_recall` is true, the launcher calls `tracker.recall()`.
3. Decoder recall restores epoch/task/sample counters plus trainer state with `strict=True`.
4. Prior recall restores `current_epoch`, `best_validation_loss`, and `num_samples_seen`, then adjusts the reader start position to finish the resumed epoch.

For first-pass debugging, avoid remote loaders/savers and use local checkpoint paths. Route credentialed W&B/HuggingFace behavior to `../data-and-tracking/`.

## Metrics During Training

Decoder launcher:

- Logs per-UNET training loss and EMA decay.
- Runs validation loss by UNET.
- Optionally computes FID, IS, KID, and LPIPS when enabled in `evaluate`.
- Saves snapshots every `train.save_every_n_samples` and at epoch sampling points.

Prior launcher:

- Uses `EmbeddingReader` data and tracks samples/sec, samples seen, EMA decay, and training loss.
- Periodically logs online and EMA validation loss.
- Tracks cosine-style metrics during evaluation: baseline similarity, similarity with text, similarity with original image, similarity with unrelated caption, and difference from baseline.
- Saves latest checkpoints on a timed schedule and best checkpoints when validation/test loss improves.
