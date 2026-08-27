---
name: pipelines-and-nodes
description: "Design, validate, refactor, namespace, tag, slice, inspect, and
  troubleshoot Kedro Node and Pipeline objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kedro Pipelines and Nodes

Use this sub-skill when a task is about Kedro graph authoring: `node()`, `Node`, `Pipeline`, `pipeline()`, namespaces, tags, slicing, graph inspection, modular pipeline functions, `GroupedNodes`, preview payloads, or LLM context nodes.

Stay inside pure graph semantics here. For execution with `kedro run` or runners, read `../runners-and-execution/SKILL.md`; for `DataCatalog`, dataset YAML, credentials, or parameters files, read `../data-catalog-and-config/SKILL.md`; for project scaffolding and `kedro pipeline create/delete`, read `../project-cli-and-sessions/SKILL.md`.

## Start Here

1. Import current Kedro pipeline APIs from `kedro.pipeline`: `node`, `Node`, `Pipeline`, `pipeline`, `GroupedNodes`, and optional experimental preview/LLM helpers.
2. Prefer `pipeline(...)` or `Pipeline(...)` for reusable and namespaced pipelines. Do not import `kedro.pipeline.modular_pipeline`; it is absent in Kedro 1.4.0.
3. Keep node functions pure and make every dataset edge explicit through `inputs`, `outputs`, and `params:` names.
4. Use `pipeline(base_pipeline, inputs=..., outputs=..., parameters=..., namespace=...)` to reuse graph templates without duplicate node or dataset collisions.
5. Use `Pipeline.describe()`, `pipeline.inputs()`, `pipeline.outputs()`, `pipeline.datasets()`, `pipeline.nodes`, `pipeline.grouped_nodes`, `pipeline.group_nodes_by()`, and `pipeline.to_json()` before changing or executing a graph.

## References

- Read `references/api-reference.md` for current signatures, allowed node input/output shapes, graph methods, preview contracts, LLM context nodes, and registry-facing APIs.
- Read `references/workflows.md` for reusable namespaced pipeline templates, modular pipeline structure, graph slicing, registry interactions, and inspection patterns.
- Read `references/troubleshooting.md` when Kedro raises invalid node, duplicate output, circular dependency, namespacing, parameter remapping, preview, or stale-import errors.
- Run `scripts/smoke_pipeline.py --help` to inspect the bundled smoke check, then `scripts/smoke_pipeline.py` to build and run a tiny in-memory pipeline when core Kedro execution dependencies are installed.

## Decision Rules

- Use `node(func, inputs, outputs, name=..., tags=...)` for one callable step; use `Node(...)` only when matching class-based code style.
- Use string inputs/outputs for one dataset, lists for positional arguments or multiple outputs, and dicts when function argument names or returned dictionary keys differ from Kedro dataset names.
- Use `params:name` for single parameters and `parameters` only when the node function should receive the whole parameters dictionary.
- Use pipeline-level `parameters=...` for reusable parameter remapping; never put `params:*` or `parameters` under reusable `inputs=...`.
- Use pipeline-level `namespace=...` to make reused pipelines unique. Explicit `inputs`, `outputs`, and `parameters` mappings expose connection points that should not receive the namespace prefix.
- Use `prefix_datasets_with_namespace=False` only when the namespace is a grouping label for nodes and dataset names must remain unchanged.
- Use node-level `namespace=...` mainly for visual grouping; it prefixes node names but does not behave like pipeline-level dataset remapping.
- Use `pipeline.filter(...)` when several slice conditions must all apply; use `only_nodes_with_tags()` for OR-style tag selection.

## Common Cross-Routes

- If a graph is valid but inputs are missing from the catalog, switch to `../data-catalog-and-config/SKILL.md` for catalog entries or to `../runners-and-execution/SKILL.md` for run selection.
- If a task asks for `kedro run --from-nodes`, `--to-outputs`, `--tags`, `--namespaces`, or `--only-missing-outputs`, use this sub-skill to validate slice semantics, then route command construction to `../runners-and-execution/SKILL.md`.
- If a task asks where to place `create_pipeline()` or how `find_pipelines()` discovers it, read this sub-skill for API requirements and `../project-cli-and-sessions/SKILL.md` for project layout and CLI behavior.
- If LLM context nodes touch real LLM clients, prompt datasets, credentials, or serving endpoints, keep graph declaration here and route dataset/config/runtime concerns to sibling sub-skills.
