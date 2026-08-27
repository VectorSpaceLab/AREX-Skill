---
name: setup-and-data
description: "Install and validate pix2pixHD prerequisites, dataset layout,
  CLI/config basics, and small data-loader smoke checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Setup and Data

Use this sub-skill for repository setup, environment prerequisites, Cityscapes-style dataset layout checks, option parsing basics, and tiny data-loader smoke checks.

## Read first

- [Workflows](references/workflows.md)
- [Data layout](references/data-layout.md)
- [Options and configuration](references/options-and-configuration.md)
- [Troubleshooting](references/troubleshooting.md)

## Use when

- you need to confirm the Python stack is ready for pix2pixHD data inspection
- you need to validate a Cityscapes-style `dataroot` before training or inference
- you need to smoke `TrainOptions`, `TestOptions`, `AlignedDataset`, `tensor2label`, or `tensor2im`
- you need to check legacy resize/crop compatibility before choosing a non-default preprocessing mode

## Do not use when

- you are debugging training losses, checkpoint saving, or learning-rate schedules
- you are generating inference HTML, exporting ONNX, or running TensorRT
- you are clustering features or preparing feature caches for instance-conditioned workflows
- you are performing maintainer-only repo operations

## Primary scripts

- [scripts/check_cityscapes_layout.py](scripts/check_cityscapes_layout.py)
- [scripts/check_data_smoke.py](scripts/check_data_smoke.py)

## What this sub-skill covers

- README prerequisites and the minimal Python stack for data-only inspection
- `options/base_options.py`, `options/train_options.py`, and `options/test_options.py` defaults that affect data loading
- `data/aligned_dataset.py`, `data/base_dataset.py`, and `data/image_folder.py`
- `util/util.py` tensor/image conversion helpers and Cityscapes colormap smoke checks
- bundled Cityscapes sample fixture layout under `datasets/cityscapes/`
- parser smoke checks and one-sample dataset load checks
- the legacy torchvision `transforms.Scale` caveat for `resize_and_crop`

## Cross-links

- [Training](../training/SKILL.md): read this first for dataset validation and smoke-ready option defaults.
- [Inference](../inference/SKILL.md): read this for `dataroot` and label/instance folder rules before test-time input prep.
- [Instance features](../instance-features/SKILL.md): read this for `*_feat` folder layout; this sub-skill only names the loader rule.

## Validation sequence

1. Run `scripts/check_cityscapes_layout.py --repo-root <repo-root>`.
2. Run `scripts/check_data_smoke.py --repo-root <repo-root>`.
3. If you must evaluate `resize_and_crop`, rerun the smoke helper with `--probe-legacy-resize` and read the compatibility note.

## Limits

- This sub-skill stays CPU-safe for setup and data inspection.
- `TestOptions` smoke must use `save=False`; the class does not define `continue_train`.
- The bundled fixture is a smoke target only; do not add download logic here.
- Keep `load_features` and feature cache layout questions in the instance-features sub-skill.
