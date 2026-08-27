# Troubleshooting Filtering and Segmentation

Use this guide when a SimpleITK filter raises a runtime error, produces an empty mask, takes much longer than expected, or behaves differently from a compact example.

## Pixel Type Problems

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Filter says the pixel type is not supported | The filter supports only selected pixel categories; for example N4 requires real scalar pixels and shape statistics requires integer labels. | Cast deliberately: `image = sitk.Cast(image, sitk.sitkFloat32)` for N4/smoothing; `labels = sitk.Cast(labels, sitk.sitkUInt32)` for labels. |
| Output type differs from input type | Many smoothing filters output real-valued images; threshold filters often output `sitkUInt8`. | Preserve output type unless a downstream API requires a cast; avoid casting masks to floats before label statistics. |
| Threshold values seem wrong | Values are in actual pixel intensity units, not display window/level units. | Run `StatisticsImageFilter` to inspect min/max/mean before choosing `lowerThreshold` and `upperThreshold`. |

## Dimension and Metadata Mismatches

- Seed vectors, kernel radii, sigma/variance vectors, shrink factors, and trial points must match `image.GetDimension()` unless a filter explicitly accepts scalar expansion.
- Seeds for `ConnectedThresholdImageFilter` and trial points for `FastMarchingImageFilter` are index coordinates. Convert physical points to indexes before adding them.
- Mask images for N4 and masked Otsu must have compatible dimension, size, spacing, origin, and direction. Use image-core checks before assuming a mask overlays an image.
- If a filter combines two images and complains about physical space, resample or copy metadata intentionally; do not blindly overwrite spacing/origin/direction.

## Seed and Mask Mistakes

| Workflow | What to Check |
| --- | --- |
| Connected threshold | `image.GetPixel(*seed)` lies between `lower` and `upper`; seed length equals dimension; seed indexes are inside image bounds; connectivity is appropriate. |
| Confidence connected | Seed neighborhood is homogeneous; `Multiplier` is not too small; `InitialNeighborhoodRadius` is not bigger than the structure. |
| Fast marching | Speed image is non-negative; at least one trial point is set; `StoppingValue` is not too low; arrival-time threshold is not lower than the initial trial value. |
| N4 | Input is positive real-valued; mask foreground label matches `MaskLabel`; shrink factor is not larger than the foreground object; iteration vector is not accidentally huge. |
| Otsu | Histogram bins are adequate; foreground polarity matches `InsideValue`/`OutsideValue`; optional mask includes the region used to compute the threshold. |

## Expensive Filters

- N4, fast marching on large volumes, anisotropic diffusion, Feret diameter, and oriented bounding boxes can be expensive.
- Downsample N4 with `sitk.Shrink` for field estimation, then reconstruct the bias field at full resolution using `GetLogBiasFieldAsImage(reference_image)`.
- Keep smoke tests tiny and synthetic; avoid reading external datasets or opening viewers.
- Disable optional label-shape metrics unless the prompt specifically asks for them.

## Empty or Implausible Outputs

- Run `StatisticsImageFilter` on the original image, smoothed image, speed image, and mask image to confirm value ranges.
- For threshold masks, verify foreground polarity by checking whether `insideValue` or `outsideValue` represents the object.
- For connected segmentation, print seed intensities before execution and compare them to lower/upper thresholds.
- For fast marching, inspect the arrival-time min/max and confirm the binary threshold is above the initial trial value.
- For label images, run connected components and report object count, largest object size, bounding boxes, and physical sizes before trusting the result.

## Output Validation

Use validation immediately after segmentation:

```python
labels = sitk.ConnectedComponent(sitk.Cast(mask, sitk.sitkUInt8))
shape = sitk.LabelShapeStatisticsImageFilter()
shape.Execute(labels)
if shape.GetNumberOfLabels() == 0:
    raise ValueError("empty segmentation")
for label in shape.GetLabels():
    print(label, shape.GetNumberOfPixels(label), shape.GetBoundingBox(label))
```

Also check:

- `StatisticsImageFilter` on the original, smoothed, and mask images.
- Object count and largest object size after connected components.
- Physical size when spacing matters; pixel count alone can be misleading for anisotropic images.
- Metadata preservation if the result will be written or registered later.

## Viewer Side Effects

Some SimpleITK examples call `sitk.Show` unless viewer display is disabled. Generated skills and smoke scripts should not open viewers. If adapting an example:

- Remove `sitk.Show(...)` calls from reusable code.
- Do not depend on external GUI applications or environment variables for correctness.
- Print JSON, statistics, or file paths instead of launching a viewer.

## Diagnosing Generated Filter Parameters

- Print the filter object before and after setters to confirm current values.
- Keep the object alive after `Execute(...)` when reading measurements such as Otsu thresholds, confidence-connected mean/variance, or N4 convergence fields.
- Use the bundled [api-reference](api-reference.md) and [filter-patterns](filter-patterns.md) references before assuming a generated filter has a particular default or measurement.
