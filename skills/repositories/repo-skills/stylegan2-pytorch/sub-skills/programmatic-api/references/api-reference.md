# Programmatic API Reference

## When to read

Read this when writing Python code against `stylegan2_pytorch` rather than using
the CLI. Signatures were verified from an installed package environment for
version `1.9.0`.

## Public package exports

The package root exports:

```python
from stylegan2_pytorch import Trainer, StyleGAN2, NanException, ModelLoader
```

Importing these requires CUDA because the main module asserts
`torch.cuda.is_available()` at import time.

## `ModelLoader`

```python
ModelLoader(*, base_dir, name='default', load_from=-1)
```

- `base_dir`: directory where the CLI run used the default layout. `ModelLoader`
  creates `Trainer(name=name, base_dir=base_dir)`, so it expects checkpoints at
  `base_dir/models/<name>/model_<n>.pt` and config at
  `base_dir/models/<name>/.config.json`.
- `name`: project/run name, matching the CLI `--name` value.
- `load_from`: checkpoint number. `-1` means latest available.

Methods:

```python
ModelLoader.noise_to_styles(self, noise, trunc_psi=None)
ModelLoader.styles_to_images(self, w)
```

Operational notes:

- `noise_to_styles` calls `noise.cuda()` and uses the moving-average style
  network (`GAN.SE`).
- The latent dimension is `512` in this source snapshot.
- `styles_to_images` uses the moving-average generator (`GAN.GE`), builds image
  noise on CUDA device `0`, clamps outputs to `[0, 1]`, and returns a tensor.
- If no checkpoint exists, `Trainer.load(-1)` returns without initializing a
  usable GAN, so later sampling calls fail. Check for `model_*.pt` first.

## `Trainer`

Verified constructor signature:

```python
Trainer(
    name='default', results_dir='results', models_dir='models', base_dir='./',
    image_size=128, network_capacity=16, fmap_max=512, transparent=False,
    batch_size=4, mixed_prob=0.9, gradient_accumulate_every=1, lr=0.0002,
    lr_mlp=0.1, ttur_mult=2, rel_disc_loss=False, num_workers=None,
    save_every=1000, evaluate_every=1000, num_image_tiles=8, trunc_psi=0.6,
    fp16=False, cl_reg=False, no_pl_reg=False, fq_layers=[], fq_dict_size=256,
    attn_layers=[], no_const=False, aug_prob=0.0,
    aug_types=['translation', 'cutout'], top_k_training=False,
    generator_top_k_gamma=0.99, generator_top_k_frac=0.5,
    dual_contrast_loss=False, dataset_aug_prob=0.0, calculate_fid_every=None,
    calculate_fid_num_images=12800, clear_fid_cache=False, is_ddp=False,
    rank=0, world_size=1, log=False, *args, **kwargs
)
```

Important methods/behavior:

- `set_data_src(folder)` scans recursive `.jpg`, `.jpeg`, `.png` images and
  creates the DataLoader.
- `train()` runs one trainer step and increments `steps`.
- `evaluate(num=0, trunc=1.0)` writes sample grids to `results/<name>/`.
- `generate_interpolation(num=0, num_image_tiles=8, trunc=1.0, num_steps=100,
  save_frames=False)` writes a GIF and optionally frame images.
- `save(num)` writes `models/<name>/model_<num>.pt` and `.config.json`.
- `load(num=-1)` loads `.config.json`, then latest or requested checkpoint.

Prefer the CLI for ordinary training because it handles resume, retry-on-NaN,
progress display, generation modes, and DDP spawning around `Trainer`.

## `StyleGAN2`

Verified constructor summary:

```python
StyleGAN2(
    image_size, latent_dim=512, fmap_max=512, style_depth=8,
    network_capacity=16, transparent=False, fp16=False, cl_reg=False,
    steps=1, lr=0.0001, ttur_mult=2, fq_layers=[], fq_dict_size=256,
    attn_layers=[], no_const=False, lr_mlp=0.1, rank=0
)
```

It constructs the style vectorizer, generator, discriminator, EMA copies, CUDA
modules, and optimizers. Use it directly only for advanced experiments; most
users should use `Trainer` or the CLI.

## Checkpoint compatibility

Checkpoints store:

- model state under key `GAN`
- package `version`
- optional Apex AMP state when fp16 was used

If `load()` cannot load the model state, the source prints guidance to downgrade
to the version specified by the saved model before re-raising the error. When
user prompts mention old checkpoints, preserve version and architecture settings
before suggesting code changes.
