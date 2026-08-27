# Configuration and environment

Honcho configuration is layered. In practice, the effective precedence is:

1. Explicit runtime flags or request parameters.
2. Environment variables.
3. `.env` values.
4. `config.toml` / config files.
5. Built-in defaults.

## Major settings areas

| Area | What it controls |
| --- | --- |
| `DB` | Connection URI, pool sizing, timeouts, schema, tracing. |
| `EMBEDDING` | Vector dimension and token limits for embedding requests. |
| `VECTOR_STORE` | Vector-store type, namespace, migration flags, remote store settings. |
| `LLM` | Provider keys, base URLs, token limits, and model routing inputs. |
| `DIALECTIC` | Chat reasoning limits and session history sizing. |
| `SUMMARY` | Session summarization cadence and token caps. |
| `METRICS` / `SENTRY` | Observability toggles and sampling settings. |

## Self-hosting essentials

A self-hosted Honcho deployment usually needs:

- A reachable PostgreSQL database with the `vector` extension available when
  using pgvector.
- Redis for cache and queue support when enabled by the deployment.
- A correct embedding dimension that matches the physical vector columns.
- Any provider keys required by the chosen LLM paths.
- A consistent workspace/peer/session scoping strategy.

## CLI client configuration

The `honcho` CLI uses `~/.honcho/config.json`.

- `apiKey` stores the Honcho API key.
- `environmentUrl` stores the server URL.
- Workspace, peer, and session scope are handled per command via flags or
  `HONCHO_*` environment variables.

The CLI is designed so operator scope is not persisted as a hidden global
state. That makes it safer to switch between workspaces or sessions.

## Common environment variables

| Variable | Purpose |
| --- | --- |
| `HONCHO_API_KEY` | CLI/admin API key. |
| `HONCHO_BASE_URL` | Server URL. |
| `HONCHO_WORKSPACE_ID` | Workspace scope for CLI/SDK usage. |
| `HONCHO_PEER_ID` | Peer scope for CLI/SDK usage. |
| `HONCHO_SESSION_ID` | Session scope for CLI/SDK usage. |
| `PYTHON_DOTENV_DISABLED` | Useful in tests to prevent accidental `.env` loading. |

## Vector-store notes

- `pgvector` is the default inline mode.
- External vector stores are optional and should only be enabled when the
  deployment actually needs them.
- Embedding dimension mismatches are caught at startup, not silently ignored.

## Startup validation

Honcho intentionally fails closed when the configured embedding dimension does
not match the live schema. That protects you from serving traffic with vectors
in the wrong shape.

If startup validation fails:

1. Check the configured embedding dimension.
2. Check the current database schema.
3. Check whether the deployment is using pgvector or an external store.
4. Re-run the startup check only after the mismatch is resolved.

## Practical rule

When a task mixes configuration, startup, and runtime behavior, read this file
first, then move to the route-specific reference for the affected surface.
