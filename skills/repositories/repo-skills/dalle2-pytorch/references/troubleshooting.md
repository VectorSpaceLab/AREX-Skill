# DALLE2-pytorch cross-cutting troubleshooting

Use this root troubleshooting reference for install/import/backend issues that can affect more than one sub-skill.

## Install and import check fails

Start with:

```bash
python -m pip install dalle2-pytorch
python -m pip check
python scripts/check_install.py --mode imports
```

If `torch` or `torchvision` import fails, install a compatible pair for the user's backend. CPU wheels are enough for config validation and tiny smoke tests; CUDA wheels are needed for real GPU workloads.

## `pkg_resources` is missing

Symptom:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

Cause: `clip-anytorch` imports `pkg_resources`; newer setuptools versions may not provide it.

Fix:

```bash
python -m pip install 'setuptools<81'
python -m pip check
```

A deprecation warning from `pkg_resources` is acceptable when imports and CLI help pass.

## CLIP adapter downloads or offline failures

Symptoms: adapter construction hangs, fails with HTTP/cache errors, or cannot find model weights.

Causes:

- `OpenAIClipAdapter` uses the `clip-anytorch` OpenAI CLIP loader.
- `OpenClipAdapter` uses `open-clip-torch` model/pretrained pairs.
- First use may download weights.

Fixes:

- Use `scripts/check_install.py --mode imports`, not adapter construction, for offline smoke checks.
- Pre-populate model caches or enable network access before constructing adapters.
- For training with precomputed embeddings, avoid CLIP adapter construction in the config.

## CPU and GPU confusion

CPU can verify:

- Package imports.
- `dream --help`.
- JSON config parsing.
- Tiny synthetic prior/decoder forward-loss checks.

GPU is normally needed for:

- Useful CLIP encoding and prior sampling.
- Decoder image sampling or inpainting at meaningful resolutions.
- Training decoder/prior/VQGAN models.
- Large cascaded decoders and high-resolution latent diffusion.

Do not present CPU smoke success as proof that real GPU training/generation will fit memory or run fast.

## Checkpoint does not load

Determine checkpoint format first:

- `dream` combined checkpoint: should contain `version`, `init_params.prior`, `init_params.decoder`, and `model_params`.
- Trainer checkpoint: contains optimizer/scheduler/EMA/scaler/step/version plus model state, and should be loaded through `DecoderTrainer.load` or `DiffusionPriorTrainer.load`.

If architecture keys or tensor shapes mismatch, recreate the exact prior/decoder/trainer config used for training. Pay special attention to Unet count/order, `image_sizes`, VAE settings, learned variance, prior network dimensions, and conditioning flags.

## External services fail

W&B, HuggingFace, S3, URL loaders, CLIP weight downloads, and image metrics require network, credentials, or caches. Switch to console/local logging and disable metric blocks for first validation. Route provider-specific tracker setup to `sub-skills/data-and-tracking/SKILL.md`.

## Where to go next

- Generation/model API issue: `sub-skills/generation-and-api/SKILL.md`.
- Config/training launcher/trainer issue: `sub-skills/training-and-configs/SKILL.md`.
- Data layout/tracker/checkpoint-destination issue: `sub-skills/data-and-tracking/SKILL.md`.
