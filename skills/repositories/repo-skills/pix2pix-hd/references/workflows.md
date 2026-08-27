# pix2pixHD Workflows

## Purpose

Read this when you need a high-level map of the repo's user-facing workflows before choosing a sub-skill or running a helper script.

## Workflow map

| Workflow | Use this sub-skill | Primary entry points | Typical outputs |
| --- | --- | --- | --- |
| Environment and dataset setup | [setup-and-data](../sub-skills/setup-and-data/SKILL.md) | `scripts/check_environment.py`, `sub-skills/setup-and-data/scripts/check_cityscapes_layout.py`, `sub-skills/setup-and-data/scripts/check_data_smoke.py` | Layout validation, parser smoke, one-sample loader smoke |
| Training recipes | [training](../sub-skills/training/SKILL.md) | `sub-skills/training/scripts/build_train_command.py`, `sub-skills/training/scripts/inspect_training_setup.py` | Canonical training commands, checkpoint and VRAM guidance |
| Checkpointed inference | [inference](../sub-skills/inference/SKILL.md) | `sub-skills/inference/scripts/build_inference_command.py`, `sub-skills/inference/scripts/check_checkpoint.py` | Test commands, HTML output paths, checkpoint preflight |
| Instance features | [instance-features](../sub-skills/instance-features/SKILL.md) | `sub-skills/instance-features/scripts/build_feature_command.py`, `sub-skills/instance-features/scripts/check_feature_cache.py` | Encode/precompute/feature-command sequences, cache validation |

## Recommended order

1. Start with setup-and-data for a new checkout.
2. Use training for the label-only or feature-conditioned training recipe you want.
3. Use instance-features when the training or inference path depends on cached feature maps or feature clustering.
4. Use inference to synthesize images, render HTML results, or preflight checkpoints.

## Common task families

- Semantic-label-to-image synthesis at 512p or 1024p
- Cityscapes-style paired label, instance, and image data preparation
- Instance-feature encoding and clustered cache creation
- Checkpointed HTML result browsing and optional export/runtime paths
- Training recipe selection by VRAM or GPU count

## Shared caution points

- The repo is not published as a normal pip-installable package, so the helpers take an explicit `--repo-root`.
- CUDA is required for the published training, inference, and feature workflows.
- `resize_and_crop` is a legacy compatibility path; prefer `scale_width`, `scale_width_and_crop`, `crop`, or `none` unless you have a specific reason to patch `data/base_dataset.py`.
- Feature workflows need `scikit-learn` for KMeans and the expected cached `.npy` files.
