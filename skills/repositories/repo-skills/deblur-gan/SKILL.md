---
name: deblur-gan
description: "Route DeblurGAN users to data preparation, training, and
  single-image inference workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# DeblurGAN

DeblurGAN is a PyTorch image deblurring repo for learning a blur-to-sharp mapping from paired data. Use this skill when the task is about preparing paired images, training the conditional GAN, or restoring single images from a checkpoint.

## Start here

- Read `references/installation.md` if the environment is not ready.
- Run `scripts/check_deblurgan_env.py --repo-root <local DeblurGAN checkout> --cuda` for a CUDA smoke check, or omit `--cuda` if you only need import inspection.
- Use the sub-skill that matches the workflow:
  - `sub-skills/data-preparation/SKILL.md` for pair creation and layout checks.
  - `sub-skills/training/SKILL.md` for optimization, checkpoints, and loss configuration.
  - `sub-skills/inference/SKILL.md` for restoring images and HTML result export.

## What this skill expects

- Python 3.11.
- No packaging metadata is present in this checkout, so dependencies are installed manually. A practical baseline is a CUDA-enabled PyTorch/TorchVision build plus `dominate` and `opencv-python-headless`; add `ssim` only if you want to run the source `test.py` verbatim and `visdom` only if you want live training plots. See `references/installation.md` for copyable commands.
- Training and the perceptual-loss path require a CUDA-enabled PyTorch build.
- Inference and data-preparation can use CPU-only import checks, but the generated wrappers still expect the repo modules to be importable.

## Common workflows

### Prepare data
Use the data-preparation sub-skill when you have separate blur and sharp image trees or when you need to understand the `aligned` and `single` layouts.

### Train
Use the training sub-skill when you need to configure `content_gan`, `pix2pix`, `gan`, `lsgan`, or `wgan-gp`, create checkpoints, or run a smoke-sized optimization pass.

### Restore images
Use the inference sub-skill when you need to load `latest_net_G.pth`, restore a folder of images, or generate the HTML gallery under `results/<name>/<phase>_<epoch>/`.

## Shared conventions

- Training checkpoints are written under `checkpoints/<name>/`.
- Inference results are written under `results/<name>/<phase>_<which_epoch>/`.
- The local metric helpers live in `util/metrics.py`; the shipped `test.py` also references an external `ssim` package, so prefer the bundled inference wrapper.
- The repository's `unaligned` dataset stub and legacy `motion_blur/` helpers are not primary routes for this skill.

## Shared references

- `references/api-reference.md` for verified signatures and object roles.
- `references/workflows.md` for portable command patterns.
- `references/troubleshooting.md` for cross-cutting failures and recovery steps.
- `references/repo-provenance.md` and `references/repo-routing-metadata.json` for refresh and router metadata.
