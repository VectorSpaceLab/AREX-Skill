# Troubleshooting and safe customization

[Back to the data-and-preprocessing skill](../SKILL.md) · Related: [data formats](data-formats.md), [loader contracts](data-loader-contracts.md), [preprocessing](preprocessing-workflows.md), [utilities](data-utilities.md)

Use this page to diagnose a data contract before changing model code. Keep the
original case untouched and reproduce failures with a bounded synthetic array
whenever possible.

## Fast triage

| Symptom | Likely boundary | Safe check |
|---|---|---|
| `FileNotFoundError` for `<pid>_img.npy` or `<pid>_rois.npy` | manifest/file naming | Compare the exact `pid` and suffixes from `load_dataset`; do not guess a new path. |
| image/seg shape mismatch | preprocessing transpose or resampling | Inspect saved shapes and source spacing; validate a copied pair with the standalone script. |
| `ValueError` from `np.array(batch_data)` | variable crop/patch shape | Confirm padding and `pre_crop_size` on every spatial axis before batching. |
| boxes missing after conversion | wrong ROI mode or all-zero patch | Instance maps need `get_rois_from_seg_flag=False`; binary maps need `True`; an empty patch is valid. |
| classes do not match boxes | `class_target` order/id mismatch | Compare nonzero ROI ids with the preprocessing assignment order; do not use patient class as ROI class without a mapping. |
| bad labels after augmentation | segmentation interpolated as image | Set `order_seg=0`, `border_cval_seg=0`, and transform `data` and `seg` together. |
| z slices sampled with an invalid probability vector | stale/empty `fg_slices` | Check all indices are in `[0, z_size)` and handle all-background cases explicitly. |
| 2D model receives unexpected channels | `n_3D_context` or PET modality count | Recompute `cf.n_channels`; inspect `(B,C,X,Y)` immediately before the model. |
| inference boxes cannot be consolidated | lost patch coordinates or padding slicer | Preserve `patch_crop_coords`, `original_img_shape`, and any reverse-padding slicer. |
| augmenter hangs or is hard to debug | multiprocessing | Reproduce with one synthetic batch and `SingleThreadedAugmenter` in the caller's environment before changing workers. |
| `ImportError` or transform argument error | legacy environment mismatch | Re-run import/signature checks in the prepared env; do not patch around a version mismatch blindly. |

## Validator metadata contract

The bundled validator accepts optional JSON, not pickle. A minimal file is:

```json
{
  "pid": "case-001",
  "spacing": [0.7, 0.7, 1.25],
  "class_target": [1, 0],
  "fg_slices": [12, 13]
}
```

`spacing` must have two or three positive finite values and `fg_slices` must be
integer indices within the segmentation's z axis (for 2D, omit it). The
validator checks that `class_target` is a finite list but deliberately does not
force a class-vector length for binary masks, because the source families use
different patient/ROI meanings. Enforce that alignment in the family-specific
caller.

Example, bounded and read-only:

```bash
python sub-skills/data-and-preprocessing/scripts/validate_preprocessed_case.py \
  --image /reviewed/case-001_img.npy \
  --segmentation /reviewed/case-001_rois.npy \
  --metadata /reviewed/case-001.json \
  --max-voxels 4000000
```

The script refuses object arrays/pickle loading, rejects negative or fractional
segmentation labels, checks finite image values and matching spatial shapes,
and exits nonzero for a violation. It does not validate NIfTI/NRRD headers,
physical orientation, clinical labels, or model quality.

## Safe customization checklist

Before accepting a custom loader:

1. Start from one family and name the intended contract (toy 2D, LIDC
   instance-ROI, or PET-CT binary two-channel).
2. Write explicit `image_shape_before`, `image_shape_after`, `seg_shape`,
   dtype, and axis-order fields.
3. Decide whether source labels are instance ids or binary, then set the
   converter flag accordingly. If boxes are the source annotation, create a
   pseudo-mask with a documented rasterization rule and verify it after
   augmentation.
4. Use a patient-level split and keep all slices/patches from one patient in
   that split. Keep `fg_slices` as a sampling hint only.
5. Run validator fixtures for a foreground case, all-background patch, odd
   dimensions requiring padding, and a mismatched/invalid rejection case.
6. Import the loader and inspect signatures in the prepared environment. Do not
   start native workers or load private datasets for this gate.
7. Record any unresolved physical-space, label, backend, or private-data issue
   in the integration report.

## Explicit non-runnable actions

The following are not troubleshooting commands: downloading LIDC/PET/CT/TNM or
toy data, invoking raw SimpleITK/NRRD preprocessing against a mounted path,
calling `rsync`, launching multiprocessing pack/unpack, or calling
`delete_npy`. `pack_dataset.py`, `unpack_dataset`, and `delete_npy` are
explicitly destructive/storage helpers. Review and run them only outside this
skill after user authorization, backups, and a path-specific dry run.
