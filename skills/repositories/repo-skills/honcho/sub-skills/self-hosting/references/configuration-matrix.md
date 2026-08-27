# Honcho Self-hosting Configuration Matrix

Honcho configuration is layered in this priority order: environment variables, `.env`, `config.toml`, built-in defaults. Use `.env` or platform secrets for credentials. Use `config.toml` for stable non-secret defaults if that fits the deployment.

## Naming rules

| Shape | Example | Meaning |
|---|---|---|
| Top-level app setting | `LOG_LEVEL=INFO` | Maps to `[app].LOG_LEVEL` / `settings.LOG_LEVEL`. |
| Section setting | `DB_CONNECTION_URI=...` | Maps to `[db].CONNECTION_URI` / `settings.DB.CONNECTION_URI`. |
| Nested setting | `DERIVER_MODEL_CONFIG__OVERRIDES__BASE_URL=...` | Double underscore descends into nested model config. |
| Dialectic level setting | `DIALECTIC_LEVELS__minimal__MODEL_CONFIG__MODEL=...` | Configures one reasoning level. |

## Minimum local `.env`

```bash
DB_CONNECTION_URI=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
AUTH_USE_AUTH=false
LLM_OPENAI_API_KEY=sk-...
```

Current built-in defaults route text-generation features through OpenAI transport with `gpt-5.4-mini`, and embeddings through OpenAI transport with `text-embedding-3-small`. If you override a feature's transport, set a compatible model name and ensure the matching provider key is present.

## LLM provider routing

| Transport | Connects to | Key environment variable | Notes |
|---|---|---|---|
| `openai` | OpenAI or OpenAI-compatible endpoints such as OpenRouter, Together, Fireworks, LiteLLM, vLLM, Ollama | `LLM_OPENAI_API_KEY` | For proxies/self-hosted servers, set per-feature `MODEL_CONFIG__OVERRIDES__BASE_URL`. |
| `anthropic` | Anthropic Claude direct | `LLM_ANTHROPIC_API_KEY` | Use provider-supported thinking settings only when compatible. |
| `gemini` | Google Gemini direct | `LLM_GEMINI_API_KEY` | Gemini applies a conservative default embedding batch size of 100. |

All Honcho agents that use tools require models with tool/function calling support. When changing a feature's transport, specify the model explicitly; a partial transport override can leave an old model name attached to a new provider.

### OpenAI-compatible example

```bash
LLM_OPENAI_API_KEY=sk-or-v1-...
DERIVER_MODEL_CONFIG__TRANSPORT=openai
DERIVER_MODEL_CONFIG__MODEL=google/gemini-2.5-flash
DERIVER_MODEL_CONFIG__OVERRIDES__BASE_URL=https://openrouter.ai/api/v1
```

For Ollama or vLLM from Docker, remember that `localhost` inside the Honcho container is the Honcho container, not the host. Use `host.docker.internal` on macOS/Windows or an explicit host network IP.

## Core service settings

| Variable | Default/source fact | Use |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Set `DEBUG` while diagnosing startup/runtime issues. |
| `SESSION_OBSERVERS_LIMIT` | `10` | Limit session observer fan-out. |
| `GET_CONTEXT_MAX_TOKENS` | `100000` | Upper bound for context endpoint token budget. |
| `MAX_MESSAGE_SIZE` | `25000` characters | Reject oversized messages. |
| `MAX_FILE_SIZE` | `5242880` bytes | Upload size cap. |
| `EMBED_MESSAGES` | `true` | Enables message embedding pipeline. |
| `NAMESPACE` | `honcho` | Propagates to cache, vector store, metrics, and telemetry namespaces unless those nested namespaces are explicitly set. |

## Database settings

| Variable | Default/source fact | Use |
|---|---|---|
| `DB_CONNECTION_URI` | `postgresql+psycopg://postgres:postgres@localhost:5432/postgres` | Required database URI. Must use `postgresql+psycopg://`. |
| `DB_SCHEMA` | `public` | Schema used by model metadata and embedding validator. |
| `DB_POOL_CLASS` | `default` | Set `null` to use SQLAlchemy `NullPool`; otherwise pool settings below apply. |
| `DB_POOL_PRE_PING` | `true` | Pooled connection liveness checks. |
| `DB_POOL_SIZE` | `10` | Base pool size. |
| `DB_MAX_OVERFLOW` | `20` | Overflow connection count. |
| `DB_POOL_TIMEOUT` | `5` seconds | Queue wait for a pooled checkout. |
| `DB_POOL_RECYCLE` | `300` seconds | Recycle pooled connections. |
| `DB_POOL_USE_LIFO` | `true` | QueuePool LIFO behavior. |
| `DB_SQL_DEBUG` | `false` | SQL echo for debugging. |
| `DB_TRACING` | `false` | Tags checked-out connections with request/task context via `application_name`. |
| `DB_CONNECT_TIMEOUT_SECONDS` | `2` seconds | Driver connection-establish timeout. |

