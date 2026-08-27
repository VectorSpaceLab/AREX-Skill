# Runtime workflows

## 1. Start and verify the backend

Use this workflow before API, capture, storage, generation, or chat debugging.

```bash
python -c "import opencontext; print(opencontext.__version__)"
opencontext --help
mkdir -p .minecontext-data
CONTEXT_PATH="$PWD/.minecontext-data" \
opencontext start --config config/config.yaml --host 127.0.0.1 --port 1733
```

In another shell:

```bash
curl -s http://127.0.0.1:1733/health
curl -s http://127.0.0.1:1733/api/health
curl -s http://127.0.0.1:1733/api/auth/status
```

Expected `/health` envelope:

```json
{"code":0,"status":200,"message":"success","data":{"status":"healthy","service":"opencontext"}}
```

Expected `/api/health` includes `components.config`, `components.storage`,
`components.llm`, `components.capture`, and `components.consumption`. If
`storage` or `llm` is false, continue with configuration/storage checks before
running generation or search.

## 2. Configure and validate models

1. Prepare settings JSON without printing actual keys in notes.
2. Validate first:

   ```bash
   curl -s -X POST http://127.0.0.1:1733/api/model_settings/validate \
     -H 'Content-Type: application/json' \
     -d @model-settings.json
   ```

3. Save only after validation succeeds:

   ```bash
   curl -s -X POST http://127.0.0.1:1733/api/model_settings/update \
     -H 'Content-Type: application/json' \
     -d @model-settings.json
   ```

4. Recheck `/api/health`. For Doubao, ensure both the visual/chat model and the
   embedding model are enabled in the provider console. For OpenAI-compatible
   local servers, verify the base URL includes the API prefix expected by that
   server.

## 3. Run deterministic local smokes

These are CPU-only and do not start the server.

From the sub-skill directory:

```bash
python scripts/smoke_folder_monitor.py
python scripts/smoke_document_text.py
```

For a source checkout that is not installed, pass it explicitly:

```bash
python scripts/smoke_folder_monitor.py --repo-root /path/to/MineContext
python scripts/smoke_document_text.py --repo-root /path/to/MineContext
```

`smoke_folder_monitor.py` verifies create/update/delete event handling with a
temporary directory and mocked storage. `smoke_document_text.py` creates a
throwaway runtime config, uses a temporary `.txt` fixture, monkeypatches only the
LLM-backed text chunker call to keep the smoke offline, and validates that
`DocumentProcessor.real_process()` returns `knowledge_context` output.

## 4. Upload and process a local document

Use this for a running backend and a file path accessible to the backend
process.

```bash
curl -s -X POST http://127.0.0.1:1733/api/documents/upload \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"/absolute/path/to/document.txt"}'
```

Validation steps:

1. Response `code` should be `0` with a queued message.
2. Check logs for `DocumentProcessor` `Successfully processed document`.
3. Query context types:

   ```bash
   curl -s http://127.0.0.1:1733/api/context_types
   ```

4. Search for a distinctive phrase:

   ```bash
   curl -s -X POST http://127.0.0.1:1733/api/vector_search \
     -H 'Content-Type: application/json' \
     -d '{"query":"distinctive phrase","top_k":5,"context_types":["knowledge_context"]}'
   ```

Plain text and structured files can be inspected locally first with
`scripts/smoke_document_text.py`. Visual PDFs, office documents with images, and
screenshots require VLM credentials for complete extraction.

## 5. Verify folder monitoring with mocked storage

Run the bundled smoke:

```bash
python scripts/smoke_folder_monitor.py --verbose
```

What it proves:

- `FolderMonitorCapture.initialize()` accepts a watch directory config.
- Create and update events become `RawContextProperties` with `source=local_file`
  and `additional_info.event_type` set to `file_created` or `file_updated`.
- Delete events do not emit raw contexts, but do call storage cleanup for
  matching `knowledge_context` ids.

For a real server, enable `capture.folder_monitor.enabled`, set
`watch_folder_paths`, ensure paths are readable, and keep `initial_scan: true` if
existing files should not all be treated as new on startup.

## 6. Queue screenshots

For existing screenshot files:

```bash
curl -s -X POST http://127.0.0.1:1733/api/add_screenshot \
  -H 'Content-Type: application/json' \
  -d '{"path":"/absolute/path/to/screen.png","window":"Browser","create_time":"2025-01-01T12:00:00","source":"manual"}'
```

For live capture, set `capture.screenshot.enabled: true`, choose a writable
`storage_path`, and confirm OS screen-recording permissions. Full screenshot
processing uses `ScreenshotProcessor`, perceptual hashing, VLM extraction,
embedding, and storage, so blank model settings or screen permission failures
are expected blockers.

## 7. Capture a web link

API path:

```bash
curl -s -X POST http://127.0.0.1:1733/api/weblinks/upload \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","filename_hint":"example"}'
```

Direct component path for debugging:

```python
from opencontext.context_capture.web_link_capture import WebLinkCapture

cap = WebLinkCapture()
assert cap.initialize({"mode": "markdown", "output_dir": "uploads/weblinks"})
assert cap.start()
raw_contexts = cap.capture(urls=["https://example.com"])
cap.stop()
```

Prerequisites: `crawl4ai` for markdown mode, Playwright plus installed browser
for PDF mode, network access to the URL, and writable output directory. If the
API route returns `500`, inspect whether the installed `submit_url` method takes
only `url` while the route passes `filename_hint`; direct `capture(urls=[...])`
can isolate browser/crawler issues from route glue issues.

