# Configuration Guide

This guide distills Cognee's runtime configuration surface. It is intentionally
self-contained: use it without opening the source repository or copying any
machine-specific path.

## Install and Python range

Cognee targets Python `>=3.10,<3.15`.

Recommended base install:

```bash
python -m pip install "cognee"
```

Add optional extras only for selected capabilities, for example:

```bash
python -m pip install "cognee[postgres-binary]"  # Postgres + pgvector client deps
python -m pip install "cognee[neo4j]"            # Neo4j graph backend
python -m pip install "cognee[fastembed]"        # local fastembed embeddings
python -m pip install "cognee[aws]"              # S3 storage/input support
python -m pip install "cognee[redis]"            # Redis session/cache backend
```

See [backend-matrix.md](backend-matrix.md) for the complete extras matrix and
provider-specific environment variables.

## Configuration precedence and timing

Cognee configuration is pydantic-settings based. Most config classes read the
process environment and `.env` file when their singleton/config object is first
created. In scripts, notebooks, service processes, and tests:

1. Set environment variables before importing `cognee` when possible.
2. Use `cognee.config` setters for runtime overrides inside the same process.
3. Avoid mixing different embedding dimensions or database providers against an
   existing store without rebuilding or isolating that store.
4. For long-running services, restart the service after changing `.env` values
   unless the value was set via an explicit `cognee.config` setter in that same
   process.

Minimal programmatic pattern:

```python
import os
from pathlib import Path

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "openai/gpt-5-mini")
os.environ.setdefault("EMBEDDING_MODEL", "openai/text-embedding-3-large")

import cognee

base = Path.cwd() / ".cognee-runtime"
cognee.config.data_root_directory(str(base / "data"))
cognee.config.system_root_directory(str(base / "system"))
cognee.config.set_vector_db_provider("lancedb")
cognee.config.set_graph_database_provider("kuzu")
```

For ingestion/search workflows after configuration is ready, route to
[core-memory](../../core-memory/SKILL.md).

## Environment template tiers

Cognee's environment template is organized into four tiers.

### Tier 1: quick start

Set only an LLM key when using the default OpenAI-compatible cloud setup:

```bash
LLM_API_KEY="replace-with-a-real-secret"
```

Do not commit real keys. If embeddings use the same provider, the embedding
engine can fall back to `LLM_API_KEY` when `EMBEDDING_API_KEY` is unset.

### Tier 2: common overrides

Common values users change first:

```bash
LLM_PROVIDER="openai"
LLM_MODEL="openai/gpt-5-mini"
LLM_ENDPOINT=""

EMBEDDING_PROVIDER="openai"
EMBEDDING_MODEL="openai/text-embedding-3-large"
EMBEDDING_DIMENSIONS=3072

DB_PROVIDER="sqlite"
GRAPH_DATABASE_PROVIDER="kuzu"
VECTOR_DB_PROVIDER="lancedb"
```

Set `HUGGINGFACE_TOKENIZER` for local or OpenAI-compatible embedding models when
Cognee cannot infer a tokenizer that matches the embedding model. A mismatched
tokenizer can skew chunk-size and dry-run estimates.

### Tier 3: subsystem details

Use only the subsections that match the selected backend:

- LLM structured output framework and rate limits.
- Per-stage LLM routing for extraction, summarization, and query.
- Embedding endpoint, key, dimensions, batch size, and rate limits.
- Root directories and storage backend (`local` or `s3`).
- Relational, graph, vector, and migration database connection details.
- Dataset queue and database-adapter cache sizing.
- Security posture: backend access control, authentication, local file access,
  HTTP requests, Cypher query permission, API key hashing, and JWT secrets.
- Session cache (`sqlite`, `postgres`, `redis`, `fs`, `tapes`).
- Tracing and Langfuse-over-OTLP integration.
- Local providers such as Ollama and llama.cpp.

### Tier 4: provider recipes

Provider recipes supply consistent variable groups for Azure OpenAI, Ollama,
OpenRouter/custom OpenAI-compatible endpoints, DeepInfra, and MCP sampling.
Use them as patterns; never paste real keys into shared notes.

## `cognee.config` runtime setters

`cognee.config` is a namespace of static setters. The generic
`cognee.config.set(key, value)` maps common keys to specific setters and falls
back to embedding config fields when valid.

### Root directories

| Setter | Effect |
|---|---|
| `data_root_directory(path)` | Sets where ingested input files/data are stored. |
| `system_root_directory(path)` | Sets the system directory and cascades dependent default database paths. For LanceDB, it resets the default LanceDB URL under the new system database directory. |
| `monitoring_tool(tool)` | Sets the observability hook. |

When using local filesystem stores, prefer stable absolute directories for
service deployments. When using S3 roots, also configure S3 storage and cache
settings from [backend-matrix.md](backend-matrix.md).

