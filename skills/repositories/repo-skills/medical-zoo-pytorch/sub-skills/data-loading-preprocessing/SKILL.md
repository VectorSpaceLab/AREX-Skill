---
name: data-loading-preprocessing
description: "Prepare, inspect, and smoke-test MedicalZooPytorch dataset
  layouts, medical-image preprocessing, subvolume generation, normalization,
  resampling, coordinate transforms, and 3D augmentation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Data Loading and Preprocessing

Use this sub-skill for the repository's data-preparation path only:

- dataset folder layouts and manifest formats
- loader arguments and dispatcher entry points
- subvolume generation and cached patch files
- normalization, resampling, cropping, and coordinate transforms
- 3D augmentation operators and synthetic smoke checks

Do not use this route for model selection, training, checkpointing, inference, or loss design.
Hand those off to sibling sub-skills.

## Start here

- `references/data-layout.md` — dataset folders, filenames, manifests, and generated cache paths
- `references/workflows.md` — preprocessing recipes, loader argument map, and smoke-script usage
- `references/troubleshooting.md` — common missing-data, shape, and transform failures
- `scripts/smoke_preprocessing.py` — synthetic NIfTI preprocessing smoke
- `scripts/smoke_augmentations.py` — synthetic 3D augmentation smoke
- `scripts/smoke_dataloaders.py` — synthetic loader and manifest smoke

## Key entry points

- `lib.medloaders.generate_datasets(...)`
- `lib.medloaders.select_full_volume_for_infer(...)`
- `lib.medloaders.medical_image_process.load_medical_image(...)`
- `lib.medloaders.medical_loader_utils.create_sub_volumes(...)`
- `lib.augment3D.RandomChoice(...)`

## Coverage

This route covers the loader and preprocessing families that prepare data for later training or inference:

- ISEG 2017 and 2019
- BraTS 2018, 2019, and 2020
- MRBRAINS 2018
- IXI T1/T2
- MICCAI 2019 Gleason pathology
- COVIDx and COVID CT manifest-based 2D loaders

## Native-check note

The bundled scripts use tiny synthetic fixtures only. The repo's original data-loader checks remain blocked until the real datasets are placed in the documented folders.
