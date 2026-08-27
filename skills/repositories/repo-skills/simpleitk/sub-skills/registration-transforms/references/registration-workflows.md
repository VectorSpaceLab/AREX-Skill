# ImageRegistrationMethod Workflows

## Standard Setup

1. Cast or prepare fixed and moving intensity images, commonly to `sitk.sitkFloat32`.
2. Choose an initial transform with the right dimension and model: `TranslationTransform`, `Euler2DTransform`, `Euler3DTransform`, `Similarity*Transform`, `AffineTransform`, `BSplineTransform`, `DisplacementFieldTransform`, or `CompositeTransform`.
3. Set a metric with a `SetMetricAs...` method.
4. Set an optimizer with a `SetOptimizerAs...` method and configure learning rate, iterations, convergence, bounds, scales, or weights as appropriate.
5. Set the interpolator with `SetInterpolator(sitk.sitkLinear)` for intensity registration.
6. Optionally set sampling, masks, optimizer scales, multi-resolution shrink/smoothing, and callbacks.
7. Execute as `out_tx = registration.Execute(fixed, moving)` and resample the moving image onto the fixed grid using `out_tx`.

## Initialization

- Identity transforms are valid but often fail when images have little or no initial overlap.
- `sitk.CenteredTransformInitializer(fixed, moving, transform)` aligns image centers and sets the rotation center for rigid/similarity/affine transforms.
- Use `sitk.CenteredTransformInitializerFilter.GEOMETRY` when physical image geometry is reliable; use moment-based initialization only when intensities and foreground support it.
- For point-based initialization, `LandmarkBasedTransformInitializerFilter` accepts flattened fixed and moving landmark coordinate lists and can initialize rigid or affine transform types.
- For deformable workflows, register a global transform first, then use it as `SetMovingInitialTransform(out_global_tx)` before optimizing a displacement or B-spline transform.

## Metrics

- `SetMetricAsMeanSquares()` is simple and works best for same-modality, comparable intensities.
- `SetMetricAsCorrelation()` is useful when intensities are linearly related and the optimum is internally minimized as a negative value.
- `SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)` is common for multimodal registration; use metric sampling for speed and a fixed seed for reproducibility.
- `SetMetricAsJointHistogramMutualInformation(numberOfHistogramBins=20, varianceForJointPDFSmoothing=1.5)` is another multimodal choice used in SimpleITK examples.
- `SetMetricAsANTSNeighborhoodCorrelation(radius)` supports local neighborhood correlation and is used for displacement-field refinement examples.
- `SetMetricAsDemons(intensityDifferenceThreshold=0.001)` is available in the registration framework, while standalone demons filters also exist outside `ImageRegistrationMethod`.
- All registration metrics are minimized; metrics that conceptually maximize similarity are negated internally.

## Optimizers

- `SetOptimizerAsRegularStepGradientDescent(learningRate, minStep, numberOfIterations, ...)` is a common baseline for translations and rigid transforms.
- `SetOptimizerAsGradientDescent(...)` and `SetOptimizerAsGradientDescentLineSearch(...)` are common for larger transforms; `estimateLearningRate=registration.EachIteration` can stabilize deformable examples.
- `SetOptimizerAsLBFGSB(...)` is used by B-spline examples and supports bounds.
- `SetOptimizerAsExhaustive(numberOfSteps, stepLength)` is useful for a small bounded search space, often after centered initialization.
- `SetOptimizerAsAmoeba`, `SetOptimizerAsPowell`, and `SetOptimizerAsOnePlusOneEvolutionary` are gradient-free alternatives.
- Use `SetOptimizerScalesFromPhysicalShift()`, `SetOptimizerScalesFromIndexShift()`, or `SetOptimizerScalesFromJacobian()` when transform parameters have different units, such as radians and millimeters.
- `SetOptimizerWeights([...])` can freeze or downweight parameters; for example optimizer-weight examples freeze selected Euler3D rotation axes.

## Sampling and Reproducibility

- `registration.SetMetricSamplingStrategy(registration.NONE)` uses all voxel centers and is deterministic but can be slow.
- `registration.SetMetricSamplingStrategy(registration.REGULAR)` samples regularly and perturbs sample positions; `registration.RANDOM` samples with replacement.
- `registration.SetMetricSamplingPercentage(percentage, seed)` controls the sampling fraction and random seed. Use an integer seed such as `42` for reproducible sampled registration.
- The default seed is wall clock time, so repeated sampled registrations can differ unless a seed is supplied.
- Random sampling at `1.0` is not equivalent to `NONE`: it samples with replacement and perturbs within voxels.
- Multi-threaded metric evaluation can introduce tiny numeric variability. For exact smoke tests, temporarily call `sitk.ProcessObject_SetGlobalDefaultNumberOfThreads(1)` when that flat Python binding exists, or `sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(1)` when class-style static methods are exposed.
- When masks are small, rejection-based sampling can leave too few valid points; crop to the mask bounding box or increase sampling instead of only tuning the optimizer.

