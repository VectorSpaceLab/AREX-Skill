---
name: registration-transforms
description: "Configure SimpleITK transforms, resampling,
  ImageRegistrationMethod workflows, and optional elastix/transformix wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK Registration and Transforms

Use this sub-skill when a task involves registration, `ImageRegistrationMethod`, image-to-image metrics, optimizers, transform initialization, `Resample`, displacement fields, `CompositeTransform`, or optional `ElastixImageFilter`/`TransformixImageFilter` wrappers.

## Route by Task

- For transform direction, physical-space semantics, resampling grids, interpolation, inverse-transform mistakes, and label-vs-intensity interpolation, read [transform-resampling](references/transform-resampling.md).
- For `ImageRegistrationMethod` setup, initialization, metrics, optimizers, multi-resolution, reproducibility, callbacks, and output-transform use, read [registration-workflows](references/registration-workflows.md).
- For optional `ElastixImageFilter`, `TransformixImageFilter`, parameter maps, and build-dependent availability checks, read [elastix-transformix](references/elastix-transformix.md).
- For black resamples, no-overlap failures, bad masks/sampling, nondeterminism, type mismatches, and missing optional wrappers, read [troubleshooting](references/troubleshooting.md).
- To validate a local install with a deterministic generated-image translation registration and resample, run [registration_smoke.py](scripts/registration_smoke.py).

## Boundary Notes

- Use [../io-and-data/SKILL.md](../io-and-data/SKILL.md) for `ReadImage`, `WriteImage`, transform file IO, ImageIO backend discovery, DICOM, and metadata tags.
- Use [../filtering-segmentation/SKILL.md](../filtering-segmentation/SKILL.md) for preprocessing filters, masks created by thresholding/morphology, segmentation, and label statistics.
- Use [../builds-and-wrapping/SKILL.md](../builds-and-wrapping/SKILL.md) for building SimpleITK, Python wrapping, and enabling optional elastix/transformix wrappers.
- Use [../image-core/SKILL.md](../image-core/SKILL.md) for image dimensions, spacing/origin/direction, physical coordinates, pixel IDs, and NumPy conversion fundamentals.

## Essential Rules

- Import the public package as `import SimpleITK as sitk`; the Python distribution name is `simpleitk`.
- Registration output transforms map physical points from the fixed image domain to the moving image domain; pass that transform directly when resampling the moving image onto the fixed image grid.
- Treat images and transforms in physical space: spacing, origin, direction, transform center, and fixed/moving image roles are part of correctness.
- Use `sitk.sitkLinear` for continuous intensity images and `sitk.sitkNearestNeighbor` for labels; linear interpolation can invent invalid label values.
- For reproducible sampled registration, pass a fixed seed to `SetMetricSamplingPercentage` and consider forcing one global thread during smoke tests or exact comparisons.
- Guard every elastix/transformix path with `hasattr(sitk, "ElastixImageFilter")` and `hasattr(sitk, "TransformixImageFilter")`; wrappers are optional and were absent from the inspected wheel even though source wrappers exist.
