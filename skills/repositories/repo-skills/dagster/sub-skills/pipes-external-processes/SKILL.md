---
name: pipes-external-processes
description: "Integrate Python and non-Python external processes with Dagster
  using dagster-pipes, open_dagster_pipes, PipesSubprocessClient, loaders,
  message writers, logs, materializations, checks, and custom messages."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pipes External Processes

Use this sub-skill when external Python scripts, non-Python executables, notebooks, Spark jobs, or service-launched processes need to communicate back to Dagster through the Dagster Pipes protocol.

## Route Here

- Retrofitting external code to call `dagster_pipes.open_dagster_pipes()` and emit messages without importing `dagster`.
- Launching a local subprocess from a Dagster asset with `dagster.PipesSubprocessClient` and returning `get_materialize_result()`, `get_results()`, `get_asset_check_result()`, or `get_custom_messages()`.
- Choosing context and message transport pieces such as env vars vs CLI args, default file/stdout writers, temp-file readers, and blob-store writers.
- Reporting external logs, asset materializations, asset checks, custom messages, rich metadata dictionaries, partition context, run metadata, and extras.
- Debugging missing `DAGSTER_PIPES_*` bootstrap params, loader mismatches, duplicate materialization messages, closed contexts, or optional cloud transport dependencies.

## Route Elsewhere

- Designing the Dagster asset graph, `@asset`, `@multi_asset`, `@asset_check`, `Definitions`, and asset selections: use `../asset-definitions/SKILL.md`.
- Resource/config/secret modeling around subprocess credentials and environment variables: use `../configuration-resources/SKILL.md`.
- Dagster CLI execution, `dagster dev`, `dg`, project scaffolding, and code-location validation: use `../cli-local-development/SKILL.md`.
- Service-specific Pipes clients for Databricks, AWS, GCP, Kubernetes, or Spark libraries: use their integration-specific skill if present; otherwise treat this sub-skill as the generic protocol foundation only.

## Start Here

1. Read `references/workflows.md` for subprocess integration, external script retrofits, non-Python message emission, custom messages, and loader/writer choices.
2. Read `references/api-reference.md` for public `dagster_pipes` and `dagster` Pipes APIs, message payload shapes, and metadata formats.
3. Read `references/troubleshooting.md` for import failures, optional dependencies, missing bootstrap params, CLI/API misuse, and protocol-specific failures.
4. Run `python scripts/pipes_external_smoke.py --help` from this sub-skill directory, or `python scripts/pipes_external_smoke.py --inactive-demo`, to verify safe external-side behavior without launching Dagster.

## Fast Triage

- External code should usually import only `dagster_pipes`, not `dagster`; Dagster-side asset code imports `dagster as dg`.
- `open_dagster_pipes()` defaults to env-var params, default context loading, and default message writing; use `PipesCliArgsParamsLoader()` when the launcher passes `--dagster-pipes-context` and `--dagster-pipes-messages`.
- Return or yield the completed invocation results on the Dagster side; otherwise Pipes messages may be received but never surfaced as Dagster events.
- For multi-assets, pass `asset_key=` explicitly and materialize each asset key at most once in a single Pipes invocation.
- Cloud/blob writers and loaders are optional patterns; do not assume S3, GCS, Azure, DBFS, Spark, or Databricks packages are installed unless the user environment proves them.
