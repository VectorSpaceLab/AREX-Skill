# Troubleshooting

## Coordinate shape problems

**Symptoms**
- Errors about coordinate dimension mismatch.
- `SparseTensor` construction fails because coordinates are not 2D.

**Likely cause**
- Coordinates were stacked manually in the wrong shape.

**Fix**
- Use `ME.utils.batched_coordinates` or `ME.utils.sparse_collate`.
- Remember that batch index is prepended in the first column.

## Feature / coordinate row mismatch

**Symptoms**
- The constructor complains that coordinates and features do not match.

**Likely cause**
- Coordinate rows and feature rows were filtered differently.

**Fix**
- Apply the same quantization or masking path to both tensors.
- Recheck `sparse_quantize` outputs before building the sparse tensor.

## `coordinate_manager` or `coordinate_map_key` mismatch

**Symptoms**
- Binary operations, concatenation, or in-place updates fail with a coordinate-manager/key error.

**Likely cause**
- The sparse tensors were built independently.

**Fix**
- Reuse the coordinate manager when tensors must interact.
- Reuse the coordinate map key when tensors must be identical for in-place ops.
- If tensors should stay separate, do not force them through an in-place route.

## `TensorField` not slicing back correctly

**Symptoms**
- `slice()` or `inverse_mapping()` does not line up with the input field.

**Likely cause**
- The field was quantized with the wrong mode or the wrong coordinate path.

**Fix**
- Start from `TensorField` for continuous coordinates.
- Keep the quantization mode consistent with the intended aggregation behavior.

## `sparse_quantize` label or device problems

**Symptoms**
- Quantization with labels fails.
- Map outputs are not what you expected on CPU or CUDA.

**Likely causes**
- Labels were not kept on the CPU path supported by the implementation.
- `quantization_size` did not match the coordinate dimension.

**Fix**
- Keep labels aligned with the API constraints.
- Check that scalar versus per-dimension quantization sizes match the data dimension.

## Dense round-trip confusion

**Symptoms**
- `to_sparse` or `MinkowskiToDenseTensor` returns a different shape than expected.

**Likely cause**
- Dense shape assumptions and sparse tensor stride assumptions were mixed up.

**Fix**
- Pass `torch.Size` rather than a plain Python list when using the `dense(shape=...)` argument.
- Recheck tensor stride and batch layout before round-tripping.

## Integer tensor quantization edge case

**Symptoms**
- `sparse_quantize` raises a torch `floor` error on an integer tensor in some torch/build combinations.

**Likely cause**
- The helper floors coordinates internally, and the active torch build does not implement `floor` for integer tensors.

**Fix**
- Use NumPy integer coordinates, or pass floating-point torch coordinates before quantization.
- Keep label quantization on the CPU path when labels are provided.

## Invalid batch index lookup

**Symptoms**
- `coordinates_at(batch_index)` or `features_at(batch_index)` raises `IndexError` for a missing batch.

**Likely cause**
- The requested batch index was not present after collation, quantization, or pooling.

**Fix**
- Check the number of batch rows present before indexing.
- Do not rely on invalid batch indices returning an empty tensor across versions.
