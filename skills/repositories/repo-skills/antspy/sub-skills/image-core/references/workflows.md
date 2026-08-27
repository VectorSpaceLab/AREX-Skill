# ANTsPy Image Core Workflows

Use these recipes for common `ANTsImage` IO, construction, NumPy conversion, metadata repair, indexing, validation, and vector/RGB shape checks. All examples are self-contained except file paths that you supply.

## Import and Minimal Image Creation

```python
import numpy as np
import ants

arr = np.arange(12, dtype='float32').reshape(3, 4)
img = ants.from_numpy(
    arr,
    origin=(10.0, 20.0),
    spacing=(0.5, 0.75),
    direction=np.eye(2),
)
print(img.shape, img.dimension, img.pixeltype, img.dtype)
print(img.spacing, img.origin, img.direction)
```

Expected properties:

- `img.shape == (3, 4)`
- `img.dimension == 2`
- `img.pixeltype == 'float'`
- `img.dtype == 'float32'`
- `img.origin`, `img.spacing`, and `img.direction` match the values passed

## Read, Inspect, and Write an Image

```python
import ants

img = ants.image_read('input.nii.gz', pixeltype='float')
print(img)
print(img.shape, img.spacing, img.origin, img.direction)

ants.image_write(img, 'output.nii.gz')
```

For fast header inspection:

```python
info = ants.image_header_info('input.nii.gz')
print(info['dimensions'], info['pixeltype'], info['pixelclass'])
```

Use `pixeltype=None` when preserving a supported file pixel type matters. Use an explicit supported pixel type when downstream operations require a known type.

## Metadata-Preserving NumPy Round Trip

Problem: `ants.from_numpy(img.numpy())` creates a new image with default origin, spacing, and direction. That often breaks arithmetic, comparisons, masks, or registration inputs that require matching physical space.

Preferred method form:

```python
arr = img.numpy()
out = img.new_image_like(arr * 2.0)
assert ants.image_physical_space_consistency(img, out)
```

Equivalent standalone form:

```python
out = ants.from_numpy_like(arr * 2.0, img)
```

Explicit metadata form:

```python
out = ants.from_numpy(
    arr * 2.0,
    origin=img.origin,
    spacing=img.spacing,
    direction=img.direction,
)
```

Use `copy_image_info` only when the target array truly represents the same voxel grid:

```python
target = ants.from_numpy(arr.astype('float32'))
target = ants.copy_image_info(img, target)
```

Do not use metadata copying to hide a real shape, orientation, crop, padding, or resampling difference.

## Diagnose Physical-Space Comparison Failures

```python
same_space = ants.image_physical_space_consistency(img1, img2)
same_space_and_type = ants.image_physical_space_consistency(img1, img2, datatype=True)
same_values = ants.allclose(img1, img2)

if not same_space:
    print('shape:', img1.shape, img2.shape)
    print('dimension:', img1.dimension, img2.dimension)
    print('spacing:', img1.spacing, img2.spacing)
    print('origin:', img1.origin, img2.origin)
    print('direction:', img1.direction, img2.direction)
```

Interpretation:

- `image_physical_space_consistency` checks dimension, spacing, origin, and direction within tolerance.
- `datatype=True` also checks pixel type and component count.
- `allclose` checks voxel values only and ignores physical-space metadata.
- Image-image arithmetic and image-mask indexing may raise when physical spaces differ.

## Clone or Cast Pixel Types Safely

```python
img_float = img.clone('float')
img_double = img.clone('double')
img_uint8 = ants.image_clone(img, 'unsigned char')
img_float64 = img.astype('float64')
```

Notes:

- Use `clone('double')` or `astype('float64')` for a double-pixel image.
- Do not rely on `ants.from_numpy(float64_array)` to keep double precision; it casts to `float32` during construction.
- For label masks, `unsigned char` or `unsigned int` is often appropriate. For numeric image processing, `float` is the common default.

## Create Constant Images and Mask-Filled Images

Constant image:

```python
img = ants.make_image((16, 12), voxval=3.0, spacing=(1.2, 1.5), pixeltype='float')
assert img.mean() == 3.0
```

