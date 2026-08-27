# TaskingAI backend troubleshooting

Use this symptom map with [API and object model](api-and-object-model.md) and [native testing](native-testing.md). Start by identifying service purpose (`api` versus `web`), route prefix, auth type, Python version, and dependent services before changing request bodies.

## Import and startup failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Import fails on Python 3.11 with `TypeError: duplicate base class TimeoutError` or an `aioredis` traceback. | Backend pins `aioredis==2.0.1`, which is incompatible with Python 3.11's exception hierarchy. | Use Python 3.10 for backend inspection/development. Do not debug FastAPI routers, schemas, or `APIRouter` until the Python version is corrected. |
| Config import raises missing env variables. | Full backend app import initializes config and requires service URLs, database/storage settings, project ID, and secrets. | For semantic inspection, import narrow schema/model modules when possible. For app startup, provide a complete deployment environment; route env/Docker setup to `../deployment-configuration/`. |
| FastAPI app starts but fails during lifespan/startup. | Startup syncs model/plugin cache and initializes Postgres/Redis; dependent service URLs or DB/Redis are unavailable. | Check Postgres, Redis, backend-to-inference URL, backend-to-plugin URL, and storage env. Route service topology to `../deployment-configuration/`; provider/plugin internals to their sub-skills. |
| Health route not found. | Wrong route prefix or service purpose. | API mode uses `/v1/health_check`; web mode uses `/api/v1/health_check`. Verify reverse proxy/base URL before debugging code. |

## Authentication and route-prefix failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `TOKEN_VALIDATION_FAILED` on programmatic routes. | A web-mode route expects an admin JWT, not an API key. | Use admin login/refresh flow in web mode, or target API mode with API-key auth. |
| `APIKEY_VALIDATION_FAILED` on `/v1` routes. | Missing/invalid bearer API key or using an admin JWT against API-mode service. | Create/select an API key through web/admin workflow, then call API-mode routes with `Authorization: Bearer <api_key>`. |
| Admin/API-key management routes missing in API mode. | Generated admin/API-key CRUD is web-mode only except a narrow API-key read route. | Use web-mode prefix and admin token for management. Do not expect API mode to expose all web-console CRUD. |
| List filtering rejected. | API mode rejects `prefix_filter` and `equal_filter`. | Remove filters in API mode, or use web mode where supported and validate allowed filter fields. |

## Model and inference validation failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Assistant creation says model is not a valid chat completion model. | `model_id` points to a text-embedding/rerank/wildcard model or invalid model. | Use a configured model with type `chat_completion`. Provider-specific setup belongs to `../inference-providers/`. |
| Collection creation says model is not a valid embedding model or embedding size is invalid. | `embedding_model_id` is not `text_embedding` or lacks `embedding_size`. | Select/create a text-embedding model with valid embedding size. |
| Function tools or retrieval by function call rejected. | Chat model does not support function calling. | Select a chat model whose properties allow function calls, or use retrieval method `user_message`/`memory` and remove tools. |
| Streaming rejected. | Model properties do not allow streaming. | Use non-streaming request or choose a streaming-capable chat model. |
| OpenAI-compatible chat completion says invalid `model_id`. | The adapter dispatches 8-character IDs as models and 24-character IDs as assistants. | Provide a configured 8-character model ID or 24-character assistant ID, not provider model names such as `gpt-4o` unless they are mapped by a TaskingAI model object. |
| Provider error after backend validation passes. | Credentials, provider API, network, provider schema, or external inference service failure. | Route provider-specific diagnosis to `../inference-providers/` after preserving the backend request and model ID. |

## Retrieval and record/chunk failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Collection creation rejects capacity. | Source-backed backend accepts capacity `1000` in the inspected operator. | Use `1000` unless the running deployment documents expanded capacity choices. |
| Record/chunk creation fails at embedding. | Embedding model missing, invalid, provider unavailable, or inference service unreachable. | Confirm collection embedding model type/size and inference service availability. Provider execution failures route to `../inference-providers/`. |
| Record creation exceeds capacity. | Split content produced more chunks than remaining collection capacity. | Increase capacity if supported by deployment, reduce document size, increase chunk size, reduce overlap, or split into multiple collections. |
| Text splitter validation fails. | Missing `chunk_size`/`chunk_overlap` for token splitter, empty/overlapping separators for separator splitter, or overlap too large. | For token splitter set both fields and keep overlap at most half of chunk size. For separator splitter provide non-empty, non-overlapping separators. |
| File record cannot be updated. | Backend forbids updating file records. | Delete and recreate the file record. |
| Multi-collection retrieval fails with embedding model mismatch. | All retrieval collections for one assistant/query must share the same embedding model. | Recreate collections with the same embedding model or split retrievals by assistant/query. |
| Query chunks returns too few results. | `score_threshold`, `top_k`, `max_tokens`, or rerank selection filtered results. | Temporarily lower/remove `score_threshold`, increase `top_k`, remove `max_tokens`, and check whether rerank model is changing order. |

