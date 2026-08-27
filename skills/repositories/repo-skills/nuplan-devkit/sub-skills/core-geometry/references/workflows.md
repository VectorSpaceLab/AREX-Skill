# Core geometry workflows

Use these recipes as frame-explicit patterns. Replace values only after
recording the source frame, reference point, units, shape, and dtype.

## 1. Build and round-trip a pose

```python
import numpy as np
from nuplan.common.actor_state.state_representation import StateSE2
from nuplan.common.geometry.compute import principal_value
from nuplan.common.geometry.convert import matrix_from_pose, pose_from_matrix

pose = StateSE2(12.0, 3.0, principal_value(3.5))
transform = matrix_from_pose(pose)
assert transform.shape == (3, 3)
round_trip = pose_from_matrix(transform)
assert np.allclose(round_trip.serialize(), pose.serialize(), atol=1e-6)
```

Use a 3x3 planar transform for SE2 composition. Use
`StateSE2.as_matrix_3d()` only when the receiving API explicitly requires a
4x4 projected matrix. `pose_from_matrix()` and `StateSE2.from_matrix()` do not
accept 4x4 matrices.

## 2. Express a point in longitudinal/lateral coordinates

```python
from nuplan.common.actor_state.state_representation import StateSE2
from nuplan.common.geometry.transform import translate_longitudinally_and_laterally

pose = StateSE2(10.0, 4.0, 0.0)
point_pose = translate_longitudinally_and_laterally(pose, lon=2.0, lat=1.0)
assert point_pose.point.x == 12.0
assert point_pose.point.y == 5.0
assert point_pose.heading == pose.heading
```

At heading zero, positive longitudinal is global `+x` and positive lateral is
`+y`. At heading `+pi/2`, forward is global `+y`; never hard-code the axes
when the heading is nonzero.

## 3. Convert global poses to an ego-local frame and back

```python
from nuplan.common.actor_state.state_representation import StateSE2
from nuplan.common.geometry.convert import (
    absolute_to_relative_poses, relative_to_absolute_poses,
)

origin = StateSE2(100.0, 50.0, 1.5707963267948966)
global_poses = [origin, StateSE2(100.0, 52.0, origin.heading)]
local_poses = absolute_to_relative_poses(global_poses)
assert local_poses[0] == StateSE2(0.0, 0.0, 0.0)
restored = relative_to_absolute_poses(origin, local_poses)
assert restored[1] == global_poses[1]
```

The conversion composes transforms; it is not component-wise x/y subtraction.
The input list must be non-empty. For model arrays, use
`numpy_array_to_absolute_pose(origin, poses)` with shape `[N, 3]`. Its
velocity counterpart accepts `[N, 2]`, but it embeds each vector as a
zero-heading pose and can add the origin translation. For pure velocity-frame
rotation, rotate vector components by the origin heading without translating.

## 4. Build a footprint from the correct reference point

```python
from nuplan.common.actor_state.car_footprint import CarFootprint
from nuplan.common.actor_state.oriented_box import OrientedBoxPointType
from nuplan.common.actor_state.state_representation import StateSE2
from nuplan.common.actor_state.vehicle_parameters import get_pacifica_parameters

vehicle = get_pacifica_parameters()
rear_axle_pose = StateSE2(10.0, 4.0, 0.0)
footprint = CarFootprint.build_from_rear_axle(rear_axle_pose, vehicle)
assert footprint.rear_axle == rear_axle_pose
front_left = footprint.get_point_of_interest(OrientedBoxPointType.FRONT_LEFT)
assert front_left.x == rear_axle_pose.x + vehicle.front_length
assert front_left.y == rear_axle_pose.y + vehicle.half_width
```

Use `build_from_center()` for a geometric-center pose and `build_from_cog()`
for a COG pose. Inspect `.rear_axle_to_center_dist`, `.center`, `.rear_axle`,
and `.dimensions` when a box is shifted unexpectedly. Do not pre-shift a pose
and then call a builder that shifts it again.

## 5. Construct an ego state with explicit kinematics

```python
from nuplan.common.actor_state.ego_state import EgoState
from nuplan.common.actor_state.state_representation import StateSE2, StateVector2D, TimePoint
from nuplan.common.actor_state.vehicle_parameters import get_pacifica_parameters

vehicle = get_pacifica_parameters()
ego = EgoState.build_from_rear_axle(
    rear_axle_pose=StateSE2(0.0, 0.0, 0.0),
    rear_axle_velocity_2d=StateVector2D(5.0, 0.0),
    rear_axle_acceleration_2d=StateVector2D(0.2, 0.0),
    tire_steering_angle=0.0,
    time_point=TimePoint(2_000_000),
    vehicle_parameters=vehicle,
)
assert ego.rear_axle == StateSE2(0.0, 0.0, 0.0)
assert ego.time_seconds == 2.0
```

Use `build_from_center()` only when pose, velocity, and acceleration are all
center-referenced. During a turn, the center and rear-axle vectors differ;
inspect both `ego.dynamic_car_state.rear_axle_velocity_2d` and
`ego.dynamic_car_state.center_velocity_2d`.

## 6. Shift rigid-body velocity and acceleration

```python
from nuplan.common.actor_state.dynamic_car_state import (
    get_acceleration_shifted, get_velocity_shifted,
)
from nuplan.common.actor_state.state_representation import StateVector2D

displacement = StateVector2D(2.0, 0.5)
velocity = get_velocity_shifted(displacement, StateVector2D(4.0, 0.0), 0.2)
assert velocity == StateVector2D(3.9, 0.4)
acceleration = get_acceleration_shifted(displacement, StateVector2D(1.0, 0.0), 0.2, 0.1)
```

