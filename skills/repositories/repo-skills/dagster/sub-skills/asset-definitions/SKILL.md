---
name: asset-definitions
description: "Model, validate, test, and troubleshoot Dagster assets, jobs,
  Definitions, partitions, asset checks, and local materialization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Asset Definitions

Use this sub-skill when the user is working with Dagster software-defined assets, multi-assets, asset checks, jobs, ops/graphs, partitions/backfills, `Definitions`, asset selection, metadata, or local definition tests.

## Route Here

- Defining `@asset`, `@multi_asset`, `@asset_check`, `@op`, `@graph`, or `@job` code.
- Assembling `Definitions` with assets, jobs, asset checks, and module-loaded definitions.
- Creating asset jobs with `define_asset_job`, `AssetSelection`, groups, tags, owners, kinds, code versions, or metadata.
- Debugging asset dependencies, missing upstream assets, selection/subsetting, partition keys, backfill policy, or local materialization failures.
- Testing definitions with `materialize`, `materialize_to_memory`, `Definitions.resolve_job_def`, and small in-memory smoke checks.

## Route Elsewhere

- Resource construction, config schemas, `ConfigurableResource`, IO managers, secrets, and environment variables: use `../configuration-resources/SKILL.md`.
- Schedules, sensors, automation conditions, freshness sensors, or daemon-driven automation: use `../automation-schedules-sensors/SKILL.md`.
- `dagster`, `dg`, project scaffolding, webserver, and CLI run commands: use `../cli-local-development/SKILL.md`.
- Deployment, code locations, run launchers, executors, and production operations: use `../deployment-operations/SKILL.md`.

## Start Here

1. Read `references/workflows.md` for common asset definition, selection, partition, and testing workflows.
2. Read `references/api-reference.md` for the public APIs and patterns most often needed in agent-generated Dagster code.
3. Read `references/troubleshooting.md` when imports, Definitions validation, selection, materialization, or partitioned backfills fail.
4. Use `scripts/validate_defs_smoke.py --help` or run it against a user module/file to perform a safe local Definitions smoke check.

## Fast Triage

- Prefer `import dagster as dg` in examples so public APIs are clearly namespaced.
- Use function parameters or `deps=[...]` for asset dependencies; use `AssetIn` only when remapping input names, keys, partitions, or metadata.
- Use `Definitions(assets=[...], jobs=[define_asset_job(...)], asset_checks=[...])` as the unit loaded by tools and tests.
- Use `materialize_to_memory([...])` for small pure-Python tests; avoid it when assets require persistent IO managers or external services.
- For unresolved asset jobs from `define_asset_job`, use `Definitions.resolve_job_def(name)` rather than assuming `get_job_def` returns a concrete job without resolution.
