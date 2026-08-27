# Configuration Reference

This page collects the cross-cutting environment variables and runtime knobs that show up across multiple Open WebUI workflows. Sub-skills own the workflow-specific details; this file is the shared lookup table.

## Startup and identity

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `WEBUI_SECRET_KEY` | Required secret for authenticated startup when the backend is started directly. | `deployment` |
| `WEBUI_JWT_SECRET_KEY` | Alternate secret accepted by startup scripts. | `deployment` |
| `WEBUI_NAME` | Display name shown in the UI. | `admin-collaboration` |
| `WEBUI_AUTH` | Enables or disables authentication. | `admin-collaboration` |
| `WEBUI_ADMIN_EMAIL` / `WEBUI_ADMIN_PASSWORD` / `WEBUI_ADMIN_NAME` | Bootstrap the first admin account in some deployment modes. | `admin-collaboration` |
| `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` / `WEBUI_AUTH_TRUSTED_NAME_HEADER` / `WEBUI_AUTH_TRUSTED_GROUPS_HEADER` / `WEBUI_AUTH_TRUSTED_ROLE_HEADER` | Trusted-header SSO / reverse-proxy identity mapping. | `admin-collaboration` |

## Provider and model routing

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | URL for Ollama or the local model gateway. | `chat-models` |
| `ENABLE_OPENAI_API_PASSTHROUGH` | Pass OpenAI-compatible traffic through instead of rewriting it. | `chat-models` |
| `ENABLE_CUSTOM_MODEL_FALLBACK` | Enable fallback model behavior when the requested model is unavailable. | `chat-models` |
| `OPENAI_API_KEY` / provider-specific API keys | Credentials for hosted model providers. | `chat-models` |
| `AIOHTTP_CLIENT_TIMEOUT` and related timeout variables | Slow provider / streaming / upstream-request timeouts. | `chat-models` and `extensions` |

## Storage, database, and session state

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `DATABASE_URL` | Primary application database connection string. | `admin-collaboration` |
| `REDIS_URL` | Redis-backed cache/session/task configuration. | `admin-collaboration` |
| `STORAGE_PROVIDER` | Local, S3, GCS, Azure, or other storage backend selection. | `admin-collaboration` |
| `S3_*`, `GCS_*`, `AZURE_STORAGE_*` | Storage-provider credentials and endpoints. | `admin-collaboration` |
| `DATABASE_ENABLE_SQLITE_WAL`, `DATABASE_POOL_*` | SQLite and pool tuning. | `admin-collaboration` |

## Knowledge and file handling

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` | Retrieval scope behavior for knowledge collections. | `knowledge-files` |
| `KB_EXEC_MAX_OUTPUT_CHARS`, `KB_EXEC_MAX_GREP_FILES` | Knowledge execution and search safety limits. | `knowledge-files` |
| `VIEW_FILE_MAX_CHARS`, `VIEW_FILE_DEFAULT_MAX_CHARS` | File-view truncation limits. | `knowledge-files` |
| `ENABLE_PYODIDE_FILE_PERSISTENCE` | Browser-side file persistence for Pyodide-based flows. | `extensions` |
| `OFFLINE_MODE` | Prevents network-dependent model/download behavior. | `deployment` and `knowledge-files` |
| `HF_HUB_OFFLINE` | Low-level Hugging Face offline mode. | `deployment` and `knowledge-files` |

## Extensions and multimedia

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `ENABLE_PLUGINS` | Master toggle for tools/functions-style extensions. | `extensions` |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` | Allow extension manifests to install declared Python dependencies. | `extensions` |
| `WEB_LOADER_ENGINE` | Selects browser/Playwright-backed loaders. | `extensions` |
| `PLAYWRIGHT_WS_URL` | Connects Open WebUI to a Playwright remote browser server. | `extensions` |
| `ENABLE_IMAGE_GENERATION` | Enables image-generation workflows. | `extensions` |
| `AUTOMATIC1111_BASE_URL` | Image backend endpoint for A1111-style integrations. | `extensions` |

## Observability and operations

| Variable | Meaning | Typical owner |
| --- | --- | --- |
| `ENABLE_OTEL`, `ENABLE_OTEL_TRACES`, `ENABLE_OTEL_METRICS`, `ENABLE_OTEL_LOGS` | OpenTelemetry enablement flags. | `admin-collaboration` |
| `OTEL_*` | Export endpoint, credentials, and service-name configuration. | `admin-collaboration` |
| `ENABLE_AUDIT_*` | Audit logging switches. | `admin-collaboration` |
| `ENABLE_SCIM`, `SCIM_TOKEN`, `SCIM_AUTH_PROVIDER` | SCIM provisioning configuration. | `admin-collaboration` |

## Deployment reminders

- `open-webui serve` can generate or load a secret key for you; direct `uvicorn` startup usually cannot.
- Source installs may trigger the frontend build hook, so Node.js/npm is part of the practical runtime toolchain.
- The repo supports GPU and Playwright deployment overlays, but they are optional unless the chosen workflow needs them.
