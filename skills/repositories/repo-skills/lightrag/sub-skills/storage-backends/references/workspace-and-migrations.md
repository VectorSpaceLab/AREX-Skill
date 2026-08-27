# Workspace and Migrations

Storage work in LightRAG must preserve workspace isolation. A backend selection is not complete until the workspace, embedding model/dimension, and operational preconditions are understood for all four storage categories.

## Workspace Isolation Model

`LightRAG(workspace="...")` passes the workspace to every storage class. The exact isolation mechanism differs by backend family:

| Backend family | Isolation mechanism |
| --- | --- |
| JSON KV / JSON doc-status / NanoVectorDB / NetworkX | Stores files under `working_dir/<workspace>/` when workspace is non-empty; default empty workspace uses `working_dir` directly. |
| PostgreSQL KV/doc-status/vector | Tables are shared across workspaces and filtered by `workspace` columns; primary keys and indexes include workspace. |
| PostgreSQL graph | Graph name is derived from workspace and namespace for non-default workspaces. |
| Qdrant vector | Shared final collections carry a `workspace_id` payload field and tenant payload index. |
| OpenSearch | Index naming and query filters include workspace-specific namespaces. |
| MongoDB / Redis / Neo4j / Memgraph / Milvus | Storage implementations apply their own workspace naming, fields, collection names, keys, or graph namespace conventions. Treat workspace as part of the data identity. |

Use the same logical workspace value across KV, vector, graph, and doc-status categories unless deliberately reading/writing separate tenants. A mismatch can look like missing documents, empty graphs, empty vector search, cache misses, or duplicate indexing.

## Workspace Environment Overrides

Some operational tools and backend implementations support storage-specific workspace environment variables in addition to generic `WORKSPACE` or constructor `workspace` values. Examples include `POSTGRES_WORKSPACE`, `MONGODB_WORKSPACE`, `REDIS_WORKSPACE`, and `OPENSEARCH_WORKSPACE` for cache tools. PostgreSQL client configuration can prefer its workspace setting over the constructor-provided workspace.

When diagnosing workspace issues:

1. Record the constructor `workspace` value or API/server `WORKSPACE` value.
2. Check backend-specific workspace env vars for the selected storage families.
3. Confirm all four categories resolve to the same intended workspace.
4. Check whether old data lives in the default/empty workspace while new data uses an explicit workspace.

Do not merge workspaces by copying files or rows ad hoc. Use backend-aware migration or export/import steps with a backup and a read-only verification pass first.

## Automatic Startup Migrations

`initialize_storages()` calls storage initialization and then runs LightRAG storage migration checks. The migration mixin performs one-shot upgrades when legacy or partial data layouts are detected:

- Entity/relation metadata migration: if the graph has entities/relations and `full_entities` / `full_relations` KV stores are empty, LightRAG backfills document-level entity and relation metadata from graph nodes/edges and processed doc-status chunk lists.
- Chunk tracking migration: if `entity_chunks` or `relation_chunks` stores are empty, LightRAG walks graph nodes/edges and seeds chunk-id tracking stores in batches.

These migrations are startup-time storage writes. Treat the first startup after an upgrade as a controlled maintenance operation: backup data first, avoid concurrent writers, and capture logs.

## Backend-Specific Legacy Migration Notes

### PostgreSQL Vector Tables

`PGVectorStorage` can create model/workspace-specific vector tables and migrate data from legacy tables when it detects matching workspace data. It checks vector dimensions before migration and warns when a new workspace table has no rows, because an unexpected embedding model change can look like a new empty table.

Operational guidance:

- Confirm the embedding function exposes a stable `model_name` and `embedding_dim` before initializing production PostgreSQL vector storage.
- Back up PostgreSQL before first startup after changing vector storage version, embedding model, or workspace naming.
- Verify row counts by workspace after startup; do not assume a new empty table is benign.

### Qdrant Legacy Collections

`QdrantVectorDBStorage` uses final collections with workspace payload isolation and can migrate from legacy collection naming patterns. It detects candidate legacy collections, checks vector dimension compatibility, creates `workspace_id` payload indexes, and migrates when the final collection is newly created and legacy data exists.

The bundled LightRAG tool `prepare_qdrant_legacy_data` exists for preparing legacy-shaped collections for migration testing. It can run in `--dry-run` mode but can also create, clear, or copy Qdrant collections. Treat it as a mutation tool, not a harmless check.

### Milvus Schema Migration

`MilvusVectorDBStorage` has schema/index migration resilience, including retry behavior for transient connection failures and payload-size batching. Migration can create temporary collections, copy records, flush periodically, and rename/drop collections during schema changes. Run this only with a healthy Milvus service and backups.

### File-Backed Local Stores

