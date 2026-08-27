# Sensor configuration and observation reference

This reference is the operating contract for `AgentInterface` sensor fields.
Use it with a normal SMARTS environment created by the sibling
`simulation-environments` route; this document does not define reset, step, or
close behavior.

## Configuration fields

| Interface field | Config type | Output when enabled | Important options |
|---|---|---|---|
| `waypoint_paths` | `Waypoints` | list of waypoint paths | `lookahead` count; default 32 |
| `road_waypoints` | `RoadWaypoints` | `RoadWaypoints.lanes` mapping | `horizon` meters; default 20 |
| `neighborhood_vehicle_states` | `NeighborhoodVehicles` | tuple of `VehicleObservation` | `radius=None` means unlimited |
| `lidar_point_cloud` | `Lidar` | points, hit flags, rays | `sensor_params`, normally `BasicLidar` |
| `drivable_area_grid_map` | `DrivableAreaGridMap` | rendered one-channel map | width, height, meters/cell |
| `occupancy_grid_map` | `OGM` | rendered one-channel occupancy map | width, height, meters/cell |
| `top_down_rgb` | `RGB` | rendered RGB image | width, height, meters/cell |
| `occlusion_map` | `OcclusionMap` | rendered visibility map | same dimensions as OGM; optional surface noise |
| `accelerometer` | `Accelerometer` | ego acceleration and jerk | no shape options |
| `lane_positions` | `LanePositions` | ego lane `RefLinePoint` | `(s, t, h)` coordinates |
| `signals` | `Signals` | tuple of signal observations | lookahead in meters |
| `custom_renders` | tuple of `CustomRender` | tuple of shader image outputs | unique names/dependency variables |

Passing `True` creates the default dataclass; passing a config instance gives
explicit values; any other false value disables that sensor. Deprecated aliases
such as `rgb`, `ogm`, `lidar`, and `waypoints` should not be used in new code.
The `requires_rendering` property is the quick check for the main camera paths;
occlusion is implicitly rendered because its constructor requires OGM.

## Non-rendered sensors

### Waypoints and road waypoints

`waypoint_paths` is a `List[List[Waypoint]]`. Each `Waypoint` contains:

- `pos`: three-dimensional NumPy position on the lane center;
- `heading`: lane heading in radians;
- `lane_id`, `lane_index`, `lane_width`, `speed_limit`, and `lane_offset`.

The paths follow the current plan/route and are evenly spaced according to the
scenario map. `road_waypoints` is a `RoadWaypoints` named tuple whose `lanes`
field maps each lane id to one or more paths. It covers lanes on the current
road, including oncoming/parallel lanes, and is not restricted to the current
mission. An empty mapping can occur when no nearest lane is available.

### Neighborhood vehicles

`neighborhood_vehicle_states` is a tuple of `VehicleObservation` records. Each
record carries id, `(x, y, z)` position, bounding box, heading, speed, nearest
road/lane ids and indexes, optional lane position, and an interest flag. Use a
finite `radius` to bound work and make the policy's sensing range explicit.
Do not infer that the ego vehicle is included.

### Lidar

`lidar_point_cloud` is a three-part tuple:

```text
(points: list[np.ndarray], hits: list[bool],
 rays: list[(origin: np.ndarray, direction: np.ndarray)])
```

A missed point is `[inf, inf, inf]`; `hits` aligns one-for-one with points and
rays. The default `BasicLidar` has 50 vertical laser angles, a 0–2π sweep,
angle resolution 1, maximum distance 20 m, and Gaussian parameters
`noise_mu=0`, `noise_sigma=0.078`. `VelodyneHDL32E` has 24 laser angles,
resolution 0.1728, and maximum distance 100 m. The point-cloud calculation
uses the simulator's Bullet ray-test client, so a lidar signature/import smoke
is not a physical scene test.

### Motion, lane, and signal observations

`EgoVehicleObservation` always exposes velocity and angular velocity. With the
accelerometer enabled, its linear/angular acceleration and linear/angular jerk
are three-component values; otherwise those four fields are `None`. The
accelerometer keeps a short velocity history, returns zero vectors until enough
samples exist, and returns zero acceleration/jerk when `dt` is zero.

`lane_positions` yields `RefLinePoint(s, t, h)`: longitudinal offset along the
lane, lateral displacement from lane center, and currently unsupported/usually
zero vertical displacement. It requires a nearest lane.

`signals` is a tuple of `SignalObservation` records containing signal-light
state, stop point, controlled lane ids (possibly empty), and optional
`last_changed` simulation time. The sensor searches the current lane and route
ahead up to its configured lookahead. An absent lane or no upcoming signal
returns an empty tuple.

`via_data` is present in the base `Observation` even though it is not an
interface toggle described here. It reports nearby mission via points and
whether a point was hit on the previous step; do not assume it is a camera
output.

## Interface validation pattern

1. Build a low-dimensional interface with only waypoint/neighborhood/lane
   fields and run the CPU path first.
2. Assert the expected fields are non-`None` and inspect lengths rather than
   hard-coding a fixed number of actors or paths.
3. Add lidar separately; confirm `len(points) == len(hits) == len(rays)`.
4. Add rendered sensors only after the rendering helper succeeds.
5. Match camera dimensions between OGM and occlusion; SMARTS rejects mismatched
   width or height during `AgentInterface` construction.
