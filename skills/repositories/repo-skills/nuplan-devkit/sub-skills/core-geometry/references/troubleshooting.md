# Core geometry troubleshooting

Use the symptom and recovery order below. Preserve the first exception and
report the input frame, reference point, units, shape, dtype, and device.

## 1. Footprint or local-frame offset is wrong

**Symptoms:** the footprint is shifted by approximately the rear-axle-to-center
distance, a corner is mirrored, or local coordinates have the right magnitude
but the wrong sign.

**Likely causes:** a rear-axle pose was passed to a center builder; a center
pose was passed to a rear-axle builder; positive lateral was treated as right;
or a global vector was mixed with a body-frame vector.

**Recovery:** write source and target frames beside every input. At heading zero,
forward is `+x` and positive lateral is `+y`; at `+pi/2`, forward is global
`+y`. Use the matching `CarFootprint.build_from_*` or `EgoState.build_from_*`
constructor. For frame conversion use
`absolute_to_relative_poses()`/`relative_to_absolute_poses()` or the Torch
local-frame helpers, not component-wise subtraction. Check
`footprint.rear_axle`, `footprint.center`, and
`footprint.rear_axle_to_center_dist`.

## 2. Matrix or NumPy shape error

**Symptoms:** `pose_from_matrix()` or `StateSE2.from_matrix()` raises a runtime
error; an array helper raises an assertion; or the returned heading is wrong.

**Recovery:** a planar matrix must be exactly `(3, 3)` and a pose row must be
`[x, y, heading]`. `numpy_array_to_absolute_pose()` requires `(*, 3)`;
`numpy_array_to_absolute_velocity()` requires `(*, 2)`. Confirm the matrix
uses `[[cos, -sin, x], [sin, cos, y], [0, 0, 1]]`. Do not pass a 4x4 matrix to
a 3x3 helper. Matrix conversion extracts `atan2`; use `principal_value()` if a
different display interval is required.

## 3. Non-monotonic interpolation or out-of-range query

**Symptoms:** `interpolate_*_waypoints()` reports that waypoints are not
monotonically increasing, SciPy interpolation fails, or
`InterpolatedTrajectory` rejects an out-of-range query or a one-state input.

**Recovery:** inspect `[state.time_us for state in states]`. Timestamps must be
strictly increasing, not merely non-decreasing, and must be integer
microseconds. Remove or resolve duplicate samples. Use the higher-level
future/past helpers for one-state data and handle their `None` padding. Use a
raw trajectory only with at least two compatible interpolatable states and
query within its time range.

## 4. Heading interpolation jumps by almost 2pi

**Symptoms:** interpolation between headings just across `+/-pi` travels the
long way around, or a tensor yaw sequence contains a sudden branch jump.

**Recovery:** use `AngularInterpolator`, which unwraps before interpolation and
calls `principal_value()` afterward. For Torch sequences call `unwrap(angles,
dim=...)` before derivative work. Explicitly select the interval with
`principal_value(angle, min_=...)`; the default is `[-pi, pi)`, where exact
`+pi` becomes `-pi`. Never average raw angles across a branch cut.

## 5. Torch state or coordinate shape error

**Symptoms:** `ValueError: Improper se2 tensor shape`, `Unexpected coords shape`,
or an availability mismatch error.

**Recovery:** use `[3]` only for one state/anchor, `[N,3]` for a state batch,
`[N,2]` for plain coordinates, `[M,P,2]` for vector sets, `[M,P]` for their
availability mask, `[3,3]` for one transform, and `[N,3,3]` for transform
batches. A bare `[3,3]` is not a batch of states. Avoid accidental `squeeze()`
that removes a batch dimension. Empty coordinates must retain shape `[0,2]`.

## 6. Mixed dtype, device, or stride mismatch

**Symptoms:** a local-frame helper reports mixed datatypes; a later model op
reports CPU/CUDA mismatch; output appears on an unexpected device; or an older
Torch assertion reports matching values but different strides.

**Recovery:** inspect `.dtype`, `.device`, and `.stride()` for every tensor. If
input dtypes intentionally differ, pass `precision` to
`global_state_se2_tensor_to_local()` or `coordinates_to_local_frame()`. The
vector-set helper transforms in float64 and casts to `output_precision` (default
float32). The single-state inverse conversion constructs a fresh output without
preserving the input device; move it explicitly. The batch inverse writes into
the input matrix's third-column view; clone the matrix first if it must remain
unchanged. For value-only assertions on older Torch, compare with
`check_stride=False` or call `.contiguous()` on both tensors.

## 7. Derivative helper fails

**Symptoms:** `approximate_derivatives_tensor()` rejects shapes, reports that
`x` is not monotonically increasing, or convolution fails with a dtype error.

**Recovery:** pass `y` as `[B,N]` and `x` as `[N]` with equal sample count and
strictly increasing values. Set `window_length=3`; although the public default
is 5, the current filter implementation supports only 3. Keep
`poly_order < window_length`. Start with float64 `x` and `y`, then cast the
result if needed. For nonuniform sampling, remember the implementation uses
mean `dx`, so the derivative is an approximation.

## 8. Box collision or corner surprise

**Symptoms:** a radius check says boxes are near but `in_collision()` is false,
or the corner order is unexpected.

**Recovery:** `collision_by_radius_check()` is an over-approximate center
precheck; `in_collision()` then uses exact Shapely polygon intersection. Check
constructor order: `OrientedBox(center, length, width, height)` and
`Dimension(length, width, height)`. `all_corners()` is
front-left, rear-left, rear-right, front-right. A custom radius is a quick
center-distance threshold, not a polygon margin. Confirm dimensions are meters
and finite before construction.

## 9. Serialization or temporal-state validation fails

**Symptoms:** `RuntimeError` or assertion says a vector has the wrong length;
`TimePoint` rejects a timestamp; prediction assignment rejects probabilities;
or a past trajectory does not end at the current state.

**Recovery:** use the exact formats: `StateSE2` length 3, `ProgressStateSE2`
length 4, `Waypoint` length 9, and `EgoState` length 9 plus vehicle
parameters. Timestamps are non-negative microseconds. Future prediction
probabilities must sum to 1 within tolerance; a past trajectory's last
waypoint timestamp must equal the current timestamp. Do not replace missing
waypoints with zero-valued fake states.

## 10. Import or optional dependency failure

**Symptoms:** state imports work but `OrientedBox.geometry`, angular
interpolation, or Torch helpers fail at import or first use.

**Recovery:** verify the active package environment can import NumPy and nuPlan.
Shapely is required for polygon geometry/collision; SciPy is required for
angular and trajectory interpolation; PyTorch is required for Torch geometry
and tensor math. Run `python scripts/geometry_smoke.py --skip-torch` to isolate
the state/NumPy layer, then the default smoke for Torch. This route does not
install packages, fetch data, repair CUDA, or diagnose map/database/planner/
training infrastructure; hand those failures to the owning sibling route.
