---
name: model-loading-inference
description: "Load CLIP models, prepare images/text, and run safe image-text inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLIP Model Loading and Inference

Use this sub-skill when an agent needs to import CLIP, choose a checkpoint, load the model/preprocess pair, prepare PIL images and tokenized text, or run image-text scoring and feature encoding.

## Start Here

- For a no-download environment check, run `python scripts/clip_smoke_check.py --json` from this directory or call it by path from any project.
- For API details, model names, tensor shapes, Torch Hub entrypoints, and dtype/device expectations, read [references/api-reference.md](references/api-reference.md).
- For common loading and inference workflows, including local checkpoints and offline-safe validation, read [references/workflows.md](references/workflows.md).
- For install/import, cache, checksum, JIT, CPU/GPU, preprocessing, and network failures, read [references/troubleshooting.md](references/troubleshooting.md).
- For a runnable one-image helper, use `python scripts/image_text_similarity.py --help`; it only downloads weights if the user runs it with a named model that is not already cached.

## Scope Boundaries

This sub-skill owns model loading, cache/download choices, preprocessing, device/JIT placement, forward inference, logits/probabilities, and `encode_image` / `encode_text` usage.

Do not use this sub-skill for prompt template search, prompt ensembling, or label wording strategy; route those decisions to [../prompt-engineering/](../prompt-engineering/). Do not use it for dataset-scale embedding extraction, linear probes, or evaluation loops; route those workflows to [../feature-evaluation/](../feature-evaluation/).
