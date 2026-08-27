---
name: sparse-tensor-data
description: "Helps with MinkowskiEngine SparseTensor, TensorField, batching,
  quantization, coordinate-manager, and dense/sparse conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Sparse Tensor Data

Use this sub-skill when the task is about coordinates, sparse tensor construction, voxelization, batching, TensorField slicing/splatting, or dense/sparse conversion.

## What This Route Covers

- `SparseTensor` and `TensorField` creation.
- `sparse_quantize`, `sparse_collate`, `batched_coordinates`, and `SparseCollation`.
- Coordinate-manager/key sharing and sparse tensor arithmetic.
- Batch-wise decomposition and coordinate lookup.
- Dense-to-sparse and sparse-to-dense conversion helpers.
- Continuous-coordinate workflows that start from `TensorField`.

## What It Excludes

- Build/install problems; use `../build-and-install/SKILL.md`.
- Layer/network construction; use `../layers-and-networks/SKILL.md`.
- Training/demo pipelines; use `../training-and-demos/SKILL.md`.

## Read These Bundled Files First

- `references/api-reference.md` for verified signatures and public API names.
- `references/workflows.md` for step-by-step recipes.
- `references/troubleshooting.md` for coordinate, dtype, quantization, and manager/key failures.
- `scripts/sparse_tensor_smoke.py` for a safe synthetic smoke test.

## Typical Triggers

- You need to turn points into batched sparse tensors.
- You need to quantize coordinates or recover inverse maps.
- You see coordinate-manager/key mismatch errors.
- You need to slice a sparse output back onto an input field.
- You want to inspect batch-wise coordinates or features.

## Fast Workflow

1. Read the API reference to confirm the exact constructor and helper signatures.
2. Decide whether the input is discrete coordinates or continuous coordinates.
3. Pick `sparse_collate`/`batched_coordinates` for batches and `sparse_quantize` for voxelization.
4. Share the coordinate manager or map key when tensors must interact.
5. Run the bundled smoke script to verify a minimal path.

## Public Semantic Rules

- Batch indices are prepended in the first coordinate column.
- Coordinates and features must be 2D matrices.
- `TensorField` is the right starting point for continuous coordinates that need quantization or splatting.
- Sparse tensor arithmetic requires compatible coordinate managers or keys.

## Related Helpers

- `../../scripts/check_minkowski_engine.py` — import and tiny package smoke.
- `scripts/sparse_tensor_smoke.py` — tiny sparse tensor workflow smoke.

## When to Stop

If the issue is really about a convolution or pooling operator, stop here and route to `layers-and-networks`. If it is about dataset loading, collate functions, or demos, route to `training-and-demos`.
