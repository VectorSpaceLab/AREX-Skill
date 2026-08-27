---
name: data-io-signal
description: "Handle Nilearn Niimg image I/O, volume image operations,
  masking/unmasking, and signal cleaning with tiny no-network checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Nilearn Data I/O and Signal Skill

Use this sub-skill when the task is about low-level Nilearn volume images and
array time series: loading 3D/4D Niimg inputs, creating new NIfTI images,
resampling, smoothing, thresholding, applying or computing masks, and cleaning
signals with confounds or sample masks.

## Route Tasks

- **Image input validation:** Use `nilearn.image.load_img` and
  `nilearn.image.check_niimg` for path, glob, `pathlib.Path`, or in-memory
  nibabel inputs. See [data formats](references/data-formats.md) and
  [API reference](references/api-reference.md).
- **Image transforms:** Use `index_img`, `iter_img`, `concat_imgs`, `mean_img`,
  `new_img_like`, `math_img`, `resample_img`, `resample_to_img`, `smooth_img`,
  `threshold_img`, and `clean_img`. See [workflows](references/workflows.md).
- **Masking:** Use `compute_epi_mask`, `compute_background_mask`,
  `compute_brain_mask`, `intersect_masks`, `apply_mask`, and `unmask` for
  direct image-to-array workflows. See [API reference](references/api-reference.md).
- **Signal arrays:** Use `nilearn.signal.clean` for 2D arrays shaped
  `(n_samples, n_features)`, confounds, run labels, temporal filtering,
  scrubbing, and standardization. See [data formats](references/data-formats.md).
- **Smoke checks:** Run the bundled no-network script:
  `python scripts/smoke_image_signal.py` from this sub-skill directory.

## Boundaries

- Route estimator objects such as `NiftiMasker`, labels/spheres maskers,
  region extraction, and scikit-learn pipeline integration to `maskers-regions`.
- Route surface mesh/image workflows, `SurfaceImage`, and `vol_to_surf` to
  `surface-workflows`.
- Route plotting displays, reports, HTML views, and figure export to
  `plotting-reporting`.
- Keep examples no-network by generating tiny `numpy` arrays and
  `nibabel.Nifti1Image` objects in memory.

## Quick Checklist

1. Confirm dimensionality with `check_niimg(..., ensure_ndim=3 or 4)` before
   assuming a 3D map or 4D run.
2. Compare both `shape[:3]` and `affine` before `apply_mask`; resample to a
   shared field of view before masking.
3. Ensure masks are 3D, binary, non-empty, and in the same field of view as
   the image.
4. Treat `apply_mask` output as `(n_samples, n_voxels)` and `signal.clean`
   input as `(n_samples, n_features)`.
5. Pass `t_r` when using temporal filters (`low_pass` or `high_pass`) and make
   confounds/sample masks align to the original number of time points.

## References

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Data formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/smoke_image_signal.py)