Fill positive mask voxels from a vector while preserving mask metadata:

```python
mask = ants.make_image((4, 4), voxval=0).clone('unsigned char')
mask[1:3, 1:3] = 1
values = np.arange(int((mask > 0).sum()), dtype='float32')
filled = ants.make_image(mask, voxval=values)
assert ants.image_physical_space_consistency(mask, filled)
```

Route mask generation, morphology, thresholding, and resampling details to [image-ops-math](../../image-ops-math/SKILL.md).

## Index, Slice, and Mutate Images

```python
sub = img[:10, :10]        # ANTsImage when result is at least 2D
row = img[10, :]           # NumPy array for 1D result
value = img[10, 10]        # scalar
img[:5, :5] = 0            # in-place mutation
```

Mask indexing:

```python
mask = img > img.mean()
values = img[mask]
img[mask] = values.mean()
```

Rules:

- Reverse slicing is unsupported.
- Image masks must occupy the same physical space as the indexed image.
- If a slice returns an `ANTsImage`, it keeps the source pixel type and image-like behavior.
- For component images, slicing preserves components by internally splitting and merging channels.

## Use `numpy()` and `view()` Deliberately

Safe copy:

```python
arr = img.numpy()
arr[:] = 0
assert img.sum() != 0  # original image unchanged
```

Shared view:

```python
arr = img.view()
arr[:] = 0
assert img.sum() == 0  # original image mutated
```

Prefer `numpy()` unless you intentionally need in-place mutation through a NumPy array.

## Preserve RGB and Vector Component Axes

Vector image with trailing component axis:

```python
arr = np.zeros((5, 6, 3), dtype='float32')
arr[..., 0] = 1
arr[..., 1] = 2
arr[..., 2] = 3
vec = ants.from_numpy(arr, has_components=True)
assert vec.dimension == 2
assert vec.components == 3
np.testing.assert_allclose(vec.numpy()[..., 2], 3)
```

RGB image:

```python
rgb_arr = np.zeros((5, 6, 3), dtype='uint8')
rgb_arr[..., 0] = 255
rgb = ants.from_numpy(rgb_arr, is_rgb=True)
assert rgb.is_rgb
assert rgb.has_components
assert rgb.components == 3
```

Channel-first input must be moved before construction:

```python
channels_first = np.zeros((3, 5, 6), dtype='float32')
trailing_components = np.moveaxis(channels_first, 0, -1)
vec = ants.from_numpy(trailing_components, has_components=True)
```

When in doubt, inspect:

```python
print(img.dimension, img.shape, img.has_components, img.components, img.is_rgb)
print(img.numpy().shape)
```

Use [visualization-interop](../../visualization-interop/SKILL.md) for display-specific RGB conversions and external image format interop.

## Copy Metadata from One Image to Another

Use this only when arrays describe the same physical locations:

```python
candidate = ants.from_numpy(processed.astype('float32'))
candidate = ants.copy_image_info(reference, candidate)
assert ants.image_physical_space_consistency(reference, candidate)
```

If `processed` came from a crop, pad, resize, resample, affine transform, or orientation change, do not copy metadata blindly. Route to [image-ops-math](../../image-ops-math/SKILL.md) for image-space operations or [registration-transforms](../../registration-transforms/SKILL.md) for transform application.

## Read and Write `.npy` with Metadata Sidecar

ANTsPy writes a JSON sidecar next to `.npy` files:

```python
ants.image_write(img, 'image.npy')
img2 = ants.image_read('image.npy')
assert ants.image_physical_space_consistency(img, img2)
assert ants.allclose(img, img2)
```

If the `.json` sidecar is missing, `image_read('image.npy')` can still construct an image from array values but uses default metadata.

## Use Fixture Data Deliberately

```python
import ants
print(ants.get_ants_data('show'))
r16_path = ants.get_ants_data('r16')
r16 = ants.image_read(r16_path)
```

Guidance:

- Fixture ids are convenient for tutorials and exploratory examples.
- The helper may download files if they are not cached, so prefer in-memory arrays for deterministic smoke checks.
- If network use is not allowed, provide a known local `target_file_name` or avoid fixture-dependent examples.
