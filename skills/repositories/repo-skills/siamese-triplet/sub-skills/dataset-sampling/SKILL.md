---
name: dataset-sampling
description: "Routes dataset-wrapper and batch-sampling tasks for SiameseMNIST,
  TripletMNIST, and BalancedBatchSampler in the Siamese-triplet repository."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Dataset Sampling

Use this sub-skill when the task is about how the repository builds pair and triplet examples, how it samples balanced mini-batches, or how it adapts MNIST-like datasets to the repository's legacy torchvision conventions.

## Covered surface

- `SiameseMNIST`
- `TripletMNIST`
- `BalancedBatchSampler`
- Legacy MNIST/FashionMNIST attribute names used by the notebooks
- Tiny synthetic fixtures that mimic the notebook data contract

## When to route here

Read this sub-skill for tasks that mention:

- positive/negative pairs
- anchor/positive/negative triplets
- test-time fixed pairs or triplets
- balanced batches for online mining
- legacy `train_data` / `train_labels` / `test_data` / `test_labels` compatibility
- PIL conversion from MNIST-like tensors

## What to do first

1. Read `references/api-reference.md` for the wrapper contracts and returned shapes.
2. Read `references/troubleshooting.md` if a fixture or dataset does not expose the attributes this repo expects.
3. Run `scripts/check_dataset_wrappers.py` when you want a tiny no-download smoke.

## Evidence signals

- Source evidence comes from `datasets.py` and the loader cells in both notebooks.
- The wrappers are generic enough for MNIST-like grayscale datasets, but their attribute names are legacy torchvision-specific.
- The smoke script intentionally uses a tiny fake fixture so verification does not depend on a network download.

## Short workflow

- Build or adapt a dataset object that exposes the legacy MNIST attributes.
- Attach `transform=None` for the smoke check, or attach the same transforms the notebook would use.
- Verify the returned object shapes:
  - `SiameseMNIST` -> `(img1, img2), target`
  - `TripletMNIST` -> `(img1, img2, img3), []` for the test fixture path
  - `BalancedBatchSampler` -> `n_classes × n_samples` indices per batch
- Check that class balance is sufficient for the chosen batch shape.

## Decision points

- Use `SiameseMNIST` when the downstream loss is contrastive and the model expects exactly two inputs.
- Use `TripletMNIST` when the downstream loss is triplet-based and the model expects three inputs.
- Use `BalancedBatchSampler` only when the next stage mines pairs or triplets inside a mini-batch.
- Prefer a tiny fake MNIST-like object for verification; do not download the full datasets just to prove the wrapper contract.

## Common failure modes

- The wrapped dataset has `data` and `targets` instead of `train_data` and `train_labels`.
- The sample tensor is not grayscale `28×28` `uint8` data before PIL conversion.
- The label distribution is too sparse for the selected batch sampler shape.
- A custom transform changes the image size or number of channels and breaks the downstream embedding network.

## Acceptance checks

- A pair wrapper returns two grayscale PIL images plus a binary target.
- A triplet wrapper returns three grayscale PIL images and an empty target placeholder.
- A balanced sampler emits exactly `n_classes × n_samples` indices.
- The downstream model still receives `1×28×28` tensors after transforms are applied.

## Read next

- `references/api-reference.md` for exact return values and sampler behavior.
- `references/troubleshooting.md` for legacy torchvision compatibility and batch-shape issues.
- `../embedding-losses-mining/SKILL.md` if the next step is a loss or mining check.
- `../training-experiments/SKILL.md` if the next step is an end-to-end fit loop.
