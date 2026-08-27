# Programmatic path planners

## Common contract

IR-SIM planners are not selected by a behavior field. Build a map and call the
planner from Python:

```python
import irsim
from irsim.lib.path_planners import AStarPlanner

env = irsim.make("scene.yaml", display=False, save_ani=False,
                 disable_all_plot=True, full=False)
env_map = env.get_map(resolution=0.2)
planner = AStarPlanner(env_map)
start = env.get_robot_state()
goal = env.get_robot_info().goal[:2, 0].tolist()
path = planner.planning(start, goal, show_animation=False)
if path is not None and getattr(path, "size", 1):
    env.draw_trajectory(path, traj_type="r-")
env.end(suppress_summary=True)
```

The live environment signatures are:

```text
irsim.make(world_name=None, projection=None, step_mode=None, **kwargs)
EnvBase.get_map(resolution=0.1)
EnvBase.draw_trajectory(traj, traj_type='g-', **kwargs)
EnvBase.get_robot_state()
EnvBase.get_robot_info(id=0)
```

`get_map` returns the map object used by the planners. Its grid resolution,
world offset, width, height, and obstacle list define bounds and collision
queries. The `resolution` argument is metres per cell; choose it to match the
scene scale and robot footprint. Use `show_animation=False` in batch or
headless work. `draw_trajectory` only overlays the result; it does not move a
robot or make a path collision-free.

All six planners use a `2 x N` NumPy array in this release, with the final goal
at column zero and the start at the last column. This is the source
implementation's parent-trace convention, even though older prose examples
call it a list of points. Reverse the columns for a follower that consumes
start-to-goal waypoints:

```python
follow_path = path[:, ::-1] if path is not None else None
```

Always check for `None` and, for PRM, an empty array before drawing or
following. Sampling planners are finite-budget searches; a `None` result is a
normal planning outcome, not proof that the map is globally impossible.

## Constructors and choices

The public imports are:

```python
from irsim.lib.path_planners import (
    AStarPlanner, JPSPlanner, RRT, RRTStar, InformedRRTStar, PRMPlanner,
)
```

The live constructor defaults are:

| Planner | Constructor | Default/search controls |
| --- | --- | --- |
| A* | `AStarPlanner(env_map)` | grid, 8-connected; `planning(start_pose, goal_pose, show_animation=True)` |
| JPS | `JPSPlanner(env_map)` | uniform-cost 8-connected grid; same planning signature |
| RRT | `RRT(env_map, robot, expand_dis=1.0, path_resolution=0.25, goal_sample_rate=5, max_iter=500)` | feasible sampling path, first feasible goal connection |
| RRT* | `RRTStar(env_map, robot, expand_dis=1.5, path_resolution=0.25, goal_sample_rate=5, max_iter=500, connect_circle_dist=0.5, search_until_max_iter=False)` | parent selection and rewiring |
| Informed RRT* | `InformedRRTStar(env_map, robot, expand_dis=1.5, path_resolution=0.25, goal_sample_rate=10, max_iter=500, connect_circle_dist=50.0, search_until_max_iter=True)` | informed ellipse after a first solution |
| PRM | `PRMPlanner(env_map, robot_radius, n_sample=500, n_knn=10, max_edge_len=30.0)` | sampled roadmap and Dijkstra; `planning(start_pose, goal_pose, rng=None, show_animation=True)` |

A*/JPS use grid cells and the map's collision interface. RRT, RRT*, and
Informed RRT* take a robot object so the robot's original Shapely geometry is
translated along sampled edges. PRM takes an explicit circular
`robot_radius`; it does not infer the radius from the robot. Use
`robot=env.robot` or the intended member of `env.robot_list`, not a robot info
snapshot.

Use:

- **A*** when a grid path and predictable search are more important than
  sampling flexibility. It uses 8-neighbor motions.
- **JPS** when the same uniform grid is open enough for jump-point pruning.
- **RRT** when one feasible path is sufficient and finite sampling variability
  is acceptable. `planner.end.cost` and `len(planner.node_list)` are available
  after a successful run.
- **RRT*** when rewiring and lower path cost are useful. Set
  `search_until_max_iter=True` when spending the whole budget to improve a
  found path is intentional.
- **Informed RRT*** when an initial solution can be found and subsequent
  samples should be focused by the start/goal ellipse. Its default searches
  through the full iteration budget.
- **PRM** for repeated queries against one static map. Increase `n_sample`
  and `n_knn` for connectivity, and keep `max_edge_len` large enough for the
  scene while respecting obstacle clearance.

## Failure handling

Before planning, verify that the start and goal are inside the map bounds and
not occupied at the chosen map resolution. A coarse cell can erase a narrow
passage; a fine grid increases memory and grid-search work. Sampling planners
also need clearance for the robot geometry. Increase the budget only after
checking the map and footprint.

Expected failure forms differ:

- **JPS** explicitly returns `None` when the start/goal cell is not walkable or
  its open set is exhausted.
- **RRT**, **RRT***, and **Informed RRT*** return `None` after their finite
  iteration budget if no collision-free goal connection is found.
- **PRM** delegates an unreachable roadmap to Dijkstra and returns an empty
  `2 x 0` NumPy array in this release; treat it as no route, not as a path.
- **A*** prints an open-set message when it cannot expand further. Its current
  final-path routine can still return a degenerate goal-only array, so do not
  use `path is not None` alone as a blocked-map success criterion. Validate
  endpoints/edges before following and prefer JPS or a sampling planner when a
  strict `None` contract is required.

A useful bounded recovery sequence is:

1. Call the same planner with `show_animation=False` and inspect the return
   shape and endpoint order.
2. Check start/goal occupancy and the robot radius/geometry against the map.
3. Adjust `resolution`: finer for narrow passages, coarser for an oversized
   search; regenerate the map after changing it.
4. For RRT-family planners, set a deterministic Python `random.seed`, raise
   `max_iter`, and tune `expand_dis`/`path_resolution`. For RRT* variants,
   decide explicitly whether to search until the full budget.
5. For PRM, use a deterministic `rng` object or IR-SIM's seeded RNG, then raise
   `n_sample`, `n_knn`, or `max_edge_len` if the roadmap is disconnected.
6. If the map is genuinely blocked, report no route and do not silently fall
   back to dash. Replan after the scene/map changes.

The bundled helper demonstrates both a tiny open map and a goal-blocked map:

```bash
python skills/disco/ir-sim/sub-skills/navigation-and-planning/scripts/planner_smoke.py --help
python path/to/generated-skill/sub-skills/navigation-and-planning/scripts/planner_smoke.py --planners astar,jps
python skills/disco/ir-sim/sub-skills/navigation-and-planning/scripts/planner_smoke.py --blocked --planners jps,rrt,prm
```

The helper bounds sampling and never runs the original path-planning examples.
For map generation and occupancy semantics, route to
[sensing-and-mapping](../../sensing-and-mapping/SKILL.md). For robot shapes,
clearance, and kinematics, route to [scene-configuration](../../scene-configuration/SKILL.md).
