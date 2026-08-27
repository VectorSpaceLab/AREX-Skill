# HTTP services and endpoint contracts

DB-GPT 0.8.1 composes several `dbgpt-serve` components into the application FastAPI process. The route prefix is part of the contract. Confirm the deployed OpenAPI document at `<origin>/docs` before using a compatibility or custom prefix.

## Origin, authentication, and response shape

The ordinary web application defaults to `http://localhost:5670` (host `0.0.0.0`, port `5670`). Stable v2 application endpoints are under `/api/v2`; the service components are generally under `/api/v2/serve/<component>`. A server can be configured differently, and a standalone sandbox service defaults to port `8000`.

When global or per-service API keys are configured, send:

```http
Authorization: Bearer <key>
```

The configured key list is comma-separated. A missing key list means the endpoint's auth dependency allows requests; do not interpret that as a production-safe configuration. Invalid or absent credentials produce HTTP 401 with an OpenAI-shaped error detail whose code is `invalid_api_key`. Never log a bearer token.

Many DB-GPT service methods return an envelope like:

```json
{"success": true, "err_code": null, "err_msg": null, "data": {}}
```

Failure can be represented as `success: false` inside HTTP 200, or as HTTP 400/401/404/5xx depending on the route. Always inspect both status and envelope. A health response only proves the route/process is reachable.

## Mounted service families

| Capability | Default prefix | Main routes |
|---|---|---|
| Datasource service | `/api/v2/serve` | `/datasources`, `/datasource-types`, `/datasources/test-connection`, `/datasources/{id}/refresh` |
| Knowledge/RAG service | `/api/v2/serve/knowledge` | `/spaces`, `/documents`, `/spaces/{id}/retrieve`, `/documents/{id}/sync`, `/{space}/stats` |
| AWEL flow service | `/api/v2/serve/awel` and compatibility `/api/v1/serve/awel` | `/flows`, `/flows/{uid}`, `/chat/flows`, `/nodes`, `/variables`, `/flow/debug`, import/export/templates |
| File service | `/api/v2/serve/file` | `/files/{bucket}`, `/files/{bucket}/{file_id}`, `/files/metadata` |
| Model service | `/api/v2/serve/model` and compatibility `/api/v1/worker` | `/model-types`, `/models`, `/models/start`, `/models/stop` |
| App service | `/api/v2/serve/apps` | collection app list/create/update/delete and `/{app_id}` detail |
| Connector service | `/api/v2/serve/connectors` | connector collection, types, test, tools, confirmation |
| Conversation service | `/api/v1/chat/dialogue` | legacy conversation query/list/history routes |
| Standalone sandbox | `/api` when using its standalone server | `/health`, `/connect`, `/configure`, `/execute`, `/manual`, `/status`, `/sessions`, `/get_file` |

The service implementation mounts routers with these prefixes; the path shown in a component router is relative to that prefix. Do not concatenate the app's `/api` prefix twice.

## Application OpenAPI routes

The web application mounts the v1 application router under `/api`, so its paths include `/api/v1/...`:

- `/api/v1/test` is a simple status route.
- `/api/v1/chat/completions` is the legacy chat route and emits streaming response records even for some non-streaming paths. `/api/v2/chat/completions` is the preferred typed/OpenAI-compatible route.
- `/api/v1/chat/db/list`, `/api/v1/chat/db/add`, `/api/v1/chat/db/edit`, `/api/v1/chat/db/delete`, `/api/v1/chat/db/test/connect`, `/api/v1/chat/db/refresh`, `/api/v1/chat/db/summary`, and `/api/v1/chat/db/support/type` manage legacy application datasource profiles. These are not the same request schemas as `/api/v2/serve/datasources`.
- `/api/v1/resource/params/list` and `/api/v1/chat/mode/params/list` return selectable database, knowledge, or tool parameters for the legacy UI.
- `/api/v1/resource/file/upload`, `/api/v1/resource/file/read`, and `/api/v1/resource/file/delete` handle conversation files. Upload uses multipart files plus a conversation/chat-mode context; read/delete use conversation and file keys.
- `/api/v1/python/file/upload` stores a user-scoped Python file beneath the configured work directory. User IDs are restricted to safe alphanumeric/underscore/hyphen components and filenames must remain beneath the upload directory. Empty files fail. A response may contain an absolute server path; it is not portable and must not be exposed as a trusted client-side path.
- `/api/v1/skills/list`, `/api/v1/skills/detail`, `/api/v1/skills/upload`, and `/api/v1/skills/import_github` list, inspect, upload, or import skill packages. Uploading/importing is a state-changing operation; review archive paths and source trust first. Remote import downloads a GitHub/skills.sh archive, has a 50 MiB download limit, and is not a safe default validation action.
- `/api/v1/agent/files/download` serves only files under server-approved agent temporary/root directories and returns 403 for paths outside that allow-list; `/api/v1/agent/skills/download` packages an existing skill directory.
- `/api/v1/app/...` and `/api/v1/agents/list` expose legacy app/agent management. The v2 app collection is under `/api/v2/serve/apps`.
- `/api/v1/model/types` and deprecated `/api/v1/model/supports` are legacy model discovery routes. Prefer the v2 model service for service operations.

