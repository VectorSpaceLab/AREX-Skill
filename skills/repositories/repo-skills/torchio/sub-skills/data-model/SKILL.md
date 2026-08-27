---
name: data-model
description: "Construct and validate TorchIO images, subjects/studies, affines,
  points, bounding boxes, lazy/eager sources, and safe save/load workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchIO Data Model

Use this sub-skill when an agent needs to create, inspect, validate, or persist TorchIO data containers before applying transforms, sampling patches, or using CLI workflows.

## Route by task

- Build in-memory images, choose `ScalarImage` vs `LabelMap`, inspect shape/spacing/orientation, or handle tensor layout errors: read [API reference](references/api-reference.md#images).
- Combine images, annotations, and metadata into `Subject` or `Study`: read [API reference](references/api-reference.md#subjects-and-studies).
- Add landmarks or 3D boxes with voxel/anatomical axes: read [API reference](references/api-reference.md#points-and-bounding-boxes).
- Choose tensor, NumPy, path, NiBabel, SimpleITK, bytes, file-like, remote, or zarr sources: read [I/O and formats](references/io-and-formats.md#source-types).
- Understand lazy loading, backend behavior, saving, and round-trip checks: read [I/O and formats](references/io-and-formats.md#lazy-and-eager-loading).
- Recover from validation errors or API drift such as `source=tensor`, 3D tensors, channel-last arrays, bad affines, and annotation format confusion: read [Troubleshooting](references/troubleshooting.md).
- Run a synthetic data sanity check without repository files: `python scripts/data_model_smoke.py`.

## Core patterns

### Construct valid images

```python
import torch
import torchio as tio

image = tio.ScalarImage(torch.randn(1, 32, 40, 24))
label = tio.LabelMap(torch.randint(0, 4, (1, 32, 40, 24), dtype=torch.int16))
```

TorchIO tensor images are channel-first 4D tensors with shape `(C, I, J, K)`. A single 3D volume still needs a leading channel dimension, usually `tensor.unsqueeze(0)`. In-memory tensor and NumPy images are eager and immediately loaded; path and supported lazy backend sources are loaded on demand.

### Preserve physical metadata

```python
affine = tio.AffineMatrix.from_spacing((0.8, 0.8, 2.5), origin=(10, 20, 30))
image = tio.ScalarImage(torch.randn(1, 32, 40, 24), affine=affine, sequence="T1")

assert image.spacing == (0.8, 0.8, 2.5)
assert image.orientation == ("R", "A", "S")
assert image.metadata["sequence"] == "T1"
```

Use a 4x4 voxel-to-world affine for spacing, origin, direction, and orientation. Arbitrary keyword metadata is available through `image.metadata`, attribute access, or dict-style lookup.

### Group data in a Subject or Study

```python
subject = tio.Subject(
    t1=image,
    seg=label,
    age=62,
)
study = tio.Study(t1=image, seg=label)  # alias for Subject
```

A `Subject` stores named images, `Points`, `BoundingBoxes`, and metadata. Spatial properties such as `subject.spatial_shape` and `subject.spacing` check consistency across all images and raise if they disagree.

### Add annotations

```python
points = tio.Points(torch.tensor([[5.0, 6.0, 7.0]]), affine=image.affine)
boxes = tio.BoundingBoxes(
    torch.tensor([[2, 3, 4, 10, 12, 16]], dtype=torch.float32),
    format=tio.BoundingBoxFormat.IJKIJK,
    labels=torch.tensor([1]),
    affine=image.affine,
)
subject = tio.Subject(t1=image, landmarks=points, lesions=boxes)
```

Points require `(N, 3)` coordinates; bounding boxes require `(N, 6)` coordinates plus a `BoundingBoxFormat`. Attach annotations either at subject level or image level using the `points=` and `bounding_boxes=` image constructor keywords.

## Drift guardrails

- For in-memory tensors, prefer `tio.ScalarImage(tensor)` and `tio.LabelMap(tensor)`. Do not write old-style `source=tensor` in generated examples unless matching an existing compatibility path intentionally.
- Use `ScalarImage` for continuous intensity data and `LabelMap` for segmentation labels. Transform logic treats labels semantically, especially for interpolation.
- Keep transform pipeline design in the `transforms` sub-skill, patch queues/samplers in `patch-workflows`, and CLI conversion/cache workflows in `cli-and-io`.

## Quick validation

Run the bundled smoke test after editing data-model examples:

```bash
python scripts/data_model_smoke.py
```

The script uses only synthetic tensors, temporary files, and public TorchIO imports. It checks construction, metadata, affine spacing/orientation, annotations, `Subject`/`Study`, and save/load round trips.
