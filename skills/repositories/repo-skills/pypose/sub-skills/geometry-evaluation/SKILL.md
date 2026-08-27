---
name: geometry-evaluation
description: "Use PyPose's projection and homogeneous-coordinate geometry,
  reprojection residuals, point-cloud transform estimation and filters,
  Euclidean/SE3 splines, trajectory timestamp association, APE/RPE metrics,
  testing comparison, and ReduceToBason convergence utility; choose the API from
  shape, frame, time, and threshold contracts and validate with deterministic
  smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Geometry and evaluation

Use this sub-skill when a Researcher needs camera-coordinate geometry, point-cloud
preprocessing/alignment, spline interpolation, trajectory association or error
statistics, comparison assertions, or a small convergence stopper. This skill is
for operating PyPose's existing APIs, not for re-deriving LieTensor representation
fundamentals.

## Scope boundary

Included:

- Cartesian/homogeneous conversion and camera projection/back-projection:
  `cart2homo`, `homo2cart`, `point2pixel`, `pixel2point`, `reprojerr`.
- Rigid and similarity point-set estimation: `svdtf` and `svdstf`.
- Generic nearest-neighbor and point-cloud reduction/filtering: `knn`,
  `random_filter`, `voxel_filter`, `nbr_filter`, `knn_filter`.
- Euclidean cubic Hermite and SE3 B-spline interpolation: `chspline`, `bspline`.
- Trajectory containers, timestamp matching, alignment, frame/distance pair
  selection, and APE/RPE: `StampedSE3`, `matching_time_indices`,
  `associate_traj`, `compute_error`, `pairs_by_frames`, `pairs_by_dist`,
  `pair_id`, `metric.ape`, and `metric.rpe`.
- `pypose.testing.assert_close` and `pypose.utils.ReduceToBason`.

Excluded:

- SE3/SO3/Sim3 representation, composition, logarithms, exponentials, and other
  fundamentals: use `lie-tensor`.
- ICP, EPnP, robotics pipelines, and robotics modules: use `robotics-modules`.
- Optimizers, schedulers, and optimization loops: use `optimization`.

Read the focused references before writing a pipeline:

1. [geometry-api.md](references/geometry-api.md)
2. [splines-and-downsampling.md](references/splines-and-downsampling.md)
3. [trajectory-metrics.md](references/trajectory-metrics.md)
4. [troubleshooting.md](references/troubleshooting.md)

Run the bundled offline check from any directory with:

From the `pypose` skill directory, run:

```bash
python sub-skills/geometry-evaluation/scripts/geometry_smoke.py
```

The helper can also be invoked by absolute path from any working directory.

Use `python sub-skills/geometry-evaluation/scripts/geometry_smoke.py --help`
from the skill directory to see options. The helper sets no
random global state outside its own deterministic checks, does not access the
network, and does not create plots or files.

## Operating procedure

1. Normalize the data contract before calling an API:
   - point coordinates are `(..., N, 3)` and pixels are `(..., N, 2)`;
   - an intrinsic matrix is `(..., 3, 3)` with nonzero `fx=K[...,0,0]` and
     `fy=K[...,1,1]`;
   - poses are `SE3` LieTensors with a final size of 7 when an extrinsic is
     supplied; and
   - a trajectory is one unbatched sequence of SE3 poses plus a one-dimensional,
     nondecreasing timestamp vector.
2. Make frame and direction conventions explicit. `point2pixel` expects camera
   points if `extrinsics=None`; with `extrinsics`, points are world-frame and
   the supplied pose acts before projection. `pixel2point` returns camera-frame
   points whose z coordinate is the supplied sensor-plane depth. It does not
   invert an extrinsic automatically.
3. Use lower-case public function names exactly as exported (`point2pixel`,
   `reprojerr`, `svdtf`, `metric.ape`, `metric.rpe`). Metrics are functions and
   `StampedSE3` is an internal helper class in `pypose.metric.ape_rpe`; do not
   search for or instantiate `APE`/`RPE` classes.
4. Validate shapes and dtype/device with a small synthetic case. For a round trip,
   project positive-depth camera points then back-project using the original z.
   For transforms, apply a known rigid/similarity transform and compare estimated
   matrix action, not only raw quaternion storage.
5. For trajectories, associate timestamps before evaluating. Inspect match count,
   `max_diff`/`diff`, `offset_2`/`offset`, and `threshold`/`thresh`; a nonzero
   association warning means the score may be unreliable. Decide whether APE
   alignment, scale correction, origin alignment, and RPE pair unit are wanted.
6. Record the exact options used and the result statistic (`All`, `Mean`, `RMSE`,
   etc.). Use `pp.testing.assert_close` for tensors or LieTensors rather than
   comparing quaternion coordinates directly.

## Minimal examples

```python
import torch
import pypose as pp

K = torch.tensor([[4., 0., 2.], [0., 4., 1.], [0., 0., 1.]])
xyz = torch.tensor([[0.5, -0.25, 2.], [1., 1., 4.]])
uv = pp.point2pixel(xyz, K)
xyz_again = pp.pixel2point(uv, xyz[:, 2], K)
pp.testing.assert_close(xyz_again, xyz)

# A metric call uses functions, not metric classes.
t = torch.arange(4, dtype=torch.float64)
poses = pp.SE3([[0., 0., 0., 0., 0., 0., 1.],
                [1., 0., 0., 0., 0., 0., 1.],
                [2., 0., 0., 0., 0., 0., 1.],
                [3., 0., 0., 0., 0., 0., 1.]])
score = pp.metric.ape(t, poses, t, poses, etype='translation', otype='Mean')
assert torch.equal(score, torch.zeros_like(score))
```

Keep any backend-specific failures, unsupported degenerate cases, timestamp
collisions, and unresolved coordinate assumptions explicit in the handoff rather
than silently changing conventions.
