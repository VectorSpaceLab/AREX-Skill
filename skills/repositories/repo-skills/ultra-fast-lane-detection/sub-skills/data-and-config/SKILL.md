---
name: data-and-config
description: "Routes CULane and TuSimple dataset preparation, config overrides,
  and data-layout checks for Ultra-Fast-Lane-Detection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-and-config

Use this sub-skill when a task is about the lane-detection dataset layout, config files, TuSimple annotation conversion, or command-line overrides for the repo's training and evaluation scripts.

## Read this when

- You need to explain or fix `data_root`, `log_path`, `finetune`, `resume`, `test_model`, or `test_work_dir`.
- You need to convert TuSimple JSON annotations into segmentation masks and list files.
- You need to validate whether a CULane or TuSimple directory is ready for training or evaluation.
- You need to pick the correct row anchors or `griding_num` for a dataset family.

## What this sub-skill owns

- Dataset root layout and file naming.
- Config file defaults and command-line overrides.
- TuSimple conversion from JSON labels to segmentation masks.
- The dataset classes and loaders used by training and evaluation.
- Common data-layout and config mistakes.

## What it does not own

- Training loop details, optimizers, and checkpoint lifecycle: see `training`.
- Evaluation metrics, demo output files, and score formatting: see `evaluation-and-visualization`.
- TorchScript export or speed benchmarking: see `export-and-speed`.

## Start here

- Read `references/configuration.md` for the repo's config defaults and override patterns.
- Read `references/data-formats.md` for the CULane and TuSimple directory layouts and expected list files.
- Read `references/api-reference.md` when you need exact function/class signatures.
- Run `scripts/validate_dataset_layout.py` when the user only wants to know whether a dataset root is ready.
- Run `scripts/convert_tusimple_safe.py` when TuSimple masks and list files must be generated.

## Typical flow

1. Identify the dataset family: CULane or TuSimple.
2. Check the dataset root layout with the bundled validator.
3. Load the appropriate config and override only the values that differ from the user's environment.
4. Convert TuSimple labels when the segmentation masks or list files are missing.
5. Hand the prepared layout to `training` or `evaluation-and-visualization`.

## Caution points

- The repo's source scripts assume CULane and TuSimple paths are already mounted or unpacked correctly.
- TuSimple conversion writes `train_gt.txt`, `test.txt`, and segmentation PNGs into the dataset root.
- The loaders expect the dataset roots and list files to match the documented file names exactly.
- The repo uses a custom `Config` loader rather than a package-style install-time config object.

## Reference and script links

- `references/configuration.md` for override examples and the most useful config fields.
- `references/data-formats.md` for folder layouts, row anchors, and dataset outputs.
- `references/api-reference.md` for verified signatures.
- `references/troubleshooting.md` for path, layout, and conversion errors.
- `scripts/convert_tusimple_safe.py` to generate TuSimple segmentation masks and lists.
- `scripts/validate_dataset_layout.py` to check dataset roots without modifying them.
