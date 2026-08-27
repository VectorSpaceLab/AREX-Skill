# Segmentation Data Layout

## Purpose

Read this before arranging 3D NIfTI data for segmentation training, validation,
or feature-map export.

## Training and validation folder contract

`CMR3DDataset` and `UKBBDataset` expect paired images and labels under split
folders:

```text
<dataset-root>/
  train/
    image/*.nii.gz
    label/*.nii.gz
  validation/ or val/
    image/*.nii.gz
    label/*.nii.gz
  test/
    image/*.nii.gz
    label/*.nii.gz
```

Important details:

- File lists are sorted independently, so names should sort in matching order.
- Image and label counts must match exactly.
- Every image/label pair must have the same shape after singleton dimensions
  are squeezed.
- `check_exceptions` raises on blank images (`image.max() < 1e-6`).
- `CMR3DDataset` uses the full 3D volume.
- `UKBBDataset` samples one random slice from the 3D volume before applying the
  transform.

The shipped CT configs use `arch_type='acdc_sax'` and call
`CMR3DDataset`. They use `split='train'`, `split='validation'`, and
`split='test'` in `train_segmentation.py`, while some helper code uses `val` in
other workflows. Align split folder names with the script being run.

## Test-only folder contract

`TestDataset(root_dir, transform)` expects:

```text
<test-root>/
  image/*.nii.gz
  label/*.nii.gz   # optional
```

If labels are present, the class verifies that the number of labels matches the
number of images and that each image/label pair has the same shape. If labels
are absent, it still checks that the image is not blank.

## Config fields for CT segmentation

Representative fields from the bundled CT configs:

```json
"training": {
  "arch_type": "acdc_sax",
  "n_epochs": 1000,
  "batchSize": 2,
  "preloadData": true
},
"augmentation": {
  "acdc_sax": {
    "scale_size": [160, 160, 96],
    "patch_size": [160, 160, 96],
    "shift": [0.1, 0.1],
    "rotate": 15.0,
    "scale": [0.7, 1.3]
  }
},
"model": {
  "type": "seg",
  "model_type": "unet_ct_dsv" or "unet_ct_multi_att_dsv",
  "tensor_dim": "3D",
  "input_nc": 1,
  "output_nc": 4,
  "gpu_ids": [0],
  "criterion": "dice_loss"
}
```

Replace private dataset paths with current machine paths. Keep `gpu_ids`
non-empty for the unmodified code.

## Transform expectations

The `acdc_sax` transform path performs:

- padding to `scale_size`;
- tensor conversion and channels-first conversion;
- random flip and affine augmentation for train;
- medical intensity normalization;
- channels-last conversion, add-channel, and crop/special-crop;
- final float/long casts.

For `test_sax`, the transform path pads by `division_factor`, converts to a
single-channel tensor, normalizes, and does not require labels.

## Tiny fixture notes

A synthetic volume for helper smoke checks should use a shape divisible by the
model downsampling stack. `16 x 16 x 16` is the smallest practical cube used by
this skill's smoke helpers for the CT deep-supervision model. Real CT configs
use much larger `160 x 160 x 96` patches.

If creating real mini fixtures, write NIfTI files rather than NumPy arrays when
you want to exercise the original dataset classes. Use NumPy arrays only for the
bundled generated helpers, which intentionally avoid depending on private file
layouts.
