# API Routes

The API server mounts routes at natural FastAPI paths. If `LIGHTRAG_API_PREFIX` or `--api-prefix` is set, the prefix is FastAPI `root_path` metadata for reverse proxies and WebUI runtime config; it is not duplicated in OpenAPI path keys.

## Authentication Pattern

Most API routes use the combined auth dependency:

- JWT: call `POST /login` with OAuth2 password-form fields and send `Authorization: Bearer <token>`.
- API key: set `X-API-Key` when `LIGHTRAG_API_KEY` or `--key` is configured.
- Whitelist: paths matching `WHITELIST_PATHS` can bypass credentials; default includes `/health` and `/api/*`.

Example automation headers:

```bash
curl -H 'X-API-Key: <configured-api-key>' http://localhost:9621/health
curl -H 'Authorization: Bearer <jwt>' http://localhost:9621/documents
```

Do not place secrets in reusable examples or logs. When documenting user-specific commands, use placeholders.

## Root, Health, Auth, Docs, And WebUI

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Redirects browsers to the WebUI mount. |
| `GET` | `/health` | Returns system status, storage/provider configuration summary, pipeline busy flags, queue status, versions, and WebUI availability. |
| `GET` | `/auth-status` | Reports auth mode and returns a guest token when login auth is disabled. |
| `POST` | `/login` | OAuth2 password login; returns a JWT token or guest token in no-account mode. |
| `GET` | `/docs` | Offline Swagger UI. |
| `GET` | `/openapi.json` | OpenAPI schema. |
| `GET` | `/webui` and `/webui/` | Packaged WebUI entry point when assets are installed or built. |

Health payloads are operational diagnostics, not a stable public config contract for secrets. The server intentionally reports provider/storage names, status, and queue health without exposing API keys.

## Document Routes

All document routes are mounted under `/documents`.

| Method | Path | Purpose | Safe usage pattern |
| --- | --- | --- | --- |
| `POST` | `/documents/upload` | Upload one file into the input directory and enqueue processing. | Use multipart file upload; respect `MAX_UPLOAD_SIZE`; keep original source filename meaningful for citations. |
| `POST` | `/documents/text` | Insert one text document. | Body includes `text`, optional `file_source`, optional shared chunking config. |
| `POST` | `/documents/texts` | Insert multiple text documents. | `texts` and optional `file_sources` lengths must match. |
| `POST` | `/documents/scan` | Scan `INPUT_DIR` for new or retryable files. | Refuses if the pipeline, another scan, or pending uploads are active. |
| `GET` | `/documents` | Return documents grouped by status. | Use for simple status inspection. |
| `POST` | `/documents/paginated` | Return paginated status records with filters and sort options. | Prefer for WebUI-like tables and polling. |
| `GET` | `/documents/pipeline_status` | Return current pipeline progress and messages. | High-frequency polling path; token auto-renew is skipped here. |
| `GET` | `/documents/track_status/{track_id}` | Return documents associated with an upload/insert/scan track ID. | Use track IDs returned by upload/insert/scan responses. |
| `GET` | `/documents/status_counts` | Return counts by document status. | Lightweight dashboard/status query. |
| `POST` | `/documents/reprocess_failed` | Requeue failed documents. | Retains original track IDs. |
| `POST` | `/documents/cancel_pipeline` | Request pipeline cancellation. | Cancellation is cooperative; inspect status afterward. |
| `DELETE` | `/documents` | Clear all document data. | Destructive; refuses while busy. |
| `DELETE` | `/documents/delete_document` | Delete selected document IDs and optional files/cache. | Destructive; send `doc_ids`, `delete_file`, and `delete_llm_cache` intentionally. |
| `POST` | `/documents/clear_cache` | Clear selected cache data. | Operational cache cleanup; avoid while ingestion/query work is active. |

Document route details such as parser hints, chunking payload schemas, scan classification, `request_pending`, destructive busy windows, and upload/scan/delete concurrency internals belong to `../../document-pipeline/SKILL.md`. For API-level debugging, the key rule is: upload/text enqueue can overlap normal processing, but scan classification and destructive delete/clear windows intentionally reject conflicting requests to avoid lost files or torn-down storage writes.

## Query Routes

