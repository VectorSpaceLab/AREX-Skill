# Sparse Tensor Workflows

## 1) Create batched sparse inputs

Use `batched_coordinates` when you already have a list of coordinate matrices, or `sparse_collate` when you also have features and optional labels.

```python
coords_batch, feats_batch = ME.utils.sparse_collate(coords_list, feats_list)
st = ME.SparseTensor(features=feats_batch, coordinates=coords_batch)
```

Use `SparseCollation` when the collate logic needs a configurable point limit.

## 2) Quantize continuous coordinates

Use `sparse_quantize` when coordinates are floating-point point clouds or voxel positions.

```python
coords_q, feats_q = ME.utils.sparse_quantize(
    coordinates=points,
    features=features,
    quantization_size=0.05,
)
```

Rules:

- Use `return_index=True` and `return_inverse=True` when you need to recover original rows.
- If you are carrying labels, make sure to keep the label path consistent with the CPU-only label behavior described in the API reference.

## 3) Build a sparse tensor

```python
st = ME.SparseTensor(
    features=feats_batch,
    coordinates=coords_batch,
    tensor_stride=1,
)
```

If another sparse tensor must interact with this one, reuse the coordinate manager:

```python
other = ME.SparseTensor(
    features=other_feats,
    coordinates=other_coords,
    coordinate_manager=st.coordinate_manager,
)
```

For in-place binary operations, also reuse the same coordinate map key.

## 4) Use `TensorField` for continuous inputs

`TensorField` is the better starting point when coordinates are not already discrete.

```python
field = ME.TensorField(
    features=colors,
    coordinates=ME.utils.batched_coordinates([points / voxel_size], dtype=torch.float32),
    quantization_mode=ME.SparseTensorQuantizationMode.UNWEIGHTED_AVERAGE,
)
st = field.sparse()
```

Project the sparse output back to the field with `slice()`.

## 5) Inspect batch-wise outputs

Useful properties and methods:

- `decomposed_coordinates`
- `decomposed_features`
- `decomposed_coordinates_and_features`
- `coordinates_at(batch_index)`
- `features_at(batch_index)`

Check that the batch index exists before indexing; a missing batch can raise `IndexError`.

These are the right tools when you need per-example outputs after a batched sparse forward pass.

## 6) Convert to dense and back

```python
dense, min_coordinate, tensor_stride = st.dense()
round_trip = ME.to_sparse(dense)
```

If you need to pass an explicit dense shape, use a `torch.Size` value rather than a plain Python list.

Use `MinkowskiToDenseTensor` / `MinkowskiToSparseTensor` when you want the conversion inside a module.

## 7) Tiny synthetic smoke pattern

A good local smoke pattern is:

1. Create two tiny coordinate batches.
2. Collate them.
3. Build one sparse tensor and one tensor field.
4. Run a trivial arithmetic or slicing check.
5. Verify batch-wise decomposition.

This pattern is intentionally small enough to run without downloads or pretrained weights.
