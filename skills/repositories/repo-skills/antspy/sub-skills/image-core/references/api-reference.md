# ANTsPy Image Core API Reference

This reference covers `ants.ANTsImage` creation, IO, inspection, cloning, indexing, NumPy conversion, physical-space validation, small fixture lookup, and only the transform facts needed for routing. It assumes the public package distribution `antspyx` is installed and imported as `ants`.

## Verified Public Signatures

Live inspection of `antspyx` verified these image-core signatures:

| API | Signature |
| --- | --- |
| `ants.ANTsImage` | `(pointer)` |
| `ants.image_read` | `(filename, dimension=None, pixeltype='float', reorient=False)` |
| `ants.image_write` | `(image, filename, ri=False)` |
| `ants.from_numpy` | `(data, origin=None, spacing=None, direction=None, has_components=False, is_rgb=False)` |
| `ants.from_numpy_like` | `(data, image)` |
| `ants.make_image` | `(imagesize, voxval=0, spacing=None, origin=None, direction=None, has_components=False, pixeltype='float')` |
| `ants.image_header_info` | `(filename)` |
| `ants.copy_image_info` | `(reference, target)` |
| `ants.image_physical_space_consistency` | `(image1, image2, tolerance=0.01, datatype=False)` |
| `ants.allclose` | `(image1, image2)` |
| `ants.get_ants_data` / `ants.get_data` | `(file_id=None, target_file_name=None, antsx_cache_directory=None)` |
| `ants.set_origin` | `(image, origin)` |
| `ants.set_spacing` | `(image, spacing)` |
| `ants.set_direction` | `(image, direction)` |
| `ants.image_clone` | `(image, pixeltype=None)` |
| `ants.ANTsTransform` | `(precision='float', dimension=3, transform_type='AffineTransform', pointer=None)` |
| `ants.create_ants_transform` | `(transform_type='AffineTransform', precision='float', dimension=3, matrix=None, offset=None, center=None, translation=None, parameters=None, fixed_parameters=None, displacement_field=None, supported_types=False)` |
| `ants.read_transform` | `(filename, precision='float')` |
| `ants.write_transform` | `(transform, filename)` |

Transform APIs are listed only to prevent ambiguous routing: use this sub-skill when handling image objects and physical metadata, and use [registration-transforms](../../registration-transforms/SKILL.md) for transform workflows.

## Image IO and Constructors

| API | Use for | Key behavior |
| --- | --- | --- |
| `ants.image_read(filename, dimension=None, pixeltype='float', reorient=False)` | Read NIfTI, supported ITK image formats, or `.npy` plus the `.json` sidecar written by ANTsPy. | `dimension` can force 2D/3D/4D. The default `pixeltype='float'` reads as float; `pixeltype=None` preserves supported file pixel type. Unsupported file pixel types may be mapped to supported types. `reorient=True` reorients 3D images to `RPI`; a 3-letter orientation string requests that orientation. |
| `ants.image_write(image, filename, ri=False)` | Write an `ANTsImage`. | For `.npy`, writes array data and a `.json` sidecar with origin, spacing, direction, and component count. For other extensions, delegates to compiled image IO. `ri=True` returns the input image for chaining. |
| `img.to_file(filename)` / `img.to_filename(filename)` | Method form of file write. | Writes through the compiled backend and does not return the image. |
| `ants.image_header_info(filename)` | Inspect file metadata without loading full image data into a Python image object. | Returns keys such as `dimensions`, `origin`, `spacing`, `direction`, `nComponents`, `nDimensions`, `pixeltype`, and `pixelclass`; raises when the file is missing or unreadable. |
| `ants.from_numpy(data, origin=None, spacing=None, direction=None, has_components=False, is_rgb=False)` | Build an `ANTsImage` from a NumPy array. | Defaults to zero origin, unit spacing, and identity direction. Pass metadata explicitly when the image must remain in another image's physical space. The last axis is treated as components when `has_components=True` or `is_rgb=True`. |
| `ants.from_numpy_like(data, image)` | Build from an array while copying metadata from a reference image. | Equivalent to `image.new_image_like(data)`. Shape must match image shape, or image shape plus trailing component count for component images. |
| `image.new_image_like(data)` | Method form for metadata-preserving replacement data. | Returns a new image with the same origin, spacing, and direction. Raises if `data` is not a NumPy array or the shape does not match. |
| `ants.make_image(imagesize, voxval=0, spacing=None, origin=None, direction=None, has_components=False, pixeltype='float')` | Make a constant image, an image from a voxel vector, or fill a mask image. | If `imagesize` is a tuple, creates that spatial shape. If `imagesize` is an image mask, fills positive voxels from `voxval` and preserves the mask's physical space. |

