---
name: data-preparation
description: "Prepare nnU-Net v2-compatible datasets, path variables,
  dataset.json metadata, conversions, inference input naming,
  labels/regions/ignore-label conventions, and validation troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-preparation

Use this sub-skill when the task is to make data acceptable to nnU-Net v2 before planning/preprocessing.

## Route here for

- Setting `nnUNet_raw`, `nnUNet_preprocessed`, `nnUNet_results`, or optional `nnUNet_extTrainer`.
- Creating `nnUNet_raw/DatasetXXX_Name` folders with `imagesTr`, `labelsTr`, optional `imagesTs`, and `dataset.json`.
- Naming training or inference inputs with `_0000`, `_0001`, ... channel suffixes and a consistent file ending.
- Authoring or checking `dataset.json`, including labels, regions, `regions_class_order`, ignore labels, and reader/writer overrides.
- Converting Medical Segmentation Decathlon or old nnU-Net v1 datasets into nnU-Net v2 format.
- Diagnosing validation errors before `nnUNetv2_plan_and_preprocess`.

## Do not handle here

- Planning fingerprints, experiment planners, or preprocessing outputs: use `planning-preprocessing`.
- Trainer classes, folds, losses, schedules, or training commands: use `training-configuration`.
- Prediction, ensembling, evaluation, or postprocessing after a trained model exists: use `inference-evaluation`.

## Start with these references

- Dataset layout, naming, `dataset.json`, regions, ignore labels, and inference input format: `references/data-formats.md`.
- Storage path environment variables and lazy path failure behavior: `references/path-setup.md`.
- MSD/v1 conversion command patterns and preflight validation: `references/conversion-and-validation.md`.
- Common failure modes and fixes: `references/troubleshooting.md`.

## Bundled helper

Run the lightweight validator before planning/preprocessing:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset
```

Add `--check-files` to verify that `imagesTr` and `labelsTr` filenames match `dataset.json` channel count and file ending. The helper checks metadata and names only; it does not inspect image geometry or label voxel values.
