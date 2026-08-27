---
name: siamese-triplet
description: "Routes metric-learning workflows for the Siamese-triplet PyTorch
  repository: dataset pair/triplet wrappers, embedding networks, contrastive and
  triplet losses, online mining, and MNIST/FashionMNIST experiment recipes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Siamese Triplet

Use this skill for the repository's image metric-learning surface: sampled positive/negative pairs, triplet generation, online mining, embedding networks, and the notebook-style MNIST/FashionMNIST experiment recipes.

The repo is organized as top-level modules rather than an installable package. For later Researcher use, the modules should be importable from a checkout or module directory that contains `datasets.py`, `losses.py`, `metrics.py`, `networks.py`, `trainer.py`, and `utils.py`.

## Route to the right sub-skill

- Read `sub-skills/dataset-sampling/SKILL.md` when you need pair or triplet dataset wrappers, the balanced batch sampler, or legacy torchvision dataset compatibility.
- Read `sub-skills/embedding-losses-mining/SKILL.md` when you need the embedding networks, siamese/triplet wrappers, contrastive or triplet losses, pair selectors, or online mining logic.
- Read `sub-skills/training-experiments/SKILL.md` when you need the `fit` loop, metrics, notebook recipes, embedding extraction, or tiny end-to-end training smoke checks.

## What this skill covers

- MNIST-like dataset wrappers that emit pairs, triplets, or balanced batches.
- Small convolutional embedding models and classification/siamese/triplet wrappers.
- Contrastive, triplet, online contrastive, and online triplet losses.
- Pair and triplet selectors for mining hard examples inside a mini-batch.
- The shared training loop and metric helpers used by the notebooks.
- Distilled MNIST and FashionMNIST workflows, including the defaults used in the README notebooks.

## What this skill does not do

- It does not download MNIST or FashionMNIST by default.
- It does not run the full 20-epoch notebook experiments.
- It does not require a GPU; CUDA is optional and only used for a smoke check when available.
- It does not depend on the original repository checkout remaining available at a fixed path.

## Skill composition

- Root `SKILL.md` owns routing, dependency expectations, and cross-surface smoke selection.
- `dataset-sampling` owns data contracts and sampler behavior.
- `embedding-losses-mining` owns model, loss, selector, and mining behavior.
- `training-experiments` owns fit-loop, metric, and notebook-recipe behavior.
- Root references hold cross-cutting API, workflow, compatibility, and troubleshooting summaries.
- Sub-skill references hold focused details and failure modes.
- Root and sub-skill scripts use synthetic fixtures so future agents can validate the contracts without downloads.

## Handoff checklist

- Confirm the task is actually about this repository's metric-learning surface.
- Confirm the repo modules are importable from the current checkout, installed path, or a supplied module directory.
- Choose one sub-skill owner before diving into detailed references.
- Prefer the narrow sub-skill smoke when debugging one surface.
- Prefer `scripts/smoke_repo_surface.py` when checking end-to-end compatibility.
- Do not route ordinary image classification, segmentation, or augmentation tasks here unless they use this repo's modules.

## Quick start

1. Decide which surface you are working on.
2. Open the matching sub-skill and its reference files.
3. If you need a one-shot check, run `scripts/smoke_repo_surface.py` from a checkout or module directory that exposes the repo's top-level modules.
4. If you need a narrower check, use the sub-skill script for that surface.

## Runtime expectations

- PyTorch, torchvision, numpy, Pillow, and matplotlib are the primary runtime dependencies.
- The dataset wrappers still reflect the older torchvision MNIST/FashionMNIST attribute names used by the repository notebooks (`train_data`, `train_labels`, `test_data`, `test_labels`).
- `EmbeddingNet` defaults to a 2D embedding, so the repo's plotting and extraction helpers assume 2-dimensional outputs.
- `fit` prints train and validation status per epoch and is intentionally simple; it is a notebook-friendly training loop, not a generic production engine.

## Install or inspect

- Start from a Python environment that already has PyTorch, torchvision, numpy, Pillow, and matplotlib available.
- If those libraries are missing, install them with your environment manager first; a plain example is `python -m pip install torch torchvision numpy pillow matplotlib`.
- If you are working from a checkout, point the bundled smoke at that checkout by passing `--module-dir <repo-root>`.
- If you are only checking compatibility, run the bundled smoke script instead of the full notebooks.
- Minimal verification command: `python scripts/smoke_repo_surface.py --module-dir <repo-root>`.

## Read these references

- `references/api-reference.md` for the core module and class/function map.
- `references/workflows.md` for the distilled MNIST and FashionMNIST experiment recipes.
- `references/compatibility.md` for torchvision and tensor-shape compatibility notes.
- `references/troubleshooting.md` for common failures and warning messages.
- `references/repo-provenance.md` for the source snapshot used to build this skill.
- `references/repo-routing-metadata.json` for repo-skills-router placement metadata.

## Run this script

- `scripts/smoke_repo_surface.py` is the bundled end-to-end smoke check for the repo surface. Use it when you want to confirm imports, shapes, selectors, and a tiny training pass from a current checkout or module directory.
