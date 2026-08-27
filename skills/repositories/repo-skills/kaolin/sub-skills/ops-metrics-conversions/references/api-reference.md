# API Reference: Ops, Metrics, Conversions, and Transforms

Use this reference after data is already in memory. Route file parsing, datasets, materials, and container-selection policy to `geometry-io-representations`.

## Shared tensor contracts

- **Exact batches**: homogeneous batch-first tensors such as points `(B, N, 3)`, vertices `(B, V, 3)`, voxelgrids `(B, X, Y, Z)`.
- **Packed batches**: variable-size examples flattened to `(sum_i N_i, C)` plus metadata.
- **Padded batches**: dense batch tensors `(B, *max_shape, C)` plus `shape_per_tensor` to identify valid extents.
- In Kaolin batch helpers, `shape_per_tensor` excludes the final feature/channel dimension.
- Triangle mesh faces are `torch.long` indices; many mesh ops assume fixed unbatched topology `(F, 3)` shared by vertices `(B, V, 3)`.
- `kaolin.math.quat` uses xyzw quaternions: xyz imaginary components, real `w` last.
- `kaolin.ops.gaussians.transform_gaussians` defaults to wxyz orientations unless `use_xyzw=True`.
- SPC `lengths` for `scan_octrees` should be a CPU int tensor; SPC compute tensors generally live on CUDA.

## `kaolin.ops.batch`

- `get_shape_per_tensor(tensor_list)` -> `(B, ndim_without_feature)`. All tensors must share rank, dtype, and final feature dimension.
- `list_to_packed(tensor_list)` -> `(packed_tensor, shape_per_tensor)`; each item is reshaped to `(-1, C)`.
- `get_first_idx(numel_per_tensor)` -> offsets of length `B + 1`.
- `tile_to_packed(values, numel_per_tensor)` -> `(sum(numel_per_tensor), 1)` repeated values; CUDA fast path expects CUDA `values` and CPU `numel_per_tensor`.
- `packed_to_list(packed_tensor, shape_per_tensor, first_idx)` round-trips packed data to a Python list.
- `fill_max_shape(shape_per_tensor, partial_max_shape=None)` resolves `-1` dimensions and validates requested maxima.
- `list_to_padded(tensor_list, padding_value, max_shape=None)` -> `(padded_tensor, shape_per_tensor)`.
- `padded_to_list(padded_tensor, shape_per_tensor)` extracts valid regions.
- `packed_to_padded(...)` and `padded_to_packed(...)` convert between packed and padded layouts.

## Mesh ops

Common tensors:
- `vertices`: `(B, V, 3)` float tensor.
- `faces`: `(F, 3)` long tensor for fixed-topology triangle meshes.
- `face_vertices`: `(B, F, 3, 3)` from `index_vertices_by_faces(vertices, faces)`.

Key APIs:
- `index_vertices_by_faces(vertices_features, faces)` gathers `(B, V, C)` to `(B, F, face_size, C)`.
- `unindex_vertices_by_faces(face_vertex_features)` flattens per-face-per-vertex features and creates face indices.
- `adjacency_matrix(num_vertices, faces, sparse=True)` returns sparse/dense adjacency.
- `uniform_laplacian(num_vertices, faces)` returns a dense uniform Laplacian.
- `average_face_vertex_features(faces, face_features, num_vertices=None)` averages face features to vertices.
- `compute_vertex_normals(faces, face_normals, num_vertices=None)` averages per-face normals to vertices.
- `face_areas(vertices, faces)` -> `(B, F)`.
- `packed_face_areas(vertices, first_idx_vertices, faces, num_faces_per_mesh)` handles packed vertices/faces.
- `sample_points(vertices, faces, num_samples, areas=None, face_features=None)` -> sampled points `(B, num_samples, 3)`, face choices `(B, num_samples)`, and optional interpolated features `(B, num_samples, D)`.
- `packed_sample_points(vertices, first_idx_vertices, faces, num_faces_per_mesh, num_samples, areas=None)` samples packed mesh batches and returns exact-batched points.
- `face_normals(face_vertices, unit=False)` -> `(B, F, 3)`.
- `subdivide_trianglemesh(vertices, faces, iterations, alpha=None)` performs Loop-style subdivision.
- `vertex_tangents(faces, face_vertices, face_uvs, vertex_normals)` computes tangents from geometry, UVs, and normals.

