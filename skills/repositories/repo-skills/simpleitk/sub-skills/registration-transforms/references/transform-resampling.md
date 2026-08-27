# Transform and Resampling Semantics

## Physical-Space Model

- SimpleITK images occupy a physical region described by size, origin, spacing, and direction; transforms operate on physical points, not NumPy array indexes.
- Use `image.TransformIndexToPhysicalPoint(index)` and `image.TransformPhysicalPointToIndex(point)` when debugging coordinate-frame expectations instead of manually combining metadata.
- Global-domain transforms such as `TranslationTransform`, `Euler2DTransform`, `Euler3DTransform`, `Similarity*Transform`, `ScaleTransform`, and `AffineTransform` are unbounded and usually have parameters such as matrix/rotation, center, and translation.
- Bounded-domain transforms such as `BSplineTransform` and `DisplacementFieldTransform` are identity outside their defined domain and must be initialized on a spatial domain compatible with the images.
- `CompositeTransform` applies transforms in stack order: for `CompositeTransform([T0, T1])` followed by `AddTransform(T2)`, points are mapped as `T0(T1(T2(point)))`; in registration, only the last transform's parameters are optimized when a composite is the optimized transform.

## Transform Direction

- SimpleITK registration estimates a transform that maps points from the fixed image coordinate system to the moving image coordinate system.
- To resample a moving image onto the fixed grid, pass the registration output transform directly to `Resample` or `ResampleImageFilter`; do not invert it unless the transform you already have maps moving-to-fixed.
- If an external tool reports a moving-to-fixed transform, invert it with `transform.GetInverse()` before using it as the `Resample` transform for moving-on-fixed output.
- Test transform direction with a single known point: fixed-grid physical point -> transform -> moving-image physical point that should sample corresponding anatomy.

## Resampling Grids

- Resampling has four parts: input image to sample, output grid, transform from output-grid coordinates to input-image coordinates, and interpolator.
- The most common registration output is `sitk.Resample(moving, fixed, transform=out_tx, interpolator=sitk.sitkLinear, defaultPixelValue=...)`, where the output grid is copied from `fixed`.
- `ResampleImageFilter` is clearer for multi-step setup: `SetReferenceImage(fixed)`, `SetTransform(out_tx)`, `SetInterpolator(...)`, `SetDefaultPixelValue(...)`, then `Execute(moving)`.
- If no reference image is used, set size, output origin, spacing, and direction explicitly; otherwise the output grid may be spatially unrelated to either input image.
- Pixels whose output-grid physical points map outside the sampled input image are filled with `defaultPixelValue`.

## Interpolation Choices

- Use `sitk.sitkLinear` for CT/MR/PET, scalar probability maps, and most continuous intensities.
- Use `sitk.sitkNearestNeighbor` for labels, masks, connected components, and categorical values; linear, B-spline, or Gaussian interpolation can create labels that never existed.
- Cast integer intensity images to `sitk.sitkFloat32` before registration when metrics or preprocessing expect continuous numeric values; resampling labels should preserve the label pixel type when possible.
- Choose a sentinel `defaultPixelValue` that is meaningful for the image type: background label `0`, black intensity `0`, or a visibly distinct diagnostic value during debugging.

## Common Patterns

```python
registration = sitk.ImageRegistrationMethod()
registration.SetMetricAsMeanSquares()
registration.SetOptimizerAsRegularStepGradientDescent(learningRate=1.0, minStep=1e-4, numberOfIterations=100)
registration.SetInitialTransform(sitk.TranslationTransform(fixed.GetDimension()))
registration.SetInterpolator(sitk.sitkLinear)
out_tx = registration.Execute(fixed, moving)
resampled = sitk.Resample(moving, fixed, transform=out_tx, interpolator=sitk.sitkLinear, defaultPixelValue=0.0)
```

```python
label_resampled = sitk.Resample(label_image, reference_image, transform=label_tx, interpolator=sitk.sitkNearestNeighbor, defaultPixelValue=0)
```

## Transform Families

- `TranslationTransform(dim)` is useful for simple shifts and for deterministic smoke tests.
- `Euler2DTransform()` and `Euler3DTransform()` handle rigid rotation plus translation; set or initialize the rotation center carefully.
- `AffineTransform(dim)` handles translation, rotation, scale, shear, and skew; optimizer scales are important because parameter units differ.
- `BSplineTransformInitializer(fixed, mesh_size)` creates a bounded deformable transform over the fixed image domain for free-form deformation registration.
- `DisplacementFieldTransform(field)` wraps a vector image, usually `sitk.sitkVectorFloat64`, whose geometry should copy the fixed image.
- `TransformToDisplacementFieldFilter` converts a transform into a displacement field on a reference grid when a demons or field-based workflow needs an initial field.

## Inverse-Transform Pitfalls

- A black or mostly default-valued resample often means the grid and transform direction do not overlap.
- Calling `out_tx.GetInverse()` after `ImageRegistrationMethod.Execute(fixed, moving)` and then resampling `moving` to `fixed` is usually wrong.
- Some transforms are not analytically invertible or may fail to invert if singular; test `GetInverse()` in a small guard before relying on it.
- Composite transform inverse order is not the same as component order; prefer `composite.GetInverse()` over manually reversing unless you are validating each component.

## Evidence Anchors

- `docs/source/fundamentalConcepts.rst` defines images as physical objects, global and bounded transforms, composite stack semantics, resampling components, interpolator guidance, and black-resample causes.
- `docs/source/registrationOverview.rst` states the registration transform maps fixed coordinates to moving coordinates.
- `Examples/ImageRegistrationMethod1/ImageRegistrationMethod1.py` and related examples show `ResampleImageFilter` with `SetReferenceImage(fixed)` and `SetTransform(outTx)`.
- `Examples/LandmarkRegistration/LandmarkRegistration.py` shows `LandmarkBasedTransformInitializerFilter` followed by procedural `Resample`.
- `Wrapping/Python/tests/sitkTransformTests.py` exercises transform families, `CompositeTransform`, pickling, and `GetInverse()`.
