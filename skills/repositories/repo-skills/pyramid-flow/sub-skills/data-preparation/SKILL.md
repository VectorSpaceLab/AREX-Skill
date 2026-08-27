---
name: data-preparation
description: "Route Pyramid-Flow dataset annotations, loader checks, and
  text-feature or VAE-latent precomputation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pyramid-Flow data preparation router

Use this sub-skill when the task is about Pyramid-Flow JSONL annotations, image/video dataset loading, or precomputing artifacts consumed by DiT training.

## Route here for

- Authoring or validating `image_text.jsonl` and `video_text.jsonl`-style JSONL rows.
- Checking image-text, raw video, precomputed text-feature, and precomputed VAE-latent layouts.
- Building safe command lines for text feature extraction and video VAE latent extraction.
- Debugging missing annotation fields, unreadable videos, missing data-helper imports, and latent-resolution mismatches.

## Route elsewhere

- Generation demos, Gradio apps, image-to-video, text-to-video, and inference launchers: `../generation-inference/SKILL.md`.
- Training launchers, distributed training invariants, LPIPS checkpoints, and fine-tuning flags: `../training-workflows/SKILL.md`.
- Model internals, Causal VAE APIs, scheduler math, and latent semantics beyond loader-facing shape checks: `../core-components/SKILL.md`.

## Read first

1. `references/data-formats.md` for schemas, loader signatures, returned keys, and shape expectations.
2. `references/workflows.md` for annotation-to-precompute workflows and distilled extractor CLI contracts.
3. `references/troubleshooting.md` for deterministic failure diagnosis.

## Bundled helpers

- `scripts/check_dataset_fixtures.py` validates JSONL rows, latent/text-feature `.pt` files, dependency imports, and tiny synthetic fixtures. It can optionally exercise Pyramid-Flow dataset loaders when run from a checkout or environment that exposes `dataset.dataset_cls`.
- `scripts/build_precompute_commands.py` prints validated `torchrun` command shapes for text-feature and VAE-latent extraction. It does not launch long jobs or download checkpoints.

Keep validation deterministic before any expensive extraction or training run. Prefer failing early on schema and shape problems instead of relying on Pyramid-Flow dataset classes, which retry failed rows recursively and can hide the first bad record.
