# Sensor API and scan contracts

## Attach sensors in YAML

Attach a list under an object (normally a robot):

```yaml
robot:
  - kinematics: {name: diff}
    shape: {name: circle, radius: 0.2}
    state: [1.0, 1.0, 0.0]
    sensors:
      - name: lidar2d
        range_min: 0.0
        range_max: 5.0
        angle_range: 3.141592653589793
        number: 64
        scan_time: 0.1
        noise: false
        std: 0.2
        angle_std: 0.02
        offset: [0.1, 0.0, 0.0]
        plot: {alpha: 0.3, color: r}
```

`name` and `type` are accepted by `SensorFactory`; an omitted type defaults
to `lidar2d`. The currently registered names are exactly `lidar2d` and
`fmcw_lidar2d`. Unknown names raise `NotImplementedError` during construction.
The constructor signatures are:

```text
Lidar2D(state=None, obj_id=0, range_min=0, range_max=10,
        angle_range=pi, number=100, scan_time=0.1, noise=False,
        std=0.2, angle_std=0.02, offset=None, alpha=0.3,
        has_velocity=False, **kwargs)
FMCWLidar2D(state=None, obj_id=0, motion_compensate=False,
            velocity_noise_std=0.0, **kwargs)
SensorFactory.create_sensor(state, obj_id, **kwargs)
```

FMCW inherits all standard geometry/range fields. Its plot-only Doppler options
are accepted inside `plot:` (flat keys remain a backward-compatible fallback):
`velocity_color`, `velocity_color_max`, `velocity_linewidth`,
`no_hit_linewidth`, `no_hit_alpha`, `show_velocity_markers`,
`velocity_marker_size`, `velocity_marker_edge_color`,
`velocity_marker_edge_width`, `zero_velocity_color`,
`positive_velocity_color`, `negative_velocity_color`, and `no_hit_color`.
Plotting options do not alter measurements.

## Selecting and reading a scan

`EnvBase.get_lidar_scan(id: int = 0)` selects a **robot list index** and returns
that object's `obj.lidar.get_scan()`. It does not take a sensor index. Object
helpers are `obj.get_lidar_scan()`, `obj.get_lidar_points()`, and
`obj.get_lidar_offset()`. During object construction, `obj.lidar` is the first
sensor whose type is either LiDAR class. Therefore, when standard and FMCW
sensors coexist, inspect `obj.sensors` and call the desired instance directly:

```python
robot = env.robot_list[0]
for sensor in robot.sensors:
    print(sensor.sensor_type, sensor.get_scan().keys())
standard = next(s for s in robot.sensors if s.sensor_type == "lidar2d")
fmcw = next(s for s in robot.sensors if s.sensor_type == "fmcw_lidar2d")
standard_scan = standard.get_scan()
fmcw_scan = fmcw.get_scan()
```

### Common metadata and arrays

Both scan dictionaries contain scalar metadata:

- `angle_min`, `angle_max`: local scan endpoints, `±angle_range/2` after the
  package's angle normalization.
- `angle_increment`: source value `angle_range / number` (do not infer
  `angle_range / (number - 1)`). The actual `angle_list` used by the sensor is
  `number` linearly spaced values including both endpoints.
- There is no `angles` array key in the returned dictionary. Use the scalar
  metadata to reconstruct the local beam angles, or inspect the sensor's
  `angle_list` when you have the sensor object.
- `time_increment`: `(angle_range / (2*pi)) * scan_time / number`.
- `scan_time`, `range_min`, `range_max`, `intensities` (`None`).
- `ranges`: a NumPy array of length `number`; a no-hit standard beam remains at
  `range_max`.

The standard `lidar2d` dictionary additionally contains:

- `velocity`: a `(2, number)` Cartesian XY velocity array. It is zero-filled
  unless `has_velocity: true`; detected dynamic-object velocity may then be
  assigned to a hit beam. It does **not** contain `valid` or
  `radial_velocity`.

The `fmcw_lidar2d` dictionary removes `velocity` and adds:

