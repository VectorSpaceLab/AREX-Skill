# EverOS Setup and Configuration Reference

## Installation

```bash
python -m pip install everos
# optional parser support
python -m pip install 'everos[multimodal]'
# optional OpenTelemetry support
python -m pip install 'everos[otel]'
```

EverOS requires Python 3.12 or newer. The distribution exposes the `everos` console script.

## Memory root and config files

The memory root resolution order is:

1. Explicit `--root <path>` CLI option.
2. `EVEROS_ROOT` environment variable.
3. Default `~/.everos`.

Generate starter files:

```bash
everos init --root /data/everos
```

This writes:

| File | Purpose | Reload behavior |
|---|---|---|
| `everos.toml` | Application settings: API bind, provider credentials, SQLite/LanceDB, search, memorize, clustering, knowledge, observability | Server restart required for most settings |
| `ome.toml` | Offline Memory Engine strategy toggles, schedules, retry/gate settings | Hot-reloaded within a short interval |

Useful `init` options:

```bash
everos init --print             # print everos.toml template, no disk write
everos init --force --root ROOT  # overwrite existing config files
```

Without `--force`, existing config files are preserved. If both config files already exist, `everos init` exits non-zero and tells you to use `--force`.

## Effective config inspection

```bash
everos config show --root /data/everos
```

The output prints the resolved root, whether config files were found, and all setting sections. API keys are masked.

Environment override naming:

```text
EVEROS_<SECTION>__<KEY>
```

Examples:

```bash
export EVEROS_ROOT=/data/everos
export EVEROS_LLM__API_KEY=sk-...
export EVEROS_API__PORT=8080
export EVEROS_MEMORY__TIMEZONE=UTC
```

## Provider sections

Minimum useful server configuration:

```toml
[llm]
model = "openai/gpt-4.1-mini"
base_url = "https://openrouter.ai/api/v1"
api_key = "..."

[embedding]
model = "Qwen/Qwen3-Embedding-4B"
base_url = "https://api.deepinfra.com/v1/openai"
api_key = "..."

[rerank]
provider = "deepinfra"
model = "Qwen/Qwen3-Reranker-4B"
base_url = "https://api.deepinfra.com/v1/inference"
api_key = "..."
```

`[llm]` is required for normal server startup and memory extraction. `[embedding]` and `[rerank]` unlock vector/hybrid/agentic retrieval, knowledge write/search, clustering, reflection, and backfill paths. `[multimodal]` is separate from `[llm]` and is used only for multimodal parsing.

## Server startup

```bash
everos server start --root /data/everos --host 127.0.0.1 --port 8000
```

Resolution order for bind settings is CLI flag, config/env, then defaults. The command checks that `<root>/everos.toml` exists before starting. It starts Uvicorn with the app factory `everos.entrypoints.api.app:create_app`.

Security note: the default host is loopback. EverOS ships no built-in authentication, so binding to `0.0.0.0` should only happen behind an authenticated gateway.

## Health and capability checks

```bash
curl http://127.0.0.1:8000/health
```

The health response includes:

- `status`: liveness, normally `ok`.
- `version`: package version.
- `capabilities`: booleans for `llm`, `embed`, `rerank`, `multimodal_llm`, `parser`.
- `disabled_features`: derived feature names such as `vector_search`, `hybrid_search`, `agentic_search`, `knowledge`, or `multimodal_upload`.
- `cascade`: readiness block when cascade lifespan is running, otherwise `null`.

## Demo modes

```bash
everos demo            # interactive Textual demo
everos demo --plain    # static terminal preview, no server or credentials
everos demo --cinematic

everos demo --live --server-url http://127.0.0.1:8000
```

Plain/cinematic demo is educational and deterministic. Live mode performs the real server flow: `/health` -> `/api/v2/memory/add` -> `/api/v2/memory/flush` -> `/api/v2/memory/search`.
