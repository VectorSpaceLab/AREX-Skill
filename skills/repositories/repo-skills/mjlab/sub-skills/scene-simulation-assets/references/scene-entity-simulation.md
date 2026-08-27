# Scene, entity, and simulation object model

## Object model

| Object | Role |
|---|---|
| `EntityCfg` | Describes one physical object: an MjSpec factory, initial state, optional articulation/actuators, and spec editors. |
| `Entity` | Runtime wrapper for one entity's names, IDs, data views, actuators, and spec. |
| `SceneCfg` | Combines terrain, named entities, sensors, environment count, spacing, and an optional final spec edit callback. |
| `Scene` | Builds the combined `mujoco.MjSpec`, initializes runtime entities/sensors, exposes `scene[...]`, and writes export packages. |
| `SimulationCfg` | Controls MuJoCo and MuJoCo Warp allocation, broadphase, sensor contact limits, and NaN guard. |
| `Simulation` | Owns MuJoCo/MuJoCo Warp model/data and graph-captured `step`, `forward`, `reset`, and `sense` operations. |

## Minimal manual runtime

```python
from mjlab.scene import Scene
from mjlab.sim import Simulation, SimulationCfg

scene = Scene(scene_cfg, device="cuda:0")
sim = Simulation(
    num_envs=scene.num_envs,
    cfg=SimulationCfg(),
    spec=scene.spec,
    variant_info=scene.collect_variant_info(),
    device="cuda:0",
)
scene.initialize(sim.mj_model, sim.model, sim.data)
if scene.sensor_context is not None:
    sim.set_sensor_context(scene.sensor_context)
```

A `ManagerBasedRlEnv` performs this assembly for ordinary RL workflows. Use the
manual path for focused scene/simulation inspection, custom loops, or export
helpers.

## Entity categories

mjlab treats an entity as one rooted physical object. Useful categories:

- fixed non-articulated: table, wall, static prop
- fixed articulated: robot arm or door welded to the world
- floating non-articulated: box, ball, mug
- floating articulated: humanoid or quadruped

Fixed-base entities are automatically wrapped in a mocap body so parallel
environments can be placed and reset independently.

## Namespacing

Scene composition prefixes entity elements with the scene entity name to avoid
collisions. Manager terms should generally refer to the scene entity key first,
then match joints/bodies/geoms/sites inside that entity via `SceneEntityCfg`.

When a regex fails, determine whether the name is an entity key, a local element
name, or a composed global name before changing the expression.

## Data access

- Use `scene["name"]` to retrieve an entity or sensor by configured name.
- Use entity data properties for batched root, body, joint, and actuator state.
- Use `sim.model` / `sim.data` when you need low-level MuJoCo Warp fields.
- If you write state and immediately read derived kinematics, ensure the
  lifecycle has run `forward()` before relying on derived values.

## Simulation configuration

Important `SimulationCfg` / `MujocoCfg` fields:

- `nconmax`, `njmax`: per-world contact/constraint allocation.
- `contact_sensor_maxmatch`: maximum contact matches stored for contact sensors.
- `broadphase`, `broadphase_filter`: MuJoCo Warp broadphase choices.
- `mujoco.timestep`, `integrator`, `solver`, `iterations`, `tolerance`.
- `mujoco.disableflags`, `mujoco.enableflags` for MuJoCo option flags.
- `nan_guard` for state capture when NaN/Inf appears.

## CUDA graph caution

MuJoCo Warp graph capture remembers array pointers. If code expands or replaces
model/data arrays outside mjlab's managed helpers, recreate graphs before
expecting simulation steps to see the new fields. Domain randomization helpers
handle their own expansion/recapture requirements.
