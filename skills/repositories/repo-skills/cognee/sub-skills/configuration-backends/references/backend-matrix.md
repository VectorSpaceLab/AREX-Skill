# Backend and Extra Matrix

Read this when choosing Cognee extras or provider settings. It summarizes the
public configuration options that matter most for a usable install.

## Base install

- Distribution: `cognee`
- Python: `>=3.10,<3.15`
- Base runtime works with the default local stack: SQLite relational storage,
  LanceDB vector storage, and the embedded Ladybug/Kuzu graph layer.

## Common extras and their purpose

| Extra | Purpose | When to install |
| --- | --- | --- |
| `postgres-binary` / `postgres` | PostgreSQL + pgvector backend support | When you want remote Postgres instead of file-backed defaults. Prefer `postgres-binary` for local inspection. |
| `neo4j` | Neo4j graph backend support | When the graph database will be Neo4j. |
| `turso` | libSQL/Turso support | When the relational/vector/graph stores should use Turso/libSQL. |
| `aws` | S3 storage support | When data, system, or cache roots live on S3. |
| `redis` | Redis cache/session support | When you need Redis-backed session/cache behavior. |
| `docs` | Document parsing extras | When the workflow must ingest office/PDF/document formats beyond the core install. |
| `scraping` | Web scraping ingestion | When a workflow ingests pages or crawls web content. |
| `fastembed` | Local embedding models | When you want a local embedding engine instead of remote API embeddings. |
| `ollama` / `huggingface` | Local model support | When running against local model providers or Hugging Face-based local paths. |
| `codegraph` | Code graph extraction | When the workflow analyzes repositories or code structure. |
| `evals` | Evaluation/benchmark tooling | When running benchmark or evaluation workflows. |
| `distributed` | Modal/distributed helpers | When you are using distributed execution paths. |
| `tracing` | OpenTelemetry tracing | When tracing or Langfuse/OTLP integration is selected. |
| `langchain`, `llama-index`, `anthropic`, `azure`, `groq`, `mistral`, `llama-cpp`, `docling`, `deepeval`, `graphiti`, `dlt`, `baml`, `notebook`, `posthog` | Provider or workflow-specific integrations | Only when the selected task explicitly needs that provider or toolchain. |

## Provider defaults and notable settings

### LLM

- `LLM_PROVIDER` defaults to `openai`.
- `LLM_MODEL` defaults to `openai/gpt-5-mini`.
- `LLM_API_KEY` is required for cloud-backed extraction/search workflows.
- `LLM_RATE_LIMIT_*` controls request budgets.
- `STRUCTURED_OUTPUT_FRAMEWORK` defaults to `instructor`.
- Local providers such as `ollama` and `llama_cpp` may need extra rate-limit
  tuning because they process requests serially.

### Embeddings

- `EMBEDDING_PROVIDER` defaults to `openai`.
- `EMBEDDING_MODEL` defaults to `openai/text-embedding-3-large`.
- `EMBEDDING_DIMENSIONS` is auto-derived when possible, but non-default models
  may need an explicit dimension to avoid shape mismatches.
- `HUGGINGFACE_TOKENIZER` may be needed when Cognee cannot infer a tokenizer.

### Graph backend

- Source-level defaults are file-backed and local.
- `GRAPH_DATABASE_PROVIDER` may be `ladybug`, `kuzu`, `neo4j`, `postgres`, or
  `turso` depending on the selected workflow.
- `GRAPH_DATASET_DATABASE_HANDLER` should align with the chosen graph provider
  when access control or multi-user isolation is on.
- `graph_database_subprocess_enabled` can isolate embedded graph workers.

### Vector backend

- `VECTOR_DB_PROVIDER` defaults to `lancedb`.
- `VECTOR_DATASET_DATABASE_HANDLER` should align with `pgvector` or `turso`
  when those providers are selected.
- `vector_pool_args` is JSON for pgvector connection tuning.

### Relational backend

- `DB_PROVIDER` defaults to `sqlite`.
- `db_provider` may be `sqlite`, `postgres`, or `turso`.
- `DATABASE_CONNECT_ARGS` and `POOL_ARGS` must be JSON dictionaries.

### Storage and cache

- `STORAGE_BACKEND` may be `local` or `s3`.
- `CACHE_BACKEND` may be `sqlite`, `postgres`, `redis`, `fs`, or `tapes`.
- For S3-backed roots, configure cache and database paths intentionally rather
  than assuming a local filesystem path will work.

### Security and access control

- `ENABLE_BACKEND_ACCESS_CONTROL` turns on the multi-tenant posture.
- `REQUIRE_AUTHENTICATION` must be aligned with backend access control.
- `ALLOW_HTTP_REQUESTS`, `ALLOW_CYPHER_QUERY`, and API-key hashing switches are
  privileged settings that should be documented when a workflow uses them.

## Practical selection rule

Choose the smallest extra set that matches the selected workflow. Do not install
all extras by default. If a workflow needs a service or credentialed provider,
document it as an optional requirement rather than a default assumption.