The application v2 chat route is `/api/v2/chat/completions`. Its request schema requires `model` and `messages`; a specialized `chat_mode` requires `chat_param`. It accepts normal, app, flow, knowledge, data, DB-QA, and dashboard modes. `chat_app` requires `stream=true`; flow can be streamed or non-streamed. A valid JSON request can still fail later if the model, flow, app, database, or knowledge space is unavailable.

## Datasource service

### Schemas

The preferred dynamic request has:

```json
{
  "type": "sqlite",
  "params": {"path": "/approved/local/file.db"},
  "description": "optional description",
  "id": null
}
```

The compatibility request has `db_type`, `db_name`, optional file `db_path`, `db_host`, `db_port`, `db_user`, `db_pwd`, `comment`, and `ext_config`. Do not transmit a database password in logs or fixtures.

### Operations

```text
POST /api/v2/serve/datasources
PUT  /api/v2/serve/datasources
GET  /api/v2/serve/datasources[?db_type=sqlite]
GET  /api/v2/serve/datasources/{datasource_id}
DELETE /api/v2/serve/datasources/{datasource_id}
POST /api/v2/serve/datasources/test-connection
POST /api/v2/serve/datasources/{datasource_id}/refresh
GET  /api/v2/serve/datasource-types
```

Create and update use JSON. Test-connection validates the configuration but does not create it. A listed type only means the server catalog recognizes it; the connector package and external server may still be missing.

## Knowledge and document service

Spaces use JSON fields `id`, `name`, `vector_type`, `domain_type`, `desc`, `owner`, and `context`. Space creation is the dependency for documents. The service routes are:

```text
POST /api/v2/serve/knowledge/spaces
PUT  /api/v2/serve/knowledge/spaces
GET  /api/v2/serve/knowledge/spaces[?page=1&page_size=20]
GET  /api/v2/serve/knowledge/spaces/{space_id}
DELETE /api/v2/serve/knowledge/spaces/{space_id}
POST /api/v2/serve/knowledge/spaces/{space_id}/retrieve
GET  /api/v2/serve/knowledge/{space_id}/stats
```

A retrieve body is `{ "query": "...", "top_k": 5, "score_threshold": 0.0 }`; `space_id` is supplied by the path and populated by the server. Retrieval and indexing dependencies belong to the data/RAG route; this route only identifies the HTTP boundary.

Document creation is multipart form data, not a JSON local-path reference:

```text
POST /api/v2/serve/knowledge/documents
form: doc_name, doc_type, space_id
optional: content, doc_file
```

Other document routes are:

```text
GET    /api/v2/serve/knowledge/documents[?page=1&page_size=20]
GET    /api/v2/serve/knowledge/documents/{document_id}
DELETE /api/v2/serve/knowledge/documents/{document_id}
POST   /api/v2/serve/knowledge/documents/sync       # JSON list
POST   /api/v2/serve/knowledge/documents/batch_sync  # JSON list
POST   /api/v2/serve/knowledge/documents/{document_id}/sync
```

A sync item has optional integer `doc_id`, `space_id`, `model_name`, and `chunk_parameters`. The single-document sync defaults a missing chunk configuration to `ChunkParameters(chunk_strategy="Automatic")`. Use the RAG route for chunk strategy and embedding/provider semantics.

## Flow service and flow execution

Flow CRUD uses `FlowPanel`-shaped JSON:

```text
POST   /api/v2/serve/awel/flows
PUT    /api/v2/serve/awel/flows/{uid}
GET    /api/v2/serve/awel/flows/{uid}
DELETE /api/v2/serve/awel/flows/{uid}
GET    /api/v2/serve/awel/flows[?name=...&uid=...&page=1&page_size=20]
GET    /api/v2/serve/awel/chat/flows[?name=...&uid=...]
```

`POST /nodes` discovers registered operator/resource metadata; `POST /nodes/refresh` accepts a node ID, `flow_type` (`operator` or `resource`), class/type names, and refresh options. Variables and debug/import/export/template routes are service APIs and require their exact OpenAPI schemas.

