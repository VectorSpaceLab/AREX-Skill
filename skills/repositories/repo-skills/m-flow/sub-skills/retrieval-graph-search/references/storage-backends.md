# Storage backends

M-flow retrieval reads four storage layers. A backend switch is not only a search setting: graph, vector, relational metadata, and cache choices must remain compatible with ingestion/memorization and later search.

## Backend layers

| Layer | Default | Used by retrieval for | Runtime config API | Main environment keys |
|---|---|---|---|---|
| Graph | Kuzu | graph projection, Cypher, Episode/Facet/Entity edges | `m_flow.config.set_graph_db_config({...})` | `MFLOW_GRAPH_DATABASE_PROVIDER` or `GRAPH_DATABASE_PROVIDER`, `GRAPH_DATABASE_URL`, credentials |
| Vector | LanceDB | collection search and embedding similarity | `m_flow.config.set_vector_db_config({...})` | `MFLOW_VECTOR_DB_PROVIDER` or `VECTOR_DB_PROVIDER`, `VECTOR_DB_URL`, `VECTOR_DB_KEY` |
| Relational | SQLite | datasets, users, search logs, pgvector connection source | `m_flow.config.set_relational_db_config({...})` | `MFLOW_DB_PROVIDER` or `DB_PROVIDER`, `DB_HOST`, `DB_PORT`, credentials |
| Cache | filesystem/no global cache | conversation/session cache and distributed locks | env/config object | `MFLOW_CACHE_BACKEND`, `CACHE_HOST`, `CACHE_PORT`, credentials |

M-flow settings prefer `MFLOW_`-prefixed variables and also fall back to the bare variable names shown in `.env` examples. Avoid mixing two conflicting versions of the same setting in one environment.

## Supported providers at a glance

| Layer | Provider name | Extra / import hint | Remote connection needed? | Notes |
|---|---|---|---|---|
| Graph | `kuzu` | bundled `kuzu` dependency | no | Embedded graph default; uses local database path. |
| Graph | `kuzu-remote` | `aiohttp`, Kuzu adapter code | yes | REST-backed Kuzu; requires `GRAPH_DATABASE_URL`. |
| Graph | `neo4j` | `mflow-ai[neo4j]` / `neo4j` | yes | Requires Bolt/Neo4j URI and usually username/password. |
| Graph | `neptune` | `mflow-ai[neptune]` / `langchain_aws` | yes | Requires AWS Neptune endpoint prefix expected by adapter. |
| Graph + Vector | `neptune_analytics` | `mflow-ai[neptune]` / `langchain_aws` | yes | Can serve both graph and vector through Neptune Analytics. |
| Vector | `lancedb` | bundled `lancedb` dependency | no | Local vector default. |
| Vector | `pgvector` | `mflow-ai[postgres]` or `[postgres-binary]` | yes | Uses relational Postgres settings for the connection string. |
| Vector | `chromadb` | `mflow-ai[chromadb]` / `chromadb` | usually yes | M-flow adapter uses an HTTP client URL. |
| Vector | `pinecone` | `mflow-ai[pinecone]` / `pinecone` | yes | Uses `VECTOR_DB_KEY` or `PINECONE_API_KEY`; index name from `VECTOR_DB_NAME` or provider env. |
| Vector | `milvus` | `mflow-ai[milvus]` / `pymilvus` | yes | URL/token can come from `VECTOR_DB_URL`/`VECTOR_DB_KEY` or Milvus-specific env. |
| Relational | `sqlite` | bundled `aiosqlite` + SQLAlchemy | no | Default metadata/search-log store. |
| Relational | `postgres` / `postgresql` | `mflow-ai[postgres]` or `[postgres-binary]` | yes | Needed for pgvector and production metadata. |
| Cache | `fs` | stdlib/filesystem adapter | no | Default lightweight cache backend. |
| Cache | `redis` | `mflow-ai[redis]` / `redis` | yes | Needed for shared cache/distributed locks. |

Run the safe probe before changing a live process:

```bash
python scripts/backend_config_probe.py --json
python scripts/backend_config_probe.py --provider neo4j
python scripts/backend_config_probe.py --kind vector --provider pgvector
```

The probe validates provider names and imports only; it does not initialize adapters or test network reachability.

## Switch local defaults to Neo4j + pgvector

Use this when the user has already provisioned Neo4j and PostgreSQL with the pgvector extension. This does not start services.

```python
import m_flow

m_flow.config.set_graph_db_config({
    "graph_database_provider": "neo4j",
    "graph_database_url": "bolt://localhost:7687",
    "graph_database_name": "neo4j",
    "graph_database_username": "neo4j",
    "graph_database_password": "password",
})

m_flow.config.set_relational_db_config({
    "db_provider": "postgres",
    "db_host": "localhost",
    "db_port": "5432",
    "db_name": "mflow_store",
    "db_username": "m_flow",
    "db_password": "m_flow",
})

m_flow.config.set_vector_db_config({
    "vector_db_provider": "pgvector",
})
```