## Pointcloud, coords, and voxelgrid ops

- `center_points(points, normalize=False, eps=1e-6)` centers each point cloud `(B, N, 3)`; optional normalization scales each cloud to approximately `[-0.5, 0.5]`.
- `farthest_point_sampling(points, k)` returns indices `(B, k)`; CUDA + Warp + float32 only.
- `spherical2cartesian(azimuth, elevation, distance=None)` and `cartesian2spherical(x, y, z)` use radians and the documented X-toward-camera, Z-up, Y-right convention.
- `downsample(voxelgrids, scale)` average-pools `(B, X, Y, Z)` and does not threshold.
- `extract_surface(voxelgrids, mode="wide" | "thin")` returns bool surface voxels.
- `fill(voxelgrids)` fills enclosed holes; CPU-only and not differentiable.
- `extract_odms(voxelgrids)` -> `(B, 6, dim, dim)` ordered `z_neg, z_pos, y_neg, y_pos, x_neg, x_pos`.
- `project_odms(odms, voxelgrids=None, votes=1)` projects ODMs back to occupancy.

## Representation conversions

- `pointclouds_to_voxelgrids(pointclouds, resolution, origin=None, scale=None, return_sparse=False)` normalizes `(point - origin) / scale`, discards out-of-range points, and returns dense or sparse voxelgrids.
- `trianglemeshes_to_voxelgrids(vertices, faces, resolution, origin=None, scale=None, return_sparse=False)` voxelizes mesh surface support after the same normalization.
- `voxelgrids_to_cubic_meshes(voxelgrids, is_trimesh=True)` returns Python lists of per-batch vertices/faces; CPU and CUDA are supported.
- `voxelgrids_to_trianglemeshes(voxelgrids, iso_value=0.5)` uses CUDA marching cubes and returns per-batch lists.
- `unbatched_pointcloud_to_spc(pointcloud, level, features=None)` creates a single-entry `Spc` from normalized `[-1, 1]` points; duplicate quantized cells are merged and features are averaged.
- `unbatched_mesh_to_spc(face_vertices, level)` converts one triangle mesh `(F, 3, 3)` to SPC on CUDA.
- `gs_to_voxelgrid(xyz, scales, rots, opacities, level, iso=11.345, tol=1./8., step=10)` voxelizes 3D Gaussians on CUDA and returns quantized voxel coordinates plus accumulated opacities.

## SPC ops

Core tensors:
- `octrees`: packed `torch.uint8` bytes.
- `lengths`: CPU int tensor `(B,)`, sum equals `octrees.numel()`.
- `pyramids`: `(B, 2, max_level + 2)` counts/offsets per level.
- `exsum`: current inclusive bit-count prefix-sum length `num_bytes`; legacy layout length `num_bytes + B` is accepted with warning.
- `point_hierarchies`: packed short tensor `(num_points_all_levels, 3)`.

Key APIs:
- `quantize_points(x, level)` clips `[-1, 1]` float coordinates to short integer grid points.
- `points_to_morton`, `morton_to_points`, `points_to_corners` convert quantized coordinates and corners.
- `unbatched_points_to_octree(points, level, sorted=False)` builds one octree from quantized points.
- `scan_octrees(octrees, lengths, legacy_exsum=False)` -> `(max_level, pyramids, exsum)`; keep `lengths` on CPU.
- `generate_points(octrees, pyramids, exsum)` decodes point hierarchies; current or legacy `exsum` accepted.
- `feature_grids_to_spc(feature_grids, masks=None)` converts `(B, C, X, Y, Z)` grids to `(octrees, lengths, coalescent_features)`.
- `to_dense(point_hierarchies, pyramids, input, level=-1)` scatters packed features into dense grids.
- `unbatched_query(octree, exsum, query_coords, level, with_parents=False)` returns point indices or `-1`; float queries are normalized `[-1, 1]`, integer queries are grid coordinates.
- `unbatched_get_level_points`, `unbatched_make_dual`, `unbatched_make_trinkets`, `coords_to_trilinear_coeffs`, and `unbatched_interpolate_trilinear` support level slicing and dual-octree interpolation.
- `create_dense_spc(level, device)` creates a fully occupied SPC octree.
- `conv3d`, `Conv3d`, `conv_transpose3d`, `ConvTranspose3d` apply sparse SPC convolution; `kernel_vectors` is `(K, 3)` short offsets and `weight` is `(K, in_channels, out_channels)`.

