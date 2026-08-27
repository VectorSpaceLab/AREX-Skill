# Storage Troubleshooting

Use this guide to diagnose LightRAG storage issues from installed package behavior and bundled references. Start by identifying the selected classes for all four categories, the workspace, and whether the task is read-only or can mutate storage.

## Quick Triage

1. Print or inspect the selected class names: `kv_storage`, `vector_storage`, `graph_storage`, and `doc_status_storage`.
2. Verify class names are compatible with their category using `../scripts/check_storage_registry.py`.
3. Confirm optional storage dependencies are installed for non-default backends.
4. Confirm external services are reachable and required env vars are set.
5. Confirm all categories use the intended workspace.
6. If vector search is wrong or empty, check embedding model/dimension changes before assuming graph/KV corruption.
7. Before cleanup, migration, rebuild, or clear operations, stop writers and back up storage.

## Missing Optional Dependencies

### Symptoms

- `ModuleNotFoundError` for packages such as `redis`, `neo4j`, `pymilvus`, `pymongo`, `asyncpg`, `pgvector`, `qdrant_client`, `opensearchpy`, or `faiss`.
- Runtime messages about dynamic package installation failing.
- Storage class import fails for an optional backend while local defaults import successfully.

### Likely Cause

The base package supports local defaults, but optional service backends require additional dependencies. Some implementations use dynamic installation helpers, but offline, restricted, or reproducible environments should preinstall optional groups.

### Fix

- For storage backends only, install the package with the `offline-storage` extra.
- For an API deployment with storage and providers, install the `offline` extra.
- In offline environments, download wheels in an online staging environment and install from the local package cache.
- Avoid relying on dynamic installs at runtime for production services.

## Invalid Backend Name or Category Mismatch

### Symptoms

- `ValueError: Storage implementation '...' is not compatible with ...`.
- A class exists in the module mapping but fails category validation.
- A typo such as `PostgresKVStorage` instead of `PGKVStorage`.

### Fix

Use exact registry names from [storage-reference.md](storage-reference.md). Common gotchas:

- Use `PGKVStorage`, `PGVectorStorage`, `PGGraphStorage`, and `PGDocStatusStorage`, not `Postgres...` names.
- Use `Neo4JStorage` with capital `J` as registered.
- `ChromaVectorDBStorage` and `AGEStorage` may appear in module mappings but are not compatible registry choices for the current category list.
- Run `python scripts/check_storage_registry.py --json` from this sub-skill directory to inspect the installed registry safely.

## Missing Environment Variables

### Symptoms

- Startup warnings about missing env vars for selected storage classes.
- Connection parameters falling back to defaults such as local hostnames.
- Service authentication or database selection is wrong.

### Required Registry Vars

| Backend | Required env vars according to registry |
| --- | --- |
| Redis KV/doc-status | `REDIS_URI` |
| PostgreSQL KV/vector/graph/doc-status | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` |
| MongoDB KV/vector/graph/doc-status | `MONGO_URI`, `MONGO_DATABASE` |
| Neo4j graph | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` |
| Memgraph graph | `MEMGRAPH_URI` |
| Milvus vector | `MILVUS_URI`, `MILVUS_DB_NAME` |
| Qdrant vector | `QDRANT_URL` |
| OpenSearch family | `OPENSEARCH_HOSTS` |

Some implementations also read optional host, port, SSL, workspace, index, token, or tuning env vars. The registry requirements are the minimal fail-fast hints, not the full production configuration.

## Service Connection Failures

### Symptoms

- Connection refused, timeout, authentication failed, TLS/certificate errors, database not found, collection/index creation failures.
- Startup works for local defaults but fails when switching to a service backend.

### Diagnosis

- Confirm the storage class family matches the running service.
- Confirm service URL/host env vars point to the service from the runtime environment, not from another container or host context.
- Confirm credentials and database names are valid.
- Confirm optional service capabilities: PostgreSQL vector extension/index support for `PGVectorStorage`, OpenSearch k-NN for `OpenSearchVectorDBStorage`, Milvus version support for selected index types, and Qdrant collection access for `QdrantVectorDBStorage`.
- Confirm the selected workspace is valid and not silently overridden by storage-specific workspace env vars.

### Fix

- Start with one category or a minimal read-only import check before enabling all four service-backed categories.
- For all-PostgreSQL deployments, verify normal PostgreSQL connectivity before adding vector storage and graph storage.
- For OpenSearch, verify k-NN support before expecting vector queries to work.
- For Milvus, use supported index and metric values for the running Milvus version.

## Vector Dimension Mismatch

### Symptoms

- Vector backend reports dimension mismatch during startup, collection/table setup, upsert, or query.
- Queries return no relevant chunks after an embedding model change.
- New vector table/collection appears empty after changing `embedding_func.model_name` or `embedding_dim`.
- PostgreSQL/Qdrant migration warnings mention empty workspace data or vector dimension compatibility.

