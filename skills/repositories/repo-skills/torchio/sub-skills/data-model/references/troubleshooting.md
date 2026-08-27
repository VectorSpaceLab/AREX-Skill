# Data Model Troubleshooting

## Tensor shape errors

### Error pattern

`ValueError: Tensor must be 4D (C, I, J, K), got 3D`

### Fix

Add a channel dimension or use channel-last conversion intentionally.

```python
volume = torch.randn(64, 64, 32)
image = tio.ScalarImage(volume.unsqueeze(0))

channels_last = torch.randn(64, 64, 32, 2)
image = tio.ScalarImage(channels_last, channels_last=True)
assert image.shape == (2, 64, 64, 32)
```

Do not silently reshape unknown data. Confirm whether the leading dimension is channels or a spatial axis before constructing the image.

## Preferred tensor constructor

### Symptom

Examples or generated code use old or confusing patterns such as:

```python
image = tio.ScalarImage(source=tensor)
```

### Fix

Use the direct positional source for in-memory data:

```python
image = tio.ScalarImage(tensor)
label = tio.LabelMap(label_tensor)
```

Reserve `source=` for cases where a named source keyword is useful for readability with paths or source objects.

## Channel-last confusion

### Symptom

An array shaped `(I, J, K, C)` is interpreted as `(C, I, J, K)`, producing an unexpected channel count or spatial shape.

### Fix

Pass `channels_last=True` for in-memory tensor or NumPy sources.

```python
array = np.zeros((128, 128, 64, 4), dtype=np.float32)
image = tio.ScalarImage(array, channels_last=True)
assert image.shape == (4, 128, 128, 64)
```

For path/NiBabel sources, TorchIO backends already normalize common NIfTI layouts into channel-first output.

## Missing path or backend for lazy loading

### Error patterns

- `RuntimeError: Cannot determine shape: no data or path`
- `RuntimeError: Cannot load: no path or backend set`
- `RuntimeError: Cannot create backend: no path or store set`

### Causes

- An empty `ScalarImage()` or `LabelMap()` was created and inspected before `set_data()`.
- A file-like object was passed without `suffix=`.
- Optional zarr/remote dependencies are unavailable.
- A custom reader does not provide a lazy backend and needs full loading.

### Fixes

```python
image = tio.ScalarImage()
image.set_data(torch.zeros(1, 8, 8, 8))
assert image.shape == (1, 8, 8, 8)
```

```python
image = tio.ScalarImage(file_like_object, suffix=".nii.gz")
```

For cloud, zarr, cache, and conversion operational failures, route to the `cli-and-io` sub-skill.

## Affine shape errors

### Error pattern

`ValueError: AffineMatrix must be 4x4`

### Fix

Pass a full 4x4 voxel-to-world matrix or build one from spacing/origin/direction.

```python
affine = tio.AffineMatrix.from_spacing((0.7, 0.7, 2.0), origin=(0, 0, -40))
image = tio.ScalarImage(torch.randn(1, 32, 32, 20), affine=affine)
```

A 3-vector spacing, 3x3 direction matrix, or 4-element origin vector is not a valid `affine=` value by itself.

## ScalarImage vs LabelMap mistakes

### Symptom

A segmentation mask is created as `ScalarImage`, or a continuous intensity image is created as `LabelMap`.

### Why it matters

The distinction is semantic but important: transforms use image class checks to choose behavior such as label-safe nearest-neighbor interpolation for label maps. Wrong class choice can blur labels or make intensity images behave like discrete masks.

### Fix

```python
intensity = tio.ScalarImage(intensity_tensor.float())
segmentation = tio.LabelMap(label_tensor.to(torch.int16))
```

Keep labels in `LabelMap` form through transform and save/load workflows.

## Subject consistency errors

### Error pattern

`RuntimeError: Inconsistent spatial_shape` or `RuntimeError: Inconsistent spacing`

### Cause

`Subject` computes shared spatial properties only when all images agree. A scalar image and label map with different shapes or affines should fail validation.

### Fix

Inspect each image before constructing downstream workflows:

```python
for name, image in subject.images.items():
    print(name, image.shape, image.spacing, image.orientation)
```

Then resample, crop/pad, or otherwise harmonize images in the transform sub-skill. Do not bypass the consistency check if downstream transforms or patch sampling assume alignment.

## Points axes and shape confusion

### Error patterns

- `ValueError: Points must have shape (N, 3)`
- `ValueError: Invalid ... axes`
- Landmarks appear mirrored or permuted after conversion.

### Fix

Use a 2D `(N, 3)` coordinate tensor and declare axes explicitly when data is not voxel `IJK`.

```python
points = tio.Points(torch.tensor([[10.0, 20.0, 30.0]]), axes="IJK", affine=image.affine)
ras_points = points.to_axes("RAS")
world = points.to_world()
```

Valid voxel axes are permutations of `IJK`. Valid anatomical axes use one axis from each anatomical pair, such as `RAS` or `LPI`.

## Bounding box format confusion

### Error patterns

- `ValueError: BoundingBoxes must have shape (N, 6)`
- Wrong interpretation of box columns.
- `ValueError` from invalid axes or representation.
- `Expected N labels, got M`.

### Fix

Always pair box data with the exact format.

```python
boxes = tio.BoundingBoxes(
    torch.tensor([[10, 20, 30, 50, 60, 70]], dtype=torch.float32),
    format=tio.BoundingBoxFormat.IJKIJK,
    labels=torch.tensor([1]),
    affine=image.affine,
)
center_size = boxes.to_format(tio.BoundingBoxFormat.IJKWHD)
```

Use `IJKIJK` for two voxel corners and `IJKWHD` for voxel center plus size. Use `BoundingBoxFormat("RAS", "corners")` only when coordinates are already anatomical/world coordinates.

## Annotation constructor errors

### Symptom

Image-level annotations fail with a type error.

### Cause

The `points=` and `bounding_boxes=` image constructor keywords expect dictionaries of already constructed `Points` or `BoundingBoxes` objects, not raw tensors.

### Fix

```python
points = tio.Points(torch.tensor([[1.0, 2.0, 3.0]]), affine=image_affine)
boxes = tio.BoundingBoxes(
    torch.tensor([[0, 0, 0, 5, 5, 5]], dtype=torch.float32),
    format=tio.BoundingBoxFormat.IJKIJK,
    affine=image_affine,
)
image = tio.ScalarImage(
    torch.randn(1, 8, 8, 8),
    affine=image_affine,
    points={"seed": points},
    bounding_boxes={"roi": boxes},
)
```

## Save/load surprises

### Symptoms

- Saved image loads with unexpected orientation or spacing.
- Saving remote/zarr target fails.
- Label dtype or values look changed after a downstream workflow.

### Fixes

- Check `image.affine`, `image.spacing`, and `image.orientation` before saving.
- Use a temporary local `.nii.gz` file for smoke tests.
- Use `LabelMap` for masks and avoid intensity-style interpolation in transform workflows.
- Route `.nii.zarr`, remote storage, CLI cache, and conversion operations to `cli-and-io`.

```python
image.save("checked.nii.gz")
loaded = tio.ScalarImage("checked.nii.gz")
assert loaded.shape == image.shape
assert loaded.spacing == image.spacing
```