See [spc-workflows.md](spc-workflows.md) for assembly and diagnostics.

## Gaussian ops

- `transform_gaussians(positions, orientations, scales, transform, sh_coeff=None, use_log_scales=False, use_xyzw=False)` applies a 4x4 transform to positions `(N, 3)`, orientations `(N, 4)`, scales `(N, 3)`, and optional SH coefficients. Default orientation order is wxyz.
- `transform_shs(shs_feat, R)` rotates SH coefficients `(N, (degree + 1)^2, 3)` for degrees 0 through 3; DC band is unchanged.
- `sample_points_in_volume(...)` is the CUDA/SPC Gaussian densifier. It supports `octree_level` 6 through 10 and returns interior points `(K, 3)` or an empty tensor when shell filling fails.

## Quaternion and transform math

All helpers are tensor-only and suitable for CPU probes. Pass explicit CPU device to identity helpers when CUDA is not available.

Quaternion xyzw helpers:
- component/norm: `quat_real`, `quat_imaginary`, `quat_abs`
- canonicalization: `quat_positive`, `quat_unit`, `quat_unit_positive`, `quat_identity`
- algebra: `quat_conjugate`, `quat_inverse`, `quat_mul`, `quat_rotate`
- conversions: `quat_from_angle_axis`, `quat_from_rot33`, `angle_axis_from_quat`, `angle_axis_from_rot33`

Matrix and Euclidean helpers:
- `rot33_from_quat`, `rot33_from_angle_axis`, `rot33_inverse`, `rot33_rotate`, `is_rot33_valid`
- `rot44_from_quat`, `translation_to_mat44`, `scale_to_mat44`
- `euclidean_identity`, `euclidean_from_rotation_translation`, `euclidean_rotation_matrix`, `euclidean_translation_vector`, `is_euclidean_valid`, `euclidean_inverse`

Compact transform helpers:
- `transform_from_rotation_translation(rotation=None, translation=None)` -> `[quat_xyzw, translation_xyz]` `(B, 7)`.
- `transform_from_euclidean`, `transform_identity`, `transform_rotation`, `transform_translation`, `transform_inverse`, `transform_mul`, `transform_apply`.

## Metrics and losses

Pointcloud metrics:
- `sided_distance(p1, p2)` -> squared distances and indices `(B, N1)`; CUDA extension path.
- `chamfer_distance(p1, p2, w1=1., w2=1., squared=True)` -> `(B,)`; CUDA extension path.
- `f_score(gt_points, pred_points, radius=0.01, eps=1e-8)` -> `(B,)`.

Mesh metrics:
- `point_to_mesh_distance(pointclouds, face_vertices)` accepts `(B, N, 3)` and `(B, F, 3, 3)` and returns squared distances, face indices, and distance type codes `(B, N)`.
- `average_edge_length(vertices, faces)` -> `(B, F)`.
- `uniform_laplacian_smoothing(vertices, faces)` -> `(B, V, 3)`.

Voxel/mask metrics:
- `voxelgrid.iou(pred, gt)` expects same-shaped voxelgrids `(B, X, Y, Z)`, casts to bool, and returns `(B,)`.
- `render.mask_iou(lhs_mask, rhs_mask)` expects `(B, H, W)` and returns loss scalar `1 - mean(IoU)`, not an IoU similarity.