| Method | Path | Response type | Purpose |
| --- | --- | --- | --- |
| `POST` | `/query` | `application/json` | Non-streaming query endpoint. Ignores request `stream` and forces `stream=false`. |
| `POST` | `/query/stream` | `application/x-ndjson` | Streaming-capable endpoint. Defaults to streaming unless `stream=false`; cached or non-streaming results still arrive as NDJSON. |
| `POST` | `/query/data` | `application/json` | Structured query result data with entities, relationships, chunks, references, and metadata. |

Shared query body fields include:

| Field | Meaning |
| --- | --- |
| `query` | User query text; minimum length validation applies. |
| `mode` | One of `local`, `global`, `hybrid`, `naive`, `mix`, or `bypass`; `mix` is the usual graph-plus-vector mode. |
| `top_k`, `chunk_top_k` | Retrieval counts; omitted values use server defaults. |
| `max_entity_tokens`, `max_relation_tokens`, `max_total_tokens` | Context budget controls. |
| `only_need_context`, `only_need_prompt` | Diagnostics that return retrieved context or assembled prompt instead of a normal answer. |
| `conversation_history` | History passed for LLM response context, not retrieval. |
| `user_prompt` | Per-request prompt override/addition. |
| `enable_rerank` | Per-request rerank toggle. |
| `include_references` | Include references in `/query` and `/query/stream`; `/query/data` always includes reference data. |
| `include_chunk_content` | Include actual chunk text in references for debugging/evaluation. |

Minimal non-streaming body:

```json
{
  "query": "What does this knowledge base say about project risks?",
  "mode": "mix",
  "enable_rerank": false
}
```

For `/query/stream`, consume newline-delimited JSON objects. The first object may contain `references`; later objects contain `response` chunks or an `error` object. Proxies should not buffer streaming responses; the server sets `X-Accel-Buffering: no` on streaming routes.

## Graph Routes

Read routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/graph/label/list` | List graph labels. |
| `GET` | `/graph/label/popular` | Return popular labels with a default limit. |
| `GET` | `/graph/label/search` | Search labels by query text. |
| `GET` | `/graphs` | Return a graph neighborhood/data view. |
| `GET` | `/graph/entity/exists` | Check whether an entity exists. |

Mutation routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/graph/entity/edit` | Update entity data; optional rename/merge behavior. |
| `POST` | `/graph/relation/edit` | Update relation data. |
| `POST` | `/graph/entity/create` | Create an entity with property data. |
| `POST` | `/graph/relation/create` | Create a relation between existing entities. |
| `POST` | `/graph/entities/merge` | Merge duplicate/misspelled entities into a target entity. |
| `DELETE` | `/graph/entity/delete` | Delete one entity. |
| `DELETE` | `/graph/relation/delete` | Delete one relation. |

All graph mutation routes check the document pipeline busy guard and return HTTP `409` when ingestion, scan, delete, or another protected operation makes mutation unsafe. This prevents editing graph state while document-derived graph updates are in flight. Storage backend behavior and graph persistence details belong to `../../storage-backends/SKILL.md`.

## Ollama-Compatible Routes

Ollama emulation is mounted under `/api`:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/version` | Return an Ollama-style version response. |
| `GET` | `/api/tags` | Return the simulated model name/tag. |
| `GET` | `/api/ps` | Return simulated running model information. |
| `POST` | `/api/generate` | Ollama-style generate endpoint backed by LightRAG query behavior. |
| `POST` | `/api/chat` | Ollama-style chat endpoint backed by LightRAG query behavior. |

Configuration fields `OLLAMA_EMULATING_MODEL_NAME` and `OLLAMA_EMULATING_MODEL_TAG` control the advertised model identity. These routes support JSON and octet-stream JSON-style request parsing in the implementation. `/api/*` is in the default whitelist, so tighten `WHITELIST_PATHS` if Ollama compatibility should require auth in a deployed environment.

## Safe Operational Checks

Use route checks that do not upload, delete, or trigger model calls when validating deployment wiring:

```bash
curl http://localhost:9621/health
curl http://localhost:9621/openapi.json
curl http://localhost:9621/auth-status
```

When auth is enabled, use either a JWT or API key header. Avoid using `/query`, `/documents/upload`, graph mutation routes, or destructive document routes as generic liveness probes because they can call models, mutate state, or depend on backend readiness beyond HTTP routing.
