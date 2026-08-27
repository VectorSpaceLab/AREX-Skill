# I/O and Formats

## Source types

TorchIO image constructors accept many source types through the first positional argument. For current code examples, pass in-memory tensors positionally:

```python
image = tio.ScalarImage(tensor)
label = tio.LabelMap(label_tensor)
```

Use `source=` only when you intentionally want a named constructor keyword for a source object. Avoid old examples such as `tio.ScalarImage(source=tensor)` when teaching the preferred in-memory pattern.

### In-memory tensors and arrays

```python
image = tio.ScalarImage(torch.randn(1, 64, 64, 32))
array_image = tio.ScalarImage(np.zeros((1, 64, 64, 32), dtype=np.float32))
```

- Tensor and NumPy sources are eager; `image.is_loaded` is `True` immediately.
- Shape must be 4D `(C, I, J, K)` unless using `channels_last=True`.
- NumPy arrays are copied into tensors with dtype preservation where PyTorch supports it.
- A missing affine defaults to identity, so spacing becomes `(1.0, 1.0, 1.0)` and orientation is usually `('R', 'A', 'S')`.

For channel-last arrays:

```python
array = np.zeros((64, 64, 32, 2), dtype=np.float32)
image = tio.ScalarImage(array, channels_last=True)
assert image.shape == (2, 64, 64, 32)
```

### Local paths

```python
image = tio.ScalarImage("image.nii.gz")
label = tio.LabelMap("segmentation.nii.gz")
```

- Local `str` and `Path` sources store `image.path`.
- NIfTI (`.nii`, `.nii.gz`) can use a NiBabel lazy backend.
- NIfTI-Zarr (`.nii.zarr`) can use a zarr backend when optional dependencies are installed.
- Other SimpleITK-readable formats can be read, but lazy slicing may fall back to full loading.
- `shape`, `dtype`, `affine`, `spacing`, and `orientation` are header-only when a lazy backend or header reader supports them.

### NiBabel and SimpleITK objects

```python
nifti_image = nib.Nifti1Image(data_ijk, affine)
image = tio.ScalarImage(nifti_image)

sitk_image = sitk.GetImageFromArray(array_kji)
image = tio.ScalarImage(sitk_image)
```

- `nibabel.Nifti1Image` sources are lazy and use NIfTI conventions.
- `SimpleITK.Image` sources are converted eagerly to TorchIO layout.
- SimpleITK uses LPS internally; TorchIO stores RAS-oriented affines for consistency.

### Bytes, file-like objects, and remote sources

```python
image = tio.ScalarImage(open_file_like, suffix=".nii.gz")
image = tio.ScalarImage(raw_bytes, suffix=".nii.gz")
image = tio.ScalarImage("https://example.invalid/image.nii.gz")
```

- File-like objects need `suffix=` so the reader can infer format.
- Bytes and `BytesIO` are decoded via a temporary file, then materialized if needed before the temporary source disappears.
- Remote URI support uses file-system adapters and optional dependencies. Keep operational cache/conversion commands in the `cli-and-io` sub-skill.

## Lazy and eager loading

TorchIO laziness is an I/O behavior, not a deferred computation graph.

| Operation | Lazy source behavior |
| --- | --- |
| Construct `ScalarImage(path)` | Stores source only. |
| Read `.shape`, `.dtype`, `.affine`, `.spacing`, `.orientation` | Uses backend/header when possible; does not load full tensor for supported formats. |
| Read `.dataobj` | Returns backend object for advanced lazy access. |
| Slice `image[:, i0:i1, j0:j1, k0:k1]` | Reads a region through backend when supported. |
| Read `.data`, call `.load()`, `.numpy()`, `.save()`, `.to()` | Materializes full tensor data. |
| Apply transforms, build batches, sample queued patches | Materializes the tensor needed by that workflow. |

The backend contract normalizes all storage layouts to `(C, I, J, K)`. Advanced users can inspect `image.dataobj`, but generated workflows should usually use public image properties unless they specifically need lazy region reads.

## Saving and round-trip checks

### Save an image

```python
image.save("out.nii.gz")
reloaded = tio.ScalarImage("out.nii.gz")
assert reloaded.shape == image.shape
assert reloaded.spacing == image.spacing
```

`save()` writes most formats through SimpleITK. For `.nii.zarr`, it uses NIfTI-Zarr support and requires optional zarr dependencies.

### Save labels safely

```python
label = tio.LabelMap(torch.randint(0, 3, (1, 16, 16, 16), dtype=torch.int16))
label.save("labels.nii.gz")
reloaded = tio.LabelMap("labels.nii.gz")
```

Use `LabelMap` for labels from construction through saving. This preserves the semantic signal that downstream spatial operations should treat values as discrete classes.

### Validate before writing

Before saving or handing data to transforms, check:

```python
assert image.data.ndim == 4
assert image.shape[0] >= 1
assert tuple(image.affine.data.shape) == (4, 4)
assert label.spatial_shape == image.spatial_shape
```

For a full subject:

```python
subject = tio.Subject(t1=image, seg=label)
assert subject.spatial_shape == image.spatial_shape
assert subject.spacing == image.spacing
subject.load()
```

`subject.spatial_shape` and `subject.spacing` intentionally raise when images are inconsistent. Treat that as a data validation signal rather than suppressing it.

## Backend-specific notes

### NIfTI

- `.nii` can be memory-mapped and supports efficient partial reads.
- `.nii.gz` is compressed; lazy slicing can avoid full tensor allocation but cannot always avoid decompression work.
- NiBabel stores common arrays as `(I, J, K)` or `(I, J, K, C)`; TorchIO exposes them as `(1, I, J, K)` or `(C, I, J, K)`.

### SimpleITK formats

- Formats such as NRRD or MHA can be read and written through SimpleITK.
- Some header properties can be read without full tensor load.
- Lazy region slicing is not equivalent to NIfTI backends for these formats.

### Zarr and remote storage

- `.nii.zarr`, zarr stores, and remote NIfTI-Zarr require optional dependencies.
- If a workflow is mainly about conversion, cache management, cloud credentials, or CLI subcommands, route to `cli-and-io`.
- In data-model examples, keep remote/zarr mention conceptual unless the optional dependency is known to be installed.

## Minimal synthetic round trip

```python
import tempfile
import torch
import torchio as tio

affine = tio.AffineMatrix.from_spacing((1.0, 1.0, 2.0))
image = tio.ScalarImage(torch.randn(1, 8, 9, 10), affine=affine)

with tempfile.TemporaryDirectory() as tmpdir:
    path = f"{tmpdir}/image.nii.gz"
    image.save(path)
    loaded = tio.ScalarImage(path)
    assert loaded.shape == image.shape
    assert loaded.spacing == image.spacing
```

Use temporary files for smoke checks and examples. Do not require original repository example data or local checkout paths in runtime skill content.
