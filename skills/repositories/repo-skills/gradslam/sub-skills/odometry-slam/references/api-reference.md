# Odometry and SLAM API reference

This reference records the public contracts needed by the operating skill. It
uses the package's tensor conventions rather than dataset-specific wrappers.

## Input containers

```python
RGBDImages(
    rgb_image, depth_image, intrinsics, poses=None,
    channels_first=False, device=None, pixel_pos=None
)
Pointclouds(points=None, normals=None, colors=None, features=None, device=None)
```

`RGBDImages` expects five-dimensional image tensors. With the default
`channels_first=False`, use `(B,L,H,W,3)` colors and `(B,L,H,W,1)` depths;
with `True`, use `(B,L,3,H,W)` and `(B,L,1,H,W)`. Intrinsics are `(B,1,4,4)`
and poses are `(B,L,4,4)`. `poses=None` is allowed for ICP/GradICP after the
first frame, but `gt` needs poses. `RGBDImages[:, t]` preserves a sequence
length of one. Its `vertex_map`, `normal_map`, `global_vertex_map`, and
`global_normal_map` are computed lazily.

A `Pointclouds` batch accepts either a padded `(B,N,3)` tensor or a list of
`B` `(N_b,3)` tensors. Normals and colors, when supplied, match points; fusion
features are `(N_b,C)` or `(B,N,C)`. Use `points_list`, `normals_list`,
`points_padded`, `normals_padded`, `num_points_per_pointcloud`, and
`device` to inspect a result. Empty `Pointclouds(device=...)` is the initial
map for `ICPSLAM.step` or `PointFusion.step`.

## Odometry providers

### `GroundTruthOdometryProvider`

```python
provider = GroundTruthOdometryProvider()
delta = provider.provide(rgbdimages1, rgbdimages2)
# delta: (B,1,4,4)
```

Both inputs must be `RGBDImages`, each with sequence length one, equal batch
size, and non-`None` poses. The returned relative pose is
`inverse(rgbdimages1.poses) @ rgbdimages2.poses`. It is not a point-cloud
provider and does not estimate motion from colors or depths.

### `ICPOdometryProvider`

```python
provider = ICPOdometryProvider(
    numiters=20, damp=1e-8, dist_thresh=None
)
delta = provider.provide(map_pointclouds, frame_pointclouds)
# delta: (B,1,4,4)
```

Both arguments must be `Pointclouds` with equal batch size. The map must have
per-point normals. Each batch element is passed to point-to-plane ICP with an
identity initial transform. `numiters` controls LM iterations, `damp` adds
normal-equation damping, and `dist_thresh` filters distant nearest-neighbor
matches (`None` retains all matches). The output is the transform used by
`ICPSLAM` to place the live frame relative to its previous pose.

### `GradICPOdometryProvider`

```python
provider = GradICPOdometryProvider(
    numiters=20, damp=1e-8, dist_thresh=None,
    lambda_max=2.0, B=1.0, B2=1.0, nu=200.0
)
delta = provider.provide(map_pointclouds, frame_pointclouds)
# delta: (B,1,4,4)
```

The input and normal requirements match ICP. `lambda_max` sets the upper
smooth damping factor (`lambda_min=1/lambda_max`); `B` controls the damping
sigmoid, while `B2` and `nu` control the smooth residual-step perturbation.
These are solver controls, not metric or pixel units. Keep defaults until a
small fixture is stable, then change one control at a time.

## Low-level odometry utilities

The module also exposes:

```python
solve_linear_system(A, b, damp=1e-8)
gauss_newton_solve(src_pc, tgt_pc, tgt_normals, dist_thresh=None)
point_to_plane_ICP(src_pc, tgt_pc, tgt_normals,
                   initial_transform, numiters=20, damp=1e-8,
                   dist_thresh=None)
point_to_plane_gradICP(src_pc, tgt_pc, tgt_normals,
                      initial_transform, numiters=20, damp=1e-8,
                      dist_thresh=None, lambda_max=2.0,
                      B=1.0, B2=1.0, nu=200.0)
downsample_pointclouds(pointclouds, pc2im_bnhw, ds_ratio)
downsample_rgbdimages(rgbdimages, ds_ratio)
```

