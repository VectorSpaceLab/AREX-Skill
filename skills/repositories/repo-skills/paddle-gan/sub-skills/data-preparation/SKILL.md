---
name: data-preparation
description: "Prepare and validate PaddleGAN dataset layouts, dataroot mappings,
  and preprocessing inputs for translation, super-resolution, and lip-sync
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this sub-skill when the task is about making PaddleGAN data usable before training or inference.

It covers:
- CycleGAN / U-GAT-IT style unpaired layouts
- Pix2Pix-style paired layouts with split AB images
- custom paired or unpaired image folders
- DIV2K cropping and other SR inputs
- LRS2 preprocessing for Wav2Lip
- REDS and Vimeo90K sequence expectations
- RealSR synthetic degradation outputs
- config `dataroot` and related path updates

## Entry points

- `references/dataset-layouts.md`
- `references/preprocessing-scripts.md`
- `references/troubleshooting.md`

## Bundled helpers

- `scripts/check_dataset_layout.py`
- `scripts/process_div2k_data.py`

## Route elsewhere

- train/evaluate/resume command construction → `training-configs`
- export/static inference/deployment outputs → `deployment-export`
- benchmark execution and performance harnesses → out of scope

## Guardrails

- Do not run downloads, training, inference, or face/video preprocessing by default.
- Prefer explicit local paths over hidden repository defaults.
- If a dataset layout is ambiguous, validate the directory tree first with `scripts/check_dataset_layout.py`.
