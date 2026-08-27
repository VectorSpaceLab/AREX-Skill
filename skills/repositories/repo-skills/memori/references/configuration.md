# Memori Configuration

## Python environment variables

| Variable | Effect | Default / notes |
| --- | --- | --- |
| `MEMORI_API_KEY` | Cloud API key used when no BYODB connection is supplied | unset; required for cloud mode |
| `MEMORI_API_URL_BASE` | Memori Cloud base URL | cloud default from source code |
| `MEMORI_COCKROACHDB_CONNECTION_STRING` | CockroachDB connection string for default connection mode | unset; if present, Memori uses a DB connection factory |
| `MEMORI_EMBEDDINGS_MODEL` | Embedding model name used by `Config.embeddings.model` | `all-MiniLM-L6-v2` |
| `MEMORI_RECALL_EMBEDDINGS_LIMIT` | Dense candidate limit for recall | `1000` |
| `MEMORI_DISABLE_RUST_CORE` | Force native Rust core off | `false` |
| `MEMORI_USE_RUST_CORE` | Explicitly enable/disable the Rust core | unset means default on |
| `MEMORI_TEST_MODE` | Switch cloud endpoints into test mode | unset |
| `MEMORI_X_API_KEY` | Native core / cloud transport header override from the Rust README | built-in public key when unset |
| `MEMORI_RECALL_LEX_WEIGHT` | Lexical weight for hybrid re-rank | `0.15` in the native core docs |
| `MEMORI_RECALL_LEX_WEIGHT_SHORT` | Short-query lexical weight | `0.30` in the native core docs |

## Python config defaults

| Setting | Default | Notes |
| --- | --- | --- |
| `Config.debug_truncate` | `True` | Truncates long debug output |
| `Config.recall_facts_limit` | `5` | Used when no recall limit is supplied |
| `Config.recall_relevance_threshold` | `0.1` | Influences recall filtering |
| `Config.request_secs_timeout` | `5` | Cloud request timeout |
| `Config.request_num_backoff` | `5` | Cloud retry count |
| `Config.request_backoff_factor` | `1` | Cloud backoff factor |
| `Config.session_timeout_minutes` | `30` | Session lifetime default |
| `Config.use_rust_core` | default on | Can be disabled for diagnosis |

## CLI environment behavior

- `python -m memori` loads a `.env` file from the current working directory
  before it resolves the command.
- Existing environment variables win over `.env` values.
- The CLI supports cloud and provisioning commands, so set credentials and
  service variables before invoking a live action.

## Practical startup order

1. Decide cloud mode or BYODB mode.
2. Set `MEMORI_API_KEY` for cloud, or provide `conn=...` / a connection string
   for BYODB.
3. Call `llm.register(...)` before expecting automatic recall injection.
4. Call `attribution(entity_id, process_id)` before a short script expects
   memories to persist.
5. Use `augmentation.wait()` when a script ends immediately after a write.
