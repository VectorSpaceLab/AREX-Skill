---
name: data-preparation
description: "Prepare MMDetection3D datasets, custom dataset layouts, conversion
  commands, and info-file migrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this sub-skill when the task is to prepare, inspect, or troubleshoot dataset roots and conversion commands for MMDetection3D v1.4.0.

## Use this for

- Validating dataset root layouts for KITTI, Waymo, NuScenes, Lyft, SemanticKITTI, S3DIS, ScanNet, SUN RGB-D, and custom datasets.
- Rendering safe dataset-conversion commands for the repository's native data converter without executing downloads or conversions.
- Planning v1 info-file migrations and coordinate-update commands before touching user data.
- Explaining ready-made annotation files, ground-truth databases, and dataset-specific preparation caveats.

## First steps

1. Identify the dataset family, dataset root, desired stage (`source`, `preconvert`, or `converted`), version, and whether the user only needs command construction or also layout validation.
2. Read [`references/datasets.md`](references/datasets.md) for built-in dataset layouts and conversion command families.
3. For custom data, read [`references/custom-dataset.md`](references/custom-dataset.md) before suggesting a converter or config.
4. Run the bundled safe checker when paths are available:

   ```bash
   python scripts/check_dataset_layout.py kitti --root data/kitti --stage preconvert
   ```

5. Render, but do not execute, conversion or migration commands with:

   ```bash
   python scripts/build_create_data_command.py create-data kitti --root-path data/kitti --out-dir data/kitti --extra-tag kitti
   ```

6. Read [`references/troubleshooting.md`](references/troubleshooting.md) when conversion hangs, files are missing, info pickles are stale, or custom data fails to load.

## Route away

- Model/config inheritance, class count changes, and model-zoo selection: use `configuration-model-zoo`.
- Training, testing, distributed launch, metric submission commands, and evaluator prefix flags: use `training-evaluation`.
- Dataset visualization, coordinate-system debugging, box projections, or geometry APIs: use `structures-visualization`.
- Implementing a new dataset class, transform, sampler, or registry component: use `customization-extensions` after using this sub-skill for the data schema.
- Inference input formatting after the dataset is already prepared: use `inference`.

## Safety boundaries

The bundled scripts in [`scripts/`](scripts/) are intentionally non-mutating: they only validate local path existence or print commands. They never download datasets, convert files, update pickles, launch training, or import large SDKs. Before running any rendered command, copy or back up valuable annotation files and confirm that the command is being run from a MMDetection3D checkout that contains the native conversion tools.
