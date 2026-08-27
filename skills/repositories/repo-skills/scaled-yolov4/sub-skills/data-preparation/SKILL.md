---
name: data-preparation
description: "Dataset YAMLs, label layout, augmentation, anchor planning,
  caching, and dataset sanity checks for ScaledYOLOv4."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Data preparation

Use this sub-skill when the user needs to understand or repair the data side of the repository rather than training the model itself.

## Typical requests

- How should a custom dataset be laid out for this repo?
- Why does the loader reject a label file or image path?
- How do I check anchors, cache files, or image lists before training?
- How do I convert or reorganize a dataset into the format this checkout expects?
- Why does a dataset YAML or label sample fail validation?

## What this sub-skill owns

- Dataset YAML structure and path resolution.
- YOLO label format and cache behavior.
- Image and video source classification for the shared loaders.
- Augmentation and resizing helpers used by training.
- Anchor planning and dataset conversion helpers.
- Data-related failures such as missing files, malformed labels, or bad class counts.

## What it does not own

- The training loop, checkpointing, or distributed launch details → `../training/`.
- Standalone validation metrics and COCO scoring → `../evaluation/`.
- Image/video/webcam/stream detection runs → `../inference/`.
- TorchScript, ONNX, or CoreML export → `../export/`.

## Read before acting

- `../../references/data-layout.md` for the canonical dataset and label layout.
- `../../references/model-overview.md` when anchor or stride behavior matters.
- `references/data-workflows.md` for the main data-side functions and decision points.
- `references/troubleshooting.md` for dataset-specific failures and recovery steps.

## Bundled helper

- `scripts/inspect_dataset.py` validates dataset YAMLs, split sources, and sample labels without starting training.

## Workflow in practice

1. Inspect the YAML and make sure `train`, `val`, `test`, `nc`, and `names` agree.
2. Confirm the split sources resolve to the expected image lists or directories.
3. Check a few sample label files for the five-column normalized YOLO format.
4. Only then move on to anchor planning, caching, or training.

## Good signs

- The label files exist where the split source implies they should.
- `nc` matches the number of class names.
- Sample labels stay in `[0, 1]` and use zero-based classes.
- Anchor planning can proceed without obvious class-count or layout errors.

## Bad signs

- A split source points to an empty directory or broken image list.
- Labels have too many columns, negative values, or out-of-range coordinates.
- The dataset names do not match `nc`.
- A cache rebuild keeps discovering the same malformed source files.
