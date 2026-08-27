---
name: datalayer-and-config
description: "Build and configure Superduper Datalayer connections, schemas,
  tables, documents, and query operations safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datalayer-and-config

Use this sub-skill when a task needs to create or diagnose a Superduper `Datalayer`, choose connection/configuration settings, define `Table`/`Schema`/`Document` data structures, or use the base query API safely.

## Read when

- Building with `superduper(item=None, **kwargs)` or a URI such as `mongomock://...`, `sqlite://...`, `duckdb://...`, `mongodb://...`, `redis://...`, or `inmemory://...`.
- Deciding which fields belong in `Config`, config files, `SUPERDUPER_*` environment variables, metadata/artifact/vector/cluster settings, or backend URIs.
- Creating tables and schemas, inserting documents, filtering/selecting/getting rows, running backend-native `execute`, or using `Datalayer.show/load/apply/drop/select_nearest`.
- Diagnosing local/mongomock smoke failures, missing backend plugins, invalid connection strings, config-file/env mistakes, schema/datatype mismatches, or the declared CLI entry point failing.

## Do not use for

- Model, listener, trainer, metric, application, or deployment construction; use `components-and-workflows`.
- Vector-index recipes, embedding listener wiring, or retrieval flows; use `vector-search-and-retrieval`.
- Optional plugin installation matrices or external-service setup; use `plugins-and-integrations`.

## Operating sequence

1. Choose the backend URI and plugin family first. Prefer `mongomock://...` for a no-service Mongo-like smoke when the MongoDB plugin is installed, or `inmemory://...` for builtin ephemeral metadata/data experiments.
2. Set config before importing `superduper` when config files, env overrides, or artifact-store paths matter. The process-global `CFG` is created at import time.
3. Build the `Datalayer` with `superduper(uri, **kwargs)` or `superduper(**kwargs)`; avoid the console script unless a refreshed version proves `superduper.__main__` exists.
4. Define tables with `Table(identifier, fields={...})`; use `Schema.build`/`Schema.parse` and supported datatype strings for encoded fields.
5. Use `db[table]` query operations for normal data work. Keep destructive calls (`drop`, backend `drop_table`) restricted to scratch databases.
6. If the task only needs a health check, run the bundled smoke helper before writing task logic.

## References and bundled helper

- [Configuration and Datalayer](references/configuration-and-datalayer.md): connection builder behavior, config precedence, backend URI mapping, Datalayer lifecycle, local smoke patterns, and CLI caveat.
- [Query and Data Model](references/query-and-data-model.md): `Document`, `Schema`, `Table`, datatypes, query operations, safe insert/select/update/delete patterns, and vector-query routing notes.
- [Troubleshooting](references/troubleshooting.md): common import, backend, config, secrets, CLI, drop, query, and schema/datatype failures with targeted fixes.
- [superduper_datalayer_smoke.py](scripts/superduper_datalayer_smoke.py): deterministic import/config/Datalayer smoke helper with `--help`, `--check-imports`, and optional `--build-db`.
