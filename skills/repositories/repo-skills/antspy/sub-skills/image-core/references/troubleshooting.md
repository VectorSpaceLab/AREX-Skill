# ANTsPy Image Core Troubleshooting

Use this guide for failures around importing `ants`, reading or writing images, NumPy conversion, metadata preservation, physical-space comparison, pixel types, indexing, and vector/RGB images.

## Import and Backend Failures

### Symptom: `import ants` fails or imports the wrong package

Likely causes:

- Python is importing an unbuilt local `ants` package directory instead of the installed `antspyx` package.
- The current working directory or `PYTHONPATH` shadows the installed package.
- The compiled backend extension is missing because a source build did not complete.

Fixes:

1. Run image scripts from a neutral working directory, not from inside an unbuilt source checkout.
2. Check what Python imports:

   ```python
   import ants
   print(ants.__file__)
   ```

3. If the path points to an unintended local package, remove that directory from `PYTHONPATH` or change directories before running.
4. Prefer installing the published package distribution `antspyx` into the active environment instead of importing directly from source.

### Symptom: missing compiled library, symbol, or backend extension

Likely causes:

- The wheel is not compatible with the Python version, platform, or architecture.
- A source install started but did not complete the CMake/ITK/ANTs build.
- A partial or mixed package install remains in the environment.

Fixes:

1. Verify that a compatible `antspyx` installation exists in the active environment.
2. Reinstall from a binary source when possible.
3. Avoid broad source builds unless the environment has the required compiler, CMake, and build dependencies.
4. Test with a minimal import and constructor:

   ```python
   import numpy as np
   import ants
   img = ants.from_numpy(np.zeros((2, 2), dtype='float32'))
   print(img)
   ```

## Data Type, Pixeltype, and List Input Errors

### Symptom: a `float64` NumPy array becomes a float image

`ants.from_numpy()` historically casts `float64` input arrays to `float32`, so the resulting image usually has `pixeltype == 'float'` and `dtype == 'float32'`.

Fixes:

- Use `img.clone('double')` or `img.astype('float64')` after construction when double pixel storage is required.
- Use `ants.image_read(..., pixeltype='double')` when reading a file as double.
- Use `ants.image_read(..., pixeltype=None)` only when you want to preserve a supported file pixel type.

### Symptom: unsupported dtype is silently changed or rejected later

ANTsImage supports these practical dtype mappings:

- `uint8` -> `unsigned char`
- `uint32` -> `unsigned int`
- `float32` -> `float`
- `float64` -> `double` for clone/cast, but not preserved by `from_numpy()` construction as noted above

Fixes:

- Cast arrays explicitly before construction: `arr.astype('float32')`, `arr.astype('uint8')`, or `arr.astype('uint32')`.
- Inspect `img.pixeltype` and `img.dtype` immediately after construction.
- For labels or masks, choose integer pixel types deliberately; for arithmetic workflows, prefer `float`.

### Symptom: constructor fails because data is a Python list

`ants.from_numpy()` expects a NumPy array with dtype information. Convert lists first:

```python
arr = np.asarray(values, dtype='float32')
img = ants.from_numpy(arr)
```

For `ants.make_image(shape, voxval=list_or_array)`, the number of values must match the requested tuple shape or the number of positive voxels in the mask image.

## Metadata Length and Shape Errors

### Symptom: `set_spacing` or `set_origin` raises a length error

Spacing and origin must have exactly one value per spatial dimension.

```python
img.dimension  # 2 requires length-2 spacing/origin; 3 requires length-3
img.set_spacing((1.0, 1.0))
img.set_origin((0.0, 0.0))
```

For vector images, the component axis is not a spatial dimension. A 2D vector image with shape `(64, 64)` and `components == 3` still needs length-2 origin and spacing.

### Symptom: `set_direction` raises or stores unexpected orientation

Direction must be a square matrix with shape `(dimension, dimension)`.

```python
img.set_direction(np.eye(img.dimension))
```

Do not include a row or column for vector/RGB components.

### Symptom: `new_image_like` or `from_numpy_like` rejects shape

For scalar images, `data.shape` must equal `image.shape`. For component images, `data.shape[:-1]` must equal `image.shape` and `data.shape[-1]` must equal `image.components`.

Fixes:

```python
print('image:', image.shape, image.components, image.has_components)
print('data:', data.shape)
```

- For scalar images, remove accidental singleton or channel axes.
- For vector images, keep components in the trailing axis.
- Do not pass channel-first arrays unless you convert them to trailing-component layout first.

## Physical-Space Mismatches

### Symptom: arithmetic or image-mask indexing raises `images do not occupy same physical space`

