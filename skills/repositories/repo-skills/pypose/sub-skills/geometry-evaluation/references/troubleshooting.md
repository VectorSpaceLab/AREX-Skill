# Troubleshooting and safe checks

## Projection failures

- **Shape assertion:** Keep points at `(..., N, 3)`, pixels at `(..., N, 2)`, depth at
  `(..., N)`, and intrinsics at `(..., 3, 3)`. A single point should still have
  an `N` axis, e.g. `(1, 3)`, not `(3,)` when calling `point2pixel`.
- **Wrong frame:** `pixel2point` always returns camera-frame points. Supplying a
  world-frame point to `point2pixel` without an extrinsic or applying the wrong
  inverse pose creates a consistent but incorrect reprojection. Validate with an
  identity pose and one known translation.
- **Bad depth/intrinsics:** `pixel2point` requires depth length `N` and rejects
  zero focal lengths. It does not reject negative/zero depth; check the sensor
  convention yourself.
- **Residual interpretation:** use `reduction='none'` to inspect signed u/v
  residuals and `'norm'` for pixel distance. The implementation's `'sum'` is a
  signed component sum, not `abs(u)+abs(v)`.
- **Broadcasting:** batch dimensions must be broadcastable across points, pixels,
  intrinsics, and (when present) extrinsics. Make the batch shape explicit before
  debugging numeric output.

## Transform estimation failures

- `svdtf` and `svdstf` need equal correspondence counts and final point dimension
  3. They do not discover correspondences; use `knn` or an external association
  first only when that is part of the experiment.
- Degenerate, collinear, duplicated, or too-small point sets do not constrain a
  unique rotation/scale. Test a non-coplanar or otherwise well-conditioned set
  and compare transformed points.
- `svdtf` returns SE3; `svdstf` returns Sim3. A scale-enabled similarity fit is
  inappropriate when a metric-preserving rigid transform is required.

## Spline failures

- `interval` must be positive and less than one. Output lengths depend on
  `torch.arange(0, 1, interval)`, so use the actual output shape rather than
  assuming exact decimal arithmetic for unusual intervals.
- `chspline` works on Euclidean tensors. `bspline` requires an SE3 LieTensor and
  has a minimum four-pose requirement unless `extrapolate=True` pads repeated
  endpoints. Neither accepts real timestamp vectors.
- Put the sample axis at `-2`; a final axis of 7 is only meaningful to `bspline`
  when the object is an SE3 LieTensor, not an ordinary tensor.
- The plotting examples import matplotlib and pytransform3d and default to
  displaying figures. Do not use them as CI smoke tests; use the bundled helper.

## Filters and neighborhoods

- `voxel_filter`, `nbr_filter`, and radius-enabled `knn_filter` require 2-D input
  because variable output sizes cannot be stacked safely across a batch.
- `pdim` selects only the leading coordinate channels for distance/counting;
  feature channels remain payload and are retained/averaged.
- `nbr_filter`'s `nbr` counts other points, excluding the point itself. A radius
  boundary is included (`<= radius`).
- `knn_filter(..., radius=None)` averages each point with itself and `k` neighbors,
  so `k+1 <= N` is required by the top-k operation. With a radius, the point must
  have at least `k` other in-radius neighbors before this average.
- `random_filter` and random voxel representatives are stochastic. Set
  `torch.manual_seed` in a test and avoid asserting a particular order or sample
  unless the seed and version are fixed.

## Trajectory association and metrics

- Construct poses as one SE3 sequence and timestamps as a 1-D vector. The
  constructor defaults to float64 even if the source pose tensor is float32.
- `matching_time_indices` uses a strict `< max_diff` check and mutates its
  `stamps_2` argument in place for a nonzero offset. Pass a clone when preserving
  timestamps matters.
- Matching is nearest-per-first-stamp, not globally one-to-one. Inspect duplicate
  indices if sensor timestamps can collide.
- `associate_traj` returns `(reference_subset, estimate_subset)`, raises on zero
  matches, and warns below the match ratio `threshold`. In the public wrappers,
  the corresponding spelling is `diff` and `thresh`.
- `compute_error` takes lower-case `mtype='ape'`/`'rpe'`, but the output statistic
  selector is capitalized (`'All'`, `'Mean'`, etc.). Metrics are functions under
  `pp.metric`; there are no APE/RPE classes.
- For RPE, check `associate`, `delta`, `rtol`, `all`, and `rpair`. Frame delta is
  an integer frame gap; distance delta is a translation path length. An empty
  pair list is a configuration error, not a zero score.
- APE/RPE alignment (`align`, `scale`, `origin`) changes the evaluated estimate.
  Report these flags and `nposes` with the score.

## Convergence stopper

`pp.utils.ReduceToBason(steps, patience=5, decreasing=1e-3, tol=1e-5,
verbose=False)` is a generic loop helper (the spelling `Bason` is part of the
public API). Call `continual()` in the loop and `step(loss)` once per iteration.
It stops at the loss tolerance, maximum steps, or patience condition. Call
`reset()` before reuse. The implementation increments patience when
`(last - loss) / loss < decreasing`; guard against zero/negative loss or choose a
loss domain where this expression is meaningful. Batched losses stop only when
all elements satisfy the condition.

## Verification approach

Start with the offline bundled `scripts/geometry_smoke.py` from the `pypose`
skill directory. It covers projection, rigid fitting, splines, point filters,
trajectory metrics, and the stepper without downloads or files. Native test
suites may additionally require external fixtures; do not make them runtime
dependencies. In particular, trajectory evaluation against TUM fixtures needs
explicit network/data approval. The bundled helper intentionally uses synthetic
identity trajectories and does not download data.

## Evidence

- `pypose/function/geometry.py`
- `pypose/function/spline.py`
- `pypose/metric/ape_rpe.py`
- `pypose/utils/stepper.py`
- `tests/function/test_spline.py`
- `tests/function/test_downsample.py`
- `tests/function/test_metric.py`
