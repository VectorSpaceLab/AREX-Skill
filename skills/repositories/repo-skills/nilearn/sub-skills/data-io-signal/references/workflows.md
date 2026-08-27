# Data I/O and Signal Workflows

These recipes use generated `numpy` arrays and in-memory `nibabel.Nifti1Image`
objects. They are safe for smoke checks and do not require datasets or network
access.

## Create Tiny 3D and 4D Images

```python
import numpy as np
import nibabel as nib

shape_3d = (5, 6, 7)
identity_affine = np.eye(4)
map_data = np.zeros(shape_3d, dtype="float32")
map_data[2:4, 2:5, 3:6] = 5.0
stat_img = nib.Nifti1Image(map_data, identity_affine)

rng = np.random.default_rng(0)
run_data = rng.normal(size=(*shape_3d, 12)).astype("float32")
run_img = nib.Nifti1Image(run_data, identity_affine)
```

Use this as the starting point for no-network tests. Prefer `float32` when the
exact dtype does not matter.

## Validate Inputs and Split 4D Runs

```python
from nilearn import image

checked_run = image.check_niimg(run_img, ensure_ndim=4)
first_volume = image.index_img(checked_run, 0)
volumes = list(image.iter_img(checked_run))
recombined = image.concat_imgs(volumes)
assert recombined.shape == checked_run.shape
```

Key checks:

- `ensure_ndim=3` is appropriate for one statistical map or one mask.
- `ensure_ndim=4` is appropriate before temporal cleaning or iteration.
- `index_img(run, 0)` returns a 3D image; `index_img(run, slice(0, 2))` returns
  a 4D image with two volumes.

## Make Derived Images Safely

```python
from nilearn import image

mean = image.mean_img(run_img)
z_like = image.math_img("(img - img.mean()) / img.std()", img=mean)
positive = image.threshold_img(z_like, threshold=0.0)
copy = image.new_img_like(mean, positive.get_fdata(), mean.affine)
```

Guidance:

- Use `math_img` for concise array formulas over one or more images.
- Use `new_img_like` when you already have a `numpy` array and need a valid
  NIfTI image with reference spatial metadata.
- Set `copy_header_from="img"` in `math_img` only when preserving the source
  header is required and the formula output is compatible with that header.

## Resample Before Masking

```python
import numpy as np
import nibabel as nib
from nilearn import image, masking

source_data = np.zeros((4, 4, 4), dtype="float32")
source_data[1:3, 1:3, 1:3] = 1.0
source_img = nib.Nifti1Image(source_data, np.diag([2.0, 2.0, 2.0, 1.0]))

target_data = np.zeros((8, 8, 8), dtype="float32")
target_img = nib.Nifti1Image(target_data, np.eye(4))

resampled = image.resample_to_img(
    source_img,
    target_img,
    interpolation="continuous",
)
mask_data = resampled.get_fdata() > 0.1
mask_img = image.new_img_like(target_img, mask_data.astype("uint8"), target_img.affine)
series = masking.apply_mask(resampled, mask_img)
```

Guidance:

- `resample_to_img` changes the voxel grid, not anatomical alignment.
- Use `interpolation="nearest"` for binary masks, label maps, and integer
  regions; use continuous or linear interpolation for continuous intensity
  images.
- `apply_mask` requires the same spatial shape and affine for the image and
  mask. If it fails, inspect both before retrying.

## Compute and Intersect Masks

```python
from nilearn import image, masking

mean = image.mean_img(run_img)
background_mask = masking.compute_background_mask(mean, opening=False)
epi_mask = masking.compute_epi_mask(mean, opening=False, exclude_zeros=True)
combined = masking.intersect_masks(
    [background_mask, epi_mask],
    threshold=0.0,
    connected=False,
)
```

For tiny synthetic images, mask-computation heuristics can produce empty masks.
If a smoke test only needs an extraction mask, build a known non-empty binary
mask manually with `new_img_like`.

## Apply and Undo a Mask

```python
from nilearn import masking

mask_data = np.zeros(run_img.shape[:3], dtype="uint8")
mask_data[1:4, 2:5, 3:6] = 1
mask_img = image.new_img_like(run_img, mask_data, run_img.affine)

signals = masking.apply_mask(run_img, mask_img)
restored_img = masking.unmask(signals, mask_img)
assert signals.shape == (run_img.shape[-1], int(mask_data.sum()))
assert restored_img.shape == (*run_img.shape[:3], run_img.shape[-1])
```

Remember that `apply_mask` returns rows as samples/time points and columns as
voxels/features. This orientation already matches `nilearn.signal.clean`.

## Clean Image Time Series

```python
from nilearn import image

n_scans = run_img.shape[-1]
confounds = np.column_stack([
    np.linspace(-1, 1, n_scans),
    np.ones(n_scans),
])
cleaned_img = image.clean_img(
    run_img,
    detrend=True,
    standardize="zscore_sample",
    confounds=confounds,
    high_pass=0.01,
    t_r=2.0,
    ensure_finite=True,
    mask_img=mask_img,
)
```

Use `clean_img` when you want the result as a 4D image. Use `signal.clean` when
you already have a 2D array from `apply_mask` or another extractor.

## Clean 2D Signal Arrays

```python
from nilearn import signal

signals = masking.apply_mask(run_img, mask_img)
sample_mask = np.arange(n_scans)
sample_mask = sample_mask[sample_mask != 2]

cleaned = signal.clean(
    signals,
    confounds=confounds,
    sample_mask=sample_mask,
    detrend=True,
    standardize="zscore_sample",
    filter="butterworth",
    high_pass=0.01,
    t_r=2.0,
    ensure_finite=True,
)
assert cleaned.shape[0] == len(sample_mask)
```

Checklist for array cleaning:

- `signals` must be 2D: `(n_samples, n_features)`.
- `confounds` must have the same original `n_samples` as `signals`.
- `sample_mask` can be integer indices to keep or a boolean mask where `True`
  keeps a volume.
- With `runs`, pass one run label per sample. If using run-specific sample
  masks, pass a list with one mask per run.

## Tiny End-to-End Smoke Pattern

1. Generate a 4D image and matching binary mask in memory.
2. Validate dimensionality with `check_niimg`.
3. Extract signals with `apply_mask`.
4. Clean signals with `signal.clean` and confounds/sample mask.
5. Reconstruct an image with `unmask`.
6. Print shapes, affine equality, and finite-value checks as JSON.

The bundled `smoke_image_signal.py` implements this pattern.