### LLM settings

| Setter | Typical use |
|---|---|
| `set_llm_provider(provider)` | First-class provider such as `openai`, `anthropic`, `azure`, `mistral`, `ollama`, `llama_cpp`, `gemini`, `bedrock`, `custom`, or `mcp-sampling`. |
| `set_llm_model(model)` | Model id. Prefixes such as `openai/...` or `anthropic/...` can infer provider only when the prefix is known. |
| `set_llm_endpoint(url)` | Custom endpoint for Azure, local servers, or OpenAI-compatible gateways. |
| `set_llm_api_key(secret)` | API key; do not log or print. |
| `set_llm_config(dict)` | Bulk update of any `LLMConfig` field, including temperature, streaming, rate limits, fallback, BAML, stage routing, and provider-specific fields. |

Important `LLMConfig` fields:

- `structured_output_framework`: `instructor` by default; alternatives include
  `baml` and `litellm_native`.
- `llm_provider`, `llm_model`, `llm_endpoint`, `llm_api_key`,
  `llm_api_version`.
- Stage overrides: `llm_extraction_*`, `llm_summarization_*`, `llm_query_*`.
  These let a cheaper/local model handle extraction while query or summarization
  uses a stronger model.
- Rate limits: `llm_rate_limit_enabled`, `llm_rate_limit_requests`,
  `llm_rate_limit_interval`, `llm_rate_limit_tokens`, `auto_rate_limit`.
  Local serial providers such as Ollama, llama.cpp, and LM Studio-style model
  prefixes use a lower default request budget when not explicitly configured.
- `llama_cpp_model_path`, `llama_cpp_n_ctx`, `llama_cpp_n_gpu_layers`,
  `llama_cpp_chat_format` for llama.cpp.
- `fallback_model`, `fallback_api_key`, `fallback_endpoint` for fallback calls.
- `llm_args` for JSON-serializable provider kwargs.

Provider inference rule: if `LLM_PROVIDER` is not explicitly set and
`LLM_MODEL` has a slash prefix, the prefix must be a known provider. Unknown
prefixes such as many gateway names must set `LLM_PROVIDER="custom"`.

### Embedding settings

| Setter | Typical use |
|---|---|
| `set_embedding_provider(provider)` | `openai`, `fastembed`, `ollama`, `openai_compatible`, or another LiteLLM-supported provider. |
| `set_embedding_model(model)` | Embedding model id. |
| `set_embedding_dimensions(dim)` | Positive integer. Use this when auto-detection cannot identify the model dimension. |
| `set_embedding_endpoint(url)` | Endpoint for local/OpenAI-compatible embedding services. |
| `set_embedding_api_key(secret)` | Separate embedding key; falls back to LLM key in common cases. |
| `set_embedding_config(dict)` | Bulk update of embedding fields. `embedding_dimensions` is coerced and validated. |

Important `EmbeddingConfig` fields:

- `embedding_provider`, `embedding_model`, `embedding_dimensions`,
  `embedding_endpoint`, `embedding_api_key`, `embedding_api_version`.
- `embedding_max_completion_tokens`, `embedding_batch_size`,
  `embedding_max_concurrent_data_points`.
- `huggingface_tokenizer` for chunk/tokenization compatibility.
- `embedding_rate_limit_enabled`, `embedding_rate_limit_requests`,
  `embedding_rate_limit_interval`, `embedding_rate_limit_tokens`.

Dimension auto-detection is best-effort through FastEmbed metadata and LiteLLM
model metadata. If unknown, Cognee falls back to `3072` and warns; set
`EMBEDDING_DIMENSIONS` explicitly for non-default models.

### Graph database settings

| Setter | Typical use |
|---|---|
| `set_graph_database_provider(provider)` | `ladybug`, `kuzu`, `neo4j`, `postgres`, `turso`, `neptune_analytics`, or a registered adapter provider. |
| `set_graph_database_subprocess_enabled(value)` | Boolean/string bool; controls embedded graph worker subprocess isolation. |
| `set_kuzu_num_threads(value)` | Non-negative integer; `0` means Kuzu default. |
| `set_kuzu_buffer_pool_size(value)` | Positive byte count. |
| `set_kuzu_max_db_size(value)` | Positive byte count. |
| `set_graph_db_config(dict)` | Bulk update of any `GraphConfig` field. |

Important `GraphConfig` fields:

- `graph_database_provider`, `graph_database_url`, `graph_database_name`,
  `graph_database_username`, `graph_database_password`,
  `graph_database_host`, `graph_database_port`, `graph_database_key`.
- `graph_file_path`, `graph_filename` for embedded file-backed graph stores.
- `graph_dataset_database_handler` for multi-user/dataset isolation.
- `graph_database_subprocess_enabled` and Kuzu tuning fields.

