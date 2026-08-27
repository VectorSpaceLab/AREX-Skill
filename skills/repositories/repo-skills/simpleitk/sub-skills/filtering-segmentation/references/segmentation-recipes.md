# Segmentation Recipes

These recipes assume an in-memory `sitk.Image` and avoid file IO, viewers, network access, and external datasets. They are distilled from SimpleITK filtering examples, generated filter metadata, and installed package behavior. Use the IO, image-core, and registration/transform sub-skills for data loading, metadata conversion, or resampling outside these recipes.

## Recipe: Otsu Then Validate

Use when the prompt says "automatically threshold", "make a foreground mask", or "separate bright object from background".

```python
import SimpleITK as sitk

image = sitk.Cast(image, sitk.sitkFloat32)
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=[1.0] * image.GetDimension())
otsu = sitk.OtsuThresholdImageFilter()
otsu.SetInsideValue(0)
otsu.SetOutsideValue(1)
otsu.SetNumberOfHistogramBins(128)
mask = otsu.Execute(smoothed)
threshold = otsu.GetThreshold()

labels = sitk.ConnectedComponent(sitk.Cast(mask, sitk.sitkUInt8))
shape = sitk.LabelShapeStatisticsImageFilter()
shape.Execute(labels)
summary = [(label, shape.GetNumberOfPixels(label), shape.GetBoundingBox(label)) for label in shape.GetLabels()]
```

Why this pattern works:

- Otsu chooses the threshold from the image histogram; keep the object filter if you need `GetThreshold()`.
- `InsideValue=0`, `OutsideValue=1` matches the common bright-foreground mask pattern.
- Connected components plus shape statistics turns a mask into countable objects and catches empty masks early.

## Recipe: Manual Binary Threshold

Use when clinical, experimental, or prompt-provided thresholds are more important than a histogram-derived threshold.

```python
if lower > upper:
    raise ValueError("lower threshold must not exceed upper threshold")
mask = sitk.BinaryThreshold(image, lowerThreshold=lower, upperThreshold=upper, insideValue=1, outsideValue=0)
mask = sitk.Cast(mask, sitk.sitkUInt8)
```

Guardrails:

- `lowerThreshold <= upperThreshold`; SimpleITK raises if the range is inverted.
- Threshold values are interpreted in the input pixel intensity scale, not display windowing units.
- Keep spatial metadata unchanged by filtering in memory; use image-core guidance if comparing spacing/origin/direction.

## Recipe: Morphology Clean-Up

Use after thresholding when the mask has small holes, speckles, or jagged binary structures.

```python
mask = sitk.Cast(mask, sitk.sitkUInt8)
radius = [1] * mask.GetDimension()
opened = sitk.BinaryMorphologicalOpening(mask, radius, sitk.sitkBall, 1, 0)
closed = sitk.BinaryMorphologicalClosing(opened, radius, sitk.sitkBall, 1, 0)
```

Guardrails:

- Binary morphology assumes integer masks and foreground/background values that match the filter parameters.
- Radius vectors must match image dimension.
- Increase radius gradually; large radii can erase thin structures.

## Recipe: Connected Threshold From Seeds

Use when the prompt gives seed indexes and intensity bounds, such as "segment the bright object connected to `(80, 95)` between 150 and 255".

```python
seg = sitk.ConnectedThresholdImageFilter()
seg.SetLower(lower)
seg.SetUpper(upper)
seg.SetReplaceValue(1)
seg.SetConnectivity(sitk.ConnectedThresholdImageFilter.FaceConnectivity)
for seed in seeds:
    seg.AddSeed([int(v) for v in seed])
mask = seg.Execute(image)
```

Checklist:

- Seeds are **index coordinates**, not physical points. Convert physical points through image-core helpers before adding seeds.
- Seed length must equal `image.GetDimension()`.
- Inspect `image.GetPixel(*seed)` before executing if a seed unexpectedly fails to grow.
- Use `FullConnectivity` only when diagonal connections should merge regions.

## Recipe: Confidence Connected

Use when the seed intensity is representative but exact lower/upper thresholds are unknown.