## ANTsImage Properties and Methods

| Property or method | Meaning |
| --- | --- |
| `img.shape` | Spatial voxel shape, excluding vector/RGB components. |
| `img.dimension` | Spatial dimension as an integer, usually 2, 3, or 4. |
| `img.physical_shape` | Rounded `shape * spacing` tuple. |
| `img.spacing` / `img.set_spacing(seq)` | Tuple of physical voxel sizes. Setter requires one value per spatial dimension. |
| `img.origin` / `img.set_origin(seq)` | Tuple of physical origin coordinates. Setter requires one value per spatial dimension. |
| `img.direction` / `img.set_direction(matrix)` | Direction cosine matrix with shape `(dimension, dimension)`. Setter accepts a NumPy array, list, or tuple with matching dimension. |
| `img.orientation` | 3D orientation string when dimension is 3; otherwise `None`. |
| `img.pixeltype` | ANTs pixel type: `unsigned char`, `unsigned int`, `float`, or `double`. |
| `img.dtype` | NumPy dtype string mapped from `pixeltype`: `uint8`, `uint32`, `float32`, or `float64`. |
| `img.has_components` | `True` for vector or RGB images. |
| `img.components` | Number of components per voxel; scalar images report `1`. |
| `img.is_rgb` | `True` for RGB images. |
| `img.numpy(single_components=False)` | NumPy copy of image data. Edits to the returned array do not affect the image. For component images, component axis is last. |
| `img.view(single_components=False)` | Shared NumPy view into image data. Edits mutate the image. Use only for intentional in-place mutation. |
| `img.clone(pixeltype=None)` / `ants.image_clone(img, pixeltype=None)` | Copy image data and metadata, optionally casting to a supported pixel type. Vector images keep component count. |
| `img.astype(dtype)` | Clone to a supported NumPy dtype string: `uint8`, `uint32`, `float32`, or `float64`. |
| `img.copy()` | Alias for clone. |
| `img.apply(fn)` | Apply a Python function to the full `img.numpy()` array and return `img.new_image_like(result)`. |
| `img.mean()`, `img.sum()`, `img.min()`, `img.max()`, `img.std()`, `img.median()`, `img.flatten()`, `img.unique()` | Convenience NumPy reductions and array summaries. |

Standalone metadata functions mirror methods: `ants.get_origin(img)`, `ants.set_origin(img, origin)`, `ants.get_spacing(img)`, `ants.set_spacing(img, spacing)`, `ants.get_direction(img)`, and `ants.set_direction(img, direction)`.

## Metadata Semantics

ANTsPy separates array values from physical-space metadata:

- `origin` is the physical coordinate of the image origin and has length `dimension`.
- `spacing` is voxel size along each spatial axis and has length `dimension`.
- `direction` maps index axes into physical axes and has shape `(dimension, dimension)`.
- Components are not spatial axes. A NumPy array with shape `(64, 64, 3)` becomes a 2D 3-component image only when `has_components=True` or `is_rgb=True`; otherwise it is a scalar 3D image.
- Copying metadata with `copy_image_info` does not resample, reorient, crop, pad, or transform voxel values. Use it only when arrays already describe the same physical grid.

## Pixeltype and Dtype Rules

| ANTs pixel type | NumPy dtype | Typical use |
| --- | --- | --- |
| `unsigned char` | `uint8` | Byte-valued images, masks, labels, and RGB storage. |
| `unsigned int` | `uint32` | Integer images requiring a wider range. |
| `float` | `float32` | Default working type for many ANTsPy workflows. |
| `double` | `float64` | Double-pixel storage when explicitly cloned or read as double. |

Important behavior:

