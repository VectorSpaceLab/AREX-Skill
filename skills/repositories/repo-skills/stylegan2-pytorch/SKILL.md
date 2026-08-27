---
name: stylegan2-pytorch
description: "Guides StyleGAN2 PyTorch image GAN training, checkpoint
  generation, interpolation, and programmatic sampling with the
  stylegan2_pytorch package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# StyleGAN2 PyTorch Repo Skill

Use this repo skill when a task involves the `stylegan2_pytorch` package, the
`stylegan2_pytorch` command, or StyleGAN2-style image GAN training/sampling in
this implementation. The package is CUDA-first: importing the main module
asserts that `torch.cuda.is_available()` is true, so do not plan CPU-only use.

## Fast routing

- Use [training](sub-skills/training/SKILL.md) for command-line training from an
  image folder, checkpoint resume/restart decisions, sample generation,
  interpolation GIFs, low-data augmentation, FID/logging options, transparent
  images, attention/vector-quantization knobs, and multi-GPU settings.
- Use [programmatic-api](sub-skills/programmatic-api/SKILL.md) when the user
  wants Python code with `ModelLoader`, `Trainer`, or `StyleGAN2`, especially
  loading a trained checkpoint and saving generated images from tensors.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an
  install, import, CUDA, optional dependency, CLI parsing, checkpoint, or
  package-version failure blocks either workflow.
- Read [references/repo-provenance.md](references/repo-provenance.md) before
  deciding whether this skill is stale for a checkout or should be refreshed.

## Package facts to keep in mind

- Distribution name and import name: `stylegan2_pytorch`.
- Console command: `stylegan2_pytorch`.
- Public exports from the package root: `Trainer`, `StyleGAN2`, `ModelLoader`,
  and `NanException`.
- The core CLI is implemented with Python Fire around `train_from_folder`, so
  Fire help displays underscore flag names even though the README commonly shows
  hyphenated flag names.
- Training inputs are recursive image folders containing `.jpg`, `.jpeg`, or
  `.png` files.
- Default outputs are `results/<name>/` for generated images and
  `models/<name>/model_<n>.pt` plus `models/<name>/.config.json` for checkpoints
  and model settings.

## Install and environment check

The documented public install path is:

```bash
pip install stylegan2_pytorch
```

For a local clone, an editable install is useful while developing or verifying
against that checkout:

```bash
pip install -e .
```

Use a CUDA-capable PyTorch/torchvision build before relying on the package. The
main module imports `aim`, `einops`, `kornia`, `vector_quantize_pytorch`,
`torch`, `torchvision`, and other setup dependencies at import time.

After installing, run the bundled checker from this skill directory if the user
has an environment ready:

```bash
python scripts/check_install.py
```

It performs only import, CUDA, signature, and CLI-help checks; it does not train
or download data.

## Workflow starting points

1. For a new training run, open [training](sub-skills/training/SKILL.md), then
   use its data-layout and CLI references to choose `--data`, `--name`, image
   size, batch/accumulation, output directories, and augmentation settings.
2. For generation after a run, keep the same `--name`, `--models_dir`, and
   `--results_dir` layout and use the training generation/interpolation routes.
3. For Python sampling, open
   [programmatic-api](sub-skills/programmatic-api/SKILL.md); `ModelLoader`
   expects the default `base_dir/models/<name>/` checkpoint layout.
4. If the request is about another image-generation stack such as Diffusers,
   ComfyUI, Stable Diffusion LoRA training, image classification, detection, or
   segmentation, this skill is probably not the right operating graph.

## Verification status

This skill was constructed with a CUDA backend inspection environment and a
post-integration plan for CLI help, one-step training, and `ModelLoader`
sampling checks. The user requested **not to import** the skill into the managed
repo-skill library, so use the generated directory directly unless a later
request authorizes import.
