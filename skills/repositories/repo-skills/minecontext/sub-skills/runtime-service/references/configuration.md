# Runtime configuration reference

## Load order and path rules

OpenContext runtime configuration is layered:

1. Base YAML file passed by `opencontext start --config`, defaulting to
   `config/config.yaml` relative to the process working directory.
2. Environment interpolation in the form `${VAR}` or `${VAR:default}`.
   Missing `${VAR}` becomes an empty string; missing `${VAR:default}` becomes
   the default.
3. User settings YAML at `user_setting_path`, merged into base config.
4. Runtime updates made through settings endpoints, followed by component or
   service reinitialization where the route supports it.

`CONTEXT_PATH` controls the default location for logs, user settings, persisted
storage, debug generation files, and screenshots. If data appears in an
unexpected directory, inspect the effective config and `GET /api/settings/system_info`
instead of assuming a platform-specific app-data path.

## Startup-related keys

| Key | Purpose | Typical values / caveats |
| --- | --- | --- |
| `enabled` | Global switch | Normally `true`. |
| `logging.level` | Backend log level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `logging.log_path` | Log file | Default uses `${CONTEXT_PATH:.}/logs/opencontext.log`. Ensure the parent is writable. |
| `user_setting_path` | Per-user overrides | Default uses `${CONTEXT_PATH:.}/config/user_setting.yaml`. Settings APIs write here. |
| `web.host` | Uvicorn bind host | Prefer `127.0.0.1` for local use. |
| `web.port` | Uvicorn bind port | Default debugger port is `1733`; CLI `--port` wins. |

Start with overrides:

```bash
CONTEXT_PATH="$PWD/.minecontext-data" \
opencontext start --config config/config.yaml --host 127.0.0.1 --port 1733
```

## Model settings

MineContext separates the visual/chat model (`vlm_model`) from the embedding
model (`embedding_model`). Both must be valid for storage search, screenshot
analysis, document visual analysis, generated todos/tips/reports, chat, and
semantic completions.

| YAML key | Required for real generation | Notes |
| --- | --- | --- |
| `vlm_model.base_url` | Yes | OpenAI-compatible URL or Doubao/Ark-compatible base. |
| `vlm_model.api_key` | Yes | May come from `${LLM_API_KEY}`; do not print it. |
| `vlm_model.model` | Yes | Chat/VLM model id. |
| `vlm_model.provider` | Optional but important | `openai`, `doubao`, or empty for OpenAI-compatible path. |
| `embedding_model.base_url` | Yes | Defaults are often supplied by `${EMBEDDING_BASE_URL}`. |
| `embedding_model.api_key` | Yes | If using settings API, embedding key can fall back to VLM key. |
| `embedding_model.model` | Yes | Embedding model id. |
| `embedding_model.provider` | Optional but important | `doubao` uses Ark multimodal embeddings. |
| `embedding_model.output_dim` | Yes for storage consistency | Default config uses `2048`. Qdrant `vector_size` must match. |

To recover from blank settings without exposing secrets, report only missing key
names, for example:

```text
Missing model settings: vlm_model.base_url, vlm_model.api_key, vlm_model.model,
embedding_model.base_url, embedding_model.api_key, embedding_model.model.
Do not paste the secret values; set them in the environment, YAML, or settings UI.
```

Validate before saving:

```bash
curl -s -X POST http://127.0.0.1:1733/api/model_settings/validate \
  -H 'Content-Type: application/json' \
  -d @model-settings.json
```

`/api/model_settings/update` performs the same validation, saves to the user
settings file, reloads config, and reinitializes the global VLM and embedding
clients.

## Prompt files

`prompts.language` selects `prompts_zh.yaml` or `prompts_en.yaml` from the same
directory as the loaded config file. Missing files prevent prompt-manager
initialization and break workflows that read prompt groups.

Important prompt groups include:

- `chat_workflow.*` for context-agent intent, retrieval, execution, and social
  interaction steps.
- `processing.extraction.*` for screenshot or document visual extraction.
- `document_processing.vlm_analysis`, `document_processing.text_chunking`, and
  `document_processing.global_semantic_chunking` for document parsing/chunking.
- `generation.*` for activities, tips, todos, and reports.
- `completion_service.semantic_continuation` for note completions.

Settings endpoints can get, update, import, export, switch language, and reset
prompts. Prompt imports must be YAML dictionaries; invalid YAML or missing
category keys should be rejected or rolled back by the operator.

## Capture configuration

