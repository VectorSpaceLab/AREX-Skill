# Inference and Sampling Workflows

## Purpose

Use this reference when a user wants to load a checkpoint and generate images without entering a training loop.

## Public API path

Verified signatures from the installed package:

- `init_model(config, checkpoint=None, device='cuda:0', cfg_options=None)`
- `sample_unconditional_model(model, num_samples=16, num_batches=4, sample_model='ema', **kwargs)`
- `sample_conditional_model(model, num_samples=16, num_batches=4, sample_model='ema', label=None, **kwargs)`
- `sample_img2img_model(model, image_path, target_domain=None, **kwargs)`
- `sample_ddpm_model(model, num_samples=16, num_batches=4, sample_model='ema', same_noise=False, **kwargs)`

## Standard flow

1. Pick a config family from `model-overview.md`.
2. Load the model with `init_model`.
3. Choose the sampling helper that matches the model class.
4. Save the returned tensor or dict for inspection.

## Unconditional sampling

Use this for DCGAN/LSGAN/WGAN-GP/PGGAN/StyleGAN-family checkpoints when you only need generated images.

Common knobs:

- `num_samples`
- `num_batches`
- `sample_model='ema'` or `'orig'`
- optional sampling kwargs forwarded to the model

Expected output:

- A tensor with shape like `N x 3 x H x W`.

## Conditional sampling

Use this for SNGAN, SAGAN, BigGAN, or other label-conditioned models.

Key rule:

- `label` can be a single integer, a tensor, or a list of integers.
- A multi-label list must match `num_samples` unless it is a single label that can be repeated.

## Image-to-image translation

Use this for Pix2Pix and CycleGAN-style models.

Important points:

- `sample_img2img_model` expects a `BaseTranslationModel` subclass.
- The helper infers the source domain from the target domain.
- `image_path` should point to a single input image; the model's test pipeline handles the rest.

## DDPM sampling

Use this for `BasicGaussianDiffusion`-style configs.

Important points:

- `same_noise=True` reuses one initial noise tensor across batches.
- `save_intermedia=True` or similar kwargs can make the result a dict rather than a single tensor.
- Diffusion configs often need a smaller `num_timesteps` for smoke checks.

## Bundled helper

`sub-skills/inference-and-sampling/scripts/sample_mmgen.py` wraps the four main modes in one safe CLI.

Suggested patterns:

```bash
python sub-skills/inference-and-sampling/scripts/sample_mmgen.py cfg.py ckpt.pth \
    --mode unconditional --num-samples 8 --out-dir out/
```

```bash
python sub-skills/inference-and-sampling/scripts/sample_mmgen.py cfg.py ckpt.pth \
    --mode translation --image-path demo.png --target-domain photo
```

## Evidence sources

- `mmgen/apis/inference.py`
- `demo/*.py`
- `tests/test_apis/test_inference.py`
- `docs/en/tutorials/applications.md`
- `docs/en/get_started.md`
