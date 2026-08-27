# API Server Reference

Use this reference for the FastAPI service, auth, settings, health checks, and service-oriented routers.

## Server entry point

The backend app is `m_flow.api.client:app`.
Programmatic startup uses `start_api_server(host="0.0.0.0", port=8000)`.

Health endpoints:

- `GET /`
- `GET /health`
- `GET /health/detailed`

The app adds CORS middleware and custom OpenAPI auth schemes for bearer and cookie auth.

## Router families

| Prefix | Main endpoints | Notes |
| --- | --- | --- |
| `/api/v1/auth` | login, logout, register, forgot/reset password, verify | FastAPI Users-backed auth flows |
| `/api/v1/users` | `/me`, list, retrieve, update, delete | list is superuser-only |
| `/api/v1/settings` | GET / POST | system settings for LLM, vector DB, embeddings |
| `/api/v1/datasets` | CRUD, data lists, status | dataset visibility is permission-aware |
| `/api/v1/add` | POST | raw ingestion entry point |
| `/api/v1/ingest` | POST | one-step ingest |
| `/api/v1/memorize` | POST + websocket progress | graph-building pipeline |
| `/api/v1/search` | POST, GET history, simplified query | supports search and query surfaces |
| `/api/v1/delete` | DELETE + node preview/delete | destructive data removal |
| `/api/v1/update` | PATCH | replace existing data content |
| `/api/v1/graph` | graph views | visualization-oriented responses |
| `/api/v1/permissions` | roles, tenants, dataset grants | multi-tenant access control |
| `/api/v1/sync` | sync + status | cloud sync background workflow |
| `/api/v1/pipeline` | active pipeline status, dismiss | service tracking and cleanup |
| `/api/v1/maintenance` | episode quality, episode-size check | safe maintenance actions |
| `/api/v1/manual` | manual ingest, patch node, schema | bypass LLM extraction |
| `/api/v1/prune` | data/system/all pruning | guarded destructive admin actions |
| `/api/v1/prompts` | prompt browse/update/reset | prompt management |
| `/api/v1/responses` | OpenAI-compatible responses API | function-calling integration |
| `/api/v1/activity` | activity list | recent operations |
| `/api/v1/playground` | session, chat, persons, flush, link-face, rename-person, vision-status, start/stop/restart-vision, asr, set-llm | face-aware playground |
| `/api/v1` | coreference settings/debug routes | note the mixed-prefix placement |

## Auth and secrets

| Env var | Purpose |
| --- | --- |
| `MFLOW_ENV` | production safety gate for secrets |
| `REQUIRE_AUTHENTICATION` | requires login when true |
| `ENABLE_BACKEND_ACCESS_CONTROL` | per-user and per-dataset isolation; also forces auth when true |
| `FASTAPI_USERS_JWT_SECRET` | JWT secret shared by cookie and bearer auth |
| `FASTAPI_USERS_RESET_PASSWORD_TOKEN_SECRET` | password reset token secret |
| `FASTAPI_USERS_VERIFICATION_TOKEN_SECRET` | verification token secret |
| `AUTH_TOKEN_COOKIE_NAME` | cookie name used by the client transport |

Behavior notes:

- `get_authenticated_user()` returns the seed user only when auth is effectively optional.
- The cookie transport is local-development friendly (`httponly`, `samesite=Lax`, `secure=False`).
- Production/staging/test environments must set the JWT and token secrets explicitly.

## Settings endpoints

`GET /api/v1/settings` returns the current service configuration for:

- LLM provider / model / endpoint / API key
- vector DB provider / URL / key
- embedding provider / model / dimensions / endpoint

`POST /api/v1/settings` accepts a partial update payload with any of these sections:

```json
{
  "llm": { "provider": "openai", "model": "gpt-5-nano", "api_key": "..." },
  "vector_db": { "provider": "lancedb", "url": "", "api_key": "" },
  "embedding": { "provider": "openai", "model": "text-embedding-3-large", "dimensions": 3072 }
}
```

Embedding API keys are write-only in the response model.

## Service integration cues

- `GET /api/v1/pipeline/active` shows current pipeline runs.
- `GET /api/v1/sync/status` shows cloud sync status.
- `POST /api/v1/memorize` has websocket progress at `/api/v1/memorize/subscribe/{workflow_run_id}`.
- `GET /api/v1/settings/coreference` and `POST /api/v1/settings/coreference` support the frontend coreference panel.
- `GET /api/v1/coreference/stats` and `POST /api/v1/coreference/sessions/{sessionId}/reset` are the corresponding debug controls.

## What this reference does not own

- In-process `m_flow.add/search/query/memorize/learn` usage belongs to `core-memory-api`.
- Storage-provider configuration details belong to `retrieval-graph-search`.
- Loader and pipeline internals belong to `ingestion-pipelines`.
