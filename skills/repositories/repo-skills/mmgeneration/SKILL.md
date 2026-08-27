---
name: "mmgeneration"
description: "Routes MMGeneration tasks across sampling, training, evaluation,
  configuration, and latent-editing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMGeneration

MMGeneration is OpenMMLab's generative-model toolkit for GANs, translation models, SinGAN, and diffusion workflows.

Use this repo skill when the task mentions `mmgen`, MMGeneration, one of the model families below, or the repo's train/eval/demo/application scripts.

## Start here

1. Read `references/installation-and-compatibility.md` if the environment is not already verified.
2. Read `references/repo-provenance.md` when you need to check whether this skill still matches the current checkout.
3. Use the route map below to choose the right sub-skill.
4. Use `scripts/check_install.py` for a fast import and backend smoke check.

## Installation and verification

MMGeneration depends on a compatible PyTorch wheel, `mmcv-full` in the 1.x line, and `mmcls` in the 0.x line.
A practical install order is:

1. Install PyTorch and torchvision.
2. Install a matching `mmcv-full` wheel for that torch/CUDA combination.
3. Install `mmcls<1.0.0` and the runtime requirements used by this repo.
4. Install the repo itself in editable mode when working from a checkout.
5. Run `python scripts/check_install.py`.

For detailed compatibility notes, backend guidance, and common failure modes, read `references/installation-and-compatibility.md` and `references/troubleshooting.md`.

## Route map

| Sub-skill | Use it for | Typical signals |
| --- | --- | --- |
| `sub-skills/inference-and-sampling/` | Load a generator and sample unconditional, conditional, translation, or DDPM outputs | `init_model`, `sample_unconditional_model`, `sample_img2img_model`, demo scripts, sample shapes, device selection |
| `sub-skills/training-and-distribution/` | Train or resume configs, choose launcher mode, or debug distributed training | `tools/train.py`, `dist_train.sh`, `slurm_train.sh`, `DynamicIterBasedRunner`, EMA, CPU training, DDP wrapper |
| `sub-skills/evaluation-and-metrics/` | Run evaluation, precompute inception stats, or reason about FID/IS/PPL/SWD/PR/MS-SSIM | `tools/evaluation.py`, `inception_stat.py`, `translation_eval.py`, metrics, online/offline evaluation |
| `sub-skills/configuration-and-extension/` | Edit configs, define datasets/pipelines, register new models/losses/hooks, or inspect config expansion | `_base_`, `_delete_`, `custom_imports`, `cfg-options`, registries, dataset layouts, `print_config.py` |
| `sub-skills/applications-and-deployment/` | Latent interpolation, projection, SeFa, StyleCLIP, or TorchServe packaging | `apps/`, `mmgen2torchserver.py`, `projector.py`, `modified_sefa.py`, `styleclip.py` |

## Public model families

MMGeneration's supported workflows cluster around these families:

- Unconditional GANs: DCGAN, LSGAN, WGAN-GP, PGGAN, StyleGANv1/v2/v3, MS-PIE StyleGAN2, ADA.
- Conditional GANs: SNGAN/Projection GAN, SAGAN, BigGAN, BigGAN-Deep.
- Image translation: Pix2Pix and CycleGAN.
- Internal learning: SinGAN and PESinGAN.
- Diffusion: Improved DDPM.

See `references/model-overview.md` for the repo-facing model map and where each family lives.

## Key public APIs

The installed package exposes `mmgen.apis` helpers for model loading and sampling, `mmgen.models` builders and registries, `mmgen.datasets` builders and dataset classes, and `mmgen.core` evaluation, hook, optimizer, and runner utilities.
Read `references/api-reference.md` for verified signatures and `references/data-formats.md` for dataset layouts and pipeline keys.

## CLI and command references

The repo does not define a console entry point; use the repository scripts directly.
Read `references/cli-reference.md` for the main command families and flag meanings.

## Shared helpers

- `scripts/check_install.py` — verify that the installed package imports, the public modules are visible, and the expected backend is usable.
- `sub-skills/configuration-and-extension/scripts/print_config.py` — print a fully resolved config with optional overrides.
- `sub-skills/inference-and-sampling/scripts/sample_mmgen.py` — run a safe sampling helper across the common inference modes.

## Troubleshooting

If a workflow fails, start with `references/troubleshooting.md`. The most common issues are:

- `mmcv.runner` import failures from an incompatible MMCV version.
- `mmcv.ops`/CUDA extension problems from the wrong wheel or missing GPU runtime.
- `styleclip.py` requiring the optional `clip` package.
- Dataset layout mismatches for paired or unpaired translation data.
- Metric/extraction commands that need cached inception or VGG assets.

## Provenance

When the repo changes, compare it with `references/repo-provenance.md` before reusing this skill.
