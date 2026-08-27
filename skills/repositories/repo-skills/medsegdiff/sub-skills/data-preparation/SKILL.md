---
name: data-preparation
description: "Prepare and validate ISIC, BRATS, and custom 2D/3D
  image-segmentation data for the MedSegDiff dataset loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this sub-skill when a MedSegDiff run needs an input directory, a loader
choice, or a diagnosis of missing/misaligned image and mask data. Data is not
bundled with this skill; acquire it separately and keep the split directory
layout described in [data-formats.md](references/data-formats.md).

## Route by dataset

- **ISIC**: use `ISICDataset`; first resolve the source-code CSV-name versus
  README CSV-name mismatch. See [data-formats.md](references/data-formats.md).
- **BRATS**: use `BRATSDataset` for full-volume tensors or
  `BRATSDataset3D` for the repository's fixed 155 virtual slices per case.
- **Custom 2D**: use `CustomDataset` with `images/*.png` and `masks/*.png`.
- **Custom 3D**: use `CustomDataset3D` with paired NIfTI volumes and account
  for its constructor and launcher integration caveat.

Read [api-reference.md](references/api-reference.md) before writing a caller
or transform. Read [troubleshooting.md](references/troubleshooting.md) when a
constructor assertion, empty dataset, shape error, or unexpected tensor value
appears. The bundled validator is a conservative layout check, not a
replacement for loading every dataset-specific file:

```bash
python scripts/validate_dataset_layout.py DATA_ROOT --kind custom2d
python scripts/validate_dataset_layout.py SPLIT_ROOT --kind isic --mode Training
python scripts/validate_dataset_layout.py CASE_ROOT --kind brats --mode 3d
```

## Preparation invariant

Before handing data to training or sampling, identify the exact loader and
confirm its tuple contract, modality set, spatial crop/resize policy, and mask
binarization policy. Do not silently repair filenames, pair lists by basename,
or normalize medical volumes: those are behavior changes that require an
explicit loader extension.

This sub-skill covers data discovery and loader behavior only. Route optimizer,
checkpoint, training flags, sampling, and evaluation to the sibling skills.
