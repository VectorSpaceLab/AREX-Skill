---
name: storage-backends
description: "Configure and troubleshoot LightRAG storage backends, workspace
  isolation, migrations, vector rebuilds, cache tools, and safe operational
  preconditions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightRAG Storage Backends

Use this sub-skill when a task involves LightRAG KV, vector, graph, or document-status storage selection, migration, workspace isolation, backend optional dependencies, vector rebuilds, LLM cache cleanup/migration, Qdrant legacy preparation, or graph export/visualization planning.

## Route by Task

- Choose or wire storage classes: use [storage-reference.md](references/storage-reference.md) for exact backend names, categories, constructor arguments, environment selection, optional dependency groups, and service prerequisites.
- Preserve workspace isolation or move data between backends: use [workspace-and-migrations.md](references/workspace-and-migrations.md) for workspace behavior, automatic startup migrations, backup-first operational tooling, and graph export notes.
- Diagnose failures: use [troubleshooting.md](references/troubleshooting.md) for missing optional dependencies, service connection failures, vector dimension mismatches, workspace collisions, and destructive-operation preconditions.
- Verify an installed LightRAG package exposes the expected registry safely: run `python scripts/check_storage_registry.py` from this sub-skill directory or pass `--json` for machine-readable output.

## Boundaries

- This sub-skill covers storage backend names, four storage categories, workspace behavior, `vector_db_storage_cls_kwargs`, backend extras, service requirements, migration/rebuild/cache tools, and destructive cautions.
- For insert/query application flow, use the core LightRAG skill area rather than this storage sub-skill.
- For embedding-provider model choice and embedding dimension source, use the LLM/provider skill area; this sub-skill only explains storage implications after a dimension changes.
- For API server environment orchestration, use the API/server skill area; this sub-skill mentions storage env vars only to support backend selection and diagnostics.
- For document-status content semantics from parser and ingestion flows, use the document pipeline skill area; this sub-skill treats doc-status as a storage category.

## Safe Defaults

- Local prototype: `JsonKVStorage`, `NanoVectorDBStorage`, `NetworkXStorage`, `JsonDocStatusStorage`.
- Single external database for all four categories: PostgreSQL classes (`PGKVStorage`, `PGVectorStorage`, `PGGraphStorage`, `PGDocStatusStorage`) with PostgreSQL service and vector extension support.
- Mixed storage is allowed, but keep workspace names, embedding dimensions, and operational windows consistent across all selected categories.
- Never run rebuild, cleanup, migration, legacy-preparation, drop, or clear operations while a LightRAG server, ingestion pipeline, or another writer is active for the same workspace.
