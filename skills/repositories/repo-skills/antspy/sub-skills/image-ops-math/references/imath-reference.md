# iMath Reference

`ants.iMath(image, operation, *args)` exposes a curated subset of ANTs ImageMath operations through ANTsPy. Operation names are case-sensitive, arguments are positional, and unsupported operation names raise `ValueError("Operation not recognized")` before reaching the compiled backend.

## Prefer Wrappers When Available

| Intent | Wrapper | Equivalent generic call |
| --- | --- | --- |
| Canny edge detection | `ants.iMath_canny(image, sigma, lower, upper)` | `ants.iMath(image, "Canny", sigma, lower, upper)` |
| Fill holes | `ants.iMath_fill_holes(image, hole_type=2)` | `ants.iMath(image, "FillHoles", hole_type)` |
| Largest component | `ants.iMath_get_largest_component(image, min_size=50)` | `ants.iMath(image, "GetLargestComponent", min_size)` |
| Normalize intensities | `ants.iMath_normalize(image)` | `ants.iMath(image, "Normalize")` |
| Truncate intensities | `ants.iMath_truncate_intensity(image, lower_q, upper_q, n_bins=64)` | `ants.iMath(image, "TruncateIntensity", lower_q, upper_q, n_bins)` |
| Sharpen | `ants.iMath_sharpen(image)` | `ants.iMath(image, "Sharpen")` |
| Pad through iMath | `ants.iMath_pad(image, padding)` | `ants.iMath(image, "Pad", padding)` |
| Maurer distance | `ants.iMath_maurer_distance(image, foreground=1)` | `ants.iMath(image, "MaurerDistance", foreground)` |
| Perona-Malik diffusion | `ants.iMath_perona_malik(image, conductance=0.25, n_iterations=1)` | `ants.iMath(image, "PeronaMalik", conductance, n_iterations)` |
| Gradient magnitude | `ants.iMath_grad(image, sigma=0.5, normalize=False)` | `ants.iMath(image, "Grad", sigma, normalize)` |
| Laplacian | `ants.iMath_laplacian(image, sigma=0.5, normalize=False)` | `ants.iMath(image, "Laplacian", sigma, normalize)` |
| Binary dilation | `ants.iMath_MD(image, radius=1, value=1, shape=1, parametric=False, lines=3, thickness=1, include_center=False)` | `ants.iMath(image, "MD", radius, value, shape, parametric, lines, thickness, include_center)` |
| Binary erosion | `ants.iMath_ME(...)` | `ants.iMath(image, "ME", ...)` |
| Binary opening | `ants.iMath_MO(...)` | `ants.iMath(image, "MO", ...)` |
| Binary closing | `ants.iMath_MC(...)` | `ants.iMath(image, "MC", ...)` |
| Grayscale dilation | `ants.iMath_GD(image, radius=1)` | `ants.iMath(image, "GD", radius)` |
| Grayscale erosion | `ants.iMath_GE(image, radius=1)` | `ants.iMath(image, "GE", radius)` |
| Grayscale opening | `ants.iMath_GO(image, radius=1)` | `ants.iMath(image, "GO", radius)` |
| Grayscale closing | `ants.iMath_GC(image, radius=1)` | `ants.iMath(image, "GC", radius)` |
| Propagate labels | `ants.iMath_propagate_labels_through_mask(image, labels, stopping_value=100, propagation_method=0)` | `ants.iMath(image, "PropagateLabelsThroughMask", labels, stopping_value, propagation_method)` |

Wrappers are safer than stringly typed calls because they encode the exact ANTsPy operation name and argument order used in the source.

## Recognized ANTsPy Operation Names

The source-supported operation set includes:

- `FillHoles`
- `GetLargestComponent`
- `Normalize`
- `Sharpen`
- `Pad`
- `D`
- `MaurerDistance`
- `PeronaMalik`
- `Grad`
- `Laplacian`
- `Canny`
- `HistogramEqualization`
- `MD`, `ME`, `MO`, `MC`
- `GD`, `GE`, `GO`, `GC`
- `LabelStats`
- `TruncateIntensity`
- `PropagateLabelsThroughMask`

The ANTs ImageMath tutorial documents many additional CLI operators, including arithmetic, tensor, time-series, file-output, and transform-related operations. Do not assume those are accepted by ANTsPy's `ants.iMath` wrapper. Some CLI operations require multiple images, output text/CSV files, or are better routed to other sub-skills.

## Operation Families

### Intensity Operations