The displacement is from reference to query point and must share the frame of
the reference vector. Units are meters, m/s or m/s², rad/s, and rad/s². If a
source gives global vectors but the helper is being used with body-frame
vectors, transform both signals into the same frame first.

## 7. Query oriented-box geometry and collision

```python
import math
from nuplan.common.actor_state.oriented_box import (
    Dimension, OrientedBox, OrientedBoxPointType, in_collision,
)
from nuplan.common.actor_state.state_representation import StateSE2

size = Dimension(length=4.0, width=2.0, height=1.5)
box = OrientedBox(StateSE2(0.0, 0.0, 0.0), size.length, size.width, size.height)
front_left = box.corner(OrientedBoxPointType.FRONT_LEFT)
assert math.isclose(front_left.x, 2.0)
assert math.isclose(front_left.y, 1.0)
polygon = box.geometry  # lazy Shapely Polygon
other = OrientedBox(StateSE2(1.0, 0.0, 0.0), 4.0, 2.0, 1.5)
assert in_collision(box, other)
```

At heading zero the box corners are `(front-left, rear-left, rear-right,
front-right)` and front/left are `+x/+y`. `in_collision()` performs exact
polygon intersection only after a center-radius quick check. Shapely is needed
when `.geometry` is first read. For signed point distances use
`longitudinal_distance()` and `lateral_distance()`; the polygon signed helpers
use the packaged Pacifica half-width/half-length and are not generic
arbitrary-vehicle metrics.

## 8. Interpolate time-ordered waypoints

```python
from nuplan.common.actor_state.state_representation import TimePoint
from nuplan.common.geometry.interpolate_state import interpolate_future_waypoints

# `waypoints` must contain compatible Waypoint/EgoState values with
# strictly increasing time_us.
sampled = interpolate_future_waypoints(
    waypoints, horizon_len_s=2.0, interval_s=0.5
)
assert len(sampled) == 5  # current sample plus four future slots
```

Validate `time_us` with `all(a < b for a, b in zip(times, times[1:]))` before
calling. Future helpers append `None` when the requested horizon is not
covered; past helpers pad at the front and require the final current state to
exist. A one-state input is handled by those helpers but is not enough for a
raw `InterpolatedTrajectory`. Treat `None` as an explicit unavailable sample,
not as a zero-valued state.

## 9. Wrap and interpolate angles

```python
import numpy as np
from nuplan.common.geometry.compute import AngularInterpolator, principal_value

wrapped = principal_value(np.array([0.0, np.pi, 2.0 * np.pi]))
assert np.allclose(wrapped, [0.0, -np.pi, 0.0])
interpolator = AngularInterpolator(
    np.array([0.0, 1.0]), np.array([[3.0], [-3.0]])
)
midpoint = interpolator.interpolate(0.5)
```

`AngularInterpolator` unwraps before interpolation. Do not average raw values
across `+/-pi`. Select `[0, 2*pi)` with `principal_value(angle, min_=0.0)`.
Non-finite angles are rejected.

## 10. Convert Torch states and coordinates to local frame

```python
import math
import torch
from nuplan.common.geometry.torch_geometry import (
    coordinates_to_local_frame, global_state_se2_tensor_to_local,
)

anchor = torch.tensor([5.0, 5.0, math.pi / 2], dtype=torch.float32)
states = torch.tensor([[1.0, 1.0, 0.0]], dtype=torch.float32)
coords = torch.tensor([[1.0, 1.0]], dtype=torch.float32)
local_states = global_state_se2_tensor_to_local(states, anchor, precision=torch.float32)
local_coords = coordinates_to_local_frame(coords, anchor, precision=torch.float32)
assert tuple(local_states.shape) == (1, 3)
assert tuple(local_coords.shape) == (1, 2)
```

The functions apply the inverse anchor transform. Use state shape `[N,3]`,
coordinate shape `[N,2]`, and anchor shape `[3]`. For vector-set data use
`coords[M,P,2]` plus a boolean `avails[M,P]`; unavailable entries are zeroed
by `vector_set_coordinates_to_local_frame()`. Pass `precision` deliberately
when input dtypes differ. Check devices before combining outputs with model
tensors.

## 11. Validate Torch derivatives and angle sequences

```python
import torch
from nuplan.common.utils.torch_math import approximate_derivatives_tensor, unwrap

x = torch.arange(0, 5, dtype=torch.float64)
y = torch.stack((x, x * x))
dy_dx = approximate_derivatives_tensor(
    y, x, window_length=3, poly_order=2, deriv_order=1
)
assert tuple(dy_dx.shape) == (2, 5)
angles = torch.tensor([3.04, -3.04], dtype=torch.float64)
assert bool(torch.diff(unwrap(angles)) > 0)
```

Use `y[B,N]`, `x[N]`, strictly increasing `x`, and explicit
`window_length=3`; the implementation's default of 5 is not the supported
filter path. Float64 avoids common convolution/coefficient dtype errors.

## 12. Verification order for a difficult case

1. Run `python scripts/geometry_smoke.py --help` and then the default smoke.
2. Round-trip one `StateSE2` through a matrix before adding a trajectory.
3. Verify rear-axle/center consistency with a known vehicle parameter object.
4. Check `shape`, `dtype`, `device`, and finite values before every Torch call.
5. Validate timestamp monotonicity and treat `None` padding explicitly.
6. If the task now requires a DB, map, scenario, planner, training cache, or
   submission, hand it to the sibling route instead of extending this recipe.
