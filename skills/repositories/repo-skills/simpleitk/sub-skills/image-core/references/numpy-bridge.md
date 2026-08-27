# NumPy Bridge

## Axis And Shape Order

SimpleITK and NumPy expose image buffers using different axis conventions:

- SimpleITK image size is `(x, y)` for 2D and `(x, y, z)` for 3D.
- NumPy scalar array shape is `(rows, cols)` for 2D and `(slices, rows, cols)` for 3D.
- Therefore a scalar 2D array with shape `(rows, cols)` becomes image size `(cols, rows)`.
- A scalar 3D array with shape `(slices, rows, cols)` becomes image size `(cols, rows, slices)`.
- Vector images keep spatial axes reversed and add a final NumPy component axis, such as `(rows, cols, components)` or `(slices, rows, cols, components)`.

Do not transpose just because the displayed sizes look reversed. Validate with known pixel samples: `array[z, y, x]` corresponds to `image[x, y, z]` for 3D scalar images.

## Image To Array

Use a copy when the NumPy array will be modified or kept independently:

```python
array = sitk.GetArrayFromImage(image)
array[0, 0] = 42
```

Use a view only for read-only diagnostics or memory-sensitive inspection:

```python
view = sitk.GetArrayViewFromImage(image)
print(view.shape, view.dtype, view.flags.writeable)
```

`GetArrayFromImage(image)` returns a deep copy of the buffer. `GetArrayViewFromImage(image)` returns a read-only NumPy view. The wrapper notes that modifying the underlying SimpleITK image while a view exists has undefined behavior, so prefer a copy unless a view is clearly needed.

## Array To Image

Scalar conversion reverses spatial axes:

```python
array = np.zeros((20, 48, 64), dtype=np.float32)  # z, y, x
image = sitk.GetImageFromArray(array)
assert image.GetSize() == (64, 48, 20)
```

Vector conversion treats the final NumPy axis as components when `isVector=True`:

```python
rgb = np.zeros((48, 64, 3), dtype=np.uint8)  # y, x, components
image = sitk.GetImageFromArray(rgb, isVector=True)
assert image.GetSize() == (64, 48)
assert image.GetNumberOfComponentsPerPixel() == 3
```

`isVector` behavior:

- `isVector=True`: creates a vector image. For arrays with more than two dimensions, the last axis is the component axis and remaining axes become reversed spatial axes. For a 2D array, the image has one component per pixel.
- `isVector=None`: 4D non-complex arrays automatically become 3D vector images; 3D arrays become scalar 3D images.
- `isVector=False`: all array axes are spatial axes, so a 4D array becomes a 4D scalar image.
- Complex arrays map to scalar complex images by default. Complex vector conversion is not supported by the Python dtype-to-vector-pixel map.

## Preserve Metadata While Replacing Pixels

`GetImageFromArray` creates a fresh image with default origin, spacing, and direction and no copied metadata dictionary entries. Copy compatible geometry and metadata explicitly:

```python
array = sitk.GetArrayFromImage(reference)
array = np.clip(array, 0, 100).astype(np.float32)
out = sitk.GetImageFromArray(array)
out.CopyInformation(reference)
for key in reference.GetMetaDataKeys():
    out.SetMetaData(key, reference.GetMetaData(key))
```

`CopyInformation(reference)` requires compatible image dimension and size. If the buffer shape or dimensionality changed, set `SetOrigin`, `SetSpacing`, and `SetDirection` deliberately instead of copying incompatible geometry. If spacing must change because resampling or downsampling changed the grid, route the processing decision to the registration/resampling sub-skill.

## Dtypes And Pixel IDs

Common scalar mappings include:

| NumPy dtype | Scalar SimpleITK pixel id |
| --- | --- |
| `np.uint8`, `np.uint16`, `np.uint32`, `np.uint64` | `sitk.sitkUInt8`, `sitk.sitkUInt16`, `sitk.sitkUInt32`, `sitk.sitkUInt64` |
| `np.int8`, `np.int16`, `np.int32`, `np.int64` | `sitk.sitkInt8`, `sitk.sitkInt16`, `sitk.sitkInt32`, `sitk.sitkInt64` |
| `np.float32`, `np.float64` | `sitk.sitkFloat32`, `sitk.sitkFloat64` |
| `np.complex64`, `np.complex128` | `sitk.sitkComplexFloat32`, `sitk.sitkComplexFloat64` |

Vector conversion supports integer and floating dtypes such as `np.uint8`, `np.int16`, `np.uint32`, `np.float32`, and `np.float64`. Unsupported dtypes raise `TypeError`, for example `dtype: bool is not supported.` or `dtype: complex64 is not supported as an array.` Cast explicitly before conversion.

## Component Axis Recipes

### Reversed 3D Scalar Shape

```python
volume = np.zeros((40, 128, 256), dtype=np.float32)  # z, y, x
image = sitk.GetImageFromArray(volume)
print("array shape:", volume.shape)
print("image size:", image.GetSize())  # (256, 128, 40)
```

### 2D Vector Image

```python
rgb = np.zeros((128, 256, 3), dtype=np.uint8)  # y, x, components
image = sitk.GetImageFromArray(rgb, isVector=True)
assert image.GetSize() == (256, 128)
assert image.GetNumberOfComponentsPerPixel() == 3
```

### 3D Vector Field Versus 4D Scalar Image

```python
field = np.zeros((20, 48, 64, 3), dtype=np.float32)  # z, y, x, components
vector_image = sitk.GetImageFromArray(field, isVector=True)
assert vector_image.GetSize() == (64, 48, 20)
assert vector_image.GetNumberOfComponentsPerPixel() == 3

stack = np.zeros((5, 20, 48, 64), dtype=np.float32)
scalar_4d = sitk.GetImageFromArray(stack, isVector=False)
assert scalar_4d.GetSize() == (64, 48, 20, 5)
```

For a 3D array where the last axis is actually components, pass `isVector=True`; otherwise SimpleITK will treat it as a scalar 3D image.

## Copy/View Decision Table

| Need | Use | Reason |
| --- | --- | --- |
| Modify pixels in NumPy | `sitk.GetArrayFromImage` | Deep copy is writeable and independent. |
| Inspect shape/dtype quickly | `sitk.GetArrayViewFromImage` | Avoids copying and exposes read-only shape/dtype. |
| Keep array after image may be deleted or mutated | `sitk.GetArrayFromImage` | View lifetime and mutation semantics are tied to the image. |
| Rebuild image after NumPy processing | `sitk.GetImageFromArray` plus metadata copy | Array conversion does not preserve physical geometry. |
