# Core geometry API reference

Use this reference after routing a task to `core-geometry`. The signatures and
runtime notes below were checked against the nuPlan 1.2.2 package surface with
live imports. Keep the package installed in the active environment; these
references do not require the original source checkout.

## Coordinate, frame, and unit contract

`StateSE2(x, y, heading)` represents a planar pose. `x` and `y` are meters and
`heading` is radians. The heading's forward axis is longitudinal; positive
lateral is the left-hand axis obtained by rotating forward by `+pi/2`.
`StateSE2` does not normalize headings on construction. Use
`principal_value()` when a bounded interval is required.

`Point2D(x, y)` is a position. `StateVector2D(x, y)` is a 2D vector with a
NumPy `float64` array of shape `(2,)` and a `magnitude()` method. Do not infer a
vector's frame from its type: record whether its components are global or body
coordinates.

A standard homogeneous transform is:

```text
[[cos(heading), -sin(heading), x],
 [sin(heading),  cos(heading), y],
 [0,             0,            1]]
```

This is the convention used by `StateSE2.as_matrix()`, `matrix_from_pose()`,
and the SE2 Torch helpers. It maps local column-vector coordinates into the
pose's parent frame. `StateSE2.as_matrix_3d()` embeds the planar transform in a
4x4 matrix; it is not accepted by the 3x3 pose conversion helpers.

The schema-level data convention distinguishes global positions/orientations
from local kinematic signals: ego/object positions are global in the schema,
while ego velocity, acceleration, and angular-rate fields are described in
local coordinates. Preserve the source convention when constructing an
`EgoState`; never assume all fields share one frame.

## State and time representations

```python
from nuplan.common.actor_state.state_representation import (
    Point2D, ProgressStateSE2, StateSE2, StateVector2D,
    TemporalStateSE2, TimeDuration, TimePoint,
)

Point2D(x: float, y: float)
StateSE2(x: float, y: float, heading: float)
StateVector2D(x: float, y: float)
TimePoint(time_us: int)
TimeDuration.from_us(t_us: int)
TimeDuration.from_ms(t_ms: float)
TimeDuration.from_s(t_s: float)
```

`TimePoint.time_us` must be non-negative and `time_s` is `time_us * 1e-6`.
`TimeDuration` stores integer microseconds; `from_ms()` and `from_s()` convert
through `int`, so fractional values are truncated. Use a `TimeDuration` when
adding/subtracting a duration from a `TimePoint`. The direct
`TimeDuration(time_us=...)` constructor intentionally raises unless its private
internal flag is supplied.

`StateSE2` exposes `.x`, `.y`, `.heading`, `.point`, `.array`,
`.as_matrix()`, `.as_matrix_3d()`, `.distance_to(other)`,
`.serialize()`, `StateSE2.deserialize(vector)`, and
`StateSE2.from_matrix(matrix)`. `deserialize()` requires a length-3 vector;
`from_matrix()` requires shape `(3, 3)` and extracts heading with `atan2`.
Equality is approximate (about `1e-3` for x/y and `1e-4` for heading), while
`StateVector2D` equality compares its array exactly.

`ProgressStateSE2(progress, x, y, heading)` iterates as
`[progress, x, y, heading]` and its `deserialize()` requires length 4.
`TemporalStateSE2` adds a `TimePoint` and exposes `time_us` and
`time_seconds`.

## Vehicle parameters, footprint, and ego

```python
from nuplan.common.actor_state.vehicle_parameters import (
    BoxParameters, VehicleParameters, get_pacifica_parameters,
)
from nuplan.common.actor_state.car_footprint import CarFootprint
from nuplan.common.actor_state.ego_state import EgoState

BoxParameters(width: float, length: float)
VehicleParameters(
    width, front_length, rear_length, cog_position_from_rear_axle,
    wheel_base, vehicle_name, vehicle_type, height=None,
)
CarFootprint(center: StateSE2, vehicle_parameters: VehicleParameters)
```

`BoxParameters` uses constructor order `(width, length)` and exposes
`half_width` and `half_length`. `Dimension` below uses `(length, width,
height)`, so do not interchange those two orders.

`VehicleParameters` derives total `length` as
`front_length + rear_length`. It exposes `wheel_base`,
`cog_position_from_rear_axle`, `rear_axle_to_center`,
`length_cog_to_front_axle`, `height`, and identity fields. The packaged
`get_pacifica_parameters()` returns approximately width `2.297 m`, front
length `4.049 m`, rear length `1.127 m`, total length `5.176 m`, wheelbase
`3.089 m`, COG-from-rear-axle `1.67 m`, height `1.777 m`, and
rear-axle-to-center `1.461 m`.

Use the builder that matches the source reference:

```python
CarFootprint.build_from_center(center, vehicle_parameters)
CarFootprint.build_from_rear_axle(rear_axle_pose, vehicle_parameters)
CarFootprint.build_from_cog(cog_pose, vehicle_parameters)
```

