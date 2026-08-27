# Spec editors

`EntityCfg` can layer Python edits on top of an MJCF/MjSpec factory without
modifying the original XML. Editors run before actuators and initial state are
finalized.

## Editor families

| Editor family | Typical use |
|---|---|
| `TextureCfg` | create or patch texture size, type, color channels, file/image content, grid layout, flip options |
| `MaterialCfg` | material colors, emission/specular/shininess, texture bindings, repeats |
| `MeshCfg` | mesh file/data/path settings and scaling |
| `GeomCfg` | geom size, pose, color, group, material, collision attributes |
| `CollisionCfg` | collision-specific patching for matched geoms |
| `LightCfg` | diffuse/specular/ambient/attenuation/cutoff/exponent and pose |
| `CameraCfg` | camera pose, field of view, intrinsics, and camera model settings |

## Matching rules

Spec editors generally match by names or regex-like expressions. Keep patterns
specific enough to avoid changing helper/default geoms unexpectedly. If an
editor should patch every matched geom, ensure the catch-all behavior is
explicit and intentional.

## Collision and geom overlap

`GeomCfg` and `CollisionCfg` share some fields. mjlab warns when collision
patches overwrite geom collision edits. Treat that warning as a config design
signal:

1. Put visual/material edits in `GeomCfg`.
2. Put collision masks, priorities, `condim`, and friction contact behavior in
   `CollisionCfg` when the intent is collision-specific.
3. Avoid setting the same collision field in both unless the later override is
   deliberate.

## Actuator attachment

Entity-level actuator configs are part of the entity articulation. Common
attachment choices:

- `XmlActuatorCfg`: use actuators already present in XML.
- Built-in MuJoCo position/velocity/motor/muscle/DC motor configs: create
  implicit-actuator entries in the MjSpec.
- Explicit PD/DC/learned actuators: compute commands in Python/Warp and write
  targets/efforts.

For policy action terms and detailed actuator tradeoffs, use the MDP components
sub-skill.

## Debugging editor results

- Compile or export a tiny scene before launching training.
- Check matched element names and counts.
- If exported XML contains stale files, clear the export destination and rerun.
- If a fixed-base entity unexpectedly moves or cannot be placed per-world,
  remember that mjlab wraps fixed-base entities with mocap bodies.
- If camera or texture rendering is wrong, distinguish MuJoCo spec edits from
  GL/EGL/offscreen renderer issues.
