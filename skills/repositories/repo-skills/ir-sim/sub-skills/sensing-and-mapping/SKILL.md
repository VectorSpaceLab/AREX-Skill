---
name: sensing-and-mapping
description: "This skill guides users through IR-SIM LiDAR, FMCW sensing,
  field-of-view fog, and occupancy-map workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sensing and mapping

Use this route when a task involves `lidar2d`, `fmcw_lidar2d`, scan payloads,
radial velocity, FOV sensing, fog-of-map exploration, image/Perlin occupancy
grids, or a map passed to a planner. The package target is `ir-sim==2.10.2`
with Python 3.10 or newer.

## Route the task

1. Start with the sensor contract in [sensor-api.md](references/sensor-api.md)
   when the question is about YAML fields, `env.get_lidar_scan(id)`, arrays,
   offsets, noise, or update timing.
2. Start with [map-api.md](references/map-api.md) for image/Perlin generators,
   `resolve_obstacle_map`, `build_grid_from_generator`, `World.get_map`,
   resolution, downsampling, collision, or planner handoff.
3. Use [troubleshooting.md](references/troubleshooting.md) for installation,
   optional backends, missing map data, malformed sensor/map configuration, and
   stale readings after manual state changes.
4. Run the bundled deterministic checks from arbitrary working directories:
   `python scripts/scan_smoke.py --help`, then
   `python scripts/scan_smoke.py --sensor-type lidar2d` (or `fmcw_lidar2d`),
   and `python scripts/map_smoke.py`. They create only temporary tiny fixtures.

A scan belongs to a robot index, not a sensor index: `env.get_lidar_scan(id)`
selects `env.robot_list[id]`. If one object has both sensor classes, inspect
`env.robot_list[id].sensors` and call the selected sensor's `get_scan()` rather
than assuming the convenience getter selected the desired class. The first
LiDAR-like sensor is also exposed as `obj.lidar` by the object layer.

Scene/object YAML and shapes belong to
[scene-configuration](../scene-configuration/SKILL.md); environment lifecycle,
headless rendering, and external stepping belong to
[simulation-environments](../simulation-environments/SKILL.md); planner
selection and path algorithms belong to
[navigation-and-planning](../navigation-and-planning/SKILL.md). The package
must be installed/importable before using any route; do not depend on an
original checkout, source example, private environment path, or bundled large
map asset at runtime.

## Operating contracts

- **Sensor lookup:** `env.get_lidar_scan(id=0)` takes a robot-list index, not a
  sensor index. If one robot carries both classes, select the instance from
  `env.robot_list[id].sensors` by `sensor.sensor_type` and call its `get_scan()`.
- **Payload branching:** standard `lidar2d` returns `ranges` plus Cartesian
  `velocity` and no `valid`/`radial_velocity`; `fmcw_lidar2d` returns
  `ranges`, boolean `valid`, and scalar `radial_velocity`, and removes
  `velocity`. Both keep the scalar angle/timing metadata and
  `intensities=None`.
- **Map handoff:** use `env.get_map(resolution=...)` once for a planner and
  inspect `grid`, `grid_resolution`, and `world_offset` before choosing planner
  parameters. The planner constructor and `planning()` contract belong to
  [navigation-and-planning](../navigation-and-planning/SKILL.md), not this
  route.

## Minimal access pattern

```python
scan = env.get_lidar_scan(id=0)
ranges = scan["ranges"]
points = env.robot_list[0].get_lidar_points()  # local 2 x N, or None
```

Use `scan["valid"]` and `scan["radial_velocity"]` only for an FMCW scan. A
standard scan instead exposes a Cartesian `velocity` array (usually zeros)
and has no validity mask or radial-velocity key. Full keys, timing semantics,
map construction, and collision details are in the linked references.
