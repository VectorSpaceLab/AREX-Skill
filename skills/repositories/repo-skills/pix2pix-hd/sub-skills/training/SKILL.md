---
name: training
description: "Understand pix2pixHD training, checkpointing, debug mode, memory
  trade-offs, and safe command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill for `train.py`, recipe selection, checkpoint/resume questions, memory planning, and safe command construction for the published training scripts.

## Route away when needed
- Dataset layout and loader validation: [setup-and-data](../setup-and-data/SKILL.md)
- Feature cache prep, clustering, and feature-workflow sequencing: [instance-features](../instance-features/SKILL.md)
- Inference HTML/result generation or export: [inference](../inference/SKILL.md)
- Maintainer-only repo tasks: out of scope

## What this covers
- `train.py` loop behavior, debug mode, and checkpoint cadence
- `models/base_model.py`, `models/models.py`, `models/pix2pixHD_model.py`, and `models/networks.py`
- recipe construction for 512p, 1024p 12G/24G, feature-conditioned, multi-GPU, and FP16 variants
- save/load locations under `checkpoints/<name>/`
- backend notes for CUDA, VRAM, Apex, and VGG downloads

## Detailed references and helpers
- [Workflows](references/workflows.md): read for recipe tables, 512p/1024p choices, and debug-smoke guidance.
- [CLI reference](references/cli-reference.md): read for training flags and defaults.
- [Checkpoints and outputs](references/checkpoints-and-outputs.md): read before changing `--name`, `--which_epoch`, or `--load_pretrain`.
- [Troubleshooting](references/troubleshooting.md): read for CUDA, VRAM, Apex, VGG, and Python compatibility failures.
- [build_train_command.py](scripts/build_train_command.py): run to print canonical commands without launching training.
- [inspect_training_setup.py](scripts/inspect_training_setup.py): run to surface environment and path warnings before a manual run.

## Use the helpers first
1. Check [workflows](references/workflows.md) for the matching recipe and trade-offs.
2. Use `scripts/build_train_command.py --repo-root <repo>` to print the canonical command; it never launches training.
3. Use `scripts/inspect_training_setup.py --repo-root <repo>` to surface environment and path warnings before any manual run.
4. If the recipe uses `--load_features`, read [instance-features](../instance-features/SKILL.md) first for the separate feature-cache step.
5. If the recipe depends on paired labels or dataset shape assumptions, confirm them via [setup-and-data](../setup-and-data/SKILL.md).

## Safety notes
- Prefer `--debug --no_vgg_loss` for the smallest smoke.
- Debug mode does not guarantee a checkpoint by itself; the default save cadence can skip it.
- The helper scripts are dry-run only. They print or validate commands and do not start long training jobs.
- CPU training is not a supported target in this repo; the training path calls `.cuda()` in multiple places.
