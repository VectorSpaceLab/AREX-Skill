# Startup and Configuration

## Entrypoints

LangBot has two public package entry paths:

```bash
uv run main.py          # source checkout
langbot                 # installed package console script
python -m langbot       # module execution when installed/importable
```

The package entrypoint parses these flags:

| Flag/subcommand | Meaning |
|---|---|
| `--standalone-runtime` | Connect to an external Plugin Runtime instead of spawning/owning the default local runtime path. |
| `--standalone-box` | Connect to an external Box Runtime instead of local auto-managed Box behavior. |
| `--debug` | Set LangBot debug mode. |
| `migrate --cloud` | Operator-only cloud PostgreSQL migration command. |

## Boot Sequence

The boot path is layered:

1. Parse flags and set standalone runtime/box booleans.
2. Check dependency availability and install missing dependency records when the
   non-migration startup path says to do so.
3. Generate missing `data/` and config files.
4. Build the `Application` object through boot stages.
5. Initialize managers/services/runtime connectors/controllers.
6. Start platform manager, query controller, HTTP controller, telemetry, cleanup
   loops, and plugin initialization.

`Application` is the runtime service locator. Representative public methods
verified from the installed package are `initialize()`, `run()`, `shutdown()`,
`dispose()`, and `get_runtime_resource_stats()`.

## Config File Model

Fresh installs generate `data/config.yaml` from the template packaged under
`langbot.templates`. Important top-level sections:

| Section | Important keys |
|---|---|
| `api` | `port`, `webhook_prefix`, `global_api_key` |
| `workspace` | invitation/public URL/email controls |
| `concurrency` | pipeline/session/pending query limits |
| `proxy` | HTTP/HTTPS proxy values used by managers |
| `database` | SQLite path or PostgreSQL connection settings |
| `vdb` | `chroma`, `qdrant`, `seekdb`, `milvus`, `pgvector`, `valkey_search` settings |
| `storage` | local/S3 storage and cleanup limits |
| `plugin` | Plugin Runtime enablement, WebSocket URL, worker limits, binary storage |
| `mcp` | MCP stdio lifecycle settings |
| `box` | Box enablement, backend, runtime endpoint, admission, local workspace settings |
| `space` | LangBot Space URLs and cloud service toggles |

When adding config keys, update the template, startup validation, docs, tests,
and any agent-facing skills that mention the key.

## Local Development Loop

```bash
uv sync --dev
uv run main.py
# separate terminal for web UI development
cd web
pnpm install
pnpm dev
```

The web dev server expects a backend on the configured API base URL. In
production/package mode, built web assets are served by the backend.

## Minimal Startup Evidence

For a runtime issue, collect:

- Command and flags used.
- Python version and `langbot --help` output.
- Whether `data/config.yaml` was generated or edited.
- `/healthz` response or failure.
- Port owner if `api.port` is already bound.
- Whether standalone Plugin Runtime or Box endpoints are configured.
- Recent logs around dependency checks, config generation, migrations, and
  HTTP controller startup.
