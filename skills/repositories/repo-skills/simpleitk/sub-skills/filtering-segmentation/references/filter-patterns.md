# Filter Patterns

SimpleITK exposes most filters in two Python styles: a procedural function for one-off calls and an object-oriented `*ImageFilter` class for tuning, measurements, callbacks, and repeated execution. This reference is distilled from the generated filter catalog, SimpleITK filter documentation, examples, tests, and installed package inspection.

## Choose a Pattern

| Pattern | Use When | Example |
| --- | --- | --- |
| Procedural call | The defaults are enough, arguments are simple, and no post-execution measurements are needed. | `smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=[1.5, 1.5])` |
| Filter object | You need named setters, repeated execution, measurements such as an Otsu threshold, event callbacks, or easier parameter logging. | `f = sitk.OtsuThresholdImageFilter(); mask = f.Execute(image); threshold = f.GetThreshold()` |
| Source filter/procedure | You need a synthetic image for examples or tests without reading files. | `image = sitk.GaussianSource(sitk.sitkFloat32, [64, 64], [10, 10], [32, 32], 255)` |
| Statistics object | The filter returns measurements rather than an image. | `stats = sitk.LabelShapeStatisticsImageFilter(); stats.Execute(labels)` |

Procedural wrappers are generated from the same filter catalog as object filters, but not every object has a procedure. `LabelShapeStatisticsImageFilter` is object-only because it reports measurements instead of returning a transformed image.

## Object Filter Template

```python
import SimpleITK as sitk

filter_object = sitk.SmoothingRecursiveGaussianImageFilter()
filter_object.SetSigma([1.0, 1.0])
smoothed = filter_object.Execute(image)
print(filter_object)  # useful parameter and implementation summary
```

Use object filters when a prompt says "inspect parameters", "show the threshold", "reuse this filter", "add seeds in a loop", or "diagnose why this filter is behaving differently".

## Procedural Template

```python
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=[1.0, 1.0])
mask = sitk.BinaryThreshold(smoothed, lowerThreshold=40.0, upperThreshold=255.0, insideValue=1, outsideValue=0)
```

Use procedural calls for compact examples, notebooks, and smoke tests. Prefer keyword arguments when clarity matters, but positional arguments are common in SimpleITK examples.

## Source Image Generators

- `sitk.GaussianSource(pixel_id, size, sigma, mean, scale)` is the safest default for deterministic filtering examples.
- `sitk.GaborSource`, `sitk.GridSource`, and `sitk.PhysicalPointSource` are useful when examples need texture, grids, or coordinate fields.
- Set spacing/origin/direction on synthetic images when the workflow uses physical sigma, physical size, or centroid measurements.
- Keep source images small for smoke tests; prefer `[32, 32]` or `[64, 64]` unless the algorithm needs a larger field.

## Common Parameter Patterns

- **Dimensional vectors:** sigma, variance, radius, shrink factors, and seeds usually need one value per image dimension. Build them from `image.GetDimension()` when writing generic code.
- **Smoothing scale:** `SmoothingRecursiveGaussian` uses sigma in physical units; `DiscreteGaussian` uses variance and honors spacing by default.
- **Threshold ranges:** `BinaryThreshold` includes both endpoints. Validate `lowerThreshold <= upperThreshold` before calling it.
- **Seeds:** `ConnectedThresholdImageFilter` and `ConfidenceConnectedImageFilter` seeds are index coordinates, not physical points.
- **Fast marching trials:** example-style trial points contain the index plus an initial trial value, such as `[x, y, 0.0]` in 2D.
- **Morphology radii:** binary/grayscale morphology filters expect integer radius vectors; cast masks to an integer pixel type before binary morphology.

## Events and Progress

Use callbacks only for long-running filters or interactive diagnostics. Avoid progress callbacks in library code unless the caller requests them.

```python
filter_object = sitk.N4BiasFieldCorrectionImageFilter()
filter_object.AddCommand(
    sitk.sitkProgressEvent,
    lambda: print(f"progress={filter_object.GetProgress():.3f}"),
)
corrected = filter_object.Execute(image, mask)
```

Event callbacks capture the filter object by closure. Keep callback work lightweight; printing too often can dominate runtime for small filters.

## Parameter Inspection

- `print(filter_object)` usually shows current parameters and the wrapped ITK filter summary.
- `dir(filter_object)` is useful when discovering generated `Set*`, `Get*`, `Add*`, and measurement methods.
- Keep the object around after `Execute(...)` when you need measurements such as `OtsuThresholdImageFilter.GetThreshold()`, `ConfidenceConnectedImageFilter.GetMean()`, `GetVariance()`, or N4 convergence fields.
- Prefer the bundled [api-reference](api-reference.md) for representative defaults and the bundled [troubleshooting](troubleshooting.md) guide for common generated-filter errors.

## Pixel Casts and Output Types

- Many smoothing filters compute real-valued output even when input pixels are integers. Preserve the original pixel type only if a downstream consumer truly needs it: `sitk.Cast(smoothed, image.GetPixelID())`.
- Binary segmentation filters commonly return `sitkUInt8` labels or masks. Cast to an integer label type before label statistics if the previous operation produced a boolean-like or real-valued image.
- `N4BiasFieldCorrectionImageFilter` expects real pixel types. Read or cast MRI-like scalar images to `sitk.sitkFloat32` before N4.
- Do not cast a segmentation mask through a lossy image file format just to validate it. Use in-memory statistics or metadata-preserving formats through the IO sub-skill.

## Common Filter Families

- **Sources:** `GaussianSource`, `GaborSource`, `GridSource`, and `PhysicalPointSource` generate images without input files.
- **Smoothing:** `SmoothingRecursiveGaussian`, `DiscreteGaussian`, `CurvatureFlow`, `CurvatureAnisotropicDiffusion`, `Median`, and `Bilateral` reduce noise with different edge and spacing trade-offs.
- **Thresholding:** `OtsuThreshold`, `BinaryThreshold`, `Threshold`, and named histogram threshold filters produce binary masks or clipped scalar images.
- **Morphology:** `BinaryDilate`, `BinaryErode`, `BinaryMorphologicalOpening`, `BinaryMorphologicalClosing`, grayscale morphology, and reconstruction filters clean masks or intensity structures.
- **Region growing:** `ConnectedThresholdImageFilter`, `ConfidenceConnectedImageFilter`, and `NeighborhoodConnectedImageFilter` expand from seed indexes under intensity rules.
- **Level-set/front propagation:** `FastMarchingImageFilter`, geodesic active contour filters, and threshold segmentation level-set filters are useful when a speed/edge image controls growth.
- **Statistics:** `StatisticsImageFilter`, `LabelStatisticsImageFilter`, `LabelIntensityStatisticsImageFilter`, and `LabelShapeStatisticsImageFilter` validate values and objects after filtering.
