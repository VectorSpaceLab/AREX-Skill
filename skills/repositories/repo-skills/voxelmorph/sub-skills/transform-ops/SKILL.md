---
name: transform-ops
description: "Use VoxelMorph PyTorch tensor transform operations for affine,
  displacement, coordinate, warping, integration, resizing, composition, random
  transform, and module wrapper workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VoxelMorph transform operations

Use this sub-skill when the task is about VoxelMorph's PyTorch tensor transform primitives, not about model training or data generation. It covers dense displacement fields, affine transforms, coordinate normalization, spatial warping, scaling-and-squaring integration, displacement resizing/composition, random transform generation, and the module wrappers around these operations.

## Use this for

- Building 2D/3D affine matrices with `voxelmorph.params_to_affine()` or `voxelmorph.random_affine()`.
- Converting affine matrices to dense displacement fields with `voxelmorph.affine_to_disp()`.
- Converting among displacement fields, absolute transformation fields, and normalized sampling coordinates with `disp_to_trf()`, `trf_to_disp()`, and `disp_to_coords()`.
- Warping tensors with `voxelmorph.spatial_transform()` or `voxelmorph.nn.functional.spatial_transform()`.
- Integrating stationary velocity fields using scaling and squaring with `integrate_disp()` or `IntegrateVelocityField`.
- Resizing/rescaling dense displacement fields with `resize_disp()` or `ResizeDisplacementField`.
- Composing affine and dense transforms with `compose()`.
- Creating synthetic affine, displacement, or mixed random transforms for tests and augmentation-like utilities.
- Using `SpatialTransformer`, `IntegrateVelocityField`, and `ResizeDisplacementField` inside PyTorch modules.

## Do not use this for

- Pairwise-registration model construction, loss selection, optimizer setup, training loops, checkpoints, or inference workflows; use the pairwise-registration sub-skill instead.
- Volume loading, file I/O, batching, generator design, scan pair sampling, or data augmentation pipelines around datasets; use the data-generators sub-skill instead.
- TensorFlow-era VoxelMorph APIs. This sub-skill describes the PyTorch branch behavior.

## First routing decisions

1. **Choose the API layer.** Use top-level `voxelmorph` functions for unbatched fields, affine utilities, and shape-agnostic transforms. Use `voxelmorph.nn.functional` when tensors are already in neural-network format `(B, C, *spatial)` for images and `(B, ndim, *spatial)` for fields. Use module wrappers when the operation belongs in an `nn.Module` graph.
2. **Normalize shape language.** Dense fields are channels-first: `(ndim, *spatial)` or `(B, ndim, *spatial)`. Image tensors use `non_spatial_dims` to identify leading channel/batch dimensions. Meshgrids are `(ndim, *spatial)` with `ij` indexing.
3. **Remember backward warping.** `spatial_transform()` samples the source image at `x + disp(x)`, so a positive displacement samples from a larger coordinate and can make visible image content move in the opposite direction.
4. **Treat `coords_to_disp()` as unavailable.** It exists in both public layers but currently raises `NotImplementedError`; do not plan workflows that require the inverse normalized-coordinate conversion.
5. **Keep model and data responsibilities out.** If the task starts asking for training, VxmPairwise, losses, volume readers, or generators, stop routing through this sub-skill.

## Reference map

- [API reference](references/api-reference.md): signatures, shape conventions, return types, and gotchas for `voxelmorph.functional`, `voxelmorph.nn.functional`, and module wrappers.
- [Workflows](references/workflows.md): copied/adapted runnable patterns for affine-to-displacement, warping, integration, resizing, composition, random transforms, and module use.
- [Troubleshooting](references/troubleshooting.md): common assertion errors, axis/sign mistakes, interpolation issues, unavailable inverse conversion, random seeding, and composition limitations.
- [Smoke script](scripts/transform_ops_smoke.py): deterministic CPU/GPU-safe checks for core transform operations; run with `python scripts/transform_ops_smoke.py --help` from this sub-skill directory or with the script path from any project that has `voxelmorph` importable.
