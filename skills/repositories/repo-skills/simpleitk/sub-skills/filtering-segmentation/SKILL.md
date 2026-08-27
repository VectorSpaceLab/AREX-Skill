---
name: filtering-segmentation
description: "Apply SimpleITK filters for smoothing, thresholding, morphology,
  segmentation, N4 bias correction, and label-statistics validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK Filtering and Segmentation

Use this sub-skill when a task asks to apply SimpleITK filters procedurally or with `*ImageFilter` objects, smooth or threshold an image, run connected/confidence region growing, use fast marching, correct bias with N4, inspect filter parameters, or validate segmentation output with label statistics.

## Route by Task

- For choosing between procedural `sitk.FilterName(image, ...)` calls and reusable `sitk.FilterNameImageFilter()` objects, use [filter-patterns](references/filter-patterns.md).
- For source image generators, dimensional parameter vectors, event/progress callbacks, and reusable filter-object templates, use [filter-patterns](references/filter-patterns.md).
- For Otsu/manual thresholding, connected/confidence connected region growing, fast marching, N4 correction, and label-statistics validation, use [segmentation-recipes](references/segmentation-recipes.md).
- For representative Python signatures, defaults, and compact examples for smoothing, thresholding, segmentation, N4, and statistics filters, use [api-reference](references/api-reference.md).
- For pixel type and dimension errors, seed or mask mistakes, expensive filters, validation surprises, and accidental viewer calls, use [troubleshooting](references/troubleshooting.md).
- To check a local install with tiny synthetic images and no file IO or viewer, run [filter_segmentation_smoke.py](scripts/filter_segmentation_smoke.py).

## Boundary Notes

- Use the sibling [io-and-data](../io-and-data/SKILL.md) sub-skill for `ReadImage`, `WriteImage`, DICOM discovery, ImageIO choices, and transform file IO.
- Use the sibling [image-core](../image-core/SKILL.md) sub-skill for pixel ID selection, image dimensions, spacing/origin/direction, metadata, and array/image conversion fundamentals.
- Use the sibling [registration-transforms](../registration-transforms/SKILL.md) sub-skill for registration frameworks, transform initialization, resampling semantics, and transform composition.
- Do not rely on optional elastix/transformix wrappers for filtering workflows; they are build-dependent and were not exposed by the inspected wheel.

## Common Entry Points

- `sitk.GaussianSource(...)` creates deterministic synthetic images for examples and smoke tests.
- `sitk.SmoothingRecursiveGaussian(image, sigma, normalizeAcrossScale=False)` and `sitk.DiscreteGaussian(image, variance, ...)` handle Gaussian smoothing with different performance/spacing behavior.
- `sitk.BinaryThreshold(...)`, `sitk.OtsuThreshold(...)`, `sitk.ConnectedThresholdImageFilter()`, and `sitk.ConfidenceConnectedImageFilter()` cover common binary and seeded segmentation workflows.
- `sitk.FastMarchingImageFilter()` creates arrival-time maps from trial points; threshold the time map to obtain a segmentation.
- `sitk.N4BiasFieldCorrectionImageFilter()` corrects slowly varying intensity bias when given a real-valued image and usually a mask.
- `sitk.LabelShapeStatisticsImageFilter()` validates label images by object count, bounding boxes, centroids, physical size, perimeter, and shape metrics.