Without a copied environment template, the source-level graph default is
Ladybug. The public environment template often pins `GRAPH_DATABASE_PROVIDER` to
`kuzu`; Ladybug is the renamed Kuzu-compatible embedded graph layer, and Kuzu
remains a supported local provider/handler name.

### Vector database settings

| Setter | Typical use |
|---|---|
| `set_vector_db_provider(provider)` | `lancedb`, `pgvector`, `turso`, `neptune_analytics`, or a registered/community adapter. |
| `set_vector_db_url(url)` | URL/path for selected vector backend. |
| `set_vector_db_key(secret)` | Secret/token for remote vector backend. |
| `set_vector_db_subprocess_enabled(value)` | Boolean/string bool; controls LanceDB worker subprocess isolation. |
| `set_vector_db_config(dict)` | Bulk update of any `VectorConfig` field. |

Important `VectorConfig` fields:

- `vector_db_provider`, `vector_db_url`, `vector_db_name`, `vector_db_host`,
  `vector_db_port`, `vector_db_username`, `vector_db_password`,
  `vector_db_key`.
- `vector_dataset_database_handler` for multi-user/dataset isolation.
- `vector_db_subprocess_enabled` for LanceDB subprocess isolation.
- `vector_pool_args` as JSON for pgvector per-dataset pool tuning.

When `VECTOR_DB_PROVIDER=pgvector`, the dataset handler is automatically aligned
to `pgvector` if the handler was still on the LanceDB/pgvector default. Turso
gets the same alignment behavior for vector handlers.

### Relational and migration database settings

| Setter | Typical use |
|---|---|
| `set_relational_db_config(dict)` | Set `db_provider`, name, host, port, credentials, connect args, pool args, or Turso fields. |
| `set_migration_db_config(dict)` | Set migration-source database connection fields. |

Important `RelationalConfig` fields:

- `db_provider`: `sqlite`, `postgres`, or `turso`.
- `db_path`, `db_name`, `db_host`, `db_port`, `db_username`, `db_password`.
- `database_connect_args` and `pool_args` as JSON dictionaries.
- `db_turso_url`, `db_turso_auth_token` for remote Turso/libSQL.

`DATABASE_CONNECT_ARGS`, `POOL_ARGS`, and `VECTOR_POOL_ARGS` must be valid JSON
objects when supplied as environment strings.

### Cache/session settings

The cache config is environment-driven rather than exposed through the primary
`cognee.config` namespace. Relevant variables:

```bash
CACHING=true
CACHE_BACKEND=sqlite     # sqlite | postgres | redis | fs | tapes
CACHE_DB_URL=""          # optional SQLAlchemy async URL for sqlite/postgres cache
CACHE_HOST="localhost"
CACHE_PORT=6379
CACHE_USERNAME=""
CACHE_PASSWORD=""
CACHE_SSL=false
SESSION_TTL_SECONDS=604800
USAGE_LOGGING=false
AUTO_FEEDBACK=true
```

Default cache backend is SQL `sqlite` when caching is enabled. If the SQLite
cache would be placed on S3 and the backend was not explicitly chosen, Cognee can
fall back to filesystem cache; if explicitly choosing SQLite on S3, configure
`CACHE_DB_URL` or use `CACHE_BACKEND=postgres`/`fs`.

For agent/session memory workflows that rely on the cache, route to
[agent-session-memory](../../agent-session-memory/SKILL.md).

## Access-control and auth posture

Key variables:

```bash
ENABLE_BACKEND_ACCESS_CONTROL=True
REQUIRE_AUTHENTICATION=False
FASTAPI_USERS_JWT_SECRET="change-this-in-production"
FASTAPI_USERS_VERIFICATION_TOKEN_SECRET="change-this-too"
FASTAPI_USERS_RESET_PASSWORD_TOKEN_SECRET="change-this-too"
HASH_API_KEY=False
ACCEPT_LOCAL_FILE_PATH=True
ALLOW_HTTP_REQUESTS=True
ALLOW_CYPHER_QUERY=True
```

`ENABLE_BACKEND_ACCESS_CONTROL` is the multi-tenant posture switch. When true,
Cognee requires supported graph/vector dataset handlers and API authentication.
`REQUIRE_AUTHENTICATION=false` is ignored if backend access control is true.
For CORS and service deployment details, route to
[api-cli-services](../../api-cli-services/SKILL.md).

## Safe preflight script

Use the bundled checker to inspect an installed environment without exposing
secrets or absolute paths:

```bash
python scripts/check_cognee_environment.py --json
```

It reports:

- Python version and Cognee distribution presence.
- Optional module availability grouped by extra/provider.
- Config constructor success/failure for LLM, embeddings, graph, vector,
  relational, cache, S3, and base paths.
- Redacted presence of keys, endpoints, URLs, and path-like values.

The checker does not contact cloud APIs, start services, run memory flows, or
open original repository files.
