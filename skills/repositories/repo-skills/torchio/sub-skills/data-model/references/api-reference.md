# Data Model API Reference

## Images

### Classes and source semantics

Use `tio.ScalarImage` for continuous intensity data and `tio.LabelMap` for discrete segmentation labels. Both inherit from `tio.Image` and share the same constructor and properties. The class choice is semantic: spatial transforms can use linear-like interpolation for scalar images and nearest-neighbor behavior for label maps.

Common constructors:

```python
import numpy as np
import torch
import torchio as tio

scalar = tio.ScalarImage(torch.randn(1, 32, 40, 24))
label = tio.LabelMap(torch.randint(0, 5, (1, 32, 40, 24), dtype=torch.int16))
array_image = tio.ScalarImage(np.zeros((1, 32, 40, 24), dtype=np.float32))
path_image = tio.ScalarImage("image.nii.gz")
```

Accepted image sources include:

| Source | Loading behavior | Notes |
| --- | --- | --- |
| `torch.Tensor` | eager | Must be 4D `(C, I, J, K)` unless `channels_last=True` is used for `(I, J, K, C)` input. |
| `numpy.ndarray` | eager | Converted to a tensor while preserving supported dtype where possible. |
| `str` or `Path` | lazy when backend supports it | NIfTI and NIfTI-Zarr can use lazy backends; other SimpleITK-readable formats may load fully when sliced or accessed. |
| `nibabel.Nifti1Image` | lazy | Shape and affine can be inspected without materializing full data. |
| `SimpleITK.Image` | eager | Converted into TorchIO channel-first tensor layout. |
| `bytes` or `io.BytesIO` | decoded through a temporary file | Use `suffix=` when the format is not the default `.nii.gz`. |
| file-like object | materialized to temporary file | Requires `suffix=` so TorchIO can detect the reader. |
| zarr store or `.nii.zarr` | lazy when zarr extras are installed | Route remote/zarr operational workflows to `cli-and-io` if storage setup is the main task. |

### Tensor layout

TorchIO image tensors use `(C, I, J, K)`:

- `C`: channels.
- `I, J, K`: spatial voxel axes.
- Single-channel 3D volumes still need shape `(1, I, J, K)`.
- If data arrives as `(I, J, K, C)`, pass `channels_last=True` so TorchIO permutes it to channel-first layout.

```python
volume = torch.randn(32, 40, 24)
image = tio.ScalarImage(volume.unsqueeze(0))

channels_last = torch.randn(32, 40, 24, 2)
multi = tio.ScalarImage(channels_last, channels_last=True)
assert multi.shape == (2, 32, 40, 24)
```

### Properties and metadata

Important image properties:

| Property | Meaning |
| --- | --- |
| `image.data` | 4D tensor; triggers full load for lazy images. |
| `image.shape` | `(C, I, J, K)`; header-only for lazy sources when possible. |
| `image.spatial_shape` | `(I, J, K)`. |
| `image.num_channels` | Channel count. |
| `image.affine` | `AffineMatrix` voxel-to-world mapping. |
| `image.spacing` | Voxel size in millimeters, derived from the affine. |
| `image.origin` | World coordinate of voxel `(0, 0, 0)`. |
| `image.orientation` | Anatomical orientation codes such as `('R', 'A', 'S')`. |
| `image.dtype` | Tensor or on-disk dtype. |
| `image.path` | Source path, if created from a path-like source. |
| `image.is_loaded` | Whether full tensor data is materialized. |
| `image.metadata` | Extra keyword metadata. |
| `image.points` | Image-level named `Points`. |
| `image.bounding_boxes` | Image-level named `BoundingBoxes`. |

Metadata is stored from extra keyword arguments:

```python
image = tio.ScalarImage(torch.randn(1, 8, 8, 8), protocol="MPRAGE", te=3.1)
assert image.protocol == "MPRAGE"
assert image["te"] == 3.1
assert image.metadata == {"protocol": "MPRAGE", "te": 3.1}
```

### Replace, clone, move, and save

```python
new_data = torch.zeros(1, 16, 16, 16)
resized_like = image.new_like(data=new_data)
image.set_data(new_data)
image.to(dtype=torch.float32)
image.save("out.nii.gz")
```

- `set_data()` requires a 4D tensor or NumPy array and refreshes the in-memory backend.
- `new_like(data=...)` preserves the image subclass, metadata, affine, and annotations unless a new affine is supplied.
- `to()` materializes image data, moves/casts it like `torch.Tensor.to()`, and keeps backend metadata coherent.
- `save()` materializes data and writes through SimpleITK for most formats; `.nii.zarr` uses NIfTI-Zarr support when installed.

## Affine matrices

`tio.AffineMatrix` wraps a strict 4x4 matrix mapping voxel indices `(i, j, k)` to world coordinates `(x, y, z)` in millimeters.