The footprint exposes `.vehicle_parameters`, `.oriented_box` (itself),
`.rear_axle_to_center_dist`, cached `.rear_axle`, and
`get_point_of_interest(point_type)`. A rear-axle input is shifted forward by
`vehicle_parameters.rear_axle_to_center` to obtain the box center. Applying
that shift manually before calling `build_from_rear_axle()` applies it twice.

`EgoState` is normally built with one of:

```python
EgoState.build_from_rear_axle(
    rear_axle_pose, rear_axle_velocity_2d, rear_axle_acceleration_2d,
    tire_steering_angle, time_point, vehicle_parameters,
    is_in_auto_mode=True, angular_vel=0.0, angular_accel=0.0,
    tire_steering_rate=0.0,
)
EgoState.build_from_center(
    center, center_velocity_2d, center_acceleration_2d,
    tire_steering_angle, time_point, vehicle_parameters,
    is_in_auto_mode=True, angular_vel=0.0, angular_accel=0.0,
)
```

Important properties are `.car_footprint`, `.center`, `.rear_axle`,
`.dynamic_car_state`, `.tire_steering_angle`, `.time_point`, `.time_us`,
`.time_seconds`, `.is_in_auto_mode`, `.waypoint`, and `.agent`.
`EgoState.deserialize(vector, vehicle)` requires a length-9 sequence ordered as
`time_us, rear_axle_x, rear_axle_y, rear_axle_heading, velocity_x,
velocity_y, acceleration_x, acceleration_y, steering_angle`.

## Dynamic car state

```python
from nuplan.common.actor_state.dynamic_car_state import (
    DynamicCarState, get_acceleration_shifted, get_velocity_shifted,
)

get_velocity_shifted(displacement, ref_velocity, ref_angular_vel)
get_acceleration_shifted(displacement, ref_accel, ref_angular_vel,
                         ref_angular_accel)
DynamicCarState.build_from_rear_axle(
    rear_axle_to_center_dist, rear_axle_velocity_2d,
    rear_axle_acceleration_2d, angular_velocity=0.0,
    angular_acceleration=0.0, tire_steering_rate=0.0,
)
DynamicCarState.build_from_cog(
    wheel_base, rear_axle_to_center_dist, cog_speed, cog_acceleration,
    steering_angle, angular_acceleration=0.0, tire_steering_rate=0.0,
)
```

The rigid-body velocity transfer for displacement `(dx, dy)` is:

```text
v_query = v_reference + (-dy * omega, dx * omega)
```

The acceleration helper adds `displacement * omega**2` and
`displacement * angular_acceleration` to the reference acceleration. Supply
both displacement and vectors in the same frame. `DynamicCarState` exposes
rear-axle and cached center velocity/acceleration vectors, `.speed`,
`.acceleration`, `.angular_velocity`, `.angular_acceleration`, and
`.tire_steering_rate`.

## Boxes, actors, and collections

```python
from nuplan.common.actor_state.oriented_box import (
    Dimension, OrientedBox, OrientedBoxPointType,
    collision_by_radius_check, in_collision,
)
Dimension(length: float, width: float, height: float)
OrientedBox(center: StateSE2, length: float, width: float, height: float)
```

`OrientedBox` exposes dimensions, full and half dimensions, center,
`corner(point_type)`, `all_corners()`, and lazy Shapely `.geometry`.
`all_corners()` order is front-left, rear-left, rear-right, front-right. At
heading zero, front is `+x` and left is `+y`. The enum also contains center,
front/rear bumper, left, and right points.

`in_collision(box1, box2, radius_threshold=None)` first rejects boxes that are
farther apart than an over-approximating center radius, then checks exact
Shapely polygon intersection. A custom nonzero `radius_threshold` changes only
the quick rejection threshold; it is not polygon padding. Use
`collision_by_radius_check()` when only the coarse check is wanted.

`SceneObjectMetadata(timestamp_us, token, track_id, track_token,
category_name=None)` records identity and time. `SceneObject` exposes
`.metadata`, `.token`, `.track_token`, `.tracked_object_type`, `.box`, and
`.center`. `AgentState` adds `.velocity` and optional `.angular_velocity`.
`Agent.from_agent_state()` adds empty temporal prediction fields.
`AgentTemporalState` validates that future prediction probabilities sum to one
and that a provided past trajectory ends at the current timestamp.

`TrackedObjects(tracked_objects=None)` sorts by `TrackedObjectType.value` and
supports iteration, `len()`, `get_tracked_objects_of_type()`,
`get_tracked_objects_of_types()`, `get_agents()`, and `get_static_objects()`.
`Waypoint(time_point, oriented_box, velocity=None)` implements the
interpolatable-state contract and serializes as
`[time_us, x, y, heading, length, width, height, velocity_x, velocity_y]`,
with the velocity entries set to `None` when unavailable.

## NumPy transforms and geometry

