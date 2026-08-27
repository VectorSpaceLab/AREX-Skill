# Sensing and mapping troubleshooting

## Install and import

Install the matching distribution in the active runtime, then verify the
public imports before diagnosing a scene:

```bash
python -m pip install "ir-sim==2.10.2"
python - <<'PY'
import irsim
from irsim.world.sensors import FMCWLidar2D, Lidar2D
from irsim.world.map import FogMap, Map, build_grid_from_generator
print(irsim.__version__)
PY
```

Core sensing, FOV, fog, image, and Perlin workflows use the base package
(`numpy`, `shapely`, `matplotlib`, and related dependencies). There is no
sensor-specific compiled backend. `pynput` is only for live keyboard control;
`pyrvo` is for ORCA behavior and is not needed here; video/ffmpeg extras are
not needed for scan or occupancy arrays. Use `MPLBACKEND=Agg` for headless
smokes and omit interactive plotting. If the import fails, fix the active
package environment first rather than changing YAML.

## Sensor selection and payload errors

- **The wrong scan appears:** `env.get_lidar_scan(id)` takes a robot list index,
  not a sensor index. On a robot with both sensor types, inspect
  `robot.sensors`, match `sensor.sensor_type`, and call that instance's
  `get_scan()`. The convenience `robot.lidar` is the first LiDAR-like sensor.
- **`KeyError: valid` or `radial_velocity`:** the selected scan is standard
  `lidar2d`; those keys belong only to FMCW. Conversely, FMCW removes the
  standard `velocity` key. Branch on `sensor.sensor_type`, not on an assumed
  dictionary shape.
- **No points:** `ranges` at `range_max` means no standard return; FMCW also
  reports `valid=False`. `get_points()` returns local `2 x N` points only for
  ranges below `range_max - 0.02`, otherwise `None`.
- **Unexpected beam count/angle:** `number` controls array length. The source
  uses `angle_range/number` for metadata increment but linearly spaces the
  actual `angle_list` over both endpoints. Do not derive an index using a
  number-minus-one increment.
- **`angle_std` seems ineffective:** in 2.10.2 it is stored but not applied by
  the scan implementation. Treat angular-noise behavior as an unresolved
  package limitation rather than compensating in a helper.
- **FMCW velocity is zero:** a no-hit beam is zero by contract; tangential target
  motion also projects to zero. Check `valid`, target `set_velocity`, and call
  `env.refresh()` after manual state/velocity changes. With default
  `motion_compensate: false`, subtracting ego XY velocity is expected.
- **Noise makes a hit disappear:** range noise is applied before FMCW validity;
  an out-of-range noisy reading becomes invalid with `range_max` and zero
  Doppler. Seed with `irsim.util.random.set_seed` when comparing runs.

## Update-order and stale geometry failures

Sensors are stepped after all object geometry is updated and the spatial tree
rebuilt. If direct code calls `set_state()` or `set_velocity()` and then reads a
scan without `env.refresh()`, other objects' tree entries or sensor data can be
stale. The safe sequence is:

```python
obj.set_state(new_state)
obj.set_velocity(new_velocity)
env.refresh()
scan = env.get_lidar_scan(obj_index)
```

For external step mode, update all object states/velocities, call
`env.step()` with no action, and let the environment perform refresh/tree/sensor
synchronization. Do not pass an action in external mode. Calling only
`obj.sensor_step()` is appropriate only when the environment tree is already
current. Sensors ignore the parent object itself and geometry marked
`unobstructed`.

## YAML and data failures

- **Unknown sensor:** use `name: lidar2d` or `type: lidar2d`, or
  `fmcw_lidar2d`; spelling/case is not a plugin lookup. Unknown factory names
  raise `NotImplementedError`.
- **No scan attached:** ensure `sensors` is a list of dictionaries under the
  object. Sensor construction is attached to the object; a world-level sensor
  key is not a supported substitute.
- **Image not found:** `name: image` requires a non-empty `path`; a string is
  shorthand for that form. Give the caller's project path explicitly and make
  sure it exists. Do not refer to a repository example or package test image.
  Dark pixels map to occupancy, and image axes are transposed/flipped by the
  loader, so inspect the resulting shape/orientation.
- **Generator errors:** non-image generators require `name`, `resolution`, and
  world dimensions. `perlin` derives cell counts from world size/resolution;
  do not provide YAML `width`/`height` counts. Missing resolution/world size or
  an unknown generator name is a configuration error. Perlin `fractal < 1` and
  `attenuation <= 0` raise `ValueError`; use a positive resolution and a
  sensible positive `mdownsample`.
- **Map looks the wrong size:** first compare `world.grid_map.shape` and
  `world.reso`. World construction applies `grid[::mdownsample, ::mdownsample]`,
  so the actual cell size is recomputed from world dimensions. Planner-time
  `env.get_map(resolution=...)` may then conservatively block-max downsample
  when the requested resolution is coarser; it never upsamples a finer grid.
- **Offset mismatch:** `Map.world_offset` and fog offsets are the world
  `offset`; grid indexing is in those shifted coordinates. A point outside the
  world is occupied/collision. Check `map.grid_resolution`, not just the
  requested `map.resolution`.

## Fog and planning workflow failures

- **Fog never reveals:** ensure `world.fog_map: true`, then either attach a
  LiDAR or set both object `fov` and `fov_radius`. LiDAR takes precedence over
  FOV for world reveal. Empty/zero ranges and non-positive FOV/radius are
  no-ops. Check `env._world.fog_map.explored_ratio` headlessly after `env.step()`.
- **Fog shape differs from the obstacle map:** explicit `fog_map_resolution`
  controls its own rounded grid. When omitted, it uses the current obstacle
  grid's x cell size, or 0.1 m without an obstacle map. Fog is an overlay mask,
  not an occupancy grid for collision/planning.
- **Planner cannot find a route:** route planner constructor and `planning()`
  details to `navigation-and-planning`. First verify grid dimensions,
  `grid_resolution`, `world_offset`, occupancy threshold, robot-radius margin,
  and whether `mdownsample` already removed needed corridors. `Map.is_collision`
  treats out-of-bounds geometry as occupied and uses occupied grid cells before
  Shapely obstacle geometry. A requested finer planner resolution cannot restore
  detail lost during map construction.
- **Map collision unexpectedly misses/hits:** values must be compared against
  the strict `>50` threshold. Grid collision is based on occupied cell centers
  and a half-cell radius; it is deliberately coarse. With no grid,
  `grid_occupied` returns `None` and `is_collision` relies on Shapely obstacle
  objects.
