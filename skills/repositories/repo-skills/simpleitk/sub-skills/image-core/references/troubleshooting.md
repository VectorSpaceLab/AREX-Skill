# Troubleshooting

## Metadata Disappears After NumPy Conversion

Symptom: `GetSpacing()`, `GetOrigin()`, or `GetDirection()` returns defaults after `sitk.GetImageFromArray`.

Cause: `GetImageFromArray` creates a new image from a pixel buffer and does not copy geometry or metadata dictionary entries.

Fix:

```python
array = sitk.GetArrayFromImage(reference)
out = sitk.GetImageFromArray(array)
out.CopyInformation(reference)
for key in reference.GetMetaDataKeys():
    out.SetMetaData(key, reference.GetMetaData(key))
```

If shape or dimension changed, do not call `CopyInformation`; set compatible `origin`, `spacing`, and `direction` deliberately.

## NumPy Shape Looks Reversed

Symptom: A `(slices, rows, cols)` array becomes image size `(cols, rows, slices)`.

Cause: SimpleITK index order is `(x, y, z)` while NumPy shape order is `(z, y, x)` for scalar volumes.

Fix: Do not transpose unless the data are actually in the wrong logical order. Validate by printing both `array.shape` and `image.GetSize()` and by sampling known pixels:

```python
array_value = array[z, y, x]
image_value = image[x, y, z]
```

## Vector Image Has Wrong Size Or Components

Symptom: A color image or displacement-like array becomes a scalar 3D/4D image, or component count is wrong.

Cause: `isVector` was omitted or incorrect. A 3D NumPy array defaults to scalar 3D, not 2D vector; a 4D non-complex array defaults to 3D vector when `isVector=None`.

Fix:

```python
image = sitk.GetImageFromArray(array, isVector=True)
assert image.GetNumberOfComponentsPerPixel() == array.shape[-1]
```

For a true 4D scalar image, pass `isVector=False`. For a 3D scalar image where the last axis is depth, do not pass `isVector=True`.

## Unsupported NumPy Dtype

Symptom: `TypeError: dtype: ... is not supported.` or `TypeError: dtype: ... is not supported as an array.`

Cause: The NumPy dtype is not mapped to a SimpleITK scalar or vector pixel id. Boolean, object, string, and structured dtypes are unsupported. Complex dtypes are scalar-only in the Python bridge.

Fix: Cast explicitly before conversion:

```python
array = array.astype(np.float32)
image = sitk.GetImageFromArray(array)
```

Use integer or floating dtypes for vector images.

## Cannot Modify Array View

Symptom: Assigning into an array from `sitk.GetArrayViewFromImage(image)` fails with `ValueError: assignment destination is read-only`, or `array_view.flags.writeable` is `False`.

Cause: The view is intentionally read-only and tied to the SimpleITK image buffer.

Fix: Use `sitk.GetArrayFromImage(image)` for a mutable copy, then convert back and copy metadata:

```python
array = sitk.GetArrayFromImage(image)
array[...] = 0
out = sitk.GetImageFromArray(array)
out.CopyInformation(image)
```

## Pixel ID Or Component Mismatch

Symptom: A downstream filter rejects the image type, vector length is unexpected, or equality checks fail after conversion.

Cause: Array dtype and `isVector` determine the recreated image pixel id and component count. Converting through NumPy can change pixel id if the array was cast.

Fix: Inspect both images and cast deliberately:

```python
print(image.GetPixelIDTypeAsString(), image.GetNumberOfComponentsPerPixel())
print(out.GetPixelIDTypeAsString(), out.GetNumberOfComponentsPerPixel())
out = sitk.Cast(out, image.GetPixelID())
```

For vector images, also check that `out.GetNumberOfComponentsPerPixel()` matches the intended component axis length.

## Direction Assignment Fails

Symptom: `SetDirection` or `image["direction"] = ...` raises a runtime error.

Cause: The flattened direction matrix length must be exactly `dimension * dimension`.

Fix: For 2D, pass four values; for 3D, pass nine values. Check `image.GetDimension()` before constructing the tuple.

## Physical Coordinates Are Unexpected

Symptom: `TransformIndexToPhysicalPoint` or `TransformPhysicalPointToIndex` returns values that do not match a manual calculation or another library.

Cause: Origin, spacing, and direction all participate in the transform, and physical units are only a convention.

Fix: Print `GetOrigin()`, `GetSpacing()`, and `GetDirection()`, then use SimpleITK transforms instead of reimplementing the math:

```python
point = image.TransformIndexToPhysicalPoint(index)
index2 = image.TransformPhysicalPointToIndex(point)
continuous = image.TransformPhysicalPointToContinuousIndex(point)
```

If you are aligning two images or resampling to a new grid, route to the registration/transforms sub-skill.

## Index Outside Image

Symptom: `GetPixel`, `SetPixel`, bracket indexing, or physical-point evaluation raises a SimpleITK runtime error about the requested index or point.

Cause: Direct pixel access requires every integer index component to be inside the buffered image region. Valid indices are `0 <= index[d] < image.GetSize()[d]` in SimpleITK order.

Fix:

```python
size = image.GetSize()
if all(0 <= index[d] < size[d] for d in range(image.GetDimension())):
    value = image.GetPixel(index)
else:
    raise ValueError(f"index {index} outside image size {size}")
```

For physical points, convert first with `TransformPhysicalPointToContinuousIndex(point)` and inspect whether the continuous coordinate lies inside the image extent before evaluating.

## Metadata Dictionary Value Fails

Symptom: `image["key"] = value` raises `TypeError`.

Cause: Arbitrary metadata dictionary values must be strings. Numeric geometry uses dedicated keys or setters.

Fix:

```python
image.SetMetaData("threshold", str(threshold))
image.SetSpacing((0.7, 0.7, 2.5))
```