For the low-level solvers, source, target, and target normals are
`(1,N,3)` tensors and `initial_transform` is `(4,4)`; solver output is
`(4,4)` plus nearest-neighbor indices `(1,N_filtered)`. `solve_linear_system`
expects `A: (M,6)` and `b: (M,1)` and returns `(6,1)`. The implementation's
validation accesses `initial_transform` before its documented `None` fallback;
pass an explicit identity matrix to avoid relying on that fallback.

`downsample_pointclouds` consumes an integer lookup table `(P,4)` whose columns
are batch, point, image-row, and image-column. `downsample_rgbdimages` requires
sequence length one and returns a `Pointclouds` containing valid sampled
points, normals, and colors. Its ratio is an integer and should be positive.

## `ICPSLAM`

```python
slam = ICPSLAM(
    odom="gradicp", dsratio=4, numiters=20, damp=1e-8,
    dist_thresh=None, lambda_max=2.0, B=1.0, B2=1.0,
    nu=200.0, device=None
)
maps, recovered_poses = slam(frames)
maps, pose = slam.step(map_clouds, live_frame,
                       prev_frame=None, inplace=False)
```

Only `gt`, `icp`, and `gradicp` are valid `odom` values. `device=None` means
CPU. `forward` loops over `L` frames, initializes a missing first-frame pose
for non-`gt` operation, calls `step`, and returns a map batch plus
`recovered_poses: (B,L,4,4)`. A `step` frame and previous frame are intended to
have sequence length one. The first step uses the live-frame pose; subsequent
ICP/GradICP steps use the previous frame and active map correspondences.

For ICP/GradICP localization, `dsratio` is also used to downsample the live
frame and active map. A larger value is faster but can remove all useful
correspondences. `inplace=True` permits updates to the passed map and frame
pose; keep the default when avoiding caller-visible mutation.

## `PointFusion`

```python
slam = PointFusion(
    odom="gradicp", dist_th=0.05, angle_th=20, sigma=0.6,
    dsratio=4, numiters=20, damp=1e-8, dist_thresh=None,
    lambda_max=2.0, B=1.0, B2=1.0, nu=200.0, device=None
)
maps, recovered_poses = slam(frames)
```

`PointFusion` subclasses `ICPSLAM` and changes map update from append-only
aggregation to correspondence-based fusion. `dist_th` is the Euclidean
point-distance gate. `angle_th` is in degrees and is converted internally to a
normal dot-product threshold. The implementation calls this stored quantity
`dot_th`; the constructor argument to use is `angle_th`. `sigma` is the scalar
width of the Gaussian confidence used when merging map points; the package's
published default is `0.6`.

Fusion looks for active map points projected into the one-frame input, keeps
points passing distance and normal tests, selects a unique map point per image
pixel, merges matching point/normal/color values using confidence features,
and appends valid-depth points without a match. Existing non-empty maps
therefore need normals, colors, and features. The first empty map is handled by
fusion's append path. `update_map_aggregate` and `update_map_fusion` are the
underlying map-update functions; the latter receives
`(pointclouds, rgbdimages, dist_th, dot_th, sigma, inplace=False)`.

## Output and gradient checks

Always report `type`, shape, device, dtype, finite status, and
`num_points_per_pointcloud` for a smoke result. A successful pose shape does
not establish geometric accuracy. For GradICP, call `loss = recovered_poses[..., :3,
3].sum()` only on a fixture where the output retains `requires_grad`; then
inspect `loss.backward()` and gradient finiteness. Nearest-neighbor indices and
map correspondence masks are discrete, so do not promise smooth gradients
through every SLAM operation.
