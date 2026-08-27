# Troubleshooting data preparation

Use these checks before escalating to planning/preprocessing, training, or inference.

## Environment variable is unset

Symptoms:

- A command complains that `nnUNet_raw`, `nnUNet_preprocessed`, or `nnUNet_results` is not defined.
- A Python script imports path objects but fails when joining or stringifying them.

Fix:

```bash
export nnUNet_raw="/path/to/nnUNet_raw"
export nnUNet_preprocessed="/path/to/nnUNet_preprocessed"
export nnUNet_results="/path/to/nnUNet_results"
```

Then verify in the same shell that runs nnU-Net:

```bash
echo "$nnUNet_raw"
echo "$nnUNet_preprocessed"
echo "$nnUNet_results"
```

## Dataset folder name is invalid

Symptoms:

- Dataset cannot be found by ID.
- Conversion or planning rejects the dataset name.

Fix:

- Use `DatasetXXX_Name`, for example `Dataset123_LiverLesions`.
- `XXX` must be a three-digit numeric ID.
- Use a stable name after the underscore.
- Avoid reusing an ID that already appears in raw, preprocessed, or results storage.

## Required folders or `dataset.json` are missing

Symptoms:

- Dataset validation fails immediately.
- Planning cannot locate training images or labels.

Fix expected layout:

```text
Dataset123_MyDataset/
├── dataset.json
├── imagesTr/
├── labelsTr/
└── imagesTs/        # optional
```

`imagesTs` is optional; `imagesTr`, `labelsTr`, and `dataset.json` are not.

## Multi-channel filenames are incomplete

Symptoms:

- Two-channel training or inference fails because `_0001` is missing.
- Cases are split incorrectly because the case ID contains an unexpected suffix.

Fix:

- For channel count `N`, every case needs `_0000` through `_{N-1:04d}`.
- The label file does not include a channel suffix.
- Inference inputs must follow the same rule as training inputs.

Example:

```text
imagesTr/case42_0000.nii.gz
imagesTr/case42_0001.nii.gz
labelsTr/case42.nii.gz
```

## `dataset.json` channel definitions do not match files

Symptoms:

- Files exist but nnU-Net expects a different number/order of channels.
- Channel normalization is wrong because names are swapped.

Fix:

```json
"channel_names": {
  "0": "T2",
  "1": "ADC"
}
```

The `_0000` files are channel `0`, `_0001` files are channel `1`, and so on. Keep the same order for every case and for inference.

## File ending mismatch

Symptoms:

- Training data is found but inference input is ignored, or vice versa.
- Some files end in `.nii.gz` while metadata says `.png`.

Fix:

- Set `file_ending` exactly, including the leading dot, for example `.nii.gz`.
- Use the same file ending for `imagesTr`, `labelsTr`, optional `imagesTs`, and prediction input folders.
- Do not mix lossy image formats into segmentation datasets.

## Normal labels are not consecutive

Symptoms:

- Label handling fails or metrics/classes are wrong.

Fix:

```json
"labels": {
  "background": 0,
  "organ": 1,
  "lesion": 2
}
```

Use `background: 0`; do not skip foreground integers unless you are intentionally using a region/ignore setup that remains valid.

## Region labels lack `regions_class_order`

Symptoms:

- `dataset.json` has labels such as `[1, 2, 3]` but generation or planning fails.

Fix:

```json
"labels": {
  "background": 0,
  "whole_tumor": [1, 2, 3],
  "tumor_core": [2, 3],
  "enhancing_tumor": 3
},
"regions_class_order": [1, 2, 3]
```

Rules:

- Set `regions_class_order` whenever a foreground label combines multiple integers.
- The number of entries equals the number of foreground regions.
- Put broad regions first and specific regions later because later entries overwrite earlier ones.
- Do not sort JSON label keys alphabetically when generating region datasets.

## Ignore label is misused

Symptoms:

- Sparse labels are interpreted as real classes.
- Validation complains about ignore-label placement.

Fix:

```json
"labels": {
  "background": 0,
  "class_a": 1,
  "class_b": 2,
  "ignore": 3
}
```

Rules:

- The key must be `ignore`.
- The ignore value must be the highest integer value.
- Do not include `ignore` in `regions_class_order`.
- Only use ignore for pixels/voxels that should not contribute to loss or validation metrics.

## MSD conversion target ID conflict

Symptoms:

- `nnUNetv2_convert_MSD_dataset` reports that the target dataset ID is already taken.

Fix:

- Pick a different `-overwrite_id`, or intentionally remove the old matching dataset from raw/preprocessed/results locations if it is safe.
- Do not force ID reuse when old preprocessed data or results may still exist.

## Old v1 conversion target already exists

Symptoms:

- `nnUNetv2_convert_old_nnUNet_dataset` aborts because `$nnUNet_raw/DatasetXXX_Name` already exists.

Fix:

- Choose a new `DatasetXXX_Name`, or manually delete the old target only if you are sure it is obsolete.
- Clean matching preprocessed/results data before rerunning planning for replaced raw data.

## Geometry or voxel-label problems remain

The bundled validator checks metadata and filenames, not image contents. If files are correctly named but planning/preprocessing still fails, inspect:

- Image/label readability by the selected reader/writer.
- Matching image/label shape, spacing, and orientation for each case.
- Segmentation voxel values matching the declared labels, regions, and ignore value.
- Required spacing sidecar JSON files for 3D TIFF datasets.
