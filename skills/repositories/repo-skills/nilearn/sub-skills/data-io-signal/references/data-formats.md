# Data Formats and Contracts

## Niimg-Like Inputs

A Nilearn **Niimg-like** input is a volume image representation accepted by many
`nilearn.image` and `nilearn.masking` functions:

- a path string or `pathlib.Path` pointing to a NIfTI-like image;
- a glob pattern when `wildcards=True`;
- an in-memory nibabel spatial image such as `nibabel.Nifti1Image`;
- an iterable/list of compatible images for concatenation or multi-image
  operations.

Use `load_img` when you want Nilearn to load or normalize the input. Use
`check_niimg` when you also need dimensionality validation.

## Nibabel `Nifti1Image`

A `nibabel.Nifti1Image` combines:

- `dataobj` or array data with shape `(x, y, z)` or `(x, y, z, t)`;
- a 4x4 affine mapping voxel indices to world coordinates;
- a header containing metadata such as dtype, zooms, and NIfTI forms.

For generated examples:

```python
import numpy as np
import nibabel as nib

img = nib.Nifti1Image(np.zeros((5, 6, 7, 10), dtype="float32"), np.eye(4))
```

Avoid relying on header details unless the task explicitly requires them.
`new_img_like(..., copy_header=False)` is usually safer for transformed arrays;
set `copy_header=True` only when the output data and metadata remain compatible.

## 3D Versus 4D

| Data kind | Typical shape | Use for | Validation |
| --- | --- | --- | --- |
| 3D image | `(x, y, z)` | statistical map, mean image, mask, anatomical reference | `check_niimg(img, ensure_ndim=3)` |
| 4D image | `(x, y, z, t)` | fMRI run, collection of maps, time series image | `check_niimg(img, ensure_ndim=4)` |
| 2D signals | `(n_samples, n_features)` | masked voxels or regional signals over time | `np.asarray(signals).ndim == 2` |
| Confounds | `(n_samples, n_confounds)` or `(n_samples,)` | nuisance regressors for cleaning | first dimension equals original `n_samples` |

`atleast_4d=True` promotes a 3D image to a one-volume 4D image. This is helpful
when code expects a time dimension, but do not use it to hide a genuine shape
mistake.

## Affines and Field of View

For direct masking, two images must share the same field of view:

- spatial shape: `img.shape[:3] == mask_img.shape[:3]`;
- affine: `np.allclose(img.affine, mask_img.affine)`.

If either differs, resample first. For masks and labels, use nearest-neighbor
interpolation:

```python
from nilearn import image

mask_on_img_grid = image.resample_to_img(
    mask_img,
    img,
    interpolation="nearest",
)
```

Resampling changes grid sampling only. It does not estimate a registration or
make misaligned anatomy correct.

## Mask Images

A direct `apply_mask` mask should be:

- a 3D Niimg-like object;
- binary-like, with background represented as `0`;
- non-empty after validation;
- in the same field of view as the image being masked.

`apply_mask(imgs, mask_img)` returns a 2D array with shape
`(n_samples, n_voxels)`. A 3D `imgs` input yields one sample. `unmask(X,
mask_img)` reverses this orientation: a 1D vector creates a 3D image, and a 2D
array shaped `(n_samples, n_voxels)` creates a 4D image.

## Confounds and Sample Masks

For `signal.clean` and `clean_img`:

- `signals` or image time points define the original `n_samples`.
- `confounds` must have the same original number of samples before scrubbing.
- `sample_mask` can be integer indices of kept samples or a boolean vector of
  length `n_samples` where `True` means keep.
- If `runs` is provided, it must be a 1D vector with one label per sample.
- With run-specific scrubbing, `sample_mask` must be a list of masks, one for
  each run.

Temporal filters are meaningful only for evenly sampled data. Pass `t_r` when
using `low_pass`, `high_pass`, `filter="butterworth"`, or `filter="cosine"` in
contexts where the sampling interval is not the desired default.

## Array Orientation

Nilearn's low-level masking and signal utilities use scikit-learn-style sample
orientation:

- rows are samples/time points;
- columns are voxels/features/confounds.

This means the direct output of `apply_mask` can be passed to `signal.clean`
without transposition.

## Safe Generated Data Rules

- Use small shapes, e.g. `(4, 5, 6, 12)`, to keep smoke checks fast.
- Prefer `np.eye(4)` or simple diagonal affines unless testing resampling.
- Build masks manually for smoke tests when mask heuristics are not the target.
- Avoid dataset fetchers and template-dependent workflows in no-network checks.