```python
from nuplan.common.geometry.convert import (
    absolute_to_relative_poses, matrix_from_pose,
    numpy_array_to_absolute_pose, numpy_array_to_absolute_velocity,
    pose_from_matrix, relative_to_absolute_poses,
    vector_2d_from_magnitude_angle,
)
from nuplan.common.geometry.transform import (
    rotate, rotate_2d, rotate_angle, transform, translate,
    translate_laterally, translate_longitudinally,
    translate_longitudinally_and_laterally,
)
from nuplan.common.geometry.compute import (
    AngularInterpolator, compute_distance, lateral_distance,
    longitudinal_distance, principal_value,
    signed_lateral_distance, signed_longitudinal_distance,
    l2_euclidean_corners_distance, se2_box_distances,
)
```

`absolute_to_relative_poses(absolute_poses)` uses the first absolute pose as
origin; the first output is `[0, 0, 0]`. The inverse helper multiplies an
origin pose by every relative pose. `matrix_from_pose()` and `pose_from_matrix()`
require the 3x3 convention above. Array helpers require shape `(*, 3)` for
poses and `(*, 2)` for velocities and raise an assertion for the wrong feature
width. The velocity helper embeds rows as zero-heading poses and composes them
through the full pose path; with a translated origin, that can include origin
x/y. For a pure vector rotation, rotate components without adding translation.

`translate_longitudinally(pose, distance)` moves along heading and
`translate_laterally(pose, distance)` moves left for positive distance.
`translate_longitudinally_and_laterally()` combines both and preserves heading.
Use `rotate_angle()` when an explicit angle is clearer than constructing a
rotation matrix. `rotate_2d()` requires a `(2, 2)` matrix and multiplies a
row-shaped point array; do not silently substitute a matrix from a different
row/column convention.

`lateral_distance(reference, point)` and `longitudinal_distance(reference,
point)` return signed meters. `principal_value(angle, min_=-pi)` requires finite
input and returns `[min_, min_ + 2*pi)`; with the default, exact `+pi` becomes
`-pi`. `AngularInterpolator` unwraps angular samples before SciPy interpolation
and wraps the result afterward. `l2_euclidean_corners_distance()` compares
corresponding box corners; `se2_box_distances()` can also compare a 180-degree
flipped query when `consider_flipped=True`.

## Interpolation

`interpolate_future_waypoints(waypoints, horizon_len_s, interval_s)` and
`interpolate_past_waypoints(...)` require a non-empty list with strictly
increasing `time_us`. The future result includes the current sample and pads
unavailable future samples with `None`; the past result pads at the beginning
and must retain the final current state. For a one-state input, these helpers
return the available state plus padding rather than inventing states.

`interpolate_agent(agent, horizon_len_s, interval_s)` applies these helpers to
an agent's future predictions and past trajectory. `interpolate_tracks()`
accepts `TrackedObjects` or a list and returns interpolated agents followed by
static objects. A raw `InterpolatedTrajectory` generally needs at least two
compatible `InterpolatableState` instances and rejects out-of-range queries.

## Torch geometry and tensor math

Torch state rows are `[x, y, heading]`; transform matrices are homogeneous
`3x3` tensors:

| Function | Input shape | Output shape |
|---|---:|---:|
| `state_se2_tensor_to_transform_matrix` | `[3]` | `[3, 3]` |
| `state_se2_tensor_to_transform_matrix_batch` | `[N, 3]` | `[N, 3, 3]` |
| `transform_matrix_to_state_se2_tensor` | `[3, 3]` | `[3]` |
| `transform_matrix_to_state_se2_tensor_batch` | `[N, 3, 3]` | `[N, 3]` |
| `global_state_se2_tensor_to_local` | states `[N,3]`, anchor `[3]` | `[N,3]` |
| `coordinates_to_local_frame` | coords `[N,2]`, anchor `[3]` | `[N,2]` |
| `vector_set_coordinates_to_local_frame` | coords `[M,P,2]`, mask `[M,P]` | `[M,P,2]` |

The local-frame functions apply the inverse anchor transform. They reject
wrong feature dimensions and, when `precision` is omitted, reject mixed input
dtypes. `coordinates_to_local_frame()` supports an empty coordinate tensor of
shape `[0, 2]`. The vector-set helper transforms at float64 internally, casts
to `output_precision` (default `torch.float32`), and zeros entries where the
availability mask is false.

The single-state `transform_matrix_to_state_se2_tensor()` constructs a fresh
output tensor without passing through the input device; move it explicitly
before mixing it with CUDA tensors. The batch inverse writes headings into the
third column view of its input matrix, so clone a matrix first if it must be
preserved.

`approximate_derivatives_tensor(y, x, window_length=5, poly_order=2,
deriv_order=1)` requires `y` shape `[B,N]`, `x` shape `[N]`, and strictly
increasing `x`. The current implementation's supported filter path is
`window_length=3`; set that explicitly. Float64 inputs are safest because the
internal Savitzky-Golay coefficients are float64. `unwrap(angles, dim=-1)`
removes jumps larger than pi and is TorchScript-compatible.
