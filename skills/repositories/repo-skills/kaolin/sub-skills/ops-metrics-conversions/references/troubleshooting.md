# Troubleshooting Ops, Metrics, Conversions, and SPC Workflows

Use this when a tensor-level Kaolin workflow fails after data is already in memory. Route file/container issues to `geometry-io-representations`, rendering/camera failures to `rendering-cameras-lighting`, and simulation-loop failures to `physics-simulation`.

## Safe probes

- Quaternion/math CPU probe: `python scripts/quaternion_smoke.py`
- Core tensor/mesh/voxel/metric CPU probe: `python scripts/tensor_ops_smoke.py`
- Optional CUDA/SPC probe: `python scripts/tensor_ops_smoke.py --cuda-smoke`

## Backend gates

| Capability | Backend gate | Safe decision |
|---|---|---|
| Batch helpers, coords, many mesh ops, voxel ops, quaternion math | CPU or CUDA PyTorch | Safe core checks. |
| `fill(voxelgrids)` | CPU + SciPy-style binary fill; not differentiable | Move voxelgrid to CPU or skip fill. |
| `farthest_point_sampling` | CUDA + Warp + float32 points | Probe explicitly, not in CPU default. |
| SPC scan/generate/query/interpolate/convolution | CUDA Kaolin extension; CPU `lengths` | Gate behind `--cuda-smoke`. |
| `voxelgrids_to_trianglemeshes` | CUDA marching-cubes extension | Use `voxelgrids_to_cubic_meshes` as CPU fallback. |
| `chamfer_distance`, `sided_distance`, `f_score` | CUDA metrics extension | Use point-to-mesh or voxel IoU alternatives on CPU. |
| `gs_to_voxelgrid`, Gaussian densifier | CUDA + SPC support | Probe only when selected. |

## Packed/padded shape mismatch

Likely causes:
- `shape_per_tensor` includes the final feature dimension.
- `first_idx` was computed from stale or wrong `numel_per_tensor`.
- A padded tensor was consumed without masking valid extents.

Fix:
```python
shape_per_tensor = get_shape_per_tensor(tensor_list)
numel_per_tensor = shape_per_tensor.prod(dim=1) if shape_per_tensor.shape[1] > 1 else shape_per_tensor.reshape(-1)
first_idx = get_first_idx(numel_per_tensor)
```
Then round-trip with `packed_to_list` or `padded_to_list` and compare each item.

## Choosing packed vs padded for variable-size meshes

Use packed when:
- vertex/face counts vary
- downstream ops support packed vertices/faces
- memory should scale with real elements only

Use padded when:
- a dense model/kernel requires `(B, max_N, C)`
- padding masks are acceptable and easy to maintain

Do not mix mesh-local and merged face indices. Packed mesh functions use offsets such as `first_idx_vertices` internally.

## `scan_octrees` fails or returns bad metadata

Checklist:
- `lengths` is CPU, 1D, and int32/int.
- `lengths.sum() == octrees.numel()`.
- `octrees` is contiguous `uint8`.

Fix:
```python
lengths = lengths.to(device='cpu', dtype=torch.int32).contiguous()
assert int(lengths.sum().item()) == int(octrees.numel())
max_level, pyramids, exsum = scan_octrees(octrees.contiguous(), lengths)
```
Keep `octrees` on CUDA for compute; only `lengths` must be CPU.

## Legacy/current `exsum` warning

A legacy `exsum` warning means the tensor has length `num_bytes + batch_size` with one leading zero per octree block. Current layout has length `num_bytes` and is produced by `scan_octrees` by default.

Fix:
1. Regenerate with `scan_octrees(octrees, lengths)` and no `legacy_exsum=True`.
2. If needed, normalize with the compatibility helper.
3. Do not treat the warning as octree corruption.

## `unbatched_query` returns `-1`

Likely causes:
- queried cell is absent
- float coordinates are not normalized to `[-1, 1]`
- integer coordinates are not quantized for the same `level`
- duplicate source points collapsed during quantization

Fix:
- For float queries, inspect min/max and normalize consistently.
- For integer queries, verify values are in `[0, 2^level - 1]`.
- Compare valid `point_hierarchies[pidx[pidx >= 0]]` with expected quantized points.

## Voxel conversion issues

`voxelgrids_to_trianglemeshes` on CPU:
- CUDA-only. Use `voxelgrids_to_cubic_meshes` for CPU-safe cubified meshes.

`fill(voxelgrids)` on CUDA:
- CPU-only. Use `fill(voxelgrids.cpu()).to(original_device)` only when a non-differentiable CPU round-trip is acceptable.

Voxelization output is empty or misaligned:
- pass explicit `origin` and `scale` when comparing batches
- ensure `scale > 0`
- increase `resolution` for thin structures
- remember mesh-to-voxel creates surface occupancy, not a solid fill

Voxel-to-mesh output is a list:
- `voxelgrids_to_cubic_meshes` and `voxelgrids_to_trianglemeshes` return lists of tensors, one per batch item. Pack lists explicitly if downstream code expects packed tensors.

## Mesh metric issues

`point_to_mesh_distance` expects `face_vertices` `(B, F, 3, 3)`, not raw `vertices` and `faces`. Build with `index_vertices_by_faces(vertices, faces)`.

Distance type codes:
- `0`: projection inside face
- `1`, `2`, `3`: nearest to vertex 0, 1, or 2
- `4`, `5`, `6`: nearest to edge 0-1, 1-2, or 2-0

If distances look wrong, check coordinate frame, mesh scale, triangle validity, and whether face vertices match the intended faces.

## Pointcloud metric issues

`sided_distance`, `chamfer_distance`, and `f_score` are CUDA-extension paths. On CPU-only environments:
- use `point_to_mesh_distance` if a mesh target exists
- use voxel IoU after voxelizing both shapes
- use a pure-PyTorch nearest-neighbor fallback only as a local diagnostic and record the deviation

## Farthest point sampling issues

Checklist:
- `points.ndim == 3` and shape `(B, N, 3)`
- CUDA tensor
- dtype `torch.float32`
- `0 <= k <= N`
- Warp is importable

The function returns indices `(B, k)`, not sampled coordinates.

## Gaussian transform issues

Quaternion convention is the usual culprit:
- low-level `kaolin.math.quat` uses xyzw
- `transform_gaussians` defaults to wxyz
- pass `use_xyzw=True` only when input orientations are already xyzw

Also ensure `positions`, `orientations`, `scales`, `transform`, and optional `sh_coeff` share dtype and device.

`transform_shs` supports SH degrees 0 through 3. Higher degree coefficients must be truncated, left unrotated with a caveat, or handled by another implementation.
