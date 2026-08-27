# Data I/O and Signal API Reference

Nilearn accepts **Niimg-like** inputs for volume workflows: a filename,
`pathlib.Path`, glob pattern, in-memory nibabel image, or an iterable/list of
compatible images. For direct functions in this sub-skill, prefer tiny generated
images for checks and avoid network downloads.

## Image Loading and Validation

| API | Main inputs | Returns | Shape notes | Gotchas |
| --- | --- | --- | --- | --- |
| `load_img(img, wildcards=True, dtype=None)` | Niimg-like path/object/list/glob | nibabel image, often `Nifti1Image` | 3D or 4D depending on input | Globs are enabled by default; unmatched wildcards raise `ValueError`. |
| `check_niimg(niimg, ensure_ndim=None, atleast_4d=False, dtype=None, return_iterator=False, wildcards=True)` | Niimg-like | checked image or iterator | `ensure_ndim=3` for maps/masks; `ensure_ndim=4` for runs; `atleast_4d=True` turns 3D into one-volume 4D | Surface inputs are out of scope here; route them to `surface-workflows`. |
| `index_img(imgs, index)` | 4D image and integer/slice/list index | 3D image for scalar index, 4D image for slice/list | Uses Python 0-based indexing | Scalar indexing drops the time axis. |
| `iter_img(imgs)` | 4D image | iterator of 3D images | Iterates over the last dimension | Convert to list only for small data; otherwise stream. |
| `concat_imgs(niimgs, dtype=np.float32, ensure_ndim=None, auto_resample=False, ...)` | iterable or glob of 3D/4D images | 4D image | Concatenates along time/4th dimension | Different FOVs fail unless `auto_resample=True`, which resamples to the first image. |

## Image Creation and Math

| API | Main inputs | Returns | Shape notes | Gotchas |
| --- | --- | --- | --- | --- |
| `mean_img(imgs, target_affine=None, target_shape=None, ...)` | 3D/4D/list Niimg-like | 3D mean image | Averages over time and/or image list | Optional target grid triggers resampling. |
| `new_img_like(ref_niimg, data, affine=None, copy_header=False)` | reference image/path/list, array | new image matching reference type | `data` drives output shape | Use a matching affine for spatial meaning; `copy_header=True` can preserve metadata when appropriate. |
| `math_img(formula, copy_header_from=None, **imgs)` | NumPy expression string and named images | image from formula result | Named images must share compatible shapes/affines | `copy_header_from` must name one supplied image; otherwise header defaults are safer. |
| `smooth_img(imgs, fwhm)` | 3D/4D image or list | smoothed image/list | Spatial smoothing only | Use `fwhm=None` or `0` for no smoothing; non-finite values can spread unless handled. |
| `threshold_img(img, threshold, mask_img=None, two_sided=True, cluster_threshold=0, copy=True, copy_header=False)` | image and numeric or percentile threshold | thresholded image | Works on volume maps/runs | Mask must match the image FOV; percentile strings like `"80%"` are accepted. |
| `clean_img(imgs, runs=None, detrend=True, standardize=True, confounds=None, low_pass=None, high_pass=None, t_r=None, ensure_finite=False, mask_img=None, **kwargs)` | 4D image, optional mask/confounds | cleaned 4D image | Cleans along the last/time dimension | Pass `t_r` when filtering; `mask_img` limits cleaning to masked voxels. |

## Resampling

| API | Main inputs | Returns | Shape notes | Gotchas |
| --- | --- | --- | --- | --- |
| `resample_img(img, target_affine=None, target_shape=None, interpolation="continuous", copy=True, order="F", clip=True, fill_value=0, force_resample=True, copy_header=True)` | source image and target grid definition | resampled image | `target_shape` is 3D and requires `target_affine` | No registration is performed. A bad target affine can place all data outside FOV and raise a bounding-box error. |
| `resample_to_img(source_img, target_img, interpolation="continuous", copy=True, order="F", clip=False, fill_value=0, force_resample=True, copy_header=True)` | source image and target reference image | source resampled onto target grid | Output spatial shape/affine match target | Images must already be anatomically aligned; use `interpolation="nearest"` for labels/masks. |

## Masking

| API | Main inputs | Returns | Shape notes | Gotchas |
| --- | --- | --- | --- | --- |
| `compute_epi_mask(epi_img, lower_cutoff=0.2, upper_cutoff=0.85, connected=True, opening=2, exclude_zeros=False, ensure_finite=True, target_affine=None, target_shape=None, ...)` | 3D/4D EPI-like image | 3D binary mask image | 3D input should usually be a mean image | Empty-mask warnings often mean poor contrast, wrong cutoffs, or excessive morphology. |
| `compute_background_mask(data_imgs, border_size=2, connected=False, opening=False, target_affine=None, target_shape=None, ...)` | 3D/4D image with flat background | 3D binary mask image | Uses border values to infer background | Best when background is homogeneous; can fail for cropped or non-flat backgrounds. |
| `compute_brain_mask(target_img, threshold=0.5, connected=True, opening=2, mask_type="whole-brain", ...)` | target image defining desired grid | 3D template-derived mask | Uses shape/affine of target | `mask_type` is `"whole-brain"`, `"gm"`, or `"wm"`; may be empty for odd FOVs. |
| `intersect_masks(mask_imgs, threshold=0.5, connected=True)` | list of 3D binary masks | 3D binary mask image | All masks must share shape/affine | `threshold=1` is strict intersection; `threshold=0` is union. |
| `apply_mask(imgs, mask_img, dtype="f", smoothing_fwhm=None, ensure_finite=True)` | 3D/4D image and 3D binary mask | 2D array | Output is `(n_samples, n_voxels)`; a 3D image yields one sample | Image and mask affines and spatial shapes must match exactly enough for `np.allclose`. |
| `unmask(X, mask_img, order="F")` | 1D feature vector or 2D samples/features array | 3D or 4D image | 1D `X` -> 3D image; 2D `X` -> 4D image | `X.shape[1]` must equal the number of true voxels for 2D input. |

## Signal Arrays

| API | Main inputs | Returns | Shape notes | Gotchas |
| --- | --- | --- | --- | --- |
| `signal.clean(signals, runs=None, detrend=True, standardize="zscore_sample", sample_mask=None, confounds=None, filter="butterworth", low_pass=None, high_pass=None, t_r=2.5, ensure_finite=False, extrapolate=False, **kwargs)` | 2D array, optional confounds/runs/sample mask | cleaned 2D array | `signals.shape == (n_samples, n_features)`; confounds must share `n_samples` | Filtering needs meaningful `t_r`; sample masks can reduce rows; run-specific sample masks must be a list aligned per run. |

## Default Choices

- Use `check_niimg(..., ensure_ndim=3)` for masks and statistical maps.
- Use `check_niimg(..., ensure_ndim=4)` or `atleast_4d=True` for fMRI runs.
- Use `resample_to_img(mask_or_source, target, interpolation="nearest")` for
  masks and labels; use `"continuous"` or `"linear"` for continuous images.
- Use direct `apply_mask`/`unmask` for simple array extraction. Use estimator
  maskers only when the task needs reusable fitted transformers, reports,
  caching, region extraction, or sklearn pipelines.
