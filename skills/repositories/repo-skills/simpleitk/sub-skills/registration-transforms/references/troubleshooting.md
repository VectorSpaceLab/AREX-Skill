# Registration and Transform Troubleshooting

## No Overlap or Immediate Metric Failure

Symptoms:

- Registration throws during metric evaluation.
- Metric valid point count is zero or tiny.
- Optimizer moves wildly or stops immediately.

Checks:

- Confirm fixed and moving dimensions match and both are scalar intensity images for intensity metrics.
- Inspect `GetOrigin()`, `GetSpacing()`, `GetDirection()`, and `GetSize()` for both images; registration uses physical space, not array position.
- Initialize with `CenteredTransformInitializer` or landmarks instead of identity when image origins, centers, or orientations differ.
- If masks are used, verify mask pixel type, physical metadata, and overlap with the fixed/moving image after initialization.
- Use `MetricEvaluate(fixed, moving)` with a known transform to separate metric/mask problems from optimizer problems.

## Black or Mostly Default Resample

Likely causes:

- The transform direction is reversed.
- The output grid is wrong or unrelated to the intended fixed image.
- Origin, spacing, or direction were lost during array conversion or preprocessing.
- The images truly do not overlap after applying the transform.

Fixes:

- For `out_tx = registration.Execute(fixed, moving)`, resample with `sitk.Resample(moving, fixed, transform=out_tx, ...)`.
- Do not call `out_tx.GetInverse()` unless you have proven your transform maps moving-to-fixed and the resampler needs fixed-to-moving.
- Use `ResampleImageFilter.SetReferenceImage(fixed)` or pass the reference image to procedural `Resample`.
- Set a diagnostic `defaultPixelValue` distinct from valid image background while debugging.
- Transform a few output-grid physical points and verify they land inside the moving image physical bounds.

## Wrong Inverse or Composite Order

- Registration transforms map fixed-to-moving; resampling moving-on-fixed expects fixed-to-moving.
- `CompositeTransform` applies the last-added transform first; manual mental order is easy to reverse.
- Only the last transform in an optimized composite has its parameters changed by `ImageRegistrationMethod`.
- `GetInverse()` can fail for non-invertible affine matrices or unsupported/non-invertible deformable transforms; catch exceptions and validate.
- When combining global and displacement transforms, follow the source pattern: set the global transform as a moving initial transform before optimizing the displacement, then write a composite of global plus displacement.

## Bad Masks and Sampling

- Metric masks must be images with compatible dimensions and physical metadata.
- Very small masks plus `RANDOM` or `REGULAR` metric sampling can reject most samples and leave too few points.
- For small masks, crop images to a mask bounding box, use `registration.NONE`, or increase sampling percentage before changing optimizer settings.
- `RANDOM` sampling at `1.0` is still random sampling with replacement and within-voxel perturbation; use `NONE` for all voxel centers.
- Fixed and moving masks are applied in their respective image domains; debug each domain separately.

## Nondeterministic Results

- Pass an integer seed to `SetMetricSamplingPercentage(percentage, seed)` instead of relying on wall-clock defaults.
- Use `registration.NONE` sampling for deterministic small tests where runtime is not a concern.
- For exact comparisons, temporarily force one global thread via available SimpleITK process-object static methods, then restore the previous value.
- Optimizer convergence can still be sensitive to image type, spacing, smoothing, and scales; compare tolerances rather than raw transform parameter equality for real images.

## Pixel Type or Dimension Errors

- Cast fixed and moving intensity inputs to `sitk.sitkFloat32` for registration examples unless a metric/filter explicitly supports the original type.
- Ensure fixed and moving images have the same dimension; 2D transforms cannot register 3D images and vice versa.
- Use `sitk.sitkVectorFloat64` with the right number of components when constructing displacement fields.
- Use `sitk.sitkNearestNeighbor` when resampling label images; linear interpolation creates invalid labels and can change pixel type expectations.
- If a filter reports unsupported pixel type, route casting and image construction details to [../../image-core/SKILL.md](../../image-core/SKILL.md).

## Optimizer Stalls or Diverges

- Set optimizer scales with `SetOptimizerScalesFromPhysicalShift()` or related methods for transforms mixing rotation and translation.
- Lower the learning rate or use `RegularStepGradientDescent`/line search when gradient descent overshoots.
- Increase iterations only after initialization, overlap, sampling, and scales are correct.
- Use multi-resolution shrink/smoothing to improve capture range for large shifts or rotations.
- Freeze irrelevant parameters with `SetOptimizerWeights` when prior knowledge constrains motion.

## Optional Wrappers Missing

Symptoms:

- `AttributeError: module 'SimpleITK' has no attribute 'ElastixImageFilter'`.
- `AttributeError: module 'SimpleITK' has no attribute 'TransformixImageFilter'`.
- `GetDefaultParameterMap`, `ReadParameterFile`, or `WriteParameterFile` is absent in the installed package.

Fixes:

- Guard wrapper paths with `hasattr(sitk, "ElastixImageFilter")` and `hasattr(sitk, "TransformixImageFilter")`.
- Use built-in `ImageRegistrationMethod` and SimpleITK `Transform` classes when wrappers are absent.
- Route build or packaging questions to [../../builds-and-wrapping/SKILL.md](../../builds-and-wrapping/SKILL.md); do not state that the standard wheel always includes wrappers.

## Minimal Debug Checklist

1. Print fixed/moving size, spacing, origin, direction, pixel type, and dimension.
2. Print initial transform name, dimension, fixed parameters, and parameters.
3. Verify at least one transformed fixed physical point lands inside the moving image extent.
4. Run `MetricEvaluate` before the optimizer when possible.
5. Add an iteration callback for metric, position, level, and stop condition.
6. Resample moving onto fixed with a distinct default pixel value and inspect overlap.
7. Switch labels to nearest-neighbor interpolation before judging segmentation quality.

## Evidence Anchors

- `docs/source/registrationOverview.rst` documents no-overlap initialization failures, sampling randomness, mask rejection with insufficient samples, optimizer scales, callbacks, and thread-related reproducibility.
- `docs/source/fundamentalConcepts.rst` documents physical image metadata, resampling grids, default pixel values, and inverse-transform causes of black outputs.
- `Examples/ImageRegistrationMethod*.py` and `Examples/DemonsRegistration*.py` show callbacks, stop-condition reporting, resampling, and displacement-field outputs.
- `Testing/Unit/sitkImageRegistrationMethodTests.cxx` covers masks, sampling strategies, fixed/moving initial transforms, optimizer weights, and many optimizer families.