```python
seg = sitk.ConfidenceConnectedImageFilter()
seg.SetMultiplier(2.5)
seg.SetNumberOfIterations(2)
seg.SetInitialNeighborhoodRadius(1)
seg.SetReplaceValue(1)
for seed in seeds:
    seg.AddSeed(seed)
mask = seg.Execute(image)
mean = seg.GetMean()
variance = seg.GetVariance()
```

Tune `Multiplier` upward if the region is too small and downward if it leaks. Increase `InitialNeighborhoodRadius` only when the seed neighborhood is homogeneous and the image is not tiny.

## Recipe: Fast Marching Segmentation

Use when a front should propagate through a speed image, often after smoothing, gradient magnitude, and sigmoid preprocessing.

```python
smooth = sitk.CurvatureAnisotropicDiffusionImageFilter()
smooth.SetTimeStep(0.125)
smooth.SetNumberOfIterations(5)
smooth.SetConductanceParameter(9.0)
smoothed = smooth.Execute(sitk.Cast(image, sitk.sitkFloat32))

gradient = sitk.GradientMagnitudeRecursiveGaussianImageFilter()
gradient.SetSigma(sigma)
gradient_image = gradient.Execute(smoothed)

sigmoid = sitk.SigmoidImageFilter()
sigmoid.SetOutputMinimum(0.0)
sigmoid.SetOutputMaximum(1.0)
sigmoid.SetAlpha(alpha)
sigmoid.SetBeta(beta)
speed = sigmoid.Execute(gradient_image)

march = sitk.FastMarchingImageFilter()
for seed in seeds:
    march.AddTrialPoint([int(seed[0]), int(seed[1]), 0.0])
march.SetStoppingValue(stopping_time)
arrival = march.Execute(speed)
mask = sitk.BinaryThreshold(arrival, 0.0, time_threshold, 1, 0)
```

Fast marching guardrails:

- The speed image must be non-negative and dimensionally compatible with the trial points.
- In the example-style `AddTrialPoint` form, provide one index per dimension plus an initial trial value.
- `StoppingValue` limits computation; `time_threshold` controls the final segmentation size.
- Validate the arrival image before thresholding when the result is empty or unexpectedly huge.

## Recipe: N4 Bias Field Correction

Use for MRI-like scalar images with smooth multiplicative intensity bias. The source N4 example is data/runtime dependent, so keep N4 out of smoke tests unless a task explicitly asks for it and the image size is bounded.

```python
input_image = sitk.Cast(input_image, sitk.sitkFloat32)
mask = sitk.OtsuThreshold(input_image, 0, 1, 200)

shrink_factor = 2
work_image = sitk.Shrink(input_image, [shrink_factor] * input_image.GetDimension())
work_mask = sitk.Shrink(mask, [shrink_factor] * mask.GetDimension())

corrector = sitk.N4BiasFieldCorrectionImageFilter()
corrector.SetMaximumNumberOfIterations([50, 50, 30, 20])
corrected_work = corrector.Execute(work_image, work_mask)
log_bias = corrector.GetLogBiasFieldAsImage(input_image)
corrected_full_resolution = input_image / sitk.Exp(log_bias)
```

N4 guardrails:

- Use positive real-valued intensities; negative or near-zero values can produce poor log-space behavior.
- Supply a mask when foreground occupies a small fraction of the image.
- Use shrink factors to estimate the field cheaply, then reconstruct the log bias field on the original image.
- Keep the corrected full-resolution image from `input_image / sitk.Exp(log_bias)`, not just the shrunk corrected image.

## Recipe: Statistics Validation

After any segmentation, validate before writing files or using the mask downstream.

```python
labels = sitk.ConnectedComponent(sitk.Cast(mask, sitk.sitkUInt8))
shape = sitk.LabelShapeStatisticsImageFilter()
shape.SetComputeFeretDiameter(False)
shape.SetComputeOrientedBoundingBox(False)
shape.Execute(labels)

if shape.GetNumberOfLabels() == 0:
    raise ValueError("segmentation produced no connected objects")
for label in shape.GetLabels():
    print(label, shape.GetNumberOfPixels(label), shape.GetPhysicalSize(label), shape.GetCentroid(label))
```

Prefer `GetNumberOfPixels`, `GetBoundingBox`, `GetCentroid`, and `GetPhysicalSize` as first checks. Enable expensive metrics such as Feret diameter or oriented bounding boxes only when specifically needed.