## Multi-Resolution

- `SetShrinkFactorsPerLevel([4, 2, 1])` or similar creates a coarse-to-fine pyramid.
- `SetSmoothingSigmasPerLevel([2, 1, 0])` or similar smooths each level; by default sigmas are physical units unless changed by `SetSmoothingSigmasAreSpecifiedInPhysicalUnits`.
- Use `AddCommand(sitk.sitkMultiResolutionIterationEvent, callback)` to log level transitions.
- For B-spline transforms, `SetInitialTransformAsBSpline(transform, inPlace, scaleFactors)` adapts the control grid across levels when needed.
- Keep shrink and smoothing vector lengths equal to the number of levels.

## Callbacks and Diagnostics

```python
def report(method):
    print(method.GetOptimizerIteration(), method.GetMetricValue(), method.GetOptimizerPosition())

registration.AddCommand(sitk.sitkIterationEvent, lambda: report(registration))
```

- `GetOptimizerIteration()`, `GetMetricValue()`, `GetOptimizerPosition()`, `GetOptimizerScales()`, `GetCurrentLevel()`, and `GetOptimizerStopConditionDescription()` are useful after or during execution.
- `MetricEvaluate(fixed, moving)` evaluates the configured metric and transforms without running an optimizer; it is useful for assertions and debugging masks/transforms.
- Avoid viewer calls such as `sitk.Show` in automation; return JSON or write explicit files only when requested.

## Output Transform Use

- `Execute(fixed, moving)` returns the optimized transform unless an in-place transform was supplied and modified.
- `SetInitialTransform(transform, inPlace=True)` can mutate the supplied transform object; pass `False` or a copy if callers need the original unchanged.
- `SetFixedInitialTransform(T_f)` and `SetMovingInitialTransform(T_m)` model virtual-domain registration. The effective fixed-to-moving mapping is `T_m(T_opt(T_f^-1(p_fixed)))`.
- After registration, resample the moving image onto the fixed grid with the output transform and linear interpolation for intensities.
- For labels associated with the moving image, reuse the same transform and reference grid but switch to nearest-neighbor interpolation.
- Write/read transforms through the IO sub-skill when persistence is needed; do not make runtime examples depend on repository example files.

## Deformable and Demons Workflows

- Initialize `BSplineTransform` with `sitk.BSplineTransformInitializer(fixed, mesh_size)` and choose a mesh coarse enough for the image size and expected deformation.
- Initialize a displacement field as `sitk.Image(fixed.GetSize(), sitk.sitkVectorFloat64)`, copy fixed image geometry with `CopyInformation(fixed)`, then wrap it in `sitk.DisplacementFieldTransform(field)`.
- Standalone demons filters such as `DemonsRegistrationFilter` and `FastSymmetricForcesDemonsRegistrationFilter` return displacement fields and are outside the `ImageRegistrationMethod` component model.
- For demons with an initial transform, convert the transform to a displacement field on the fixed grid with `TransformToDisplacementFieldFilter`.

## Evidence Anchors

- `docs/source/registrationOverview.rst` documents components, virtual domain transforms, multi-resolution registration, sampling, optimizer scales, callbacks, and reproducibility.
- `Examples/ImageRegistrationMethod1/ImageRegistrationMethod1.py` through `Examples/ImageRegistrationMethod4/ImageRegistrationMethod4.py` show mean squares, correlation, joint histogram MI, Mattes MI, optimizers, sampling, callbacks, and resampling.
- `Examples/ImageRegistrationMethodBSpline*/` show B-spline initialization and LBFGSB/multi-resolution patterns.
- `Examples/ImageRegistrationMethodDisplacement1/ImageRegistrationMethodDisplacement1.py` shows global-then-displacement registration and `CompositeTransform` output.
- `Examples/ImageRegistrationOptimizerWeights/ImageRegistrationOptimizerWeights.py` shows optimizer weights and physical-shift scales.
- `Examples/DemonsRegistration*.py` show standalone demons displacement-field workflows.
- `Testing/Unit/sitkImageRegistrationMethodTests.cxx` covers metric evaluation, transforms, masks, optimizers, sampling seeds, callbacks, and B-spline multi-resolution behavior.
