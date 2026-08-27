# Perception, terrain, and randomization troubleshooting

## Sensor context missing

Cameras and raycasts require a `SensorContext`. `ManagerBasedRlEnv` handles this
wiring. Manual scene/simulation code must call:

```python
if scene.sensor_context is not None:
    sim.set_sensor_context(scene.sensor_context)
```

If a camera or raycast says it needs a sensor context, fix this before changing
sensor parameters.

## Camera or rendering fails

- On Linux, mjlab defaults `MUJOCO_GL=egl` when unset.
- Native viewer, Viser, and offscreen video exercise different rendering paths.
- Reduce image resolution and disable textures/shadows for debugging.
- Verify the camera exists or that `parent_body`, pose, and `fovy` are valid.
- CPU config import is not proof that offscreen rendering works on a headless
  GPU machine.

## Raycast misses or hits the robot

- Check `frame` object type and name.
- Use `exclude_parent_body=True` to avoid self-hits when appropriate.
- Confirm `include_geom_groups`; MuJoCo group filtering can hide target geoms.
- Increase `max_distance` for terrain or obstacle scans.
- Visualize/debug with tiny environments before using height scans as policy
  observations.

## Contact matching surprises

- Distinguish `primary` and `secondary` match sets.
- Use `secondary_policy="error"` when ambiguity should fail loudly.
- `global_frame=True` needs normal/tangent outputs.
- Increase `num_slots` if multiple contacts are expected.
- For locomotion foot metrics, enable and inspect air-time tracking.

## Terrain proportions do not match expectation

- Terrain type proportions are normalized across selected sub-terrains.
- Curriculum mode maps rows to difficulty; random mode samples types/difficulty
  differently.
- Flat patches can be unavailable if patch radius or max height difference is
  too strict.
- Start with fewer rows/cols and known random seeds when debugging.

## Domain randomization has no effect

- Ensure the event term is in the correct mode.
- Confirm the target names/fields match model elements.
- Use DR helpers that declare required model fields; manual writes can miss
  expansion/recapture requirements.
- For visual fields, check whether rendering groups/materials/textures are
  enabled in the viewer or camera sensor.

## GPU vs CPU verification

CPU checks are good for config construction and some geometry generation, but
full raycast, camera, MuJoCo Warp, and training behavior should be verified on
the user's intended CUDA host when those capabilities matter.
