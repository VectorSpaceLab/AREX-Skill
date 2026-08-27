---
name: component-cli
description: "Guides SecretFlow component CLI, component evaluation payloads,
  model export, serving inferencer, and plugin packaging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Component CLI and export

Use this sub-skill when the task is driven by the `secretflow` component CLI or
by component evaluation/export payloads rather than by direct model classes.

## Owns

- `secretflow component` command flows
- component registry inspection and translation
- `comp_eval`, `Registry`, `NodeEvalParam`, `StorageConfig`, `SFClusterConfig`
- component-driven model export and serving model packaging
- plugin entry points and component registration patterns
- input/output validation for component payloads

## Does not own

- device/object creation or federated dataframe setup — use `runtime-data`
- direct preprocessing/statistics/classical ML APIs — use `analytics`
- PSI, Kuscia, TEEU, or deployment orchestration — use `privacy-orchestration`

## Trigger phrases

Use this route when a user asks things like:
- how to list or inspect SecretFlow components
- how to run a component from a NodeEvalParam payload
- how to export a trained component pipeline into a serving package
- how to build or debug a plugin entry point
- why a component id or DistData payload is rejected

## Reading order

1. Read `references/component-cli.md` for the command map and payload flow.
2. Read the root troubleshooting page if the install, protobuf, or entry-point
   path is broken.
3. Use `scripts/component_registry_smoke.py` when you want a tiny no-network
   check that the component registry is alive.
4. Use `scripts/plugin_entry_template.py` as the small reusable plugin entry
   skeleton when the task is about packaging a plugin.

## Workflow

1. Decide whether the question is about the CLI surface itself or about the
   component payloads underneath it.
2. If the task is payload-driven, verify the input/output order first. Most
   component failures here are ordering or metadata problems, not algorithm
   bugs.
3. If the task is an export or serving task, ensure the input pipeline and the
   model component are ordered exactly as the export logic expects.
4. Use the registry smoke helper only to prove that the installation is alive;
   do not treat it as a substitute for a full component payload.

## Common decisions

- Use `component ls` when you need the live registry surface.
- Use `component inspect --all` when you need the public component definitions.
- Use `component translate` when you are working on plugin/component metadata.
- Use `component run` only when you already know the `NodeEvalParam`, storage,
  and cluster inputs are valid.

## Bundled files

- `references/component-cli.md` — CLI map, payload flow, and export notes.
- `scripts/component_registry_smoke.py` — tiny registry import/check helper.
- `scripts/plugin_entry_template.py` — safe plugin entry skeleton adapted from the example plugin.