- `ants.from_numpy()` historically casts `float64` arrays to `float32` before constructing the image. Use `clone('double')`, `astype('float64')`, or `image_read(..., pixeltype='double')` when double-pixel storage is required.
- Unsupported NumPy dtypes are inferred or cast to a supported type before image creation.
- `ants.image_read(..., pixeltype='float')` reads as float by default even when the file stores another supported type.
- `img.clone(pixeltype)` and `ants.image_clone(img, pixeltype)` accept ANTs names such as `float`/`double` and NumPy names such as `float32`/`float64`.

## NumPy Conversion and Components

Scalar image round trip preserving metadata:

```python
arr = img.numpy()
out = img.new_image_like(arr * 2)
assert ants.image_physical_space_consistency(img, out)
```

Explicit construction with metadata:

```python
out = ants.from_numpy(arr, origin=img.origin, spacing=img.spacing, direction=img.direction)
```

Vector image construction uses a trailing component axis:

```python
arr = np.zeros((16, 12, 3), dtype='float32')
vec = ants.from_numpy(arr, has_components=True)
assert vec.dimension == 2
assert vec.components == 3
assert vec.numpy().shape == arr.shape
```

RGB construction uses the same trailing component axis and implies components:

```python
rgb_arr = np.zeros((16, 12, 3), dtype='uint8')
rgb = ants.from_numpy(rgb_arr, is_rgb=True)
assert rgb.is_rgb
assert rgb.components == 3
```

`ants.merge_channels([img1, img2, ...])` creates a component image from scalar images with the same pixel type. `ants.split_channels(vec)` returns scalar component images. Use these helpers to inspect or repair component layout; route display-specific RGB work to [visualization-interop](../../visualization-interop/SKILL.md).

## Copying, Comparing, and Physical-Space Validation

| API | Use |
| --- | --- |
| `ants.copy_image_info(reference, target)` | Copy `origin`, `direction`, and `spacing` from `reference` to `target`, returning the modified target. It does not copy values or resample. |
| `ants.image_physical_space_consistency(image1, image2, tolerance=0.01, datatype=False)` | Return `True` when dimensions, spacing, origin, and direction match within tolerance. With `datatype=True`, pixel type and component count must also match. |
| `ants.allclose(image1, image2)` | Return NumPy `allclose` on voxel arrays only. It does not verify physical metadata. |

Use `copy_image_info` only when the target array truly represents the same physical space. If one image was resampled, cropped, padded, reoriented, or generated in a different coordinate system, copying metadata is usually wrong; route preprocessing or resampling to [image-ops-math](../../image-ops-math/SKILL.md).

## Indexing and Mutation

- `img[i, j]` or fully scalar indexing returns a scalar or NumPy array when the result is lower than 2D.
- Slicing that remains 2D or higher returns an `ANTsImage` with matching pixel type.
- Missing trailing slice dimensions are treated as full slices, so `img[10]` acts like `img[10, :, :]` for a 3D image.
- Reverse slices such as `img[20:10, :, :]` are not supported and raise.
- Indexing with an `ANTsImage` mask requires matching physical space and returns selected NumPy values.
- Setting slices accepts scalars, NumPy arrays, or compatible `ANTsImage` values.
- Component images slice by splitting and merging channels internally, preserving component structure.
- `ANTsImage` is intentionally not iterable; use NumPy conversion or image methods for reductions.

## Fixture Data

`ants.get_ants_data(file_id=None, target_file_name=None, antsx_cache_directory=None)` and `ants.get_data(...)` are aliases for small ANTsPy test data lookup.

- `ants.get_ants_data()` or `ants.get_ants_data('show')` returns valid ids: `r16`, `r27`, `r30`, `r62`, `r64`, `r85`, `ch2`, `mni`, `surf`, and `pcasl`.
- `r16` and similar `r*` ids are 2D slice images commonly used for examples.
- `ch2`, `mni`, and `surf` return NIfTI paths.
- If the target file is not already cached, the helper downloads it. Avoid it in no-network tests unless the cache is already populated or a specific cached `target_file_name` is provided.

Prefer tiny in-memory arrays for deterministic smoke scripts. Use fixture data only for examples that explicitly need realistic image files.

## Transform Boundary

`ants.ANTsTransform` objects are not images. They have `precision`, `dimension`, `transform_type`, `parameters`, and `fixed_parameters`, and can be read or written with transform IO helpers. If a task asks to apply transforms to images, compose transforms, build transforms from registration outputs, convert displacement fields, or reason about interpolation, switch to [registration-transforms](../../registration-transforms/SKILL.md).