Honcho creates the configured schema and runs `CREATE EXTENSION IF NOT EXISTS vector` in `init_db()`. Migrations and startup can still fail if the database role cannot create extensions; preinstall pgvector once with a privileged role in least-privilege deployments.

## Embedding settings

| Variable | Default/source fact | Use |
|---|---|---|
| `EMBEDDING_VECTOR_DIMENSIONS` | `1536` | Authoritative vector dimension for pgvector and external-store validation. |
| `EMBEDDING_MAX_INPUT_TOKENS` | `8192` | Per-input truncation/cap for embeddings. |
| `EMBEDDING_MAX_TOKENS_PER_REQUEST` | `300000` | Aggregate embedding request cap. |
| `EMBEDDING_MAX_CONCURRENT_EMBEDDINGS` | `10` | Immediate message-embedding fan-out cap on API path. |
| `EMBEDDING_MAX_PENDING_EMBED_TASKS` | `50` | Cap on in-flight immediate embed background tasks; `0` disables that fast path. |
| `EMBEDDING_MODEL_CONFIG__TRANSPORT` | `openai` | Embedding provider transport. |
| `EMBEDDING_MODEL_CONFIG__MODEL` | `text-embedding-3-small` | Embedding model. |
| `EMBEDDING_MODEL_CONFIG__MAX_BATCH_SIZE` | OpenAI default 2048; Gemini client default 100 | Set for providers with lower per-request input limits. |
| `EMBEDDING_MODEL_CONFIG__DIMENSIONS_MODE` | `auto` | Controls whether OpenAI-compatible calls send `dimensions=`. |
| `EMBEDDING_MODEL_CONFIG__ENCODING_FORMAT_MODE` | `auto` | Sends base64 for OpenAI hosts and float for other OpenAI-compatible hosts unless overridden. |
| `VECTOR_STORE_DIMENSIONS` | Deprecated/ignored | Remove it; `EMBEDDING_VECTOR_DIMENSIONS` wins. |

Dimension modes:

- `auto`: send `dimensions=` only when `EMBEDDING_VECTOR_DIMENSIONS` was explicitly set and the model is not on the known rejecting list.
- `always`: always send `dimensions=`; useful when a compatible provider requires it or config layers strip default-valued explicit envs.
- `never`: never send `dimensions=`; use for providers that reject it.

Encoding modes:

- `auto`: base64 for OpenAI hosts, float for other OpenAI-compatible hosts.
- `float`: always request JSON floats.
- `base64`: always request base64.

## Deriver settings

| Variable | Default/source fact | Use |
|---|---|---|
| `DERIVER_ENABLED` | `true` | Gate deriver processing. |
| `DERIVER_WORKERS` | `1` | Increase for throughput; multiple deriver processes coordinate through the DB queue. |
| `DERIVER_POLLING_SLEEP_INTERVAL_SECONDS` | `1.0` | Base polling interval. |
| `DERIVER_POLLING_BACKOFF_ENABLED` | `true` | Allows idle/error polling backoff. |
| `DERIVER_POLLING_SLEEP_MAX_INTERVAL_SECONDS` | `30.0` | Backoff ceiling. |
| `DERIVER_MODEL_CONFIG__TRANSPORT` | `openai` | Deriver model transport. |
| `DERIVER_MODEL_CONFIG__MODEL` | `gpt-5.4-mini` | Deriver model. |
| `DERIVER_MODEL_CONFIG__STRUCTURED_OUTPUT_MODE` | unset / default backend mode | Set `json_object` for OpenAI-compatible providers that reject or ignore strict `json_schema`. |
| `DERIVER_MAX_INPUT_TOKENS` | `25000` | Max deriver prompt input. |
| `DERIVER_MAX_CUSTOM_INSTRUCTIONS_TOKENS` | `2000` | Cap for custom instructions added to deriver prompt. |
| `DERIVER_REPRESENTATION_BATCH_WORK_UNIT_TARGET_TOKENS` | documented batching gate | Set `0` to disable accumulation gate. |
| `DERIVER_REPRESENTATION_BATCH_MAX_AGE_SECONDS` | `1800` | Quiet session tails become eligible after this age. |

`DERIVER_REPRESENTATION_BATCH_TARGET_INPUT_TOKENS` cannot exceed `DERIVER_MAX_INPUT_TOKENS`.

## Cache / Redis settings

