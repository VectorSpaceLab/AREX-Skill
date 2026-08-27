---
name: customization-extensions
description: "Customize MMDetection3D datasets, data pipelines, model
  components, runtime settings, and optional project extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# customization-extensions

Use this sub-skill when the user needs to add or adapt extension code that must be registered and wired into a config.

## Start here
- `references/customization.md` for registry, dataset, pipeline, model, and runtime patterns.
- `references/projects.md` for optional `projects/` packages and compiled extras.
- `references/troubleshooting.md` for import, registry, config, and shape pitfalls.
- `scripts/scaffold_custom_component.py` to generate a starter tree in a caller-provided output directory.

## Typical targets
- new datasets or dataset subclasses
- new point or image transforms
- new backbones, necks, heads, losses, assigners, samplers, or hooks
- custom optimizers, optimizer constructors, schedulers, or runtime hooks
- optional project modules that stay outside the core package

## Routing rules
- If the request is mainly config selection or model zoo lookup, route to the configuration sub-skill.
- If the request is only training, testing, or evaluation command construction, route to the training sub-skill.
- If the request is raw dataset conversion or info-file generation, route to the data-preparation sub-skill.
- If the work needs project-specific extras or optional compilation, keep it here and consult `references/projects.md`.

## Operating rule
Prefer `custom_imports` and generated starter files over editing core package code unless the user explicitly wants an in-tree implementation.