ANTsPy checks physical space for image-image arithmetic and image-mask indexing. Differences in dimension, spacing, origin, or direction can fail even when arrays have the same shape.

Diagnostic:

```python
print(ants.image_physical_space_consistency(a, b))
print(a.shape, b.shape)
print(a.spacing, b.spacing)
print(a.origin, b.origin)
print(a.direction, b.direction)
```

Common cause after NumPy conversion:

```python
bad = ants.from_numpy(img.numpy())  # default metadata, often wrong
```

Correct patterns:

```python
good = img.new_image_like(img.numpy())
good = ants.from_numpy_like(img.numpy(), img)
good = ants.from_numpy(img.numpy(), origin=img.origin, spacing=img.spacing, direction=img.direction)
```

Use `ants.copy_image_info(reference, target)` only when `target` already represents the same voxel grid and physical locations. If real resampling, cropping, padding, or orientation correction is needed, route to [image-ops-math](../../image-ops-math/SKILL.md).

### Symptom: `ants.allclose(a, b)` is true but ANTs operations still fail

`ants.allclose` compares voxel arrays only. It does not verify physical metadata. Also check `ants.image_physical_space_consistency(a, b)`.

### Symptom: datatype-sensitive consistency fails

`ants.image_physical_space_consistency(a, b, datatype=True)` also compares pixel type and component count. Clone one image to the other's pixel type when the only mismatch is type:

```python
b = b.clone(a.pixeltype)
```

## RGB and Vector Component Confusion

### Symptom: image dimension is one less than expected

When `has_components=True` or `is_rgb=True`, the last NumPy axis is treated as components, not a spatial axis.

```python
arr = np.zeros((64, 64, 3), dtype='float32')
vec = ants.from_numpy(arr, has_components=True)
assert vec.dimension == 2
assert vec.components == 3
```

If you intended a scalar 3D image, omit `has_components=True`:

```python
vol = ants.from_numpy(arr)  # dimension == 3, components == 1
```

### Symptom: channels are reordered or missing after conversion

ANTsPy expects component data in the trailing axis for `from_numpy(..., has_components=True)` and returns the trailing component axis from `img.numpy()`.

Fixes:

- Convert channel-first arrays with `np.moveaxis(arr, 0, -1)` before `from_numpy`.
- Validate `img.components`, `img.dimension`, and `img.numpy().shape` immediately after construction.
- For RGB images, use `is_rgb=True` and `uint8` data when display semantics matter.

### Symptom: RGB conversion changes pixel type or semantics

RGB/vector conversion utilities may clone through display-oriented storage. If numeric precision matters more than display semantics, keep a vector image rather than an RGB image and route visualization-specific work to [visualization-interop](../../visualization-interop/SKILL.md).

## IO and Header Failures

### Symptom: `image_read` says file does not exist

- Verify the path exists before calling `ants.image_read`.
- Expand or normalize user-provided paths before passing them into workflow code.
- For `.npy`, keep the `.json` sidecar next to files written by `ants.image_write` if metadata preservation matters.

### Symptom: unsupported image dimension, pixel type, or pixel class

ANTsPy core image IO supports 2D, 3D, and 4D images through the reader. Unsupported pixel classes or unusual file dtypes may fail or be mapped to supported types.

Fixes:

- Inspect with `ants.image_header_info(filename)` first.
- Read with an explicit supported `pixeltype` when possible.
- Use `pixeltype=None` only if preserving a supported file type is required.
- Convert unusual images with a dedicated medical-image IO tool before passing to ANTsPy if core IO cannot read them.

### Symptom: `.npy` round trip loses metadata

`ants.image_write(img, 'image.npy')` writes both `image.npy` and a metadata sidecar `image.json`. If the sidecar is missing, `ants.image_read('image.npy')` reconstructs values but uses default metadata.

## Indexing and Mutation Pitfalls

- Reverse indexing such as `img[20:10, :]` is not supported.
- Lower-dimensional indexing can return NumPy arrays or scalars instead of `ANTsImage` objects.
- `img.view()` is shared mutable data; accidental writes through a view mutate the source image.
- Mask indexing requires the mask image to occupy the same physical space as the target image.
- `ANTsImage` is not iterable; use `img.numpy()` or methods such as `img.sum()` and `img.mean()`.

When debugging a slice, print `type(result)`, `result.shape` when available, and whether `ants.is_image(result)` is true.

## Transform Boundary Confusion

If a task involves `ANTsTransform`, transform files, applying transforms to images, displacement fields, interpolation choices, registration outputs, or transform composition, switch to [registration-transforms](../../registration-transforms/SKILL.md). This sub-skill only uses transform facts to avoid confusing image physical-space metadata with actual spatial transforms.
