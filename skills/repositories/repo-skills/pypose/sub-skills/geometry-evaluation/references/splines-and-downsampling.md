# Splines and downsampling

## `chspline`: Euclidean cubic Hermite interpolation

`pp.chspline(points, interval=0.1)` accepts a tensor with shape
`[..., point_num, dim]`. Adjacent input waypoints are one unit apart in the
spline's normalized time. If `interval=0.1`, each segment is sampled at
`[0, 0.1, ..., 0.9]` and the shared endpoint is emitted once; for the usual
intervals the output has `ceil(1 / interval) * (point_num - 1) + 1` samples.
The implementation computes endpoint tangents from neighboring finite
 differences, uses the cubic Hermite basis, and preserves leading batch
 dimensions.

The input waypoint samples are recoverable at the corresponding stride. For
example, with `interval=0.2`, select output indices
`5 * torch.arange(point_num)`. Treat `interval` as a positive fractional
sampling step strictly below 1; validate this at the call site because invalid
values can result in assertion failures or unusable timelines. The function is
for Euclidean values (positions, vectors, or features), not SE3 composition.

## `bspline`: SE3 LieTensor interpolation

`pp.bspline(data, interval=0.1, extrapolate=False)` currently supports SE3
LieTensors with shape `[..., poses_num, 7]`, including leading batch dimensions.
It interpolates on relative SE3 increments using the cubic B-spline construction
from HyperSLAM. Four consecutive poses are needed when `extrapolate=False`; the
normal output size is:

```text
ceil(1 / interval) * (poses_num - 3) + 1
```

For `extrapolate=True`, two copies of the first and last pose are padded around
the input, so the returned trajectory spans the original endpoints and has
`ceil(1 / interval) * (poses_num + 1) + 1` samples for common intervals. Verify
shape empirically for non-reciprocal intervals because the implementation builds
its timeline with `torch.arange(0, 1, interval)`. With extrapolation enabled,
compare first and last output poses to the original first and last poses using
`pp.testing.assert_close`; this is an SE3 comparison, not a raw 7-vector
comparison.

`interval` is a normalized step between adjacent input poses, not a timestamp in
seconds. `bspline` does not accept a timestamp vector and does not perform
association. If source poses have irregular real timestamps, resample or
normalize them deliberately before using this API and retain the mapping.

## Shape and failure checklist

- Keep the pose/sample axis at `-2` and representation/channel axis at `-1`.
- Use a floating dtype; the spline constructs floating timelines on the input
  device and dtype.
- `chspline` requires at least two points for meaningful segment interpolation.
- `bspline` requires an SE3 LieTensor and at least four poses without
  extrapolation. With extrapolation, short sequences are padded by repeated
  endpoints, but this does not create missing motion information.
- Interval must be less than one and should be positive. Use a fixed interval in
  tests and assert output shape plus waypoint/end-point recovery.
- Spline routines interpolate values/poses; they do not enforce collision,
  dynamic, or sensor constraints.

The repository examples `examples/module/spline/chspline.py` and
`examples/module/spline/bspline.py` visualize these results, but the examples
need plotting dependencies and default to showing figures. For automated use,
copy only their data construction idea and use the no-plot smoke helper.

## Downsampling patterns

Use the filter that matches the contract:

1. Need exactly `num` random samples from batched points: `random_filter`.
2. Need one representative per occupied spatial cell: `voxel_filter`; use the
   centroid for deterministic reduction or `random=True` only when stochastic
   representatives are intended.
3. Need to remove isolated outliers based on a count threshold: `nbr_filter`,
   optionally with `return_mask=True` so downstream code can retain alignment.
4. Need a local smoothing/averaging operation: `knn_filter`; omit `radius` for
   batch-preserving smoothing, or provide `radius` for 2-D outlier gating plus
   local averaging.
5. Need neighbor indices/distances without modifying points: `knn`.

For `pdim < D`, only the first `pdim` channels define spatial distance or voxel
membership; extra channels are payload. Do not use feature channels as spatial
coordinates by accident. Variable-count filters (`voxel_filter`, `nbr_filter`,
and radius-enabled `knn_filter`) are not batch-safe because each cloud may have a
different number of retained points.

## Evidence

- `pypose/function/spline.py`
- `pypose/function/geometry.py`
- `tests/function/test_spline.py`
- `tests/function/test_downsample.py`
- `examples/module/spline/chspline.py`
- `examples/module/spline/bspline.py`
