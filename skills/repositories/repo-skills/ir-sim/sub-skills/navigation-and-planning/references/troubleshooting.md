# Navigation and planning troubleshooting

## Install and import

- `ModuleNotFoundError: irsim`: install `ir-sim` in the interpreter that runs
  the helper/application (`python -m pip install ir-sim`) and verify
  `import irsim; print(irsim.__version__)`.
- `pyrvo` import failure: this blocks ORCA only. Do not treat the base package,
  RVO, or SFM as an ORCA substitute. Probe and report it explicitly; see
  [optional-orca.md](optional-orca.md).
- A Matplotlib backend/display error: use `display=False`,
  `disable_all_plot=True`, `save_ani=False`, and set `MPLBACKEND=Agg` before
  importing IR-SIM. Keep `show_animation=False` for planners.
- Keyboard and FFmpeg extras are unrelated to core planning. Install
  `ir-sim[keyboard]` or `ir-sim[all]` only for those optional surfaces.

## Behavior configuration

- **No method for category/action**: check the exact kinematics/behavior
  matrix in [behaviors.md](behaviors.md). `rvo` on `acker` is not an alias for
  `dash`; it is unsupported. Register a custom method through the extension
  route instead.
- **Robot never moves**: inspect `goal`, `control_mode`, and whether an
  individual behavior or external action is present. Built-ins intentionally
  return zeros when `goal is None`. A group behavior is used for group members,
  not as an individual `behavior` name.
- **Wrong command dimensions**: `diff` and `acker` use two values,
  `omni` uses two world-frame values, and `omni_angular` dash uses three. Keep
  `vel_min`/`vel_max` dimensions consistent with the kinematics; scene schema
  belongs to [scene-configuration](../../scene-configuration/SKILL.md).
- **RVO appears too timid or collides**: RVO is local and finite-sampled. Check
  `neighbor_threshold`, `vxmax`/`vymax`, `acce`, `factor`, and robot radii.
  `factor` penalizes fallback choices; a larger value favors longer collision
  time at the cost of goal tracking. Prefer `mode: rvo` for reciprocal agents,
  `mode: vo` for one-sided obstacle treatment, and `mode: hrvo` for the hybrid
  cone. Do not call these separate behavior registrations.
- **SFM oscillates, hugs a wall, or looks unlike RVO**: SFM is a force model,
  not a formal collision-free solver. Lower or raise the social/obstacle force
  weights deliberately, inspect `sigma_obstacle` and `neighbor_threshold`, and
  use `safety_radius` for personal space rather than changing geometry. Keep
  `relaxation_time`, `gamma`, and `sigma_obstacle` positive.

## Linestrings and scenes

- **Line obstacle is ignored**: use `shape: {name: linestring, vertices: [...]}`
  with at least two distinct vertices. RVO/SFM read consecutive segments via
  `rvo_line_segments`; a degenerate segment is skipped. Verify the obstacle is
  in the same world coordinate frame as the robot.
- **Robot crosses a line or reports a collision unexpectedly**: local behavior
  and collision/status policy are separate. Review `unobstructed`,
  `world.collision_mode`, robot radius, and line placement. A line obstacle
  does not create a global route around an enclosed goal.
- **Crowd order changes results**: reactive behaviors consume the current
  external-object states and group members. Use a fixed environment `seed`, a
  small deterministic fixture, and bounded steps while comparing parameter
  changes. Do not use a 200-agent ORCA example as a smoke test.

## Planner API and data

- **Planner import fails**: import classes from `irsim.lib.path_planners`:
  `AStarPlanner`, `JPSPlanner`, `RRT`, `RRTStar`, `InformedRRTStar`, and
  `PRMPlanner`. Do not import a source example.
- **Constructor argument error**: A*/JPS take only `env_map`; RRT variants
  require `env_map, robot`; PRM requires `env_map, robot_radius`. Check the
  live signatures in [path-planners.md](path-planners.md).
- **Path is missing**: use `show_animation=False`, confirm the start/goal are
  in bounds and free at the selected map resolution, then account for robot
  clearance. JPS and RRT-family planners return `None` on their documented
  failure paths; PRM can return an empty `2 x 0` array. A* may return a
  degenerate goal-only result after an exhausted open set, so validate it
  before following.
- **Blocked-map recovery**: do not blindly increase iterations first. Check
  goal occupancy, regenerate `env.get_map(resolution=...)`, use a finer grid
  for narrow passages or a coarser grid for excessive cost, and ensure the
  robot footprint can pass. For RRT tune `expand_dis`, `path_resolution`, and
  `max_iter`; for PRM tune `n_sample`, `n_knn`, and `max_edge_len`. If the
  goal is covered by an obstacle, report no route rather than falling back to
  dash.
- **Sampling result varies**: seed Python's `random` for RRT/RRT* families.
  PRM's default uses IR-SIM's RNG; pass a deterministic `rng` object to
  `PRMPlanner.planning` or seed IR-SIM's RNG. A fixed seed makes a run
  repeatable, not universally successful.
- **Path draws backwards**: planner arrays are `2 x N` and goal-to-start in
  this release. `draw_trajectory` accepts the array but does not follow it;
  reverse columns for start-to-goal controllers.
- **PRM never connects**: its sampled nodes model a circular `robot_radius` and
  edge length is capped by `max_edge_len`. Increase samples/neighbors or edge
  length only after checking the map and radius. An unreachable graph produces
  an empty result.

## Workflow hygiene

Close environments with `env.end(suppress_summary=True)` in bounded scripts.
Do not run `show_animation=True` in CI or a headless agent. Planning is a
snapshot operation: if the world, map, robot state, or obstacle geometry
changes, regenerate the map and plan again. For sensor-built occupancy maps,
use [sensing-and-mapping](../../sensing-and-mapping/SKILL.md); for stepping,
rendering, and cleanup, use
[simulation-environments](../../simulation-environments/SKILL.md).
