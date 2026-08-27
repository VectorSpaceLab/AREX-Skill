---
name: scene-simulation-assets
description: "Compose mjlab scenes, entities, variants, simulation configs,
  asset-zoo robots, and exportable MuJoCo packages."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scene, Simulation, and Assets

Use this sub-skill when the task is about mjlab scene assembly or the MuJoCo
asset layer: `EntityCfg`, `VariantEntityCfg`, `SceneCfg`, `TerrainEntityCfg`,
entity-level actuator attachment, `SimulationCfg` / `MujocoCfg`, asset-zoo
robots, scene export, or direct `mujoco.MjSpec` / MuJoCo Warp model-data access.

## Start Here

- For the scene/entity/simulation object model, lifecycle order, namespacing,
  data access, and graph constraints, read
  [scene-entity-simulation.md](references/scene-entity-simulation.md).
- For asset-zoo robot factories, export targets, `Scene.write(...)`, and
  heterogeneous mesh variants, read
  [assets-export-variants.md](references/assets-export-variants.md).
- For texture, material, mesh, geom, collision, light, camera, and cross-entity
  spec editing, read [spec-editors.md](references/spec-editors.md).
- For common MJCF, keyframe, mocap, namespacing, variant, export, and CUDA graph
  failures, read [troubleshooting.md](references/troubleshooting.md).
- For a safe scene-export smoke check, use
  [scripts/export_scene_smoke.py](scripts/export_scene_smoke.py).

## Core Runtime Contract

When manually constructing the runtime, follow the same order used by mjlab's
manager-based environment:

```python
from mjlab.scene import Scene
from mjlab.sim import Simulation, SimulationCfg

scene = Scene(scene_cfg, device="cpu")
sim = Simulation(
    scene.num_envs,
    SimulationCfg(),
    spec=scene.spec,
    variant_info=scene.collect_variant_info(),
    device="cpu",
)
scene.initialize(sim.mj_model, sim.model, sim.data)
if scene.sensor_context is not None:
    sim.set_sensor_context(scene.sensor_context)
```

Use `scene.write(output_dir, zip=False)` or `scene.write(output_dir, zip=True)`
for exportable packages. For direct runtime reads, prefer `entity.data` and use
`sim.model` / `sim.data` only when a task needs global MuJoCo IDs or fields.

## Boundary Routing

- Route action-term selection, policy-output scaling, reward/action wiring, and
  detailed actuator type tradeoffs to [../mdp-components/](../mdp-components/).
  This sub-skill only covers how actuator configs attach to an entity spec.
- Route camera/raycast/contact sensor configuration, terrain generation presets,
  flat-patch sampling, and domain-randomization recipes to
  [../perception-terrain-randomization/](../perception-terrain-randomization/).
  This sub-skill covers only how those objects connect to `SceneCfg` and
  `Simulation`.
- Route installed `export-scene` CLI usage, task-registry command workflows,
  training, playback, and debug CLI flags to
  [../training-evaluation-cli/](../training-evaluation-cli/). This sub-skill is
  the API-internals reference for what that export command builds.
