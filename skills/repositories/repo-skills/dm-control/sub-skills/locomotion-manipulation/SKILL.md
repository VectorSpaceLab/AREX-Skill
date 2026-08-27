---
name: locomotion-manipulation
description: "Use high-level dm_control locomotion, soccer, mocap, walker, prop,
  and manipulation task families."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# dm_control locomotion and manipulation router

Use this sub-skill when the task is about selecting or using built-in high-level `dm_control` manipulation, locomotion, soccer, walker, mocap, arena, or prop families. These are Composer-backed environments and components; they can be stepped with the same `dm_env` loop style as suite tasks once an environment is constructed.

## Route first

- For ready-made manipulation registry tasks, read [references/manipulation-reference.md](references/manipulation-reference.md) to choose `features` versus `vision`, validate names/tags, load with `dm_control.manipulation.load`, and smoke-test specs.
- For locomotion examples, walkers, arenas, soccer, mocap/reference-pose tracking, and asset/data caveats, read [references/locomotion-reference.md](references/locomotion-reference.md) before constructing or importing heavier task families.
- For common failures around unknown names/tags, feature/vision confusion, missing HDF5/labmaze/assets, expensive demos, and rendering requirements, read [references/troubleshooting.md](references/troubleshooting.md).
- Run [scripts/list_locomotion_manipulation.py](scripts/list_locomotion_manipulation.py) to list installed manipulation tasks/tags and verify that common locomotion example modules import; add `--smoke-manipulation` for a one-reset/one-step manipulation smoke.

## Boundaries

- Generic Control Suite tasks and benchmark loops belong in `../suite-rl-workflows/SKILL.md`.
- Building new Composer tasks/entities, custom observables, or reusable robot abstractions from scratch belongs in `../composer-environments/SKILL.md`.
- Rendering backend operations, viewer windows, and pixel-render troubleshooting belong in `../rendering-viewer-assets/SKILL.md`.

## Quick decision checklist

1. If the user names a manipulation task or asks for Jaco arm/hand tasks, validate it against `dm_control.manipulation.ALL` and load it with `dm_control.manipulation.load(name, seed=...)`.
2. If the user wants low-dimensional observations, prefer manipulation names ending in `_features`; if they want camera observations, use `_vision` and verify rendering support separately.
3. If the user names CMU humanoid, rodent, soccer, maze, corridor, bowl, target, or mocap/reference-pose tracking, treat it as locomotion/Composer-backed and inspect specs with a short reset/step before any long rollout.
4. If the task requires new arenas, reward functions, entities, or observables beyond choosing/configuring built-ins, route to Composer rather than extending this catalog inline.