### Cause

Stored vectors are tied to the embedding model and dimension. Changing embedding provider, model, dimension, asymmetric settings, or wrapper metadata can make old vectors incompatible with new queries.

### Decision: Rebuild vs Clear

Choose rebuild when:

- Graph and text chunk KV stores are still authoritative and healthy.
- You want to preserve documents, graph, and cache while regenerating vector embeddings.
- The embedding function now produces the intended dimension and can re-embed all records.

Choose clear/re-index when:

- Source documents are available and a clean rebuild from ingestion is simpler.
- Graph/KV/doc-status are inconsistent or untrusted.
- Workspace was polluted by test data or wrong embedding settings.
- The storage backend migration path is unclear.

Preconditions for either path:

- Back up affected storage first.
- Stop all writers for the workspace.
- Confirm the intended embedding model and dimension.
- Run a read-only consistency check where available.
- Verify sample queries after the operation.

Do not copy vector files/tables between embedding dimensions.

## Workspace Collisions and Empty Results

### Symptoms

- Data inserted in one process is invisible in another.
- Doc-status shows no documents but KV/graph/vector storage has data elsewhere.
- Query modes using graph/vector return empty context.
- Cache cleanup or migration affects an unexpected tenant.

### Causes

- Constructor `workspace`, API/server `WORKSPACE`, and storage-specific workspace env vars disagree.
- A service backend uses a default workspace while file-backed storage uses an explicit directory, or vice versa.
- Old data was created in the empty/default workspace and new code uses a named workspace.
- Two test runs share the same workspace against the same service.

### Fix

- Normalize on one explicit workspace per application/test tenant.
- Remove or align backend-specific workspace env vars such as `POSTGRES_WORKSPACE`, `MONGODB_WORKSPACE`, `REDIS_WORKSPACE`, or `OPENSEARCH_WORKSPACE` when they conflict with the intended workspace.
- For tests, generate unique workspace names and clean only that workspace.
- For migration, verify counts by workspace before and after.

## Destructive Operation Preconditions

### Operations That Need Maintenance Windows

- `lightrag-rebuild-vdb`: may drop vector storages and re-embed records.
- `lightrag-clean-llmqc`: deletes query cache entries.
- `migrate_llm_cache`: writes cache records to a target backend/workspace.
- `prepare_qdrant_legacy_data`: can create, clear, and copy Qdrant collections.
- Storage `drop()` or API document clear/delete operations.
- First startup after storage schema changes or package upgrades that trigger migrations.

### Required Preconditions

- A verified backup or snapshot exists for every affected backend.
- The LightRAG server and all background ingestion/query writers for the workspace are stopped, unless the operation is explicitly read-only and safe with live traffic.
- The target workspace and storage class names are recorded.
- Embedding model/dimension is recorded for vector operations.
- A rollback and verification plan exists.

If any precondition is missing, pause and gather it before mutating storage.

## Qdrant Legacy Preparation Pitfalls

### Symptoms

- Legacy Qdrant collections are unexpectedly copied, cleared, or migrated.
- Data from multiple workspaces appears in one target.
- Dry-run output differs from actual mutation plan.

### Guidance

- Use dry-run first.
- Confirm source and target collection names and workspace filters.
- Never treat an unknown legacy `workspace_id` detection result as safe to clear.
- Back up Qdrant collections before running preparation or migration tools.
- Use `QDRANT_URL` and any optional Qdrant credential setting for the intended service only.

## LLM Cache Cleanup/Migration Pitfalls

### Symptoms

- Query results change after cleanup.
- Expected cache entries are missing after migration.
- Cleanup affects the wrong workspace.

### Guidance

- Query cache cleanup intentionally removes mode-specific query/keyword cache entries; it should not be used as a general KV cleaner.
- LLM response cache migration should preserve source until target counts and sample reads are validated.
- Workspace resolution differs by storage family; confirm source and target workspace values explicitly.
- Cache mutation can run while the server is stopped to avoid races with active query writes.

## Graph Export/Visualization Issues

### Symptoms

- Graph visualization misses recent nodes/edges.
- Local GraphML appears stale while server is running.
- Service graph export returns another workspace's data.

### Fix

- Ensure pending ingestion has completed and storage callbacks have flushed before exporting.
- Stop writers or use read-only credentials for export.
- Confirm workspace filters or graph names.
- For local `NetworkXStorage`, restart or export after the writer commits; do not edit GraphML manually during runtime.

## Safe Registry Check

The bundled script is intentionally read-only:

```bash
python scripts/check_storage_registry.py
python scripts/check_storage_registry.py --json
```

It imports `lightrag.kg`, reads registry dictionaries, verifies category compatibility for registered implementations, and checks whether console scripts are discoverable through package metadata. It does not instantiate storage classes, connect to services, create schemas, import optional service modules, or mutate storage.