| Variable | Default/source fact | Use |
|---|---|---|
| `CACHE_ENABLED` | `false` in config defaults; compose sets `true` | Enables Redis-backed caching. |
| `CACHE_URL` | `redis://localhost:6379/0?suppress=true` | Redis URL. Compose uses `redis://redis:6379/0?suppress=true`. |
| `CACHE_CLUSTER` | `false` | Set true for Redis Cluster URLs. |
| `CACHE_NAMESPACE` | inherits `NAMESPACE` if unset | Cache namespace. |
| `CACHE_DEFAULT_TTL_SECONDS` | `300` | Cache TTL. |
| `CACHE_DEFAULT_LOCK_TTL_SECONDS` | `5` | Stampede-prevention lock TTL. |
| `CACHE_LOCK_WAIT_CHECK_INTERVAL_SECONDS` | `0.1` | Lock wait polling interval. |

Redis is optional for local/manual deployments. If Redis is unreachable, Honcho logs a warning and falls back to in-memory caching.

## Vector store settings

| Variable | Default/source fact | Use |
|---|---|---|
| `VECTOR_STORE_TYPE` | `pgvector` | One of `pgvector`, `turbopuffer`, `lancedb`. |
| `VECTOR_STORE_MIGRATED` | `false` | Legacy migration/cutover flag; unrelated to dimension configuration. |
| `VECTOR_STORE_NAMESPACE` | inherits `NAMESPACE` if unset | Prefix for external namespaces. |
| `VECTOR_STORE_TURBOPUFFER_API_KEY` | required for `turbopuffer` | Startup config validation fails without it. |
| `VECTOR_STORE_TURBOPUFFER_REGION` | provider-specific | Region for Turbopuffer. |
| `VECTOR_STORE_LANCEDB_PATH` | `./lancedb_data` | Local LanceDB path. |
| `VECTOR_STORE_RECONCILIATION_INTERVAL_SECONDS` | `300` | Reconciler sync interval. |

Namespace shapes documented in `.env.template` are `{NAMESPACE}.doc.{hash(workspace, observer, observed)}` for document namespaces and `{NAMESPACE}.msg.{hash(workspace)}` for message namespaces.

LanceDB is optional and absent from the default Docker image. Use `INSTALL_LANCEDB=true docker compose up -d --build` or `uv sync --extra lancedb` for manual setups. The extra is documented as unavailable on Intel macOS.

## Auth settings

| Variable | Default/source fact | Use |
|---|---|---|
| `AUTH_USE_AUTH` | `false` | Set `true` to require JWTs. |
| `AUTH_JWT_SECRET` | required when auth is enabled | Generated with `scripts/generate_jwt_secret.py`. |

JWT generation examples:

```bash
uv run python scripts/generate_jwt.py --admin --expires 24h
uv run python scripts/generate_jwt.py --workspace my-workspace --expires 30d
uv run python scripts/generate_jwt.py --workspace my-workspace --peer my-peer --expires 1y
uv run python scripts/generate_jwt.py --workspace my-workspace --session my-session --expires 8h
```

## Monitoring and telemetry

| Area | Variables | Notes |
|---|---|---|
| Prometheus | `METRICS_ENABLED`, `METRICS_NAMESPACE` | API exposes `/metrics` on port 8000; deriver exposes metrics on port 9090. |
| Sentry | `SENTRY_ENABLED`, `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, sampling settings | API initializes FastAPI/Starlette/SQLAlchemy integrations when enabled. |
| CloudEvents telemetry | `TELEMETRY_ENABLED`, endpoint, headers, batch/retry/buffer settings | API startup initializes telemetry and shutdown flushes it. |
| Local traces | `COLLECT_METRICS_LOCAL`, `LOCAL_METRICS_FILE`, `REASONING_TRACES_FILE` | Useful for local debugging. |

## Source scripts to use or avoid adapting

| Script | Use directly? | Reason |
|---|---:|---|
| `scripts/configure_embeddings.py` | Yes | Official, transaction-safe pgvector dimension bootstrap plus external-store report. Do not reimplement destructive ALTER logic. |
| `scripts/generate_jwt_secret.py` | Yes | Small official secret generator using `secrets.token_hex(32)`. |
| `scripts/generate_jwt.py` | Yes | Official scoped JWT generator; enforces admin/scope argument rules and duration parsing. |
| `scripts/migrate_db.py` | Usually no | Thin wrapper around `alembic upgrade head`; use explicit `uv run alembic upgrade head` in operator runbooks for clarity. |
| `scripts/provision_db.py` | Use cautiously | Calls `init_db()`, which creates schema/extension and runs migrations. For least-privilege DBs, preinstall pgvector with a privileged role first. |
