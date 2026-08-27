# API Reference

## Imports And Version Notes

Use the public import:

```python
import SimpleITK as sitk
```

The Python distribution name is `simpleitk`. Installed inspection used stable wheel version `2.5.5`, while the checkout version metadata indicated a newer development branch. Prefer behavior backed by public APIs, wrapper code, and tests when writing reusable guidance.

## Image Constructor Patterns

The Python `Image` constructor is dynamically overloaded, so introspection may show generic `*args`. Use these stable patterns:

| Task | Pattern |
| --- | --- |
| Empty 2D scalar image | `sitk.Image([width, height], sitk.sitkFloat32)` |
| Empty 3D scalar image | `sitk.Image([width, height, depth], sitk.sitkUInt16)` |
| Positional 2D scalar image | `sitk.Image(width, height, sitk.sitkInt32)` |
| Positional 3D scalar image | `sitk.Image(width, height, depth, sitk.sitkFloat32)` |
| Vector image | `sitk.Image([width, height], sitk.sitkVectorFloat32, components)` |
| Complex image | `sitk.Image([width, height], sitk.sitkComplexFloat64)` |
| Pixel read/write | `image[x, y]`, `image[index]`, `image.GetPixel(index)`, `image.SetPixel(index, value)` |

## Core Image Methods

| API | Use |
| --- | --- |
| `image.GetDimension()` | Number of spatial dimensions. |
| `image.GetSize()` | Size tuple in SimpleITK order `(x, y, z, ...)`. |
| `image.GetOrigin()`, `image.SetOrigin(values)` | Physical coordinate of index zero. |
| `image.GetSpacing()`, `image.SetSpacing(values)` | Physical sample spacing. |
| `image.GetDirection()`, `image.SetDirection(values)` | Flattened row-major direction cosine matrix. |
| `image.TransformIndexToPhysicalPoint(index)` | Convert integer index to physical point using image geometry. |
| `image.TransformPhysicalPointToIndex(point)` | Convert a physical point to the nearest integer image index. |
| `image.TransformPhysicalPointToContinuousIndex(point)` | Convert a physical point to continuous index coordinates. |
| `image.EvaluateAtContinuousIndex(index)` | Evaluate at continuous index for supported pixel types. |
| `image.EvaluateAtPhysicalPoint(point)` | Evaluate at physical point for supported pixel types. |
| `image.CopyInformation(reference)` | Copy origin, spacing, and direction from a compatible reference image. |
| `image.GetMetaDataKeys()`, `image.GetMetaData(key)`, `image.SetMetaData(key, value)` | Work with string metadata dictionary entries. |

## Pixel Access Notes

Direct pixel access supports positional and sequence forms:

```python
image.SetPixel(0, 0, 1)
image.SetPixel([0, 2], 4)
image[[0, 1]] = 2
value = image.GetPixel([0, 2])
value2 = image[0, 1]
```

For vector pixels, direct access returns a tuple-like component value. Index bounds are checked by SimpleITK; recover by validating `0 <= index[d] < image.GetSize()[d]` before access.

## Pixel Inspection

| API | Meaning |
| --- | --- |
| `image.GetPixelID()` | Pixel id enum value suitable for comparisons such as `sitk.sitkFloat32`. |
| `image.GetPixelIDValue()` | Integer pixel id value for helper maps/classifiers. |
| `image.GetPixelIDTypeAsString()` | Human-readable pixel type. |
| `image.GetNumberOfComponentsPerPixel()` | Component count; scalar and complex images usually report `1`, vector images report vector length. |

Diagnostic pixel type classifiers:

```python
import SimpleITK._pixel_types as pixel_types

pixel_types.is_basic(image.GetPixelIDValue())
pixel_types.is_vector(image.GetPixelIDValue())
pixel_types.is_label(image.GetPixelIDValue())
```

Use these classifiers for diagnostics, not as a requirement for ordinary user code.

## NumPy Bridge

| API | Signature | Notes |
| --- | --- | --- |
| `sitk.GetArrayFromImage` | `GetArrayFromImage(image)` | Returns a deep copy of the image buffer as a NumPy array. |
| `sitk.GetArrayViewFromImage` | `GetArrayViewFromImage(image)` | Returns a read-only NumPy view; do not mutate the SimpleITK image while the view exists. |
| `sitk.GetImageFromArray` | `GetImageFromArray(arr, isVector=None)` | Creates a new image, reverses spatial axes, and defaults geometry to origin zero, spacing one, direction identity. |

`GetImageFromArray` behavior notes:

- `isVector=True` creates a vector image and treats the last axis as components when the array has more than two dimensions.
- `isVector=None` automatically treats 4D non-complex arrays as 3D vector images; 3D arrays are scalar 3D images.
- `isVector=False` treats every axis as spatial, including 4D arrays.
- Unsupported scalar dtypes raise `TypeError: dtype: ... is not supported.`; unsupported vector dtypes raise `TypeError: dtype: ... is not supported as an array.`

## Metadata And Object Behavior

- `image["spacing"]`, `image["origin"]`, and `image["direction"]` access spatial metadata shortcuts.
- Arbitrary `image["key"] = "value"` stores string metadata; assigning non-string metadata through `[]` raises `TypeError`.
- `copy.copy(image)`, `copy.deepcopy(image)`, and pickle round-trips preserve geometry, metadata dictionary entries, pixel id, and pixel buffer content.
- In-place arithmetic and bitwise operations preserve metadata on success and leave the original metadata intact on type-mismatch failure.
- `sitk.MinimumMaximum(image)` returns `(minimum, maximum)` for scalar-like range checks.
- `sitk.Hash(image)` compares pixel-buffer content only; it is not a complete physical-image equivalence check.

## Registered ImageIO Reminder

When image-core work crosses into files, route to the IO sub-skill. Registered ImageIO names are discovered from reader/writer objects:

```python
reader_ios = sitk.ImageFileReader().GetRegisteredImageIOs()
writer_ios = sitk.ImageFileWriter().GetRegisteredImageIOs()
```

Do not use a module-level `sitk.GetRegisteredImageIOs()` helper; that is not the verified public API surface for these wrappers.