## Assistant generation failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Chat is locked. | A previous generation is in progress or failed before clearing lock; Redis lock expiry is expected to clear stale locks. | Wait for lock expiry, check Redis availability, and avoid concurrent generation for the same chat. |
| Generation fails before model call. | Assistant, chat, model, tools, or retrieval refs cannot be loaded/validated. | Verify object IDs and parent order: assistant → chat → messages; collection IDs; action/bundle-instance IDs; model type and properties. |
| Generation fails while using tools. | Model called an unknown function, exceeded tool-use round limit, action/plugin execution failed, or retrieval function had no query text. | Compare function names against action/plugin/retrieval function definitions. Use `../plugin-bundles/` for plugin payload failures; keep backend action schema/auth failures here. |
| Assistant message is not stored after failure. | Stateful generation stores the assistant message only after successful inference/tool rounds. | Inspect error event stage and retry after fixing validation/provider/tool issue; do not expect partial assistant message persistence. |
| Streaming emits errors or stops early. | Provider streaming unsupported/failing, model chunk error, or SSE client handling issue. | Verify model streaming property; compare non-streaming behavior; check SSE client reads `data:` events and terminal done message. |

## Action and backend tool failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Bulk action creation rejects OpenAPI schema. | Missing `servers`, missing `paths`, not exactly one server, missing/too-long operation descriptions, invalid/missing `operationId`, or invalid OpenAPI. | Validate and simplify the OpenAPI schema. For update, ensure exactly one path and one method. |
| Assistant tool validation fails. | Tool ref does not resolve or model lacks function-call support. | Confirm action/bundle-instance exists and the chat model supports function calling. |
| Running an action fails. | Action HTTP target, action auth, path/query/body parameter mapping, or network failure. | Validate action schema-derived parameters and authentication. For external network/API issues, preserve request/response and handle as external service dependency. |
| Plugin tool ref fails during assistant generation. | Backend can resolve the tool ref, but plugin-service schema/credential/execution fails. | Use this sub-skill for backend object wiring, then route bundle/plugin-specific payload and execution diagnosis to `../plugin-bundles/`. |

## Files, images, and object storage failures

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| File upload rejects extension. | Retrieval record files allow only `pdf`, `docx`, `md`, `txt`, `html`, and `htm`. | Convert or reject unsupported files before upload. |
| Image upload rejects extension. | User-message images allow only `jpg`, `jpeg`, and `png`. | Convert or reject unsupported images before upload. |
| File upload too large. | Source-backed file limit is 15 MB. | Compress/split the document or use a supported smaller file. |
| Image upload too large. | Source-backed image limit is 5 MB. | Resize/compress before upload. |
| Upload succeeds but URL/file access fails. | Object-storage mode, public domain, local volume, host URL, bucket, or credentials are misconfigured. | Route storage deployment configuration to `../deployment-configuration/`; use backend file/image route facts here to verify purpose and IDs. |

## Database and Redis symptoms

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Object CRUD fails with connection errors. | Postgres URL, credentials, network, migration, or pool configuration issue. | Verify database availability and migration readiness. Deployment setup belongs to `../deployment-configuration/`. |
| Collection/chunk table errors. | Retrieval collections create/use per-collection chunk tables; migrations or collection creation may be incomplete. | Recheck collection creation success and database migration state before manually touching chunk tables. |
| Chat lock/cache errors. | Redis URL/service unavailable or incompatible. | Verify Redis connection and service availability. Generation may fail or locks may behave incorrectly without Redis. |
| Cleanup route removes unexpected data. | `POST /clean_data` is destructive/test-oriented. | Do not call cleanup on user data unless explicitly authorized and scoped. |
