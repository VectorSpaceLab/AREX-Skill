---
name: datasets-and-preprocessing
description: "Guides Open3D-ML dataset loading, split handling, custom dataset
  layouts, and preprocessing validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Datasets and Preprocessing

Use this sub-skill when you need to understand how Open3D-ML loads point-cloud
datasets, how its dataset classes organize splits, or how to validate a custom
3D dataset layout before training.

## What this sub-skill covers

- Dataset constructors and split APIs.
- Common point-cloud dictionary keys for segmentation and object detection.
- `Custom3D`-style dataset layout and `.npy` file expectations.
- Custom dataset adaptation patterns.
- Preprocessing and bbox-database planning without running expensive source
  scripts or downloads by default.
- Layout validation for small fixtures and malformed examples.

## When to route here

- "How should my dataset folder be structured?"
- "Why is a split empty?"
- "How do I adapt `Custom3D` for my own point cloud data?"
- "What does `get_data()` return for segmentation or object detection?"
- "How do I check whether my `.npy` files are valid before training?"

## Use the bundled helper

Run `scripts/check_dataset_layout.py` to validate a tiny custom dataset root
for split presence, `.npy` shape, and label-column expectations.

## Reading order

1. Read `references/data-formats.md` for the expected dataset and split
   contracts.
2. Read `references/workflows.md` for the common dataset loading and custom
   dataset patterns.
3. Read `references/troubleshooting.md` when a split is empty, a file is
   malformed, or a dataset SDK/download dependency is missing.

## Boundary notes

Include:
- Dataset class selection and split handling.
- Input dictionary shapes and custom dataset layouts.
- Layout and split validation.

Exclude:
- Model training/inference mechanics; use `training-and-pipelines`.
- Visualization and TensorBoard output; use `visualization-and-extensions`.
- Install/backend problems; use `install-and-inspect`.

## Minimal workflow

1. Identify the dataset family and required split names.
2. Confirm the point-cloud dictionary keys and `.npy` layout.
3. Validate a tiny sample directory with `scripts/check_dataset_layout.py`.
4. Hand the dataset outputs to `training-and-pipelines` or
   `visualization-and-extensions`.

## Good handoff signals

A future agent should be able to answer these from this sub-skill alone:

- Which split names are accepted by the dataset base class and custom dataset.
- Which columns are expected for train/val versus test custom point clouds.
- How to recognize a dataset path or label-format error before training.
- Which upstream dataset SDKs are optional versus required for a workflow.
