# Data I/O and Signal Troubleshooting

## Invalid Image, Path, or Wildcard

**Symptoms**

- `TypeError` while loading a path or object.
- `ValueError` for unmatched wildcard input.
- Downstream functions complain about unexpected dimensionality.

**Fix**

1. Convert `Path` or string inputs explicitly with `load_img`.
2. If a literal `*` or `?` is part of the path, pass `wildcards=False`.
3. Validate the expected dimensionality early:

```python
from nilearn import image

img = image.check_niimg(input_img, ensure_ndim=4, wildcards=False)
```

Use `ensure_ndim=3` for maps/masks and `ensure_ndim=4` for runs.

## 3D/4D Shape Confusion

**Symptoms**

- A function expected a 4D run but received a 3D map.
- `index_img` unexpectedly returns a 3D image.
- Concatenation fails on mixed inputs.

**Fix**

- Use `index_img(run, 0)` when you need one 3D volume.
- Use `index_img(run, slice(0, 1))` or `check_niimg(..., atleast_4d=True)` when
  the downstream code requires a 4D image.
- Use `concat_imgs([...], auto_resample=True)` only when resampling all images
  to the first image's field of view is intended.

## Affine or Shape Mismatch Before `apply_mask`

**Symptoms**

- `Mask affine ... is different from img affine`.
- `Mask shape ... is different from img shape`.
- `apply_mask` fails after a successful `resample_to_img` elsewhere in the
  pipeline.

**Fix**

1. Print or assert both fields of view:

```python
import numpy as np

same_shape = img.shape[:3] == mask_img.shape[:3]
same_affine = np.allclose(img.affine, mask_img.affine)
```

2. Resample the mask onto the image grid with nearest-neighbor interpolation:

```python
from nilearn import image

mask_img = image.resample_to_img(mask_img, img, interpolation="nearest")
```

3. Re-binarize after resampling if needed:

```python
mask_img = image.math_img("mask > 0", mask=mask_img)
```

Do not use continuous interpolation for masks or labels.

## `resample_img` Bounding Box or Empty Output

**Symptoms**

- A bounding-box error reports that the target affine does not contain data.
- The resampled output is mostly or entirely fill values.

**Fix**

- Check that `target_affine` has shape `(4, 4)` when `target_shape` is provided.
- If using a 3x3 affine, remember Nilearn infers offset and shape.
- Confirm the source and target are already aligned; resampling is not
  registration.
- Start with `resample_to_img(source, target)` when a trusted target image
  already exists.

## Empty or Invalid Mask

**Symptoms**

- `The mask is invalid as it is empty: it masks all data.`
- `Computed an empty mask` warning.
- Binary-mask validation complains about values other than background `0` and
  foreground non-zero values.

**Fix**

- For `compute_epi_mask`, try `opening=False`, a smaller morphology opening, or
  adjust `lower_cutoff`/`upper_cutoff`.
- For padded images, try `exclude_zeros=True`.
- For flat-background images, try `compute_background_mask` instead of
  `compute_epi_mask`.
- For smoke tests, manually create a known non-empty mask with
  `new_img_like(reference, mask.astype("uint8"), reference.affine)`.
- After resampling a mask, threshold it back to binary.

## NaNs or Infs in Images and Arrays

**Symptoms**

- Cleaning or smoothing creates unexpected values.
- Output arrays contain non-finite values.
- Masking silently replaces non-finite values when `ensure_finite=True`.

**Fix**

- Use `ensure_finite=True` for `apply_mask`, `clean_img`, or `signal.clean` when
  non-finite values are expected and zero replacement is acceptable.
- Inspect whether non-finite values are meaningful missing data or real data
  errors before replacing them.
- Avoid smoothing before handling non-finite values, because smoothing can
  spread them spatially.

## Filtering Needs `t_r`

**Symptoms**

- Temporal filters behave unexpectedly.
- Errors or warnings mention `t_r`, `low_pass`, `high_pass`, or cosine filters.

**Fix**

- Pass the repetition time explicitly when filtering:

```python
cleaned = signal.clean(signals, high_pass=0.01, low_pass=0.1, t_r=2.0)
```

- Ensure `low_pass` is lower than the Nyquist frequency implied by `t_r`.
- Do not use `low_pass` with `filter="cosine"`; cosine filtering uses
  high-pass drift terms.

## Confound Shape Errors

**Symptoms**

- Confounds and signals have incompatible lengths.
- A single confound vector is interpreted unexpectedly.
- Cleaning with scrubbing removes the wrong rows.

**Fix**

- Make confounds 2D with `np.column_stack` or `confounds[:, None]`.
- Check `confounds.shape[0] == signals.shape[0]` before applying `sample_mask`.
- Do not pre-scrub confounds separately when passing `sample_mask`; let
  `signal.clean` apply the same mask.

## Sample-Mask Errors

**Symptoms**

- `sample_mask` has invalid type or out-of-range indices.
- `Number of sample_mask ... not matching` with `runs`.
- Output has fewer rows than expected.

**Fix**

- Use either integer keep indices or a boolean keep mask.
- Boolean mask length must equal the original number of samples.
- Integer indices must be within `0 <= index < n_samples`.
- With `runs`, pass one sample-mask entry per run when using a list.
- Expect output rows to equal the number of kept samples.

## `copy_header_from` and Header Copying

**Symptoms**

- `math_img` complains that `copy_header_from` names a missing image.
- Output image has unexpected header metadata.
- Transform functions preserve metadata that no longer matches output data.

**Fix**

- For `math_img`, set `copy_header_from` to the string name of one image in
  `**imgs`, such as `copy_header_from="img"`.
- Leave `copy_header_from=None` when the formula changes shape or semantics.
- For `new_img_like` and resampling functions, copy headers only when the
  transformed data remains compatible with the original metadata.

## When to Route Elsewhere

- Use `maskers-regions` for reusable fitted maskers, labels/spheres extraction,
  reports from maskers, caching policies, or sklearn pipelines.
- Use `surface-workflows` for mesh data, `SurfaceImage`, GIFTI/CIFTI-like
  surface operations, or projecting volumes to surfaces.
- Use `plotting-reporting` for static/interactive figures, HTML reports, and
  display debugging.