Local JSON, GraphML, NanoVectorDB, and Faiss-style stores depend on workspace-scoped directories and atomic file writes. Manual file edits are not picked up reliably by a running process. Stop writers and restart after any manual repair.

## Vector Rebuild Tool

LightRAG includes the `lightrag-rebuild-vdb` console script. It restores vector stores from authoritative sources:

- `entities_vdb` from graph nodes.
- `relationships_vdb` from graph edges.
- `chunks_vdb` from text chunks KV storage.

Use it when vector storage drifted from graph/KV sources or after changing embedding model/dimension. It also has a consistency-check mode, but even check mode initializes storages, and initialization can create schemas or run one-time migrations. It is not a pure no-side-effect read.

Preconditions for rebuild:

1. Back up graph, KV, vector, and doc-status stores for the workspace.
2. Stop the LightRAG server and every process that can write the same workspace.
3. Confirm `LIGHTRAG_GRAPH_STORAGE`, `LIGHTRAG_VECTOR_STORAGE`, `LIGHTRAG_KV_STORAGE`, `WORKSPACE`, `WORKING_DIR`, and embedding env/config match the target server configuration.
4. Confirm the embedding function and dimension are the intended post-rebuild values.
5. Prefer check mode before rebuild when deciding whether drift exists.
6. After rebuild, run a small read/query verification before restarting writers.

Do not run rebuild as a bundled runtime check from a skill. It can drop and recreate vector storage.

## LLM Cache Tools

LightRAG includes cache-management scripts for KV-backed LLM caches:

- `lightrag-clean-llmqc`: removes query cache entries for query modes such as `mix`, `hybrid`, `local`, and `global`, while preserving workspace isolation.
- `migrate_llm_cache`: migrates extract/summary-style LLM response cache entries between KV backends while preserving source and target workspace settings.

Both tools instantiate storage and can delete or write cache records. Use them only after confirming the selected KV backend, workspace, batch size, and backup/rollback plan.

Operational checklist:

- Stop writers if cache cleanup/migration could race with active queries or ingestion.
- Confirm source and target KV storage classes and workspace resolution.
- Back up the source KV store.
- For migrations, verify counts before and after; preserve the source until target behavior is validated.
- For cleanup, limit the scope to query cache modes that are safe to invalidate.

## Graph Visualization and Export Notes

LightRAG contains graph visualization tooling under its installed package. Treat graph visualization as a read/export workflow:

1. Initialize or connect to the graph backend for the intended workspace.
2. Export or inspect graph nodes/edges using backend APIs or packaged visualizer entry points.
3. Avoid mutating graph data during visualization.
4. For local `NetworkXStorage`, the graph file is workspace-scoped GraphML under the configured working directory; do not edit it while LightRAG is running.
5. For service graph backends, use backend-native read-only credentials where possible.

Use installed package APIs and these bundled notes for visualization guidance; do not depend on external source-tree assets.

## JSON Prototype to PostgreSQL Migration Pattern

For a difficult migration such as moving a JSON-file prototype to PostgreSQL while preserving workspace isolation:

1. Inventory the current local workspace: KV JSON files, graph GraphML, vector JSON/Faiss files, and doc-status JSON files.
2. Freeze writes and back up the full local working directory.
3. Decide whether to re-index from source documents or migrate existing storage state. Re-index is usually safer if source documents and IDs are available.
4. Configure `PGKVStorage`, `PGVectorStorage`, `PGGraphStorage`, and `PGDocStatusStorage` with the same logical workspace.
5. Initialize storages in a maintenance window and observe startup migrations.
6. If re-indexing, clear the target workspace first only after confirming it is empty or disposable.
7. If preserving cache, use the LLM cache migration tool for cache records rather than copying JSON into PostgreSQL manually.
8. Rebuild vector stores if embedding model/dimension changed or if vectors were not migrated through a supported path.
9. Verify doc-status counts, graph node/edge counts, vector consistency, and sample queries before releasing the new backend.

## Backup-First Destructive Operations

These operations can delete, overwrite, or migrate storage state:

- Vector rebuild: drops each vector storage before upserting rebuilt records.
- Cache cleanup: deletes query cache entries.
- Cache migration: writes target cache records and may rely on source/target workspace resolution.
- Qdrant legacy preparation: can create, clear, and copy collections.
- Storage `drop()` calls and API document clear/delete routes: can delete workspace-scoped data.
- First startup after backend/schema upgrades: can run migrations.

Before any destructive or migration operation, require:

- Backup of every affected backend and workspace.
- No active LightRAG server, ingestion pipeline, background scan, clear/delete job, or external writer for that workspace.
- Confirmed storage class names and workspace values.
- Confirmed embedding model/dimension for vector operations.
- A post-operation read-only verification plan.
