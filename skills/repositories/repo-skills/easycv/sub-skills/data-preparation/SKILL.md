---
name: data-preparation
description: "Routes EasyCV dataset layouts, annotation conversion, file I/O,
  and data-hub preparation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data preparation

Use this sub-skill when the task is to prepare, validate, or convert datasets for EasyCV.

It covers dataset layout guidance, annotation conversion, OSS / local file I/O, and the repo's data-preparation helper modules.

## Read these references first

- `references/data-formats.md` for the expected on-disk layouts and table schemas.
- `references/workflows.md` for the repo-maintained conversion helpers and dataset-specific prep flows.
- `references/troubleshooting.md` for layout mismatches, missing annotation files, and OSS issues.
- Root `references/model-zoo-overview.md` when the dataset choice depends on the task family.

## What belongs here

Include tasks such as:

- preparing ImageNet, CIFAR, COCO, VOC, nuScenes, Market1501, CrowdHuman, or PAI-iTAG data
- converting annotation formats into EasyCV-ready structures
- checking a file list, manifest, TFRecord, or table schema before training or prediction
- using `easycv.file.io` for local or OSS paths
- understanding which data shape a config expects before training

## What stays elsewhere

- Training / evaluation once the data is ready -> `sub-skills/training-and-evaluation/`
- Batch inference over prepared inputs -> `sub-skills/prediction-and-inference/`
- Export / optimization after training -> `sub-skills/export-and-optimization/`

## Typical decision flow

1. Identify the dataset family or table schema.
2. Confirm the expected directory or file-list layout.
3. Decide whether a conversion helper, a file I/O setup, or a manual layout fix is needed.
4. Prepare or validate the data before touching the training command.

## Common success signals

- The dataset root matches the layout documented for the chosen family.
- Annotation files, index files, or manifests are present where the loader expects them.
- OSS / ODPS credentials are configured before any remote read or write.
- The config's data roots point at the prepared dataset instead of the source notebook or download location.

## Common preparation surfaces

- `easycv.file.io` supports both local and OSS paths.
- `tools/prepare_data` modules are packaged into the installed `easycv.tools` namespace.
- Some dataset families use filelists, some use manifests, and some use TFRecords or ODPS tables.
- The train / eval sub-skill expects the data to be ready before it starts.

