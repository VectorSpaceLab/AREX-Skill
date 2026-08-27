---
name: inference-and-model-zoo
description: "Use ESPnet pretrained and local inference APIs, model-zoo tags,
  streaming classes, model file checks, and packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference And Model Zoo

Use this sub-skill for pretrained model inference, local config/checkpoint inference, `from_pretrained`, `ModelDownloader`, streaming ASR, TTS vocoders, enhancement/separation, diarization, speaker embeddings, SVS, and packaging.

## Quick use

- Read [inference-api-reference.md](references/inference-api-reference.md) and [model-zoo-and-packaging.md](references/model-zoo-and-packaging.md); use scripts for local file and entrypoint checks.

## Boundaries

Route package/backend issues to `../installation-and-diagnostics/SKILL.md`, data/recipe stage setup to `../recipes-and-data/SKILL.md`, and training config creation to `../espnet2-training/SKILL.md`.

## Safety

Do not run full recipes, model downloads, training jobs, uploads, demo servers, broad CI, or host-mutating installers without explicit user approval. Keep local/private environment details out of public answers.
