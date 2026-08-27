# Image Model

## Mental Model

A SimpleITK `Image` is a sampled grid embedded in physical space, not just an array. Pixel values are only one part of image identity. Geometry is defined by:

- `GetSize()`: number of pixels in SimpleITK index order `(x, y, z, ...)`.
- `GetOrigin()`: physical coordinate of index `(0, 0, 0, ...)`.
- `GetSpacing()`: physical distance between neighboring samples along each axis.
- `GetDirection()`: direction cosine matrix flattened in row-major order.
- `GetPixelID()`, `GetPixelIDValue()`, and `GetPixelIDTypeAsString()`: pixel storage/type identity.
- `GetNumberOfComponentsPerPixel()`: number of scalar components at each pixel for scalar, complex, vector, and label images.

New images default to origin all zeros, spacing all ones, direction identity, and zero-valued pixels. SimpleITK does not store a unit string; medical image workflows conventionally use consistent metric units, commonly millimeters.

## Construction Patterns

Use the public package import and practical overload patterns instead of relying on Python signature introspection:

```python
import SimpleITK as sitk

scalar_2d = sitk.Image([64, 48], sitk.sitkFloat32)
scalar_3d = sitk.Image([64, 48, 20], sitk.sitkUInt16)
vector_2d = sitk.Image([64, 48], sitk.sitkVectorFloat32, 3)
complex_3d = sitk.Image([32, 32, 16], sitk.sitkComplexFloat64)
```

Size is always SimpleITK order. A 2D image with size `[64, 48]` has valid integer indices `(0, 0)` through `(63, 47)`.

## Spatial Metadata

Set spatial metadata immediately after construction or after converting back from NumPy:

```python
image.SetSpacing((0.7, 0.7, 2.5))
image.SetOrigin((-10.0, 20.0, 5.0))
image.SetDirection((1.0, 0.0, 0.0,
                    0.0, 1.0, 0.0,
                    0.0, 0.0, 1.0))
```

Tuple lengths must match dimensionality: `spacing` and `origin` need `image.GetDimension()` values; `direction` needs `dimension * dimension` values. The image's physical extent starts half a voxel before the origin and ends half a voxel beyond the last voxel center.

## Metadata Dictionary Basics

SimpleITK Python images support dictionary-like shortcuts for spatial metadata plus string metadata keys:

```python
spacing = image["spacing"]
origin = image["origin"]
direction = image["direction"]
image["spacing"] = (0.7, 0.7, 2.5)
image["origin"] = (-10.0, 20.0, 5.0)
image["series_description"] = "derived volume"
```

Behavior to remember:

- `"origin"`, `"spacing"`, and `"direction"` are always present through `in` and `[]` because they expose image geometry.
- Assigning more values than needed for `origin` or `spacing` keeps the leading `dimension` values, matching Python wrapper tests.
- `direction` must have exactly `dimension * dimension` values or assignment raises a runtime error.
- Arbitrary metadata values must be strings; use `SetMetaData(key, value)` and `GetMetaData(key)` when being explicit.
- Deleting built-in spatial keys raises `KeyError` because they are geometry, not ordinary metadata entries.

## Coordinates And Pixels

Use integer indices for direct pixel access and image methods for physical coordinates:

```python
index = (10, 20, 3)
value = image[index]
value2 = image.GetPixel(index)
image.SetPixel(index, value + 1)
physical_point = image.TransformIndexToPhysicalPoint(index)
round_trip_index = image.TransformPhysicalPointToIndex(physical_point)
continuous = image.TransformPhysicalPointToContinuousIndex(physical_point)
```

Rules:

- SimpleITK Python indexing is zero-based and uses `(x, y, z, ...)` order.
- Prefer `TransformIndexToPhysicalPoint`, `TransformPhysicalPointToIndex`, and `TransformPhysicalPointToContinuousIndex` over manual matrix math.
- `TransformPhysicalPointToIndex` rounds to an integer index; `TransformPhysicalPointToContinuousIndex` preserves fractional index coordinates.
- `EvaluateAtPhysicalPoint(point)` and `EvaluateAtContinuousIndex(index)` evaluate image values at non-integer locations for supported pixel types; use them only when interpolation-style evaluation is intended.
- Out-of-bounds indices or points outside the buffered image region raise SimpleITK runtime errors in direct access/evaluation paths.

## Pixel And Component Types

SimpleITK image pixel categories include:

- Scalar basic pixels: signed/unsigned integers, floating-point, and complex scalar types such as `sitk.sitkUInt8`, `sitk.sitkFloat32`, and `sitk.sitkComplexFloat64`.
- Vector pixels: fixed-length multi-component pixels such as `sitk.sitkVectorUInt8` and `sitk.sitkVectorFloat32`.
- Label pixels: run-length encoded label map pixel ids such as `sitk.sitkLabelUInt16`.

Use public image methods first:

```python
pixel_id = image.GetPixelID()
pixel_id_value = image.GetPixelIDValue()
pixel_type = image.GetPixelIDTypeAsString()
components = image.GetNumberOfComponentsPerPixel()
```

For diagnostics, `SimpleITK._pixel_types` classifies `PixelIDValueEnum` values with `is_basic(pixel_id)`, `is_vector(pixel_id)`, and `is_label(pixel_id)`. Prefer public methods in reusable code because `_pixel_types` is a helper module, not usually needed for normal workflows.

## Copying And Object Behavior

- `copy.copy(image)` and `copy.deepcopy(image)` preserve pixel type, origin, spacing, direction, metadata keys, and pixel content while producing an independent image.
- Pickle round-trips preserve image content, geometry, metadata dictionary entries, and pixel hash.
- Arithmetic and bitwise operators are available for compatible image types and constants. In-place operators preserve metadata when the operation succeeds; failed in-place operations leave the original image and metadata intact.
- Use `sitk.Hash(image)` for pixel-buffer equality checks only. Compare geometry and metadata separately when physical identity matters.

## Validation Checklist

Before returning an image from a helper or workflow, assert the pieces that future filters, IO, or registration code will rely on:

```python
assert out.GetSize() == expected_size
assert out.GetSpacing() == reference.GetSpacing()
assert out.GetOrigin() == reference.GetOrigin()
assert out.GetDirection() == reference.GetDirection()
assert out.GetPixelID() == expected_pixel_id
assert out.GetNumberOfComponentsPerPixel() == expected_components
```

For intensity range checks, `sitk.MinimumMaximum(image)` returns `(minimum, maximum)` through the Python convenience wrapper.
