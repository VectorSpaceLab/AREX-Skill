# Server Configuration

MemMachine server configuration is YAML-oriented and references resources by
string IDs. The exact file location depends on deployment. In container or CLI
workflows, environment variables such as `MEMORY_CONFIG`, database credentials,
provider keys, and host/port settings can select the active config.

## Startup Modes

```bash
memmachine-server --help
memmachine-server --with-config-api
memmachine-server --stdio
memmachine-mcp-stdio
memmachine-mcp-http --host localhost --port 8080
```

- `--with-config-api` enables server configuration management endpoints.
- `--stdio` or `memmachine-mcp-stdio` is for local MCP stdio clients.
- `memmachine-mcp-http` exposes MCP over HTTP.
- `memmachine-configure` is interactive and may prompt to install/start Neo4j;
  do not run it in non-interactive automation unless the user requested that.

## Minimal Config Skeleton

```yaml
logging:
  path: mem-machine.log
  level: info

episode_store:
  database: profile_storage

episodic_memory:
  long_term_memory:
    backend: event
    embedder: openai_embedder
    reranker: my_reranker_id
    vector_store: event_vector_store
    segment_store: profile_storage
    properties_schema:
      category: str
  short_term_memory:
    llm_model: openai_model
    message_capacity: 500
  long_term_memory_enabled: true
  short_term_memory_enabled: true
  enabled: true

retrieval_agent:
  llm_model: openai_model
  reranker: my_reranker_id

semantic_memory:
  enabled: true
  llm_model: openai_model
  embedding_model: openai_embedder
  database: profile_storage
  config_database: profile_storage

session_manager:
  database: profile_storage

resources:
  databases:
    profile_storage:
      provider: postgres
      config: {}
    event_vector_store:
      provider: qdrant
      config: {}
  embedders:
    openai_embedder:
      provider: openai
      config: {}
  language_models:
    openai_model:
      provider: openai-responses
      config: {}
  rerankers:
    my_reranker_id:
      provider: rrf-hybrid
      config: {}
```

Fill provider/database configs with deployment-specific values. Never paste
secrets into logs or public answers.

## Long-term Memory Backend Choice

| Backend | Required fields | When to choose |
| --- | --- | --- |
| `declarative` | `embedder`, `reranker`, `vector_graph_store` | Graph-backed declarative memory, typically Neo4j/Nebula-style graph storage. |
| `event` | `embedder`, optional `reranker`, `vector_store`, `segment_store`, optional `properties_schema` | VectorStore + SegmentStore event backend; useful when using Qdrant/Milvus/SQLite vector stores with a relational segment store. |

If `backend` is omitted, verify the installed server version's default before
assuming one. When event backend is selected, missing `vector_store` or
`segment_store` is a configuration error.

## Semantic Memory Requirements

When semantic memory is enabled, provide:

- `llm_model`
- `embedding_model`
- `database`
- `config_database`

Optional vector-backed semantic storage may additionally use `storage_backend`,
`feature_store`, `vector_collection`, `vector_dimensions`, and
`vector_similarity_metric`.

## Validation Workflow

1. Validate YAML syntax.
2. Confirm required top-level sections exist.
3. Resolve every resource ID used by memory sections under `resources`.
4. Confirm provider-specific fields are present but do not print secret values.
5. Check optional service availability only after the user permits service
   probes.
6. Run server health against the intended endpoint after startup.

Use the bundled doctor:

```bash
python scripts/server_config_doctor.py --config cfg.yml
```

## Docker Compose And Helm Notes

The public quickstart uses Docker/Docker Compose to run a stack with the
MemMachine app plus storage services such as PostgreSQL/pgvector and Neo4j.
Compose commands can create persistent volumes and may prompt for provider
configuration. Helm is an operator deployment path with equivalent concerns:
ports, secrets, persistent volumes, service health, and provider credentials.

Treat `clean` or volume-removal operations as destructive and ask before
running them.
