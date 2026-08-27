# SPC Workflows and Conventions

Structured Point Clouds (SPCs) are sparse octree hierarchies for sparse voxel occupancy, multiresolution point queries, trilinear interpolation over sparse cells, and SPC convolution. Most compute paths require a CUDA-capable Kaolin extension.

## Tensor glossary

- `octrees`: packed `torch.uint8` tensor. Each byte stores occupancy bits for up to 8 children in Morton order.
- `lengths`: CPU int tensor `(B,)`; number of octree bytes per batch item. `lengths.sum() == octrees.numel()`.
- `pyramids`: int tensor `(B, 2, max_level + 2)` from `scan_octrees`. Row 0 is counts per level; row 1 is start offsets.
- `exsum`: inclusive bit-count prefix sum. Current layout length is `octrees.numel()`. Legacy layout length is `octrees.numel() + B` and has one leading zero per octree block.
- `point_hierarchies`: packed short tensor `(num_points_all_levels, 3)`.
- `Spc`: convenience wrapper around these fields with lazy `pyramids`, `exsum`, and `point_hierarchies` properties.

## Build one SPC from normalized points

Input point cloud should be unbatched float coordinates `(N, 3)` normalized to `[-1, 1]`.

```python
qpts = quantize_points(points, level)                 # short, [0, 2^level - 1]
octree = unbatched_points_to_octree(qpts, level)      # uint8, usually CUDA
lengths = torch.tensor([len(octree)], dtype=torch.int32)  # CPU
max_level, pyramids, exsum = scan_octrees(octree, lengths)
point_hierarchies = generate_points(octree, pyramids, exsum)
```

Rules:
- Do not set `sorted=True` unless quantized points are unique and Morton-sorted.
- `quantize_points` clips out-of-range float coordinates.
- `unbatched_pointcloud_to_spc` merges duplicate quantized cells; optional features in the same cell are averaged.
- Keep `lengths` on CPU for `scan_octrees`; keep `octrees` on the compute device.

## Build a batched SPC collection

1. Generate each unbatched octree on the compute device.
2. Pack octrees with `list_to_packed([octree.reshape(-1, 1), ...])` or use a `Spc` helper.
3. Convert packed octrees back to 1D `uint8`; keep `lengths` as a CPU int tensor.
4. Run `scan_octrees(packed_octrees, lengths)` once and cache `pyramids`/`exsum`.
5. Generate `point_hierarchies` once if multiple downstream queries or convolutions need it.

## Query points

Use `unbatched_query(octree, exsum, query_coords, level, with_parents=False)`.

- Float query coordinates are normalized `[-1, 1]`.
- Integer query coordinates are grid coordinates at the given level.
- Return shape is `(num_query,)`; value `-1` means absent.
- With `with_parents=True`, return shape is `(num_query, level + 1)`.

If a query unexpectedly returns `-1`, verify coordinate normalization, level, and whether the cell exists after quantization.

## Dual octree and trilinear interpolation

Use this path when features live on cell corners.

```python
pyramid = pyramids[0]
point_hierarchy_dual, pyramid_dual = unbatched_make_dual(point_hierarchies, pyramid)
trinkets, parents = unbatched_make_trinkets(point_hierarchies, pyramid, point_hierarchy_dual, pyramid_dual)
pidx = unbatched_query(octree, exsum, query_coords, level).int()
values = unbatched_interpolate_trilinear(
    coords=query_coords[:, None, :],
    pidx=pidx,
    point_hierarchy=point_hierarchies,
    trinkets=trinkets,
    feats=corner_features,
    level=level,
)
```

Shape rules:
- `coords`: `(num_coords, num_samples, 3)`.
- `pidx`: `(num_coords,)` from `unbatched_query`.
- `trinkets`: `(num_points, 8)` mapping primary cells to dual/corner points.
- `feats`: `(num_dual_points_at_level, feature_dim)`.
- `coords_to_trilinear_coeffs(coords, points, level)` returns 8 coefficients per coordinate.

## Dense feature grids to SPC and back

`feature_grids_to_spc(feature_grids, masks=None)`:
- input shape `(B, C, X, Y, Z)`
- optional masks `(B, X, Y, Z)`
- spatial dimensions are padded to a power of two internally
- output `(octrees, lengths, coalescent_features)`

`to_dense(point_hierarchies, pyramids, input, level=-1)` scatters packed features into a dense grid at a level. Negative `level` counts from the deepest available level.

## Mesh, pointcloud, and Gaussian sources

Mesh to SPC:
1. Build `face_vertices = index_vertices_by_faces(vertices, faces)`.
2. Select one mesh: `face_vertices_i` shape `(F, 3, 3)`.
3. Ensure geometry is in the `[-1, 1]` coordinate range.
4. Use `unbatched_mesh_to_spc(face_vertices_i, level)` on CUDA.

Pointcloud to `Spc`:
```python
spc_obj = unbatched_pointcloud_to_spc(pointcloud, level, features=features)
```

Gaussian occupancy:
- `gs_to_voxelgrid` returns quantized voxel coordinates and opacity values from Gaussian means/scales/rotations/opacities.
- `sample_points_in_volume` uses a heavier voxelize-and-carve process and should not be a default smoke check.

## SPC convolution

Functional path:

```python
out_features, out_level = conv3d(
    octrees, point_hierarchies, level, pyramids, exsum,
    input=features_at_level,
    weight=weight,
    kernel_vectors=kernel_vectors,
    jump=jump,
    bias=bias,
)
```

Rules:
- `features_at_level`: `(num_points_at_level, in_channels)`.
- `kernel_vectors`: short tensor `(K, 3)`.
- `weight`: `(K, in_channels, out_channels)`.
- `jump=0` keeps level; positive `jump` downsamples for `conv3d` and upsamples for `conv_transpose3d`.
- Current `exsum` is preferred; legacy `exsum` is accepted with a warning.

## Current versus legacy `exsum`

Current layout:
- length `num_bytes`
- inclusive sum through each octree byte
- produced by default from `scan_octrees(octrees, lengths)`

Legacy layout:
- length `num_bytes + batch_size`
- each octree block starts with `0`
- produced only by old code or `scan_octrees(..., legacy_exsum=True)`
- accepted by consumers with `DeprecationWarning`

Repair path:
1. Regenerate `max_level, pyramids, exsum = scan_octrees(octrees, lengths)` without `legacy_exsum=True`.
2. If regeneration is impossible, normalize legacy `exsum` with the compatibility helper.
3. Treat the warning as a layout migration issue, not octree corruption.

## Minimal CUDA/SPC smoke

A safe smoke should:
1. Create a few normalized points on CUDA.
2. Quantize and convert to one octree.
3. Create CPU `lengths = torch.tensor([len(octree)], dtype=torch.int32)`.
4. Run `scan_octrees`, `generate_points`, and `unbatched_query`.
5. Optionally build dual/trinkets and run one interpolation.

The bundled [tensor_ops_smoke.py](../scripts/tensor_ops_smoke.py) runs this when called with `--cuda-smoke`.
