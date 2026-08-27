# IR-SIM Public Surface

Read this when a request crosses multiple IR-SIM routes or when you need a
compact map of the package's public entry points. The detailed contracts live
in the nearest sub-skill; this file avoids duplicating their parameter tables.

## Core construction and lifecycle

- `irsim.make(world_name=None, projection=None, step_mode=None, **kwargs)`
  selects `EnvBase` or `EnvBase3D`. Common options are `display`,
  `disable_all_plot`, `save_ani`, `log_level`, `seed`, and `step_mode`.
- `EnvBase` owns YAML parsing, objects, collision/spatial indexes, sensors,
  status, plotting, and the simulation clock. The essential lifecycle is
  `step` → optional `render` → `done` → `end`/`close`.
- Query/drawing entry points include `get_robot_state`, `get_robot_info`,
  `get_lidar_scan`, `get_map`, `get_object_by_name`, `get_object_by_id`,
  `get_group_by_name`, `draw_trajectory`, `draw_points`, and `draw_quiver`.
- `reset(random=False)` restores the cached scene; `reload(world_name=None)`
  rereads YAML; `refresh()` synchronizes derived state without advancing time.

## Scene and object concepts

- YAML root keys are `world`, `robot`, `obstacle`, and optional `gui`.
- Objects use Shapely-backed `circle`, `rectangle`, `polygon`, `compound`, or
  `linestring` geometry and may use `diff`, `omni`, `omni_angular`, or `acker`
  kinematics.
- `ObjectBase` exposes state, velocity, goal, geometry, collision/arrival
  flags, `get_info()`, `get_obstacle_info()`, and mutation methods such as
  `set_state`, `set_velocity`, and `set_goal`.

## Sensors, maps, behaviors, and planners

- Registered sensor types are `lidar2d` and `fmcw_lidar2d`. Standard scans have
  `ranges` and Cartesian `velocity`; FMCW scans have `ranges`, `valid`, and
  scalar `radial_velocity`.
- `resolve_obstacle_map` accepts `None`, an ndarray, an image path/spec, or a
  generator spec. Built-in generators are image and Perlin; `env.get_map` gives
  planners a map object with grid/geometry collision methods.
- Per-object behaviors are `dash`, `rvo`, and `sfm` for selected kinematics;
  `group_behavior: {name: orca}` is optional and requires `pyrvo`.
- Programmatic planners are `AStarPlanner`, `JPSPlanner`, `RRT`, `RRTStar`,
  `InformedRRTStar`, and `PRMPlanner`. They return a path or a no-route value;
  map resolution, robot clearance, and finite budgets matter.
- Registries are extensible through custom behavior/group behavior decorators,
  kinematics registration, and `GridMapGenerator` subclasses. The extension
  route owns exact registration contracts and failure recovery.

## Verification anchors

The source version for this graph is recorded in
[repo-provenance.md](repo-provenance.md). Use the bundled route-specific smoke
helpers rather than original usage paths. The private construction environment
and review artifacts are not runtime dependencies.
