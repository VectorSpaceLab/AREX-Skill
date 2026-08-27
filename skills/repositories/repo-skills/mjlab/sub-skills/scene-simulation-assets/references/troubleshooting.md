# Scene, simulation, and asset troubleshooting

## MJCF or MjSpec fails to compile

- Validate the original MJCF with MuJoCo-level tooling before adding managers.
- Check that mesh and texture paths are packaged with the model or reachable by
  the user's project.
- Ensure an `EntityCfg` models one rooted system; detached bodies should be
  separate scene entities.
- If multiple free joints exist, split the asset into multiple entities.

## Initial state or keyframe errors

- `EntityCfg.InitialStateCfg.joint_pos=None` means use the model's existing
  keyframe. It fails if no compatible keyframe exists.
- Regex entries in `joint_pos` and `joint_vel` must cover the intended joints.
- For fixed-base entities, mjlab may add mocap wrapping; use entity data APIs
  instead of assuming raw qpos layout.

## Namespacing and target lookup

Scene composition prefixes entity element names. If actuator or manager targets
cannot be found:

1. Confirm the scene entity key.
2. Confirm whether the expression targets joints, bodies, geoms, sites,
   actuators, tendons, cameras, lights, materials, or textures.
3. Preserve order when target ordering controls policy action dimensions.
4. Use a scene/config inspection helper before changing training code.

## Variant topology failures

Variant specs must be compatible in topology and inertial mode. Failures usually
mean the variants differ in an unsupported structural way, not that the task
registry or runner is broken. Reduce to two variants, compare joints/geoms/body
structure, then reintroduce the full set.

## CUDA graph stale-field issues

If model or data arrays are replaced after graph capture, MuJoCo Warp can keep
reading old pointers. Use mjlab's domain-randomization helpers or recreate the
simulation graphs after manual low-level changes.

## Export problems

- The installed export command clears the output directory before writing.
- A task target exports the full task scene; an alias exports a bundled robot;
  an import path exports a custom entity factory.
- If export output is missing meshes, make sure the entity factory packages or
  resolves the assets rather than relying on a transient local path.
- If `zip=True`, check for the `.zip` file instead of the directory.

## Rendering-specific confusion

Scene export and simulation construction can succeed even when native viewer or
offscreen rendering fails. Route EGL/GL/camera issues to the perception and
training/debug sub-skills before rewriting entity specs.
