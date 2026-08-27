---
name: espnet2-training
description: "Configure, dry-run, train, resume, fine-tune, and troubleshoot
  ESPnet2 task CLIs and PyTorch training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Espnet2 Training

Use this sub-skill for ESPnet2 task training modules, ConfigArgParse/YAML configuration, component choices, CPU dry-runs, checkpointing, fine-tuning, GPU/distributed flags, and training failures.

## Quick use

- Read [training-cli-reference.md](references/training-cli-reference.md), [configuration-and-components.md](references/configuration-and-components.md), and [gpu-distributed-training.md](references/gpu-distributed-training.md); use helper scripts for safe inspection.

## Boundaries

Route data/recipe setup to `../recipes-and-data/SKILL.md`, install/backend blockers to `../installation-and-diagnostics/SKILL.md`, pretrained inference to `../inference-and-model-zoo/SKILL.md`, and tests to `../development-and-testing/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