| Section | Key fields | Runtime behavior |
| --- | --- | --- |
| `capture.enabled` | Global capture switch | Capture manager initializes enabled components. |
| `capture.screenshot.enabled` | `capture_interval`, `storage_path` | Uses `mss`; needs screen permissions and a writable screenshot directory. |
| `capture.folder_monitor.enabled` | `monitor_interval`, `watch_folder_paths`, `recursive`, `max_file_size`, `initial_scan` | Detects create/update/delete for supported files and emits local-file raw contexts. Delete cleanup queries `knowledge_file_path` in storage. |
| `capture.file_monitor` | `monitor_paths`, `ignore_patterns` | Present in config but folder monitor is the safer runtime surface documented here. |
| `capture.vault_document_monitor.enabled` | `monitor_interval`, `initial_scan` | Watches internal vault note changes. |
| Web-link capture | `output_dir`, `mode`, `timeout`, `wait_until`, `max_workers` | Not in the default YAML section, but used by `WebLinkCapture`; defaults to `uploads/weblinks`, `markdown`, `networkidle`. |

## Processing configuration

| Section | Key fields | Notes |
| --- | --- | --- |
| `document_processing` | `enabled`, `batch_size`, `max_image_size`, `dpi`, `text_threshold_per_page` | Page-by-page document analysis; scanned/visual pages use the VLM. |
| `processing.document_processor` | `enabled`, `batch_size`, `batch_timeout` | Queue and direct `real_process` handling for documents and text. |
| `processing.screenshot_processor` | `dedup_cache_size`, `similarity_hash_threshold`, `batch_size`, `batch_timeout`, `max_image_size`, `resize_quality`, `enabled_delete`, `max_raw_properties` | Dedup, resize, batch VLM extraction, and optional duplicate-file deletion. |
| `processing.context_merger` | similarity thresholds, retention, memory cleanup, cross-type conversion | Disabled by default in the base config; enabling increases model/storage coupling. |

## Storage configuration

`storage.backends` defines exactly one default vector backend and one document
backend in the default runtime:

```yaml
storage:
  enabled: true
  backends:
    - name: default_vector
      storage_type: vector_db
      backend: chromadb
      config:
        mode: local
        path: ${CONTEXT_PATH:.}/persist/chromadb
        collection_prefix: opencontext
    - name: document_store
      storage_type: document_db
      backend: sqlite
      config:
        path: ${CONTEXT_PATH:.}/persist/sqlite/app.db
```

ChromaDB local mode uses `chromadb.PersistentClient(path=...)`; server mode uses
an HTTP client with `host`, `port`, `ssl`, `headers`, and optional settings.
Qdrant can be selected by replacing the vector backend with `backend: qdrant`.
When using Qdrant, set `config.vector_size` to match `embedding_model.output_dim`
or the collection will reject vectors with a different length. SQLite creates
and migrates tables for vaults, todos, activities, tips, monitoring,
conversations, messages, and message-thinking records.

## API authentication

```yaml
api_auth:
  enabled: false
  api_keys:
    - ${CONTEXT_API_KEY:test}
  excluded_paths:
    - /health
    - /api/health
    - /api/auth/status
    - /
    - /static/*
```

When `enabled: true`, each protected request must include `X-API-Key` or
`api_key`. Wildcards in `excluded_paths` use shell-style matching. Avoid putting
high-privilege routes in `excluded_paths` unless the service is bound to a
trusted local interface.

## Content generation

| Task | Key fields | Validation |
| --- | --- | --- |
| `content_generation.activity` | `enabled`, `interval` | Interval must be at least `600` seconds when set via API. |
| `content_generation.tips` | `enabled`, `interval` | Interval must be at least `1800` seconds. |
| `content_generation.todos` | `enabled`, `interval` | Interval must be at least `1800` seconds. |
| `content_generation.report` | `enabled`, `time` | Time format is `HH:MM`. |
| `content_generation.debug` | `enabled`, `output_path` | Saves prompt messages and responses under `${CONTEXT_PATH:.}/debug/generation` by task. |

Content generation depends on storage, prompts, and model credentials. Disable
or lengthen schedules while debugging startup or storage problems.

## Tool configuration

The operation tool `tools.operation_tools.web_search_tool` uses DuckDuckGo by
default and accepts `enabled`, `web_search.engine`, `max_results`, and `timeout`.
This can affect context-agent workflows that invoke retrieval/operation tools;
network policy and provider availability should be checked before enabling
agent workflows that require web search.
