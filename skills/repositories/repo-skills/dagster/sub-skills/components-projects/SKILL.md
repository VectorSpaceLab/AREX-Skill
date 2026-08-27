---
name: components-projects
description: "Create and troubleshoot Dagster component-ready projects,
  component scaffolding, Definitions-backed components, component
  YAML/templates, and dg/create-dagster caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Components Projects

Use this sub-skill when a coding agent needs to create or inspect component-ready Dagster projects, scaffold reusable or inline components, load component trees, validate component YAML/templates, test component-built definitions, or explain why `dg`/`create-dagster` is unavailable in a checkout.

## Route Here

- Creating a component-ready project or workspace with `create-dagster`, or comparing that flow with legacy `dagster project` commands.
- Using `dg list`, `dg scaffold`, `dg check yaml`, `dg check toml`, or `dg check defs` for component projects.
- Writing custom classes based on `dagster.components.Component`, `Resolvable`, `Model`, `ComponentLoadContext`, `Scaffolder`, or `scaffold_with`.
- Building definitions from components, including `DefinitionsComponent`, component trees, `defs.yaml`, `component.py`, template variables, and component tests.
- Debugging missing `dg`/`create-dagster` entry points, unpublished dev dependency gaps, component import failures, schema errors, and YAML/template misuse.

## Route Elsewhere

- Core asset, job, `Definitions`, partition, selection, and materialization design: use `../asset-definitions/SKILL.md` if that sub-skill exists.
- General `dagster` CLI execution, `dagster dev`, and non-component local commands: use `../cli-local-development/SKILL.md` if that sub-skill exists.
- Resource/config/env-var modeling outside component YAML/template loading: use `../configuration-resources/SKILL.md` if that sub-skill exists.
- Broad integration libraries and provider-specific components are outside this sub-skill unless the task is about generic component registration or YAML shape.
- Cloud-only `dg` flows requiring `dagster-cloud-cli` are intentionally treated as caveats, not as supported runtime workflows here.

## Start Here

1. Run `python scripts/component_project_doctor.py` from this sub-skill directory, or run the script path from elsewhere, to check `dagster.components` importability and whether `dg`/`create-dagster` command entry points are visible.
2. For new projects, prefer `create-dagster project <path>` or `create-dagster workspace <path>` when that command is installed; use legacy `dagster project scaffold` only for older local project bootstrapping.
3. For component authoring, create custom component types under the project package's `components` module and component instances under the project package's `defs` tree.
4. Validate in layers: `dg check toml`, `dg check yaml`, then `dg check defs`; if `dg` is unavailable, validate Python imports and route full local CLI validation to `../cli-local-development/SKILL.md`.
5. Keep generated component examples minimal and offline-safe; do not run cloud deployment commands or install missing unpublished dev packages unless the user explicitly approves environment mutation.

## References

- [Component project workflows](references/workflows.md) for command patterns, project layout, component scaffolding, YAML/template validation, component tree loading, and component tests.
- [Component API reference](references/api-reference.md) for the public component classes, decorators, schema models, loading helpers, and scaffolding hooks future agents most often need.
- [Component troubleshooting](references/troubleshooting.md) for install/import errors, optional dependency gaps, `dg`/`create-dagster` caveats, schema/template failures, CLI misuse, and test-loading failures.
- [Component project doctor](scripts/component_project_doctor.py) for a safe non-mutating import and command-availability probe.

## Safety Notes

- `create-dagster project --uv-sync` and `create-dagster workspace --uv-sync` can create virtual environments and lockfiles; ask before using install-mutating options.
- `dg dev` starts services; do not use it as a smoke test unless the user asked to run a local server.
- `dg` and `create-dagster` may be absent in source checkouts because their dev dependencies include unpublished or optional packages; diagnose first instead of assuming the project is broken.
