---
name: perception-terrain-randomization
description: "Configure mjlab sensors, terrain generation, flat patches, and
  domain randomization with CPU/CUDA verification boundaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Perception, Terrain, and Randomization

Use this sub-skill when an mjlab task needs perception sensors, terrain,
terrain-aware resets/curriculum, or runtime domain randomization.

## Route here for

- Scene-level `BuiltinSensorCfg`, `ContactSensorCfg`, `RayCastSensorCfg`,
  `TerrainHeightSensorCfg`, and `CameraSensorCfg` selection.
- Sensor data semantics: contact reductions/history, raycast hit distances,
  terrain height scans, RGB/depth/segmentation outputs, and debug visualization.
- `TerrainEntityCfg`, `TerrainGeneratorCfg`, terrain presets, curriculum grid
  behavior, spawn proportions, and flat patch sampling.
- Domain-randomization event functions in `mjlab.envs.mdp.dr`, including model
  field expansion, recomputation levels, camera/render implications, and
  visualization limits.
- Deciding whether a check is CPU-config-only or a CUDA/full sensor validation.

## Route elsewhere

- Base entity, scene, MuJoCo spec editing, asset variants, and scene export:
  [scene-simulation-assets](../scene-simulation-assets/SKILL.md).
- Observation/reward/action/termination term dictionaries and observation-group
  wiring: [environment-configuration](../environment-configuration/SKILL.md)
  and [mdp-components](../mdp-components/SKILL.md).
- Training, playback, task registry, viewer CLI, checkpoints, W&B, and export
  commands: [training-evaluation-cli](../training-evaluation-cli/SKILL.md).

## Operating workflow

1. Identify which layer owns the request: sensor config, terrain config,
   terrain-aware reset/curriculum, or `dr` event term.
2. Confirm exact installed signatures and terrain preset names with the bundled
   [inspection script](scripts/inspect_sensor_terrain.py) when the mjlab version
   may matter. Use `--json` for machine-readable output.
3. Read the relevant reference:
   - [Sensors](references/sensors.md) for built-in/contact/raycast/camera data.
   - [Terrain](references/terrain.md) for generator modes, presets, flat patches,
     curriculum, and debug groups.
   - [Domain randomization](references/domain-randomization.md) for event modes,
     field selection, operations/distributions, and recompute behavior.
   - [Troubleshooting](references/troubleshooting.md) for common sensor, terrain,
     rendering, and DR failures.
4. Choose verification level explicitly:
   - CPU/config checks can inspect imports, dataclass signatures, CLI/help text,
     and pure terrain config construction.
   - CUDA/full checks are needed for raycast/camera sensing, MuJoCo Warp render
     context behavior, sensor-context creation, and training-scale simulation.

## Fast decisions

- Use `ContactSensorCfg` for structured contact data and gait air-time signals.
- Use `RayCastSensorCfg` with a `GridPatternCfg` for terrain scans and with a
  `PinholeCameraPatternCfg` for depth-like rays.
- Use `TerrainHeightSensorCfg` when the policy needs per-frame vertical
  clearance rather than raw raycast hit positions.
- Use `CameraSensorCfg` for RGB/depth/segmentation images; keep all camera
  render settings identical inside one scene.
- Use terrain named configs for standard locomotion terrain, then customize with
  `dataclasses.replace()` or by replacing `sub_terrains`.
- Prefer `startup` or `reset` events for DR functions that trigger model
  recomputation; reserve frequent interval/step events for cheap state or
  friction-style changes.