```python
norm = ants.iMath(image, "Normalize")
trunc = ants.iMath(image, "TruncateIntensity", 0.01, 0.99, 64)
sharp = ants.iMath(image, "Sharpen")
eq = ants.iMath(image, "HistogramEqualization", 0.5, 0.5)
```

Use `TruncateIntensity` before bias correction or registration when outliers dominate the dynamic range. Use `Normalize` when downstream algorithms expect normalized intensity ranges. Use `ants.histogram_equalize_image` or `ants.histogram_match_image` from [API reference](api-reference.md) when you need explicit histogram APIs rather than iMath's two-parameter equalization.

### Spatial Filtering and Derivatives

```python
grad = ants.iMath(image, "Grad", 0.5, False)
lap = ants.iMath(image, "Laplacian", 0.5, False)
edges = ants.iMath(image, "Canny", 1.0, 0.1, 0.9)
denoised = ants.iMath(image, "PeronaMalik", 0.25, 2)
```

For ordinary Gaussian smoothing, prefer `ants.smooth_image`, which exposes physical-coordinate, FWHM, and max-kernel controls.

### Binary Morphology

```python
dilated = ants.iMath(image, "MD", 2, 1)
eroded = ants.iMath(image, "ME", 2, 1)
opened = ants.iMath(image, "MO", 2, 1)
closed = ants.iMath(image, "MC", 2, 1)
```

Use `ants.morphology(mask, operation="dilate", radius=2, mtype="binary", shape="ball")` for clearer binary morphology. The wrapper maps `dilate`, `erode`, `open`, and `close` to `MD`, `ME`, `MO`, and `MC` and adds shape controls.

### Grayscale Morphology

```python
gray_dilate = ants.iMath(image, "GD", 2)
gray_erode = ants.iMath(image, "GE", 2)
gray_open = ants.iMath(image, "GO", 2)
gray_close = ants.iMath(image, "GC", 2)
```

Use grayscale morphology on scalar intensity images. For label maps, choose binary morphology per label or route label-specific workflows to [segmentation-labels](../../segmentation-labels/).

### Masks, Components, and Distances

```python
filled = ants.iMath(mask, "FillHoles", 2)
largest = ants.iMath(mask, "GetLargestComponent", 50)
distance = ants.iMath(mask, "MaurerDistance", 1)
padded = ants.iMath(mask, "Pad", 2)
```

`GetLargestComponent` and `FillHoles` are commonly used by `ants.get_mask(cleanup>0)`. On tiny images, this cleanup can erase the target; lower cleanup or set `cleanup=0`.

### Label Propagation Through a Mask

```python
propagated = ants.iMath_propagate_labels_through_mask(
    mask,
    labels,
    stopping_value=100,
    propagation_method=0,
)
```

Ensure `mask` and `labels` share dimension and physical space. Route label statistics, label overlap, and segmentation-specific postprocessing to [segmentation-labels](../../segmentation-labels/).

## Using `iMath_ops()` for Guardrails

Some ANTsPy builds expose `ants.iMath_ops()` as a quick accepted-operation set:

```python
if hasattr(ants, "iMath_ops"):
    assert "Normalize" in ants.iMath_ops()
```

This helps prevent typos in generated pipelines. Still prefer wrappers for operations that have them.

## Recovering From Unsupported Operations

Use this recovery pattern when a user asks for an ImageMath operation by name:

```python
operation = user_operation
try:
    out = ants.iMath(image, operation, *args)
except ValueError as exc:
    available = sorted(ants.iMath_ops()) if hasattr(ants, "iMath_ops") else []
    raise ValueError(f"Unsupported ANTsPy iMath operation {operation!r}; available operations include {available}") from exc
```

If the requested operator appears only in the ANTs CLI tutorial:

- Check whether a first-class ANTsPy function exists, such as `histogram_match_image`, `image_similarity`, `reflect_image`, `resample_image`, or `anti_alias`.
- If the operator writes text/CSV outputs or consumes multiple files, do not force it through `ants.iMath`; route to an appropriate sub-skill or implement with supported Python APIs.
- If the operation is transform-related, route to [registration-transforms](../../registration-transforms/).
- If the operation is label-statistics-related, route to [segmentation-labels](../../segmentation-labels/).

## Chained Method Examples

```python
normalized = image.iMath("Normalize")
smoothed = image.iMath("TruncateIntensity", 0.01, 0.99, 64).smooth_image(1.0)
mask = image.get_mask(cleanup=0).iMath("FillHoles", 2)
```

Break chains before any step whose output shape, physical space, component count, or pixel type must be checked. `iMath` generally returns a new image with the same dimensionality as the input, but downstream operations like crop, pad, slice, or resample can change shape or metadata.
