---
name: data-labeling-and-training-datasets
description: "Frame extraction, label checks, training dataset and shuffle
  creation, data conversion, and tiny DeepLabCut-style fixtures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Data Labeling And Training Datasets

Use this sub-skill when the current DeepLabCut task is about turning project videos and annotations into valid DeepLabCut labeled-data and training-dataset artifacts.

## Covers

- Extracting frames with `deeplabcut.extract_frames` for existing projects.
- Checking labels with `deeplabcut.check_labels` after GUI labeling, external import, or conversion.
- Understanding and repairing DeepLabCut `labeled-data/` annotation tables for standard and multi-animal projects.
- Creating shuffles and train/test splits with `create_training_dataset`, `create_training_dataset_from_existing_split`, `create_training_model_comparison`, and `mergeandsplit`.
- Converting annotation files with `convertcsv2h5` and converting older single-animal labels into maDLC-style labels with `convert2_maDLC`.
- Creating tiny safe standard or multi-animal fixture projects with the bundled script.

## Route elsewhere

- New-project creation, installation, package imports, environment preparation, and initial `config.yaml` project setup: use `install-and-project-setup`.
- Training, evaluation, model selection for real training runs, inference, analyzing videos, and exported model runtime: use `pytorch-training-evaluation-inference`.
- Tracklet conversion, stitching, identity tracking, and multi-animal temporal assembly after inference: use `multi-animal-tracking`.
- Filtering predictions, outlier-frame refinement, 3D workflows, labeled-video export, trajectory plots, and other post-prediction outputs: use `postprocessing-3d-video-exports`.

## Read in order

1. [Data formats](references/data-formats.md) for the exact folder/table layouts and trainset metadata expected by DeepLabCut.
2. [Workflows](references/workflows.md) for API sequences, safe arguments, and boundary decisions.
3. [Troubleshooting](references/troubleshooting.md) when labels are not found, shuffles collide, CSV/HDF conversion fails, or multi-animal columns are malformed.
4. [Tiny fixture script](scripts/create_tiny_dlc_project.py) when a small local standard or multi-animal project is needed for format or routing checks without GUI, training, downloads, or network access.

## Operating reminders

- Treat `config.yaml` as the authority for scorer, project path, videos, body parts, individuals, training fractions, iteration, and engine.
- Do not start training from this sub-skill. Stop after label validation and dataset/shuffle creation, then route to training/evaluation.
- In non-interactive automation, avoid prompts by setting `userfeedback=False` only after confirming that the target output may be overwritten or is disposable.
- Keep annotation paths portable: rows should identify images under `labeled-data/<video-stem>/...`, and the project path in `config.yaml` should point at the project root on the machine where the operation is being run.