Equivalent environment-style sketch:

```bash
export GRAPH_DATABASE_PROVIDER=neo4j
export GRAPH_DATABASE_URL=bolt://localhost:7687
export GRAPH_DATABASE_NAME=neo4j
export GRAPH_DATABASE_USERNAME=neo4j
export GRAPH_DATABASE_PASSWORD='...'

export DB_PROVIDER=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mflow_store
export DB_USERNAME=m_flow
export DB_PASSWORD='...'

export VECTOR_DB_PROVIDER=pgvector
```

Expected failure signals and fixes:

| Signal | Likely cause | Fix |
|---|---|---|
| `ImportError: neo4j...` | Neo4j extra missing | install the Neo4j optional extra in the active environment. |
| `Missing PGVector credentials` | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, or `DB_PASSWORD` missing | set all relational Postgres fields; pgvector reads them. |
| `ImportError: PGVector dependencies missing` | Postgres extra missing | install `postgres` or `postgres-binary` optional extra. |
| connection refused / authentication failed | external service not running or bad credentials | start service or update URI/credentials; probe cannot validate reachability. |

## ChromaDB / Pinecone / Milvus / Neptune notes

### ChromaDB

```python
m_flow.config.set_vector_db_config({
    "vector_db_provider": "chromadb",
    "vector_db_url": "http://localhost:8000",
    "vector_db_key": "",
})
```

The adapter imports `chromadb` and uses an async HTTP client. If results are empty after a switch, confirm collections were written to the Chroma instance selected by `vector_db_url`; old local LanceDB collections are not automatically copied.

### Pinecone

```python
m_flow.config.set_vector_db_config({
    "vector_db_provider": "pinecone",
    "vector_db_key": "${PINECONE_API_KEY}",
    "vector_db_name": "m_flow",
})
```

The provider can also read `PINECONE_API_KEY` and `PINECONE_INDEX_NAME`. The probe only checks import and key visibility; index existence is a live-service concern.

### Milvus / Zilliz

```python
m_flow.config.set_vector_db_config({
    "vector_db_provider": "milvus",
    "vector_db_url": "http://localhost:19530",
    "vector_db_key": "",
    "vector_db_name": "mflow",
})
```

The provider can also read `MILVUS_URI` and `MILVUS_TOKEN`. Remote Zilliz deployments typically require a token.

### Neptune Analytics

```python
endpoint = "neptune-graph://<GRAPH_ID>"
m_flow.config.set_graph_db_config({
    "graph_database_provider": "neptune_analytics",
    "graph_database_url": endpoint,
})
m_flow.config.set_vector_db_config({
    "vector_db_provider": "neptune_analytics",
    "vector_db_url": endpoint,
})
```

The graph and vector adapters validate endpoint prefixes. `langchain_aws` must be installed and AWS credentials/network routing must be available for live use.

## Cache and session effects

Search completion paths may use conversation-history caching when cache is enabled and a user/session context exists. For shared multi-process deployments:

```bash
export CACHE_BACKEND=redis
export CACHE_HOST=localhost
export CACHE_PORT=6379
export CACHE_USERNAME=''
export CACHE_PASSWORD='...'
```

Filesystem cache is simpler for local work. Redis errors usually affect session cache/distributed-lock behavior, not the pure vector/graph ranking math.

## Migration scripts: reference-only caution

Timestamp migration utilities exist for historical `created_at` repair in Kuzu and LanceDB. Treat them as **reference-only** for search troubleshooting:

- Prefer `--dry-run` when discussing them.
- Do not run them as part of ordinary empty/noisy retrieval diagnosis.
- They can update graph/vector records and should require an explicit user request, backups/snapshots, selected dataset/user scope, and a rollback plan.
- If temporal retrieval is wrong, first inspect whether `created_at`, `mentioned_time_start_ms`, `mentioned_time_end_ms`, and `mentioned_time_text` are present in results and whether `enable_time_bonus` is enabled.

## Backend-change checklist

1. Run `backend_config_probe.py` for provider/import/config visibility.
2. Confirm the target store already contains the memorized collections/graph, or plan a fresh memorize run in the appropriate workflow skill.
3. Run a small `EPISODIC` query with `display_mode="detail"` and `top_k=3`.
4. For `TRIPLET_COMPLETION`, also validate LLM and embedding credentials/endpoints.
5. If only one store was changed, remember old graph/vector data are not automatically migrated between providers.
