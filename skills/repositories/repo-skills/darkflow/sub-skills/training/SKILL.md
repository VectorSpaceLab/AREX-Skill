---
name: training
description: "Guides Darkflow custom dataset preparation, YOLO config edits,
  training, and checkpoint workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Darkflow Training and Custom Data

Use this sub-skill when the user wants to train or fine-tune Darkflow on a custom object-detection dataset, prepare Pascal VOC annotations, edit label/config files, or resume checkpoints.

## Inputs you should collect

- Image directory for `--dataset`.
- Pascal VOC XML annotation directory for `--annotation`.
- Label list: one class per line.
- A Darkflow-compatible `.cfg` model file.
- Optional pretrained `.weights` file or checkpoint step.
- Training controls such as `--trainer`, `--lr`, `--batch`, `--epoch`, `--save`, `--summary`, and `--keep`.

## First checks

1. If the package is not already proven, run `../../scripts/check_install.py`.
2. Validate the annotations and labels with `scripts/check_voc_dataset.py` before running a long training job.
3. Read `references/data-formats.md` when a dataset or label file is ambiguous.
4. Read `../../references/model-overview.md` before changing class counts or filters.
5. Read `references/troubleshooting.md` before retrying a failed training run.

## Route by task

- **Custom dataset setup**: Use `references/data-formats.md` plus `scripts/check_voc_dataset.py`.
- **Config and label edits**: Use `references/workflows.md#custom-class-configuration` and `../../references/model-overview.md`.
- **Training from weights**: Use `references/workflows.md#fine-tune-from-pretrained-weights`.
- **Training from scratch**: Use `references/workflows.md#train-from-scratch`.
- **Checkpoint resume or export handoff**: Use `references/workflows.md#checkpointing-and-resume`, then hand off to `../inference/SKILL.md` for export or prediction.

## Outputs to expect

- Checkpoints under the selected backup directory, defaulting to `ckpt/`.
- Profile files saved beside checkpoints.
- Optional TensorBoard summaries under the selected summary directory.
- A trained model that can be loaded with `--load <step>` or `--load -1` for the latest checkpoint.

## Boundaries

This sub-skill does not own image-folder prediction, video/camera demos, JSON output, or protobuf load/export details. Those are handled by `../inference/SKILL.md` after the model has weights or checkpoints.

## Quality checks before claiming success

- The label list, final `[region]` `classes`, and penultimate `[convolutional]` `filters` agree.
- The annotation XML folder exists and each object label is in the label file.
- The image filenames referenced by annotation XMLs exist when an image directory is provided.
- The checkpoint path and `--load` value match the selected model name.
- The workflow does not assume external weights or datasets are downloadable unless the user explicitly allows network access.
