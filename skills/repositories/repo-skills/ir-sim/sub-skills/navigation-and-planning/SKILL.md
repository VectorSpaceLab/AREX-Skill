---
name: navigation-and-planning
description: "This skill guides an agent through IR-SIM reactive navigation,
  multi-agent avoidance, optional ORCA coordination, and programmatic path
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Navigation and planning

Use this route when an agent must select or configure a goal-seeking behavior,
avoid other agents or line obstacles, coordinate a group, or plan a path on an
IR-SIM map. It covers the built-in `dash`, `rvo` (including `vo` and `hrvo`
modes), and `sfm` behaviors, the optional `orca` group behavior, and the six
public planners.

## Route quickly

| Need | Read next |
| --- | --- |
| Individual behavior names, kinematics compatibility, parameters, and line obstacles | [behaviors.md](references/behaviors.md) |
| `get_map`, planner constructors, `planning`, output shape, and failure recovery | [path-planners.md](references/path-planners.md) |
| `group_behavior: {name: orca}` and the `pyrvo` gate | [optional-orca.md](references/optional-orca.md) |
| Install/import, invalid configuration, blocked maps, or headless failures | [troubleshooting.md](references/troubleshooting.md) |

Run the bundled bounded checks from any working directory:

```bash
python skills/disco/ir-sim/sub-skills/navigation-and-planning/scripts/behavior_smoke.py --help
python skills/disco/ir-sim/sub-skills/navigation-and-planning/scripts/planner_smoke.py --help
```

The helpers create temporary YAML scenes, disable rendering, use a small step
or iteration budget, and never depend on the source checkout's example files.
They are smoke checks, not proof that a large crowd or optional ORCA run is
correct. ORCA is never reported as verified by the helpers unless `pyrvo` is
independently importable; see [optional-orca.md](references/optional-orca.md).

## Minimal workflow

1. Install the base package (`pip install ir-sim`) and import the planner or
   behavior surface. Install `ir-sim[all]` only when ORCA, keyboard input, or
   video output is actually needed.
2. Author a compatible robot/obstacle scene. Kinematics and geometry belong to
   [scene-configuration](../scene-configuration/SKILL.md); sensor-derived maps
   belong to [sensing-and-mapping](../sensing-and-mapping/SKILL.md).
3. For reactive navigation, give each robot a goal and a compatible
   `behavior`. Use `group_behavior` only for coordinated group control. Step a
   headless environment with `display=False`, `save_ani=False`, and a fixed
   `seed` while tuning.
4. For global planning, call `env.get_map(resolution=...)`, construct the
   planner with the map (and the robot or radius for sampling planners), call
   `planning(start, goal, show_animation=False)`, and draw only a non-empty
   result with `env.draw_trajectory(path, traj_type="r-")`. A planner path is a
   `2 x N` array in goal-to-start order in this release; reverse it before a
   follower that expects start-to-goal order.
5. Keep planning, following, stepping, and rendering separate. Lifecycle and
   headless cleanup are covered by [simulation-environments](../simulation-environments/SKILL.md);
   custom registries and external controllers belong to
   [extension-and-control](../extension-and-control/SKILL.md).

## Selection rule

- Choose `dash` for direct, non-avoiding motion and for a simple path follower.
- Choose `rvo` for geometric local avoidance. Set `mode: vo` for one-sided
  velocity obstacles, `mode: hrvo` for the hybrid variant, and leave
  `mode: rvo` for reciprocal behavior. These are modes of the `rvo` behavior,
  not additional YAML behavior names.
- Choose `sfm` when anisotropic, pedestrian-like interaction and wall forces
  matter more than a hard collision-free guarantee. Tune it with a bounded
  test scene; it is not a global planner.
- Choose `orca` only after the optional dependency probe succeeds. It is a
  group behavior, not an individual `behavior` value.
- Choose A*/JPS for grid search, RRT for a quickly found feasible sample path,
  RRT* for rewiring-based improvement, Informed RRT* for informed improvement
  after an initial solution, and PRM for repeated queries on a static map.

For parameter trade-offs, exact live signatures, and known return-value
quirks, use the linked references rather than guessing from a behavior name.
