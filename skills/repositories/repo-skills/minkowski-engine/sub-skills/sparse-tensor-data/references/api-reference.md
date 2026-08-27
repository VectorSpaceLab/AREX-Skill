# API Reference

## Purpose

Use this file to confirm the public sparse-tensor API before writing a workflow or helper script.

## Core Types

### `SparseTensor`

Signature:

```python
SparseTensor(
    features,
    coordinates=None,
    tensor_stride=1,
    coordinate_map_key=None,
    coordinate_manager=None,
    quantization_mode=SparseTensorQuantizationMode.RANDOM_SUBSAMPLE,
    allocator_type=None,
    minkowski_algorithm=None,
    requires_grad=None,
    device=None,
)
```

Key facts:

- `features` must be a 2D torch tensor.
- `coordinates` is optional only when you already have a `coordinate_map_key` and `coordinate_manager` pair.
- `coordinate_map_key` implies `coordinate_manager`.
- Batch indices are prepended in the first coordinate column.
- `tensor_stride` can be an int or per-dimension sequence.
- Useful methods/properties: `coordinate_manager`, `coordinate_key`, `tensor_stride`, `coordinates`, `features`, `C`, `F`, `sparse()`, `dense()`, `slice()`, `interpolate()`, `cat_slice()`, `features_at_coordinates()`, `coordinates_at()`, `features_at()`, and decomposition helpers.

### `TensorField`

Signature:

```python
TensorField(
    features,
    coordinates=None,
    tensor_stride=1,
    coordinate_field_map_key=None,
    coordinate_manager=None,
    quantization_mode=SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE,
    allocator_type=None,
    minkowski_algorithm=None,
    requires_grad=None,
    device=None,
)
```

Key facts:

- `TensorField` is the right starting point for continuous coordinates.
- `sparse()` converts the field to a `SparseTensor`.
- `splat()` creates splat coordinates for interpolation-style workflows.
- `inverse_mapping()` returns the mapping needed to project sparse outputs back to the field.

## Coordinate Management

### `CoordinateManager`

Useful methods:

- `insert_and_map(coordinates, tensor_stride=1, string_id='')`
- `insert_field(coordinates, tensor_stride, string_id='')`
- `field_to_sparse_insert_and_map(field_map_key, sparse_tensor_stride, sparse_tensor_string_id='')`
- `kernel_map(...)` for neighborhood lookup used by layers.

Key fact:

- A `CoordinateManager` owns cached coordinate maps and kernel maps. Reuse it when tensors must interact.

### `CoordinateMapKey`

- Keys identify cached coordinate maps.
- If two sparse tensors must share exact coordinates for in-place ops, they need the same key.

### Operation mode helpers

- `set_sparse_tensor_operation_mode(SparseTensorOperationMode.SHARE_COORDINATE_MANAGER)` shares a global manager by default.
- `clear_global_coordinate_manager()` must be called after using the shared mode.
- `global_coordinate_manager()` exposes the current shared manager.

## Quantization and Collation

### `sparse_quantize`

Signature:

```python
sparse_quantize(
    coordinates,
    features=None,
    labels=None,
    ignore_label=-100,
    return_index=False,
    return_inverse=False,
    return_maps_only=False,
    quantization_size=None,
    device='cpu',
)
```

Key facts:

- Use for voxelization or discrete coordinate deduplication.
- `quantization_size` can be scalar or per-dimension sequence.
- `return_index` and `return_inverse` are useful for recovering original rows.
- When labels are present, coordinates/labels must be CPU tensors in this checkout's implementation.
- `device='cuda'` computes maps with a CUDA coordinate map manager when available.

### `batched_coordinates`

Signature:

```python
batched_coordinates(coords, dtype=torch.int32, device=None)
```

Use for converting a list of coordinate matrices into a batch-first coordinate tensor.

### `sparse_collate`

Signature:

```python
sparse_collate(coords, feats, labels=None, dtype=torch.int32, device=None)
```

Use for batched coordinates and features, optionally with labels.

### `batch_sparse_collate`

Signature:

```python
batch_sparse_collate(data, dtype=torch.int32, device=None)
```

Use as a `DataLoader` collate function for `(coords, feats, labels)` tuples.

### `SparseCollation`

Signature:

```python
SparseCollation(limit_numpoints=-1, dtype=torch.int32, device=None)
```

Use when you want a configurable collate object, especially with a point-count cap.

## Dense/Sparse Conversion Helpers

- `to_sparse(x, format=None, coordinates=None, device=None)` converts a dense tensor to sparse form.
- `to_sparse_all(dense_tensor, coordinates=None)` returns all non-zero coordinates/features.
- `MinkowskiToSparseTensor(remove_zeros=True, coordinates=None)` wraps dense-to-sparse conversion in a module.
- `MinkowskiToDenseTensor(shape=None)` converts sparse tensors back to dense.
- `MinkowskiToFeature()` strips coordinates and keeps features.
- `dense_coordinates(shape)` creates a dense coordinate grid.

## Dataflow Rules

- Coordinates and features are 2D matrices with matching row counts.
- Batch index comes first in the coordinate matrix.
- Sharing the coordinate manager is enough for many binary ops; in-place ops also need the same key.
- `TensorField` is better than manual float-coordinate handling when inputs are continuous.
