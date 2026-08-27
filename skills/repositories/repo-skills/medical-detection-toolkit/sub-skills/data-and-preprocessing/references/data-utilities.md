# Data utilities: padding, tiling, balancing, and storage

[Back to the data-and-preprocessing skill](../SKILL.md) · Related: [data formats](data-formats.md), [loader contracts](data-loader-contracts.md), [preprocessing](preprocessing-workflows.md), [troubleshooting](troubleshooting.md)

The utility functions in `utils/dataloader_utils.py` are small but define
important geometry and sampling behavior. They operate on arrays; they do not
know physical spacing or clinical semantics.

## `pad_nd_image`

Signature:

```python
pad_nd_image(image, new_shape=None, mode="edge", kwargs=None,
             return_slicer=False, shape_must_be_divisible_by=None)
```

Important behavior:

- `new_shape` applies to the last axes of `image`; leading axes are not padded.
- It treats requested sizes as minimums: it never crops an axis if the input
  is already larger.
- Padding is centered; an odd extra voxel goes on the upper side.
- `mode` is forwarded to `numpy.pad`. The source loaders use `mode='constant'`
  for training data/segmentation and the utility default is `'edge'`.
- `return_slicer=True` returns `(padded, slicer)`, where the slicer maps back to
  the original shape. Use this when a prediction was padded for a network and
  must be cropped before patient-level consolidation.
- `shape_must_be_divisible_by` pads the trailing axes further to a divisor and
  can take a scalar or one value per trailing axis.

For an image and mask, apply the same shape request and compatible padding
semantics to both. Discrete masks should use a constant background value, not
edge replication that invents foreground labels at a boundary.

## `get_patch_crop_coords`

Signature:

```python
get_patch_crop_coords(img, patch_size, min_overlap=30)
```

`img` is spatial-only `(y, x)` or `(y, x, z)`. The function computes at least
`ceil(image_size / patch_size)` patches per axis, fixes the outside patches to
full patch size, and interpolates centers. If overlap would be below
`min_overlap`, it increases the patch count. The output is an integer array of
shape `(n_patches, 2 * dim)`:

```text
2D: [ymin, ymax, xmin, xmax]
3D: [ymin, ymax, xmin, xmax, zmin, zmax]
```

With `patch_size[2] == 1`, it creates one patch for every z slice. Inference
code must use the same coordinates for image and segmentation, retain them in
`patch_crop_coords`, and map local predictions back before weighted
consolidation. Check coordinate lengths after any context-slice padding.

## `get_class_balanced_patients`

Signature:

```python
get_class_balanced_patients(class_targets, batch_size, num_classes,
                            slack_factor=0.1)
```

Each `class_targets` element is expected to be a list of ROI class labels for a
patient. The first `int(batch_size * slack_factor)` selections are free random
choices. Later choices favor a patient containing the currently weakest class.
It returns indices, with replacement; one patient can occur multiple times in a
batch. A malformed class vector, zero `num_classes`, or a class outside the
configured range can skew sampling or loop indefinitely in the source. Validate
those conditions in a custom caller before enabling balancing.

Toy uses this helper with `cf.head_classes - 1`; LIDC uses it when
`head_classes > 2`; PET-CT samples uniformly. Class balancing is not a
substitute for a patient-level split: create folds before sampling and never
split slices from one patient across train and validation.

## Training crop behavior

LIDC and PET-CT training generators:

1. choose a patient (class-balanced or uniform);
2. transpose to loader convention and, in 2D, select a foreground-biased z
   slice using `fg_slices` with probability `p_fg=0.5`;
3. optionally add neighboring z slices as channels;
4. pad to `pre_crop_size` if needed;
5. crop dimensions larger than the pre-crop, often anchoring near a random
   foreground ROI with probability `p_fg`; and
6. let `SpatialTransform` produce the final `patch_size` during augmentation.

A crop can be background-only. Do not delete it merely because its mask is
empty; it provides negative examples. Conversely, do not let a malformed
`fg_slices` list silently cause invalid probability vectors.

## Storage helpers: non-runnable boundary

`get_case_identifiers`, `convert_to_npy`, `unpack_dataset`, and `delete_npy`
exist both in this utility module and in the LIDC packer with slightly
different `.npz` key assumptions. `unpack_dataset` starts a multiprocessing
pool and writes arrays; `delete_npy` removes files. They are **non-runnable**
from this operating skill: do not call them, pass them a user directory, or
recommend them without an explicit reviewed backup/dry-run plan. The data
validator intentionally implements none of these operations.

## Safe utility customization

When changing a utility, first construct a tiny array with an odd dimension,
a dimension smaller than the patch, and an image larger than one patch. Assert:

- image/seg padding gives identical spatial shapes;
- returned slicers recover the original values;
- patch coordinates are in bounds, full-sized, and have the promised overlap;
- z-singleton mode produces one patch per slice; and
- sampling returns only valid indices and terminates for every configured class.

These are synthetic geometry checks, not native final cases.
