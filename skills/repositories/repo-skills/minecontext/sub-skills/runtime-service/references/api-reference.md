# Runtime API reference

## Base URL and response styles

The default backend debugger listens on `http://127.0.0.1:1733` when started
with the default web config. CLI flags override YAML values:

```bash
opencontext start --config config/config.yaml --host 127.0.0.1 --port 1733
```

Most MineContext JSON routes use the standard envelope:

```json
{"code": 0, "status": 200, "message": "success", "data": {}}
```

Some newer agent/completion/monitoring routes return route-specific JSON such as
`{"success": true, "data": ...}` or Server-Sent Events. If a route depends on
`OpenContext` and the FastAPI app has no `app.state.context_lab_instance`, the
failure is `500` with detail similar to `OpenContext instance not initialized`.
That means the route was mounted without going through `opencontext start` or the
startup lifespan failed before attaching the instance.

## Authentication

Runtime auth is controlled by `api_auth` in config. When enabled, protected
routes accept either:

```bash
-H 'X-API-Key: <key>'
# or
?api_key=<key>
```

Default excluded paths include `/health`, `/api/health`, `/api/auth/status`, `/`,
`/static/*`, and several debugger pages. Never echo keys in logs or generated
notes. If `api_auth.enabled: true` but no non-empty key remains after environment
substitution, protected routes return a server-configuration error.

## Route family table

| Family | Methods and paths | Purpose | Notes |
| --- | --- | --- | --- |
| Health/auth | `GET /health`, `GET /api/health`, `GET /api/auth/status` | Basic service status, component health, auth-enabled status | `/api/health` requires an initialized `OpenContext` instance. |
| Web/debug pages | `GET /`, `/contexts`, `/vector_search`, `/debug`, `/chat`, `/advanced_chat`, `/monitoring`, `/assistant`, `/settings`, `/vaults`, `/vaults/editor`, `/files/{file_path}` | Browser-accessible debugger and UI pages | `/files/{file_path}` is protected when auth is enabled. |
| Context query | `GET /api/context_types`, `POST /api/vector_search`, `POST /contexts/detail`, `POST /contexts/delete` | List context types, vector search, HTML detail, deletion | Search requires storage and embedding/vector backends to be healthy. |
| Document/web upload | `POST /api/documents/upload`, `POST /api/weblinks/upload` | Queue local files or web links for capture/processing | Web links need browser/crawl dependencies and network permission. |
| Screenshots | `POST /api/add_screenshot`, `POST /api/add_screenshots` | Queue existing screenshot image paths for processing | The image path must be accessible to the backend process. |
| Settings/model | `GET/POST /api/model_settings/*`, `GET/POST /api/settings/general`, prompt import/export/history/reset routes | Inspect/update model settings, general capture/processing/generation settings, prompts | Model validation makes external model calls. |
| Content generation | `GET/POST /api/content_generation/config`; debug list/update/manual generation routes under `/api/debug/*` | Configure and manually trigger activities, todos, tips, and reports | Real generation needs LLM/VLM credentials and stored context. |
| Monitoring | `GET /api/monitoring/overview`, `/context-types`, `/token-usage`, `/processing`, `/stage-timing`, `/data-stats`, `/data-stats-trend`, `/data-stats-range`, `/health`, `/processing-errors`, `/recording-stats`; `POST /refresh-context-stats`, `/recording-stats/reset` | Runtime metrics, token usage, data counts, processing errors, recording stats | Many values are backed by SQLite monitoring tables. |
| Events | `GET /api/events/fetch`, `GET /api/events/status`, `POST /api/events/publish` | UI event bus for status changes | `publish` accepts an event payload body. |
| Vaults | `GET /api/vaults/list`, `GET /api/vaults/{id}`, `POST /api/vaults/create`, `POST /api/vaults/{id}`, `DELETE /api/vaults/{id}`, `GET /api/vaults/{id}/context` | CRUD notes/reports and context status | Stored in SQLite `vaults`; save/delete enqueue background context updates. |
| Context-agent chat | `POST /api/agent/chat`, `POST /api/agent/chat/stream`, `POST /api/agent/resume/{workflow_id}`, `GET /api/agent/state/{workflow_id}`, `DELETE /api/agent/cancel/{workflow_id}`, `GET /api/agent/test` | Context-agent non-streaming/streaming workflows | Uses `ContextAgent(enable_streaming=True)` lazily. Requires model/storage for real answers. |
| Agent conversations/messages | Prefix `/api/agent/chat`: `POST /conversations`, `GET /conversations/list`, `GET /conversations/{cid}`, `PATCH /conversations/{cid}/update`, `DELETE /conversations/{cid}/update`, message create/update/append/finished/list/interrupt routes | Persist chat conversations and streaming messages | Backed by SQLite `conversations`, `messages`, and `message_thinking`. |
| Completions | `POST /api/completions/suggest`, `/suggest/stream`, `/feedback`, `/precompute/{document_id}`, `/cache/optimize`, `/cache/clear`; `GET /api/completions/stats`, `/cache/stats` | Copilot-like note suggestions and cache maintenance | Real semantic completions need model/config/storage readiness. |

