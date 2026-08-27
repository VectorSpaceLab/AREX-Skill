# Data formats

Use this page to prepare nnU-Net v2 raw datasets and inference inputs.

## Required dataset layout

Every dataset lives below `nnUNet_raw` with a `DatasetXXX_Name` folder:

```text
nnUNet_raw/
└── Dataset123_MyDataset/
    ├── dataset.json
    ├── imagesTr/
    ├── labelsTr/
    └── imagesTs/        # optional convenience location for test images
```

Training images are in `imagesTr`; corresponding training segmentations are in `labelsTr`. `imagesTs` is optional and is not used for training.

## Case and channel naming

A case has a unique case identifier. Non-RGB channels are stored as separate files:

```text
imagesTr/{CASE_IDENTIFIER}_0000{FILE_ENDING}
imagesTr/{CASE_IDENTIFIER}_0001{FILE_ENDING}
labelsTr/{CASE_IDENTIFIER}{FILE_ENDING}
```

Rules:

- Channel suffixes are four digits: `_0000`, `_0001`, `_0002`, ...
- Every training case must have every channel listed in `dataset.json`.
- Channel order must be identical for all cases and for inference.
- Images and labels for a case must have matching geometry and alignment.
- Labels use integer values; background is `0`; foreground labels should be consecutive.

Example two-channel case:

```text
imagesTr/prostate_03_0000.nii.gz
imagesTr/prostate_03_0001.nii.gz
labelsTr/prostate_03.nii.gz
```

## Supported file endings

The dataset has one `file_ending`, used for images, labels, and inference inputs. Common built-in formats include:

- `.nii.gz`, `.nrrd`, `.mha`
- `.png`, `.bmp`, `.tif`
- 3D `.tif` or `.tiff` with identically named sidecar JSON files containing spacing metadata

Use lossless formats only. Do not train on one ending and infer on another, for example `.png` training inputs and `.jpg` inference inputs.

## `dataset.json` minimum schema

Typical minimal JSON:

```json
{
  "channel_names": {
    "0": "T2",
    "1": "ADC"
  },
  "labels": {
    "background": 0,
    "PZ": 1,
    "TZ": 2
  },
  "numTraining": 32,
  "file_ending": ".nii.gz"
}
```

Required fields:

- `channel_names`: maps channel index to a channel name. JSON keys are strings, but Python helpers may accept integer keys and stringify them.
- `labels`: maps label or region names to integer label values, or to lists/tuples for regions.
- `numTraining`: expected number of training cases.
- `file_ending`: dataset-level file ending, including the leading dot.

Optional fields commonly encountered:

- `overwrite_image_reader_writer`: reader/writer class name when automatic I/O detection is insufficient.
- `regions_class_order`: required for multi-label regions.
- `name`, `reference`, `release`, `description`, `license` or `licence`, `converted_by`, `citation`, and other metadata.

## Normal labels

For ordinary class labels:

```json
{
  "background": 0,
  "organ": 1,
  "lesion": 2
}
```

Use `background: 0`. Do not assign semantic foreground meaning to `0`. Foreground label integers should be consecutive.

## Region-based labels

Region-based training lets a target combine multiple integer labels while still using integer label maps as input and output:

```json
{
  "labels": {
    "background": 0,
    "whole_tumor": [1, 2, 3],
    "tumor_core": [2, 3],
    "enhancing_tumor": 3
  },
  "regions_class_order": [1, 2, 3]
}
```

Rules:

- If any label value is a list with more than one integer, set `regions_class_order`.
- The length of `regions_class_order` equals the number of foreground regions.
- Order matters: broad regions first, substructures later, because later placements overwrite earlier placements during conversion back to an integer segmentation.
- Preserve JSON insertion order when generating this file; do not sort label keys alphabetically for region datasets.

## Ignore label

The ignore label marks segmentation voxels that should not contribute to the loss or validation metrics.

```json
{
  "labels": {
    "background": 0,
    "edema": 1,
    "non_enhancing_and_necrosis": 2,
    "enhancing_tumor": 3,
    "ignore": 4
  }
}
```

Rules:

- The key must be exactly `ignore`.
- The ignore label value must be the highest integer value in the segmentation.
- Do not include the ignore label in `regions_class_order`; it is not predicted.
- Dense predictions are still produced during inference.

Regions and ignore labels can be combined:

```json
{
  "labels": {
    "background": 0,
    "whole_tumor": [1, 2, 3],
    "tumor_core": [2, 3],
    "enhancing_tumor": 3,
    "ignore": 4
  },
  "regions_class_order": [1, 2, 3]
}
```

## Inference input naming

Inference input folders use the same channel suffixes and file ending as training data. For a two-channel model:

```text
input_folder/
├── case_001_0000.nii.gz
├── case_001_0001.nii.gz
├── case_002_0000.nii.gz
└── case_002_0001.nii.gz
```

Predictions omit the channel suffix:

```text
case_001.nii.gz
case_002.nii.gz
```

If training used two channels, inference must provide both `_0000` and `_0001` for every case, with channel meanings matching `channel_names`.

## Generating `dataset.json` from Python

The nnU-Net helper `generate_dataset_json` accepts:

- `output_folder`
- `channel_names`
- `labels`
- `num_training_cases`
- `file_ending`
- Optional `citation`, `regions_class_order`, `dataset_name`, `reference`, `release`, `description`, `overwrite_image_reader_writer`, `license`, `converted_by`, and arbitrary extra metadata through `**kwargs`.

It writes `dataset.json`, converts channel keys to strings, converts label values to integers or tuples of integers, asserts `regions_class_order` when multi-integer regions are present, and preserves key order with `sort_keys=False`.
