---
name: "data-preparation"
description: "Routes PFLlib dataset generation, client-split construction, and
  dataset-layout validation for label-skew, feature-shift, and real-world
  scenarios."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this route when you need to create or validate PFLlib client-split datasets.
It covers the built-in scenario generators for label-skew, feature-shift, and
real-world data layouts.

## Use this when

- You need MNIST, CIFAR, Fashion-MNIST, AG News, Sogou News, Amazon Review,
  HAR, or another built-in PFLlib split.
- You need to regenerate a dataset after changing `train_ratio`, `alpha`, or a
  dataset-specific preprocessing step.
- You need to confirm that a `dataset/<name>/` tree has the expected
  `config.json`, `train/`, and `test/` layout before running experiments.
- You want to understand how PFLlib stores per-client `.npz` files and how
  `read_client_data()` turns them back into tensors.

## Read these references

- `references/data-formats.md` for the generated dataset tree and file schema.
- `references/workflows.md` for the common generation and validation flows.
- `references/troubleshooting.md` for download, split, and layout failures.

## Run these helpers

- `scripts/run_dataset_generator.py` to launch a repo dataset generator from a
  checkout without hard-coding source paths.
- `scripts/validate_dataset_layout.py` to check an existing split tree for
  missing files, stale metadata, or mismatched client counts.

## What belongs here

Include dataset creation, split validation, dataset-root inspection, and
scenario selection for:

- label skew: MNIST, EMNIST, FEMNIST, Fashion-MNIST, CIFAR-10, CIFAR-100,
  AG News, Sogou News, Tiny-ImageNet, Country211, Flowers102, GTSRB,
  Shakespeare, Stanford Cars, COVIDx, and kvasir
- feature shift: Amazon Review, Digit5, and DomainNet
- real-world: Camelyon17, iWildCam, Omniglot, HAR, and PAMAP2

## What does not belong here

- Launching federated learning experiments or summarizing training results;
  route that to `experiments`.
- Adding new algorithms, models, or optimizers; route that to `extension`.
- CUDA or package installation issues that happen before dataset generation;
  use the root troubleshooting and install checker.

## Common workflow

1. Confirm the target dataset family and split style.
2. Run the bundled generator launcher against a checkout.
3. Validate the output tree with the bundled layout checker.
4. Only then hand the dataset root to the experiment runner.

If the generator reports that the dataset already exists, use the validator to
confirm the tree instead of forcing a rewrite.