## Common request bodies

### Model settings validate/update

`POST /api/model_settings/validate` validates without saving;
`POST /api/model_settings/update` validates, saves to user settings, reloads
config, and reinitializes model clients.

```json
{
  "config": {
    "modelPlatform": "openai",
    "modelId": "gpt-4o-mini",
    "baseUrl": "https://api.openai.com/v1",
    "apiKey": "<secret>",
    "embeddingModelId": "text-embedding-3-large",
    "embeddingBaseUrl": "https://api.openai.com/v1",
    "embeddingApiKey": "<secret>",
    "embeddingModelPlatform": "openai"
  }
}
```

Required non-empty fields: VLM/chat `apiKey`, `modelId`, `baseUrl`; embedding
`embeddingApiKey` (or fallback `apiKey`), `embeddingModelId`, and embedding URL.
Doubao uses provider `doubao`; embedding validation calls Ark multimodal
embeddings.

### General settings update

`POST /api/settings/general` accepts any subset of these top-level fields:

```json
{
  "capture": {"folder_monitor": {"enabled": true}},
  "processing": {"document_processor": {"batch_size": 5}},
  "logging": {"level": "INFO"},
  "content_generation": {"activity": {"enabled": true, "interval": 900}}
}
```

An empty body returns `400 No settings provided`.

### Content generation config

```json
{
  "activity": {"enabled": true, "interval": 900},
  "tips": {"enabled": true, "interval": 3600},
  "todos": {"enabled": true, "interval": 1800},
  "report": {"enabled": true, "time": "08:00"}
}
```

Minimum intervals are enforced by Pydantic: activity `>=600` seconds; tips and
todos `>=1800` seconds; report time must match `HH:MM`.

### Upload local document

```bash
curl -s -X POST http://127.0.0.1:1733/api/documents/upload \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"/absolute/path/to/file.txt"}'
```

Response success means the file was queued; processing/storage can still fail
later if the format, model, embedding, or storage backend is not ready.

### Upload web link

```bash
curl -s -X POST http://127.0.0.1:1733/api/weblinks/upload \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","filename_hint":"example"}'
```

This route lazily initializes `web_link_capture` with default output directory
`uploads/weblinks`, then captures once. Some installed versions expose
`WebLinkCapture.submit_url(url)` with one URL argument while the route attempts
to pass `filename_hint`; if this route returns `500`, inspect that signature and
use direct `capture(urls=[...])` or patch the route before blaming browser
capture.

### Add screenshots

```json
{
  "path": "/absolute/path/to/screen.png",
  "window": "Browser",
  "create_time": "2025-01-01T12:00:00",
  "source": "manual"
}
```

Batch endpoint body:

```json
{"screenshots": [{"path": "...", "window": "...", "create_time": "...", "source": "manual"}]}
```

### Vector search

```json
{
  "query": "recent project planning notes",
  "top_k": 5,
  "context_types": ["knowledge_context", "activity_context"],
  "filters": {"knowledge_source": "local_file"}
}
```

The response envelope contains `data.results`, `data.total`, and the normalized
search parameters.

### Context-agent chat

Non-streaming:

```json
{
  "query": "Summarize my recent notes about the launch plan",
  "context": {},
  "session_id": "optional-session",
  "user_id": "optional-user",
  "conversation_id": 1
}
```

Streaming returns `text/event-stream` lines prefixed with `data:`. The first
stream event includes `session_id` and may include an `assistant_message_id` when
`conversation_id` is supplied. Use `POST /api/agent/chat/messages/{mid}/interrupt`
to cancel an active streaming message.

### Completion suggestions

```json
{
  "text": "Current note content...",
  "cursor_position": 21,
  "document_id": 1,
  "completion_types": ["semantic_continuation"],
  "max_suggestions": 3,
  "context": {}
}
```

The synchronous route returns `success`, `suggestions`, `processing_time_ms`, and
`cache_hit`. The streaming route emits progress and suggestion SSE events.