```python
affine = tio.AffineMatrix.from_spacing(
    spacing=(0.8, 0.8, 2.5),
    origin=(10.0, 20.0, 30.0),
)
assert affine.spacing == (0.8, 0.8, 2.5)
assert affine.origin == (10.0, 20.0, 30.0)
assert affine.orientation == ("R", "A", "S")
```

Key methods and properties:

| API | Use |
| --- | --- |
| `AffineMatrix()` | Identity affine. |
| `AffineMatrix(matrix)` | Validate and copy a 4x4 array/tensor. |
| `AffineMatrix.from_spacing(spacing, origin=..., direction=...)` | Build a common spacing/origin/direction affine. |
| `.data` | Underlying float64 tensor. |
| `.numpy()` | 4x4 NumPy copy/view from CPU. |
| `.spacing`, `.origin`, `.direction`, `.orientation` | Physical metadata. |
| `.inverse()` | Inverse voxel/world mapping. |
| `.compose(other)` or `a @ b` | Compose affine transforms. |
| `.apply(points)` | Apply to an `(N, 3)` coordinate array/tensor. |

The affine must be 4x4. A 3x3 spacing matrix or a 4-vector is not accepted.

## Subjects and studies

`tio.Subject` is a container for named images, points, bounding boxes, and non-spatial metadata. `tio.Study` is an alias for `tio.Subject`.

```python
subject = tio.Subject(
    t1=tio.ScalarImage(torch.randn(1, 16, 20, 24)),
    seg=tio.LabelMap(torch.zeros(1, 16, 20, 24, dtype=torch.int16)),
    age=58,
    site="A",
)
assert subject.t1 is subject["t1"]
assert subject.metadata["age"] == 58
```

Subject stores values by type:

| Value type | Store | Access |
| --- | --- | --- |
| `Image`, `ScalarImage`, `LabelMap` | `subject.images` | Attribute or `subject["name"]`. |
| `Points` | `subject.points` | Attribute or `subject["name"]`. |
| `BoundingBoxes` | `subject.bounding_boxes` | Attribute or `subject["name"]`. |
| Anything else | `subject.metadata` | Attribute or metadata dict. |

Useful subject behavior:

- `subject.spatial_shape`, `subject.shape`, and `subject.spacing` check all images for consistency.
- `subject.load()` loads all image tensors.
- `subject.to(...)` forwards to all images, points, and bounding boxes.
- Iteration yields spatial entry keys, not metadata keys.
- Spatial slicing, such as `subject[4:12, 5:15, 2:10]`, returns a new subject with every image sliced consistently and the channel dimension preserved.
- `subject.all_points()` and `subject.all_bounding_boxes()` collect subject-level and image-level annotations.

A metadata-only subject is valid, but many imaging workflows require at least one image. Spatial properties fail when there are no images.

## Points and bounding boxes

### Points

`tio.Points` stores an `(N, 3)` coordinate tensor with an axis convention and affine.

```python
points = tio.Points(
    torch.tensor([[4.0, 5.0, 6.0], [10.0, 12.0, 14.0]]),
    axes="IJK",
    affine=image.affine,
    metadata={"kind": "landmark"},
)
world = points.to_world()
ras = points.to_axes("RAS")
```

Point axes can be voxel permutations such as `IJK`, `KJI`, or anatomical systems such as `RAS` and `LPI`. Cross-type conversions use the stored affine; same-type conversions permute and flip coordinate columns as needed.

### Bounding boxes

`tio.BoundingBoxes` stores an `(N, 6)` tensor and requires a `BoundingBoxFormat`.

```python
boxes = tio.BoundingBoxes(
    torch.tensor([[2, 3, 4, 12, 13, 14]], dtype=torch.float32),
    format=tio.BoundingBoxFormat.IJKIJK,
    labels=torch.tensor([1]),
    affine=image.affine,
)
center_size = boxes.to_format(tio.BoundingBoxFormat.IJKWHD)
```

Formats combine axes and representation:

| Format | Meaning |
| --- | --- |
| `BoundingBoxFormat.IJKIJK` | Voxel corner coordinates `(i1, j1, k1, i2, j2, k2)`. |
| `BoundingBoxFormat.IJKWHD` | Voxel center-size coordinates `(ic, jc, kc, si, sj, sk)`. |
| `BoundingBoxFormat("RAS", "corners")` | Anatomical world corner coordinates. |
| `BoundingBoxFormat("RAS", "center_size")` | Anatomical world center-size coordinates. |

`labels` is optional but, when provided, must have length `N`. Format conversions preserve labels, metadata, and affine.

### Annotation placement

Attach annotations at subject level when they describe the whole study, or image level when they are specific to an image:

```python
image = tio.ScalarImage(
    torch.randn(1, 16, 16, 16),
    points={"fiducials": points},
    bounding_boxes={"lesions": boxes},
)
subject = tio.Subject(t1=image, landmarks=points)

all_points = subject.all_points()
all_boxes = subject.all_bounding_boxes()
```

Image-level annotation constructor mappings must contain `Points` or `BoundingBoxes` objects, not raw tensors.
