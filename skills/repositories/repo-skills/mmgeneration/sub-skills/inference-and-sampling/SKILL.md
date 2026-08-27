---
name: "inference-and-sampling"
description: "Routes MMGeneration pretrained-model loading, sampling,
  translation, and demo-style inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Sampling

Use this sub-skill when the task is to load a generator, pick a device, and produce samples or translated images.

## Typical triggers

- "How do I sample from this checkpoint?"
- "How do I load a pretrained MMGeneration model?"
- "How do I translate one image with Pix2Pix or CycleGAN?"
- "How do I sample DDPM outputs?"
- "What shape should the labels or outputs have?"

## Include here

- `mmgen.apis.init_model`
- `sample_unconditional_model`
- `sample_conditional_model`
- `sample_img2img_model`
- `sample_ddpm_model`
- Demo-style inference commands and output shape checks
- CPU vs CUDA device choice for sampling
- Label handling, image-path handling, and sample preview behavior

## Exclude here

- Training launchers and resume behavior -> `training-and-distribution`
- Metric calculation and inception-stat preparation -> `evaluation-and-metrics`
- Config editing and registry mechanics -> `configuration-and-extension`
- Latent projection / interpolation / TorchServe / CLIP-guided editing -> `applications-and-deployment`

## Read these files first

- `references/workflows.md`
- `references/troubleshooting.md`
- `../../references/api-reference.md`
- `../../references/model-overview.md`
- `../../references/data-formats.md`

## Bundled helper

- `scripts/sample_mmgen.py` — a safe sampling helper for unconditional, conditional, translation, and DDPM modes.

## What good guidance looks like

A future agent should be able to:

1. Load a config and checkpoint with the right device choice.
2. Decide whether to call unconditional, conditional, translation, or DDPM sampling.
3. Understand how labels, target domains, and image paths are consumed.
4. Save or inspect the produced tensors without reopening the repo.

## Common failure modes

- Wrong label length or label type for conditional sampling.
- Using a translation helper with a non-translation model.
- Translation image layout not matching the expected paired/unpaired format.
- Requesting the wrong device or a CUDA device that is not available.
- Assuming DDPM output is always a tensor when intermediate saves return a dict.

For concrete recovery steps, read `references/troubleshooting.md`.
