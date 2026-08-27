# Sensor and replay data formats

Use these shapes to write assertions that survive different maps and traffic
loads. Prefer checking types, alignment, and optionality over exact actor
counts.

## `Observation`

A SMARTS observation is a named tuple with common simulation fields and sensor
fields:

| Field | Shape/meaning |
|---|---|
| `dt` | float duration of the last simulation step |
| `step_count`, `steps_completed` | integer simulator/agent counters |
| `elapsed_sim_time` | float simulation time |
| `events` | event flags and collision collection |
| `ego_vehicle_state` | ego id, position, dimensions, heading, speed, steering, yaw rate, road/lane ids, mission, velocities, optional acceleration/jerk and lane position |
| `under_this_agent_control` | bool |
| `neighborhood_vehicle_states` | optional tuple of `VehicleObservation` |
| `waypoint_paths` | optional `list[list[Waypoint]]` |
| `distance_travelled` | float road distance |
| `road_waypoints` | optional `RoadWaypoints`, with `lanes: dict[lane_id, list[list[Waypoint]]]` |
| `via_data` | `Vias`; nearby points and `hit` points |
| `lidar_point_cloud` | optional `(points, hits, rays)` tuple |
| `drivable_area_grid_map`, `occupancy_grid_map` | optional one-channel render records |
| `top_down_rgb` | optional RGB render record |
| `signals` | optional tuple of `SignalObservation` |
| `occlusion_map` | optional visibility render record |
| `custom_renders` | tuple of custom render records |

`VehicleObservation.position` is `(x, y, z)`. `EgoVehicleObservation.linear_velocity`
and `angular_velocity` are global vectors. Acceleration/jerk are optional and
are present only when the accelerometer is enabled.

## Waypoints and lane coordinates

A `Waypoint` has `pos` (three-vector), `heading` (radians), `lane_id`,
`lane_width` (meters), `speed_limit` (m/s), `lane_index`, and `lane_offset`.
A `RefLinePoint` is `(s, t, h)`: offset along the lane, lateral displacement,
and vertical displacement. Convert NumPy values to ordinary lists/scalars only
at an external serialization boundary.

## Grid and image records

`TopDownRGB`, `OccupancyGridMap`, `DrivableAreaGridMap`, `OcclusionRender`, and
`CustomRenderData` each contain:

```text
metadata: GridMapMetadata
  resolution: world units per cell
  width, height: cell counts
  camera_position: (x, y, z)
  camera_heading: radians
 data: NumPy array
```

Expected camera array shapes are `(height, width, 3)` for RGB/custom and
`(height, width, 1)` for drivable/occupancy/occlusion. Verify shape at runtime;
map/build/backend issues can fail before an observation exists.

## Lidar alignment

For `points, hits, rays = observation.lidar_point_cloud`, assert all three
containers have equal length. Each ray is `(origin, direction)` as two NumPy
vectors. A miss is represented by an infinite point and `hits[i]` is false.
The default ray count is derived from the angular sweep and resolution times
the number of laser angles; do not assume the same count after custom params.

## Envision JSONL

The recorder writes one serialized JSON value per line. In normal state frames
the value is an array whose leading elements encode frame time, scenario id,
scenario name, traffic actor layers, signal layers, bubbles, scores/ego ids,
and optional reduction tables. A startup preamble is also array-shaped but
contains scenario directory metadata rather than a numeric frame time. The
server's websocket protocol expects JSON arrays and uses the first item to
distinguish a timestamp frame from a preamble.

The formatter reduces repeated actor/lane ids and appends a lookup mapping plus
a removed-id list when reduction is enabled. Booleans are integers by default,
floats are rounded to the configured decimal count, NumPy arrays become lists,
and non-finite values become string tokens. Do not parse a recording as a flat
CSV or assume every array element has the same actor count.

## Minimal assertions

```python
obs = observations[agent_id]
assert obs.ego_vehicle_state is not None
if obs.lidar_point_cloud is not None:
    points, hits, rays = obs.lidar_point_cloud
    assert len(points) == len(hits) == len(rays)
if obs.top_down_rgb is not None:
    assert obs.top_down_rgb.data.shape[-1] == 3
```

These are format checks only. They do not prove physical sensor correctness,
rendered pixel semantics, or Envision server connectivity.
