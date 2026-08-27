# Workflows: Tensor Ops, Conversions, Metrics, and Transforms

Use these recipes after geometry has been loaded or constructed. For file import/export, datasets, materials, or container choice, route to `geometry-io-representations` first.

## Choose exact, packed, or padded layout

Decision rules:

1. **Exact batch** when every example has the same size: points `(B, N, 3)`, vertices `(B, V, 3)`, voxelgrids `(B, X, Y, Z)`.
2. **Packed layout** when sizes vary and downstream code supports flattened tensors plus offsets. Keep `shape_per_tensor`, `numel_per_tensor`, and `first_idx`.
3. **Padded layout** when a dense batch axis is required by a model/kernel. Keep `shape_per_tensor` so padded values are masked out.
4. Convert at workflow boundaries only; repeated pack/pad conversions easily stale offsets.

Variable-size tensor pattern:

```python
packed, shape_per_tensor = list_to_packed(tensor_list)
numel_per_tensor = shape_per_tensor.prod(dim=1) if shape_per_tensor.shape[1] > 1 else shape_per_tensor.reshape(-1)
first_idx = get_first_idx(numel_per_tensor)
padded = packed_to_padded(packed, shape_per_tensor, first_idx, padding_value=0.0)
```

For variable-size meshes, use packed mesh APIs only when vertices/faces remain mesh-local and you also pass `first_idx_vertices` and `num_faces_per_mesh`.

## Mesh to samples, normals, and losses

Given vertices `(B, V, 3)` and triangle faces `(F, 3)`:

1. Build `face_vertices = index_vertices_by_faces(vertices, faces)`.
2. Precompute `areas = face_areas(vertices, faces)` for repeated sampling.
3. Use `sample_points(vertices, faces, num_samples, areas=areas)` for exact-batched point clouds.
4. Use `face_normals(face_vertices, unit=True)` for normal checks.
5. Use `point_to_mesh_distance(points, face_vertices)` for point-to-surface loss and inspect `dist_type` for vertex/edge/face cases.
6. Use `average_edge_length` and `uniform_laplacian_smoothing` for mesh scale and smoothness checks.

If topology varies per item, either use packed mesh APIs or sample each mesh independently before stacking equal-size point clouds.

## Pointcloud workflows

- `center_points(points, normalize=False)` removes per-cloud translation.
- `center_points(..., normalize=True)` normalizes each cloud into approximately `[-0.5, 0.5]`.
- `farthest_point_sampling(points, k)` is CUDA + Warp + float32 only and returns indices `(B, k)`. Gather coordinates separately.
- For CPU-only downsampling, use random sampling or representation-specific alternatives and document that it is not FPS-equivalent.

## Point/mesh to voxelgrid and voxelgrid back to mesh

Pointcloud to voxelgrid:

1. Choose `resolution` and dense versus sparse output.
2. Pass explicit `origin` `(B, 3)` and `scale` `(B,)` when comparing batches.
3. Use `pointclouds_to_voxelgrids(pointclouds, resolution, origin, scale, return_sparse)`.

Mesh to voxelgrid:

1. Ensure `faces` are triangles.
2. Use `trianglemeshes_to_voxelgrids(vertices, faces, resolution, origin, scale, return_sparse)`.
3. Remember the result is a surface occupancy grid, not a filled solid.

Voxelgrid post-processing:

- `downsample` average-pools and does not threshold.
- `extract_surface(mode="wide" | "thin")` isolates surface voxels.
- `fill` is CPU-only and not differentiable.
- `extract_odms`/`project_odms` handle orthographic depth map workflows; tune `votes` for projection strictness.

Voxelgrid to mesh:

- Use `voxelgrids_to_cubic_meshes` for CPU-safe cubified output.
- Use `voxelgrids_to_trianglemeshes` for CUDA marching cubes.
- Both return lists of per-batch vertices/faces; pack explicitly if later code expects packed tensors.

## SPC workflows

Use SPC for sparse hierarchical occupancy, multiresolution queries, trilinear interpolation, or SPC convolution. Follow [spc-workflows.md](spc-workflows.md) rather than assembling fields ad hoc.

Quick rules:
- Normalize float coordinates to `[-1, 1]` before `quantize_points` or `unbatched_pointcloud_to_spc`.
- Keep `lengths` for `scan_octrees` on CPU.
- Prefer current `exsum`; request `legacy_exsum=True` only for compatibility tests.
- `unbatched_query` returns `-1` for absent cells.

## Gaussian workflows

Rigid/scale transforms:

1. Keep `positions`, `orientations`, `scales`, `transform`, and optional `sh_coeff` on the same dtype/device.
2. Use `transform_gaussians(...)` for positions/orientations/scales and optional SH coefficients.
3. Default orientation order is wxyz. If inputs are xyzw, pass `use_xyzw=True`.
4. Avoid interpreting shear or anisotropic inverse scaling as a robustly supported path.

Occupancy/densification:

- `gs_to_voxelgrid` is CUDA-only and returns voxel coordinates plus accumulated opacities.
- `sample_points_in_volume` is heavier and should be run only when interior samples from a Gaussian shell are explicitly needed.
- Empty Gaussian densifier output usually points to low opacity, shell holes, too high `octree_level`, or a strict `opacity_threshold`.

## Quaternion and transform workflow

Use [../scripts/quaternion_smoke.py](../scripts/quaternion_smoke.py) for a safe environment check.

Typical path:

1. Canonicalize quaternions with `quat_unit_positive`.
2. Convert to matrices with `rot33_from_quat` or `rot44_from_quat`.
3. Build 4x4 Euclidean transforms with `euclidean_from_rotation_translation`.
4. Build compact transforms with `transform_from_rotation_translation` or `transform_from_euclidean`.
5. Apply and validate with `transform_apply` and `transform_inverse`.

Remember: low-level `kaolin.math.quat` uses xyzw, but Gaussian transforms default to wxyz.

## Metric and loss selection

- Pointcloud vs pointcloud: `chamfer_distance`, `sided_distance`, `f_score` (CUDA-extension paths).
- Pointcloud vs mesh: `point_to_mesh_distance` on `(B, N, 3)` and `(B, F, 3, 3)`.
- Mesh regularization: `average_edge_length`, `uniform_laplacian_smoothing`.
- Voxel occupancy: `voxelgrid.iou(pred, gt)` returns per-batch IoU.
- 2D masks: `render.mask_iou(lhs_mask, rhs_mask)` returns a loss scalar, so smaller is better.

Before averaging a metric, check whether it returns `(B,)`, `(B, N)`, or a scalar loss and record the reduction explicitly.

## Smoke-test workflow

- CPU/core check: `python scripts/tensor_ops_smoke.py`
- CUDA/SPC check: `python scripts/tensor_ops_smoke.py --cuda-smoke`
- Quaternion check: `python scripts/quaternion_smoke.py --device cpu`