## 8. Query contexts and manage search results

List context types:

```bash
curl -s http://127.0.0.1:1733/api/context_types
```

Vector search:

```bash
curl -s -X POST http://127.0.0.1:1733/api/vector_search \
  -H 'Content-Type: application/json' \
  -d '{"query":"launch plan","top_k":5,"context_types":["knowledge_context","activity_context"],"filters":{}}'
```

Delete a context only with user approval:

```bash
curl -s -X POST http://127.0.0.1:1733/contexts/delete \
  -H 'Content-Type: application/json' \
  -d '{"id":"<context-id>","context_type":"knowledge_context"}'
```

If search returns empty after ingestion, check storage initialization,
embedding model validity, context type filters, and whether processing actually
stored contexts.

## 9. Configure generated content and debug prompts

Read/update scheduled task config:

```bash
curl -s http://127.0.0.1:1733/api/content_generation/config
curl -s -X POST http://127.0.0.1:1733/api/content_generation/config \
  -H 'Content-Type: application/json' \
  -d '{"activity":{"enabled":true,"interval":900},"todos":{"enabled":true,"interval":1800},"tips":{"enabled":true,"interval":3600},"report":{"enabled":true,"time":"08:00"}}'
```

Manual debug generation routes:

```bash
curl -s -X POST 'http://127.0.0.1:1733/api/debug/generate/activity?minutes=60'
curl -s -X POST 'http://127.0.0.1:1733/api/debug/generate/todos?lookback_minutes=120'
curl -s -X POST 'http://127.0.0.1:1733/api/debug/generate/tips?lookback_minutes=120'
curl -s -X POST 'http://127.0.0.1:1733/api/debug/generate/report?start_time=2025-01-01T00:00:00&end_time=2025-01-01T23:59:59'
```

Prompt/debug routes can list reports/todos/activities/tips, export/restore
prompts, retrieve category prompt groups, update custom prompts, and regenerate
from saved debug files. Enable `content_generation.debug.enabled` before relying
on prompt-history endpoints.

## 10. Use context-agent chat and conversation storage

Create a conversation:

```bash
curl -s -X POST http://127.0.0.1:1733/api/agent/chat/conversations \
  -H 'Content-Type: application/json' \
  -d '{"page_name":"home"}'
```

Non-streaming chat:

```bash
curl -s -X POST http://127.0.0.1:1733/api/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"query":"What did I work on today?","context":{},"conversation_id":1}'
```

Streaming chat:

```bash
curl -N -X POST http://127.0.0.1:1733/api/agent/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"query":"Summarize my recent context","context":{},"conversation_id":1}'
```

Interrupt active message:

```bash
curl -s -X POST http://127.0.0.1:1733/api/agent/chat/messages/<assistant_message_id>/interrupt
```

Chat depends on the context-agent workflow, model credentials, tools, storage,
and prompts. Use `/api/agent/test` only after model settings are known good.

## 11. Use intelligent completions

Synchronous suggestions:

```bash
curl -s -X POST http://127.0.0.1:1733/api/completions/suggest \
  -H 'Content-Type: application/json' \
  -d '{"text":"Draft launch note","cursor_position":17,"max_suggestions":3,"context":{}}'
```

Stats and cache maintenance:

```bash
curl -s http://127.0.0.1:1733/api/completions/stats
curl -s http://127.0.0.1:1733/api/completions/cache/stats
curl -s -X POST http://127.0.0.1:1733/api/completions/cache/optimize
```

Completion suggestions can use templates, semantic continuation, and reference
suggestions. Semantic/reference suggestions require model and storage readiness.

## 12. Monitor the runtime

```bash
curl -s http://127.0.0.1:1733/api/monitoring/overview
curl -s http://127.0.0.1:1733/api/monitoring/context-types?force_refresh=true
curl -s http://127.0.0.1:1733/api/monitoring/token-usage?hours=24
curl -s http://127.0.0.1:1733/api/monitoring/processing?hours=24
curl -s http://127.0.0.1:1733/api/monitoring/processing-errors?hours=1&top=5
curl -s http://127.0.0.1:1733/api/monitoring/recording-stats
```

If monitoring endpoints fail but `/health` works, check SQLite path/schema,
monitor initialization, and whether storage was initialized before metrics were
recorded.

## Source example decisions encoded in this skill

| Source example role | Skill decision | Reason / prerequisite |
| --- | --- | --- |
| Folder monitor verification | Adapted as `scripts/smoke_folder_monitor.py` | Safe CPU-only create/update/delete behavior with mocked storage cleanup. |
| Document processor example | Adapted as `scripts/smoke_document_text.py` | Safe CPU-only text fixture; no model, server, storage, or checkout dependency. |
| Todo deduplication example | Reference-only | Requires embedding model and vector storage; not safe as default smoke. |
| Web-link processor example | Reference-only | Requires browser/crawler dependencies, network, and sometimes route signature debugging. |
| Screenshot processor examples | Reference-only | Require user screenshot files plus VLM credentials; live capture additionally needs OS screen permission. |
| Screenshot-to-insights example | Reference-only | Requires screenshot processing, generation prompts, and external model credentials. |
| Debug-file regeneration helper | Reference-only | Requires an existing debug JSON file and model credentials; output can expose user prompt/context content. |
