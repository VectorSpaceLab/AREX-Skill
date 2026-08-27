---
name: modeling
description: "Build and extend robosuite MJCF worlds, tasks, objects, arenas,
  custom environments, and robot assets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modeling

Use this sub-skill when the change is about robosuite model construction rather than runtime policy or camera math.

## Use for

- custom environments built from `MujocoWorldBase`, `Arena` / `TableArena`, `Task` / `ManipulationTask`, and `MujocoObject`
- custom robot or gripper XML assets, body-part naming, mounts, and end-effector attachment checks
- MJCF compilation, inspection, and asset-path validation
- model-focused maintainer test selection and validation guidance

## Do not use for

- controller config and action-space semantics; use `../controllers`
- camera observations, camera transforms, or rendering checks; use `../rendering`
- routine environment usage that does not change model structure
- teleoperation data and playback

## Read next

- `references/custom-environments.md`
- `references/mjcf-modeling.md`
- `references/maintainer-testing.md`
- `references/troubleshooting.md`
- `scripts/compile_mjcf_model.py`
- `scripts/check_custom_robot_model.py`

## Typical outputs

- a `ManipulationEnv` subclass for a new task
- a custom `MujocoXMLObject`, `MujocoGeneratedObject`, or `MujocoObject`
- a new arena, table setup, or manipulation task composition
- a robot or gripper XML fix that preserves joint order, mount bodies, and naming conventions

## Working pattern

1. Start from the smallest MJCF world or task that reproduces the change.
2. Use the bundled compile helper on any edited XML.
3. Use the bundled robot checker for custom robot XML or registered robots.
4. Run the narrowest maintainer tests listed in `references/maintainer-testing.md`.
5. If the issue is camera/viewer-specific, hand it to `../rendering` instead of widening modeling scope.

## Cross-links

- `../controllers` for robot composition, grippers, and controller configs
- `../rendering` for image observations, camera transforms, and display-dependent viewer debugging
