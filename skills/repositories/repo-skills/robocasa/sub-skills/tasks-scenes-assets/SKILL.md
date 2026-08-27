---
name: tasks-scenes-assets
description: "This skill guides selection and customization of RoboCasa kitchen
  tasks, scenes, fixtures, objects, placement configurations, and asset
  prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Tasks, scenes, and assets

Use this sub-skill when the user is deciding **what** kitchen task to run or
customize, **which** layout/style and object registry to use, or **which**
fixture/object configuration and assets are needed. Read the focused references
before writing a task class or changing scene sampling:

- [Task catalog](references/task-catalog.md) — atomic/composite coverage and
  registration facts.
- [Scenes, fixtures, and objects](references/scenes-fixtures-objects.md) —
  split mappings, selectors, registries, and asset boundaries.
- [Custom task configuration](references/custom-task-config.md) — `Kitchen`
  subclass lifecycle, object placement schema, and fixture overrides.
- [Troubleshooting](references/troubleshooting.md) — failure diagnosis and
  verification limits.

## Route the request

1. **Pick a task.** Match the requested behavior to an existing atomic task or
   composite activity. Preserve the registered class name; do not invent a Gym
   id when an existing task already expresses the behavior.
2. **Select a scene.** Choose `split="pretrain"`, `"target"`, or `"all"` only
   when the corresponding layout/style and object split is intended. For a
   precise scene, use a layout/style pair and do not also pass the mutually
   exclusive selector families. Run the no-download validator when integer
   selectors are supplied:
   `python scripts/validate_scene_selection.py ...`.
3. **Select assets.** Use the object groups and fixture types required by the
   task, then check that the referenced MJCF, mesh, and texture files exist in
   the user's asset installation. Package imports and YAML registries alone do
   not prove that a reset can load a complete kitchen.
4. **Customize narrowly.** Subclass `Kitchen`, set fixture references in
   `_setup_kitchen_references`, return object configurations from
   `_get_obj_cfgs`, and implement the success predicate. Reuse the source
   placement idioms rather than bypassing the placement initializer.

## Scope boundary

This sub-skill owns task/scene/fixture/object **selection and configuration**.
Generic `create_env`, Gym registration, reset/step, rendering, and rollout
execution belong to `simulation-environments`. Dataset task registries,
recording formats, and playback belong to `datasets-demonstrations`.
Teleoperation and demonstration collection belong to
`teleoperation-and-collection`. Asset downloading is an opt-in user action,
not part of validation; asset conversion pipelines, Blender, VHACD/COACD, and
large generated documentation are intentionally excluded.

The inspected package registers 374 kitchen environment classes. The checkout
contains the Python APIs and scene YAMLs, but it does not contain the complete
external kitchen fixture/object asset collection. A direct constructor probe
was possible; reset was not claimed because fixture XML/mesh prerequisites
were absent. Treat that limitation as an asset gate, not as a task-selection
failure.
