---
name: component-runtime
description: "Inspect FATE component CLI commands, component descriptors, task
  schema, and custom component discovery without running service-backed jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Component Runtime

Use this sub-skill when you need to inspect, explain, or smoke-check the local FATE component runtime exposed by `python -m fate.components`.

## Covers
- `python -m fate.components` and the `component` group.
- Exact command spellings, including the hyphenated `task-schema` command.
- Built-in component descriptors, role sets, stage support, and artifact shapes.
- `desc`, `list`, `task-schema`, and `artifact-type` as safe probes.
- Third-party component discovery via entry points.
- Developer-facing component guide material for authoring new components.

## Boundaries
- Do not use this sub-skill for service-backed pipeline training/predict recipes; use `../pipeline-workflows/SKILL.md`.
- Do not use it for direct module launcher flows; use `../local-launchers/SKILL.md`.
- Do not use it for deployment or runtime prerequisites; use `../deployment/SKILL.md`.
- Treat `execute` and `cleanup` as reference-only unless a live config/backend is explicitly available.
- The top-level `python -m fate.components` CLI also exposes a `test` group, but this sub-skill stays on component inspection.

## Start here
1. Read `references/component-cli.md` for the exact CLI surface and save-file behavior.
2. Read `references/component-catalog.md` for the built-in component families and artifact shapes.
3. Read `references/task-schema.md` when validating `TaskConfigSpec` or debugging config mismatches.
4. Read `references/component-development.md` for custom component discovery, stage support, and guide points.
5. Read `references/troubleshooting.md` for missing `pkg_resources`/`setuptools`, unknown names, unsupported stages, entry-point failures, and schema confusion.
6. Run `scripts/check_component_cli.py` in a Python environment that already has FATE installed.

## Related links
- `../deployment/SKILL.md`
- `../pipeline-workflows/SKILL.md`
- `../local-launchers/SKILL.md`
