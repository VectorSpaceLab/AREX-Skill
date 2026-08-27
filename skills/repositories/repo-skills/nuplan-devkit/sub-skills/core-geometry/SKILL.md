---
name: core-geometry
description: "Use for nuPlan actor-state objects, SE2 poses, vehicle footprints,
  tracked objects, coordinate transforms, geometric distances, interpolation,
  angle wrapping, and tensor geometry; route database/map,
  simulation/evaluation, and training questions to their sibling routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core geometry

Use this route for the reusable state and geometry layer of nuPlan. It covers
`nuplan.common.actor_state`, `nuplan.common.geometry`, and the small tensor-math
helpers that operate on those representations. It is the right entry point when
a request mentions `StateSE2`, `EgoState`, `OrientedBox`, a local frame, a
rear-axle reference, a trajectory waypoint, collision geometry, or a tensor
shape/dtype error.

## Route before acting

- **Use this skill** for `Point2D`, `StateSE2`, `StateVector2D`, `TimePoint`,
  `TimeDuration`, `ProgressStateSE2`, `TemporalStateSE2`, `Waypoint`,
  `EgoState`, `DynamicCarState`, `CarFootprint`, `VehicleParameters`,
  `OrientedBox`, `Agent`, `SceneObject`, `TrackedObjects`, NumPy geometry,
  interpolation, and the Torch SE2/local-frame helpers.
- **Route to `data-and-maps`** for SQLite/ORM records, sensor blobs, dataset
  roots, scenario builders and filters, map databases, semantic map layers, or
  map-backed geometry. This route does not retrieve records or load maps.
- **Route to `simulation-and-evaluation`** for planner interfaces, trajectory
  execution, controllers, simulation runners, metrics, aggregation, or
  nuBoard. This route can explain the state types those systems consume but
  does not run them.
- **Route to `training-and-preprocessing`** for feature/target builders,
  model inputs, cached preprocessing, training configuration, or full training.
  The tensor helpers here are shared primitives, not a training workflow.
- **Route to `submission-and-cli`** for CLI commands, submission containers,
  gRPC/protobuf protocol, or result packaging.

## Operating procedure

1. **Name the frame and reference point.** State whether each pose is global or
   local and whether it is referenced at the box center, rear axle, or COG.
   State whether each vector is expressed in global axes or body axes.
2. **Normalize units.** Positions and box dimensions are meters; velocity is
   m/s; acceleration is m/s²; heading, steering angle, and rotation are
   radians; angular velocity/acceleration are rad/s and rad/s²; timestamps are
   integer microseconds.
3. **Choose a typed representation.** Use `StateSE2` for `[x, y, heading]`,
   `StateVector2D` for `[x, y]` vectors, `TimePoint` for absolute timestamps,
   and `TimeDuration` for differences.
4. **Validate before composing.** Check matrix and tensor shapes, finite
   headings, matching dtypes/devices, and strictly increasing waypoint
   timestamps. Do not use component-wise subtraction when a frame transform is
   required.
5. **Construct from the actual reference.** Use
   `CarFootprint.build_from_rear_axle`, `build_from_center`, or `build_from_cog`
   rather than manually applying an offset and applying it again in a builder.
6. **Check an invariant.** Round-trip a pose/matrix, verify the expected
   front-left corner, restore global poses after a local conversion, or compare
   the expected output shape and dtype for a tensor helper.

## Fast API map

- **State/time:** `StateSE2`, `StateVector2D`, `Point2D`, `TimePoint`, and
  `TimeDuration.from_us/from_ms/from_s`.
- **Transforms:** `matrix_from_pose`, `pose_from_matrix`,
  `absolute_to_relative_poses`, `relative_to_absolute_poses`,
  `translate_longitudinally`, `translate_laterally`, and
  `translate_longitudinally_and_laterally`.
- **Footprints:** `get_pacifica_parameters`, `CarFootprint`,
  `OrientedBox.corner`, `OrientedBox.all_corners`, `OrientedBox.geometry`,
  `in_collision`, and `collision_by_radius_check`.
- **Dynamics:** `DynamicCarState.build_from_rear_axle`,
  `DynamicCarState.build_from_cog`, `get_velocity_shifted`, and
  `get_acceleration_shifted`.
- **Numerical geometry:** `lateral_distance`, `longitudinal_distance`,
  `signed_lateral_distance`, `signed_longitudinal_distance`, `principal_value`,
  `AngularInterpolator`, `l2_euclidean_corners_distance`, and
  `se2_box_distances`.
- **Temporal state:** `interpolate_future_waypoints`,
  `interpolate_past_waypoints`, `interpolate_agent`, and `interpolate_tracks`.
- **Torch geometry:** `state_se2_tensor_to_transform_matrix[_batch]`,
  `transform_matrix_to_state_se2_tensor[_batch]`,
  `global_state_se2_tensor_to_local`, `coordinates_to_local_frame`, and
  `vector_set_coordinates_to_local_frame`.
- **Torch math:** `approximate_derivatives_tensor` and `unwrap`.

Read [references/api-reference.md](references/api-reference.md) for verified
signatures, shape contracts, and representation details. Read
[references/workflows.md](references/workflows.md) for copyable construction and
validation recipes. Read [references/troubleshooting.md](references/troubleshooting.md)
when an assertion, shape error, unexpected offset, angle jump, or dependency
failure occurs.

## Minimal safe check

From this sub-skill directory, inspect the parser and run the local invariant
check:

```bash
python scripts/geometry_smoke.py --help
python scripts/geometry_smoke.py
```

The default check is CPU-only, deterministic, and does not access a dataset,
network, credentials, or writable experiment directory. Use
`--skip-torch` when only the NumPy/state layer is installed. Use
`--device cuda` only when CUDA availability and the compatible Torch runtime
have already been established. It fails if CUDA is unavailable and reports the
known package-level CPU-constant limitation instead of claiming CUDA coverage
for the Torch math helpers.

## Completion and handoff

Before handing a state or geometry result to another route, report the chosen
frame, reference point, units, timestamp convention, shape, dtype/device, and
any `None` padding introduced by interpolation. Hand off as soon as the task
requires database/map retrieval, scenario selection, planner execution,
metric/evaluation orchestration, model preprocessing, training, or submission
packaging.