Flow execution has two boundaries:

1. Chat-compatible execution: `POST /api/v2/chat/completions` with `chat_mode="chat_flow"`, `chat_param=<flow uid>`, `model`, and `messages`. Use `stream=true` for stream output.
2. Persisted flow trigger execution: resolve one flow, inspect its metadata for one HTTP trigger, then call the trigger path with the method and JSON/query placement declared by that trigger. Do not guess a trigger path or run a flow when multiple candidates match.

Flow update is UID-addressed in the v2 service. Older client examples may show a collection PUT; confirm the deployed schema before using such a helper.

## App and agent operations

The v2 app service supports:

```text
GET    /api/v2/serve/apps[?page=1&page_size=20&user_name=...&sys_code=...]
GET    /api/v2/serve/apps/{app_id}
POST   /api/v2/serve/apps
PUT    /api/v2/serve/apps/{app_id}
DELETE /api/v2/serve/apps/{app_id}?user_code=...&sys_code=...
```

The body is a `GptsApp` model, not the smaller read-only `AppModel` returned by the Python client helper. Legacy app management under `/api/v1/app/...` adds create/edit/publish/collect/resource and admin operations. App chat uses the v2 chat route with app mode and streaming. Agent graph/resource construction belongs to `agents-and-awel`.

Skill uploads, personal plugin uploads, and GitHub imports can write server state or install executable content. Keep them disabled in automated discovery; use allow-lists, archive traversal checks, explicit user authorization, and cleanup. Archive extraction has an explicit traversal guard, but the current 0.8.1 single-file `skill_upload` path has a native regression: a traversal-shaped upload filename was accepted and normalized into the user skill area. Do not claim filename containment is enforced until that endpoint is patched and its traversal/absolute/Windows-separator tests pass; use a server-side basename/containment guard and reject before writing the temporary file.

## File service

The file service uses a bucket plus opaque file ID:

```text
POST   /api/v2/serve/file/files/{bucket}       multipart list of files
GET    /api/v2/serve/file/files/{bucket}/{file_id}
DELETE /api/v2/serve/file/files/{bucket}/{file_id}
GET    /api/v2/serve/file/files/metadata?uri=...
GET    /api/v2/serve/file/files/metadata?bucket=...&file_id=...
POST   /api/v2/serve/file/files/metadata/batch  JSON uris OR bucket_file_pairs
```

The batch request must supply exactly one of `uris` or `bucket_file_pairs`; each pair has `bucket` and `file_id`. Download is streamed and includes a content-disposition filename. File server chunk sizes, backend, local storage location, and transfer timeout are configuration-dependent; no universal HTTP upload limit is guaranteed by the route. Check the actual deployment/storage backend before sending large files.

## Model service

The model service accepts `WorkerStartupRequest` for start/create/stop operations and exposes:

```text
GET  /api/v2/serve/model/model-types
GET  /api/v2/serve/model/models
POST /api/v2/serve/model/models
POST /api/v2/serve/model/models/start
POST /api/v2/serve/model/models/stop
```

Model startup fields include host, port, model, worker type, worker name, user/system identifiers, and a parameter mapping containing provider/backend details. The model route can return an unsuccessful `Result` for not found, multiple matches, or startup failure. Model discovery may contact a controller; a 502 or timeout is a controller/deployment problem, not proof that the model name is invalid. Provider and hardware facts belong to `models-and-serving`.

## Standalone sandbox API

`initialize_sandbox(app=existing_app)` registers routes without starting a server. Calling it without an app creates a FastAPI application and starts Uvicorn, so do not call that form during import/help checks.

The standalone service uses these Pydantic request bodies:

```json
POST /api/connect
{"user_id":"user", "task_id":"task", "image_type":"python"}

POST /api/configure
{"user_id":"user", "task_id":"task", "config_info":{"language":"python", "dependencies":[]}}

POST /api/execute
{"session_id":"user_task", "code_type":"python", "code_content":"print(1)"}

POST /api/manual
{"session_id":"user_task", "action":"..."}

POST /api/status
{"session_id":"user_task"}

POST /api/get_file
{"session_id":"user_task", "file_name":"report.csv"}

GET /api/sessions
GET /api/methods
GET /api/health
```

The control layer maps `user_id` + `task_id` to a session, serializes operations per task, and returns a status/output/error object. Connect creates a runtime session; configure can install dependencies; execute runs code; status and get-file require an existing task/session; disconnect destroys it. The API's `image_type` is a language selector, not proof an image exists.
