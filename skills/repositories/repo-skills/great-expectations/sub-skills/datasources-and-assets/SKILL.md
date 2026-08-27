---
name: datasources-and-assets
description: "Connect GX Core data sources, data assets, batch definitions, and
  optional backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datasources and Assets

Use this sub-skill when a task needs to connect GX Core to data before suites, validations, or checkpoints can run. It covers fluent datasource factories, dataframe/file/SQL assets, batch definitions, batch parameters, and optional backend dependency troubleshooting.

## Start Here

1. Create or retrieve a context first; read `../contexts-and-configuration/SKILL.md` when the task involves file projects, ephemeral contexts, config variables, or Cloud mode.
2. Choose a datasource family and asset type using `references/fluent-datasource-api.md`.
3. Add a batch definition and learn the required `batch_parameters` from `references/batch-definitions.md`.
4. If a backend import, credential, connection, or storage error appears, read `references/optional-backends.md` and `references/troubleshooting.md` before changing code.

## Bundled References and Scripts

- Read `references/fluent-datasource-api.md` to choose `context.data_sources` CRUD methods, fluent datasource factories, pandas/filesystem/SQLite/SQL assets, and table/query patterns.
- Read `references/batch-definitions.md` to define dataframe, file, directory, SQL table/query batches and diagnose required batch parameter keys.
- Read `references/optional-backends.md` before using Spark, cloud storage, warehouses, SQLAlchemy drivers, credentials, or backend-specific extras.
- Read `references/troubleshooting.md` when datasource creation, asset discovery, batch lookup, pandas reader options, SQL queries, or credentials fail.
- Run `scripts/smoke_datasource_asset.py --help` to inspect a safe local smoke helper; run it to prove that an ephemeral context can create pandas dataframe and local CSV filesystem assets without network or credentials.

## Routing Boundaries

- For context selection, config variables, and project persistence, use `../contexts-and-configuration/SKILL.md`.
- For expectation classes, suites, row conditions, and custom expectations, use `../expectations-and-suites/SKILL.md` after a batch is available.
- For running validations, passing `batch_parameters`, result formats, and unexpected rows, use `../validations-and-results/SKILL.md`.
- For checkpoints, actions, notifications, and Data Docs, use `../checkpoints-actions-and-data-docs/SKILL.md` after validations are defined.

## Default Workflow

1. Select the smallest backend that matches the data: `add_pandas` for in-memory dataframes, `add_pandas_filesystem` for local/network files, `add_sqlite` for SQLite, or `add_sql`/warehouse factories for other SQL engines.
2. Add an asset: dataframe assets use `add_dataframe_asset`; filesystem assets use file reader assets such as `add_csv_asset`, `add_excel_asset`, or `add_parquet_asset`; SQL assets use `add_table_asset` or `add_query_asset`.
3. Add a batch definition on the asset, not on the context. Use whole-data definitions for one batch, regex or column partition helpers for recurring batches, and stable names for validation reuse.
4. Inspect `asset.get_batch_parameters_keys(partitioner=batch_definition.partitioner)` and call `batch_definition.get_batch(batch_parameters=...)` with only those keys.
5. Hand the resulting `BatchDefinition` to validation code rather than embedding datasource setup inside suites or checkpoints.
