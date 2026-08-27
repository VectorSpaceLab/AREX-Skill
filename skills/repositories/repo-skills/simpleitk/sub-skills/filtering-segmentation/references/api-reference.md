# API Reference

This is a concise, representative API map for common SimpleITK filtering and segmentation tasks. The public Python import is always `import SimpleITK as sitk`; the Python distribution name is `simpleitk`. The inspected wheel version was 2.5.5, while the checkout version metadata indicated current branch/latest development. Optional `ElastixImageFilter` and `TransformixImageFilter` wrappers were absent in the inspected wheel, so this sub-skill does not depend on them.

## Smoothing and Sources

| API | Representative Call | Notes |
| --- | --- | --- |
| `sitk.GaussianSource` | `sitk.GaussianSource(sitk.sitkFloat32, [64, 64], [10, 10], [32, 32], 255)` | Deterministic source image; useful for examples and smoke tests. |
| `sitk.SmoothingRecursiveGaussian` | `sitk.SmoothingRecursiveGaussian(image, sigma=[1, 1, 1], normalizeAcrossScale=False)` | IIR Gaussian; sigma is in physical spacing units. Output is real-valued. |
| `sitk.SmoothingRecursiveGaussianImageFilter` | `f.SetSigma([1.5] * image.GetDimension()); out = f.Execute(image)` | Use object pattern for logging, callbacks, and reuse. |
| `sitk.DiscreteGaussian` | `sitk.DiscreteGaussian(image, variance=[1, 1, 1], maximumKernelWidth=32, maximumError=0.01, useImageSpacing=True)` | Discrete separable Gaussian; variance honors spacing by default. |

## Thresholding and Morphology

| API | Representative Call | Notes |
| --- | --- | --- |
| `sitk.BinaryThreshold` | `sitk.BinaryThreshold(image, lowerThreshold=0.0, upperThreshold=255.0, insideValue=1, outsideValue=0)` | Values within the inclusive range become `insideValue`; common output is `sitkUInt8`. |
| `sitk.BinaryThresholdImageFilter` | `f.SetLowerThreshold(lower); f.SetUpperThreshold(upper); f.SetInsideValue(1); f.SetOutsideValue(0)` | Prefer for incremental parameter changes or diagnostics. |
| `sitk.OtsuThreshold` | `sitk.OtsuThreshold(image, 0, 1, 128)` | Compact foreground/background split; use `0, 1` for bright foreground mask patterns. |
| `sitk.OtsuThresholdImageFilter` | `f.SetNumberOfHistogramBins(128); mask = f.Execute(image); t = f.GetThreshold()` | Use object pattern when the computed threshold must be reported. |
| `sitk.BinaryMorphologicalOpening` | `sitk.BinaryMorphologicalOpening(mask, [1, 1], sitk.sitkBall, 1, 0)` | Removes small foreground speckles from integer masks. |
| `sitk.BinaryMorphologicalClosing` | `sitk.BinaryMorphologicalClosing(mask, [1, 1], sitk.sitkBall, 1, 0)` | Fills small holes or gaps in integer masks. |

## Seeded Segmentation

| API | Representative Call | Notes |
| --- | --- | --- |
| `sitk.ConnectedThresholdImageFilter` | `f.AddSeed([x, y]); f.SetLower(lower); f.SetUpper(upper); f.SetReplaceValue(1); mask = f.Execute(image)` | Grows connected pixels within inclusive bounds. Seeds are indexes. |
| Connectivity enum | `f.SetConnectivity(sitk.ConnectedThresholdImageFilter.FullConnectivity)` | Default is face connectivity; full connectivity includes diagonals. |
| `sitk.ConfidenceConnectedImageFilter` | `f.AddSeed(seed); f.SetMultiplier(2.5); f.SetNumberOfIterations(2); mask = f.Execute(image)` | Computes seed-region mean/variance and iteratively refines region. |
| Measurements | `f.GetMean(); f.GetVariance()` | Available after confidence connected execution. |

## Fast Marching

| API | Representative Call | Notes |
| --- | --- | --- |
| `sitk.FastMarchingImageFilter` | `f.AddTrialPoint([x, y, 0.0]); f.SetStoppingValue(50.0); arrival = f.Execute(speed)` | Produces an arrival-time image from a non-negative speed image. |
| Trial point list | `f.SetTrialPoints([[70, 70, 0.0], [200, 180, 0.0]])` | Example-style entries contain one index per dimension plus an initial value. |
| Arrival threshold | `sitk.BinaryThreshold(arrival, 0.0, time_threshold, 1, 0)` | Threshold the time map to obtain a segmentation mask. |

## N4 Bias Correction

| API | Representative Call | Notes |
| --- | --- | --- |
| Procedural N4 | `sitk.N4BiasFieldCorrection(image, mask)` | Accepts a real-valued image and optional mask. Object pattern is clearer for iteration controls. |
| Object N4 | `corrector = sitk.N4BiasFieldCorrectionImageFilter(); corrected = corrector.Execute(image, mask)` | Defaults use multiple fitting levels; tune iterations for runtime. |
| Iterations | `corrector.SetMaximumNumberOfIterations([50, 50, 30, 20])` | The vector length controls the number of fitting levels. |
| Full-resolution field | `log_bias = corrector.GetLogBiasFieldAsImage(reference_image)` | Apply with `reference_image / sitk.Exp(log_bias)` after shrink-factor fitting. |
| Mask label | `corrector.SetUseMaskLabel(True); corrector.SetMaskLabel(1)` | Default mask label behavior uses label `1`; set `UseMaskLabel(False)` to use all nonzero mask voxels. |

## Label Statistics

| API | Representative Call | Notes |
| --- | --- | --- |
| `sitk.LabelShapeStatisticsImageFilter` | `shape.Execute(label_image)` | Object-only; label image must use an integer pixel type. |
| Labels | `shape.GetLabels(); shape.GetNumberOfLabels(); shape.HasLabel(1)` | Run after `Execute`. |
| Size/location | `shape.GetNumberOfPixels(label); shape.GetBoundingBox(label); shape.GetCentroid(label)` | Bounding box order is index values followed by size values. |
| Physical metrics | `shape.GetPhysicalSize(label); shape.GetPerimeter(label); shape.GetRoundness(label)` | Physical values depend on image spacing. |
| Expensive metrics | `shape.SetComputeFeretDiameter(True); shape.SetComputeOrientedBoundingBox(True)` | Enable only when required; they increase compute and memory use. |

## Minimal Combined Example

```python
import SimpleITK as sitk

image = sitk.GaussianSource(sitk.sitkFloat32, [64, 64], [10, 10], [32, 32], 200)
smoothed = sitk.SmoothingRecursiveGaussian(image, [1.0, 1.0])
otsu = sitk.OtsuThresholdImageFilter()
otsu.SetInsideValue(0)
otsu.SetOutsideValue(1)
mask = otsu.Execute(smoothed)
labels = sitk.ConnectedComponent(sitk.Cast(mask, sitk.sitkUInt8))
shape = sitk.LabelShapeStatisticsImageFilter()
shape.Execute(labels)
print(otsu.GetThreshold(), shape.GetNumberOfLabels())
```