- `radial_velocity`: a float array of length `number`, zero for invalid beams.
- `valid`: a boolean array of length `number`. It is true only when a hit,
  after optional range noise, lies within `[range_min, range_max]`.

A no-hit FMCW beam has `valid=False`, `ranges=range_max`, and
`radial_velocity=0`. Consumers should use `valid`, not merely a range comparison,
when processing FMCW returns. `get_points()` is inherited and returns a local
2-by-N point cloud for ranges strictly below `range_max - 0.02`, or `None` when
there are no such ranges. It does not return an angles array or validity column,
and it does not transform points to world coordinates; if FMCW validity matters,
filter the ranges with `scan["valid"]` yourself before converting downstream.

## Geometry, offsets, noise, and motion

`offset` is `[x, y, theta]` relative to the parent object's state. The sensor's
world origin is the transformed offset; `get_offset()` returns the configured
offset as a list. Beam angles are local to that sensor orientation. The scan
range is the first intersection with valid, obstructing scene geometry; the
sensor ignores itself, invalid geometry, and objects marked `unobstructed`.
Map-shaped obstacles use their line segments.

`noise: true` adds Gaussian range noise with standard deviation `std`. The
constructor stores `angle_std`, and documentation exposes it, but the 2.10.2
scan implementation does not apply angle noise to `angle_list` or the returned
metadata; do not promise angular perturbation. Seed reproducible stochastic
behavior through the package RNG (`irsim.util.random.set_seed`) before stepping.
FMCW additionally adds Gaussian radial-velocity noise with
`velocity_noise_std`. A noisy FMCW range outside the configured bounds is
invalidated and its range/velocity are reset to the no-hit convention.

For FMCW, the target velocity is projected onto the world beam direction:

- `motion_compensate: false` (default): target XY velocity minus the parent
  object's XY velocity, i.e. sensor-relative radial velocity.
- `motion_compensate: true`: target XY velocity only, i.e. ego-motion removed.

Purely tangential target motion has zero radial component. A parentless sensor
uses zero ego velocity. Sign is the dot product with the outward beam direction;
use the package result rather than assuming a particular approach/recede sign.

## Update order and manual state changes

A normal environment step uses one consistent scene snapshot:

1. Internal mode advances all objects with sensor updates suppressed.
2. The geometry tree is rebuilt.
3. All object sensors are stepped with updated states.
4. `World.step(objects)` updates fog from those readings and status handling
   continues.

External mode first refreshes all objects, rebuilds the geometry tree, then
steps sensors; `env.step()` must receive no action. When manually mutating an
object, `set_state()` updates that object's geometry but not the environment
spatial tree or all sensor readings. Prefer `env.refresh()` after setting state
and velocity; it refreshes geometries, rebuilds the tree, updates sensors, and
rechecks status. `obj.sensor_step()` is useful only when the tree is already
consistent. `ObjectBase.step(..., sensor_step=False)` suppresses its immediate
sensor tick, but the environment performs its synchronized sensor phase.

```python
robot.set_state([2.0, 2.0, 0.0])
robot.set_velocity([0.0, 0.0])
env.refresh()
scan = env.get_lidar_scan(0)
```

Do not use scan results captured before moving objects as if they represented
the new state. Reset/reload also rebuild the sensor state; close environments
through the simulation route.

## FOV and fog relationship

An object's `fov` is a full angle in radians and `fov_radius` is its maximum
object-detection distance. If `fov` is omitted and a LiDAR exists, object setup
defaults FOV values from that sensor's angle range and max range. Without LiDAR,
set both explicitly. `obj.fov_detect_object(other)` and
`obj.get_fov_detected_objects()` perform object-sector detection, including the
target radius in the boundary test; they are not a replacement for a LiDAR
range scan.

With `world.fog_map: true`, a LiDAR-bearing object reveals fog along its measured
beams after each environment step. A sensing object with no LiDAR but with
`fov`/`fov_radius` reveals a sector without occlusion. See [map-api.md](map-api.md)
for the fog grid and coverage API.
