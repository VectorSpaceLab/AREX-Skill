# Runtime-service troubleshooting

## Purpose

Use this page after basic installation/import checks pass and the issue is in
MineContext backend runtime behavior: server startup, API routes,
configuration, capture, processing, storage, generation, chat, completions, or
monitoring.

## Startup and FastAPI state

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No command specified` | `opencontext` was run without a subcommand. | Use `opencontext --help`, then `opencontext start --host 127.0.0.1 --port 1733`. |
| Port already in use | Existing backend or another service occupies the configured port. | Choose `--port <free-port>` and update frontend/API clients to match. |
| `/health` works but `/api/health` returns `OpenContext instance not initialized` | The FastAPI app was imported directly or startup failed before app state was attached. | Start through `opencontext start` or inspect logs for initialization failure in config, storage, capture, or LLM clients. |
| Startup fails while loading config | Config path is wrong, YAML is invalid, or prompt file is missing. | Confirm the file exists, run a YAML parser, and check `prompts.language` selects an existing prompt file. |

## Model and prompt failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `API key, base URL, and model must be provided` | `vlm_model` or `embedding_model` fields resolved to empty values. | Report missing key names only. Set env variables, edit YAML, or use `/api/model_settings/update`. |
| `/api/model_settings/validate` returns VLM or Embedding failure | Wrong endpoint, provider, model id, credential, or timeout. | Validate chat/VLM and embedding settings separately; confirm embedding output dimension matches storage config. |
| Prompt route update/import fails | Imported prompt content is not a YAML dictionary or is missing expected categories. | Export current prompts first, edit a small category, then import. Reset user prompts if the override file is corrupt. |
| Generation outputs are empty or malformed | Prompt group missing, JSON repair failed, model returned non-JSON, or no input context. | Enable debug generation, inspect saved prompt/response privately, and avoid exposing user context in public notes. |

## Storage and retrieval failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Vector database backend not initialized` | `storage.enabled` false, vector backend config invalid, or startup failed. | Recheck `/api/health`, storage logs, and `storage.backends` entries. |
| ChromaDB collection/telemetry/import errors | ChromaDB dependency issue or unwritable local path. | Run package import smoke, set a fresh writable `CONTEXT_PATH`, or switch to a clean environment. |
| Qdrant rejects vectors or searches fail | `vector_size` differs from `embedding_model.output_dim`, or server path/host is wrong. | Align vector size and verify Qdrant local/server connectivity before running ingestion. |
| Vector search returns no results after upload | Processing did not finish, embeddings failed, wrong `context_types`, or no stored vector. | Check logs, `/api/context_types`, monitoring data stats, and query without filters. |
| SQLite table errors | Old/corrupt app database or unwritable directory. | Back up the database, then use a fresh `CONTEXT_PATH` for isolation. Do not delete user data without approval. |

## Capture and processing failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Folder monitor emits no events | Unsupported suffix, file too large, watch path wrong, `initial_scan` cached existing files, or monitor not enabled. | Use `scripts/smoke_folder_monitor.py` to validate local logic, then inspect `watch_folder_paths`, `recursive`, `max_file_size`, and logs. |
| Delete events do not remove document contexts | Storage records lack `knowledge_file_path` metadata or storage cleanup failed. | Verify the bundled folder smoke, then inspect stored metadata for the deleted path. |
| Document upload succeeds but no context appears | Queue accepted the path but processor, VLM, embedding, or storage failed later. | Try `scripts/smoke_document_text.py` with a text fixture, then check logs and model/storage readiness. |
| Visual PDF/DOC/image processing fails | Scanned/visual pages require VLM credentials; file converter dependencies may also fail. | Verify model settings and use a text-only document smoke before debugging visual extraction. |
| Screenshot capture fails on live screen | Missing OS screen-recording permission, `mss` cannot capture display, bad region, or unwritable screenshot directory. | Confirm permissions, region bounds, and `capture.screenshot.storage_path`. Do not run live capture without user consent. |
| Screenshot processing fails after file upload | File path inaccessible to backend, unsupported image, VLM missing, or embedding/storage unavailable. | Validate the path from the backend process, then check model/storage settings. |
| Web-link capture fails | Invalid URL, network blocked, `crawl4ai` missing for markdown, Playwright/browser missing for PDF, route signature mismatch, or unwritable output dir. | Use direct `WebLinkCapture.capture(urls=[...])` with explicit mode after confirming network permission. If the API route passes `filename_hint` to a one-argument `submit_url`, patch route glue or call direct capture. |

## API authentication failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `401 API key required` | `api_auth.enabled` true and request lacks key. | Add `X-API-Key` header or `?api_key=` query parameter. Do not print the key. |
| `401 Invalid API key` | Secret mismatch or whitespace in config. | Compare only key fingerprints or lengths; update `api_auth.api_keys` safely. |
| `500 No valid API keys configured` | Auth enabled but env interpolation produced empty keys. | Set `CONTEXT_API_KEY` or disable auth for trusted local-only debugging. |
| Protected route unexpectedly open | Path appears in `api_auth.excluded_paths`. | Remove broad wildcard exclusions unless the service is trusted and bound locally. |

## Generation, chat, completion, and monitoring failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Manual debug generation returns no output | No source contexts, disabled task, missing prompt group, or model error. | Query contexts first, verify content-generation config, then enable debug output privately. |
| Todo deduplication fails | Embedding client, vector storage, or todo collection not initialized. | Confirm embedding settings and storage before running todo examples. |
| Chat stream never completes | Model call blocked, tool loop failed, message storage error, or stream interrupted. | Use non-streaming `/api/agent/chat` first; inspect message/conversation storage only after model settings pass. |
| Completion suggestions fail | Completion service disabled, missing document context, model/storage unavailable, or cache corrupt. | Check `/api/completions/stats`, clear cache only with approval, and verify model/storage readiness. |
| Monitoring endpoint fails | Monitor not initialized, SQLite tables unavailable, or data period invalid. | Use `/api/monitoring/health`, then check SQLite path/schema and route query parameters. |

## When to stop

Stop and ask for user input when the next step needs:

- real API keys, model endpoints, or local model server details;
- permission to capture screen contents, crawl external URLs, or read user files;
- permission to reset or delete a local database, ChromaDB/Qdrant store, prompt
  override file, or generated report/debug directory;
- a long-running server, browser, model, or packaging process in a user-owned
  workspace.
