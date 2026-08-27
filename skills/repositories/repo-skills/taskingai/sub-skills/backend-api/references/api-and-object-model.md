# TaskingAI backend API and object model

This reference distills the backend API/web-service behavior into a self-contained operating map. It is source-backed by the backend route, schema, model, operator, and service layers, but future agents should use this bundled reference rather than assuming the original source tree is present.

## Service shape and route prefixes

TaskingAI's backend is a FastAPI service. Route registration depends on the service purpose:

| Purpose | External route prefix | Auth style | Typical use |
| --- | --- | --- | --- |
| API mode | `/v1` | API key in `Authorization: Bearer ...` | Programmatic API clients and OpenAI-compatible endpoints. |
| Web mode | `/api/v1` | Admin JWT in `Authorization: Bearer ...` | Console/web-service routes, admin login, API-key management, UI helper routes. |

Use the user's running deployment to determine the base URL and prefix. If the problem is about service startup, Docker, env files, or cross-service URLs, route to `../deployment-configuration/`.

### Route groups

API mode includes health/manage, tool actions, retrieval, inference, OpenAI-compatible routes, assistant generation, files/images, and generated CRUD routes for assistant/chat/message/collection/record/chunk/action. Web mode includes these plus admin/API-key/model/plugin/bundle-instance/model CRUD and UI helper routes.

Important route families:

- Manage: `GET /health_check`, `GET /version`, `POST /clean_data`.
- Auth/admin in web mode: `POST /admins/login`, `/admins/logout`, `/admins/verify_token`, `/admins/refresh_token`; API-key CRUD under `/apikeys`.
- Model and model schema: model CRUD under `/models`; provider/schema listing under `/providers`, `/providers/get`, `/model_schemas`, `/model_schemas/get`.
- Assistant: `/assistants`, `/assistants/{assistant_id}`, nested `/assistants/{assistant_id}/chats`, nested messages, and `POST /assistants/{assistant_id}/chats/{chat_id}/generate`.
- Retrieval: `/collections`, nested `/records`, nested `/chunks`, `POST /collections/{collection_id}/chunks/query`, and `GET /collections/{collection_id}/records/{record_id}/chunks`.
- Tool/action: `/actions`, `POST /actions/bulk_create`, `POST /actions/{action_id}`, `POST /actions/{action_id}/run`.
- Plugin as backend object: bundle instance CRUD under `/bundle_instances` in web mode; bundle/plugin listing under `/bundles` and `/plugins`.
- Inference: `POST /inference/chat_completion`, `/inference/text_embedding`, `/inference/rerank`.
- OpenAI-compatible: `POST /chat/completions`, `POST /embeddings`.
- Files/images: `POST /files`, `POST /images`.

## Authentication and mode-specific behavior

The backend chooses auth by service purpose:

- API mode verifies bearer API keys. Missing or invalid keys fail with API-key validation errors.
- Web mode verifies bearer admin tokens. Admin login accepts username/password and returns admin data containing token material; API-key creation and management are web-mode operations.
- List filtering differs by mode: API mode rejects `prefix_filter` and `equal_filter`; web mode can validate allowed filter fields on selected objects.

Do not assume an API key can call web-only admin routes or that an admin JWT can call API-mode service routes. If a route is missing, check purpose/prefix before debugging request bodies.

## Common response and validation conventions

Most TaskingAI backend routes wrap successful responses as:

```json
{
  "status": "success",
  "data": { "object": "..." }
}
```

List routes add `fetched_count` and `has_more`. Generated CRUD routes validate path parameters against object primary keys and require alphanumeric/underscore path IDs. Pydantic request models enforce field length, enum, and metadata-size constraints.

Generated IDs have object-specific prefixes and lengths; agents should treat them as opaque. Important validated lengths:

- `model_id`: 8 alphanumeric characters.
- `assistant_id`, `chat_id`, `message_id`: generally 24 characters for runtime-generated IDs; assistant path validation accepts a wider range in model fields but generation dispatch treats 24-character strings as assistant IDs.
- Collection/record/chunk/action/bundle-instance IDs are opaque backend-generated identifiers.

## Models and model schemas

TaskingAI separates **model schemas** from configured **models**.

- Model schema values include the verified types `chat_completion`, `text_embedding`, `rerank`, and `wildcard`.
- A configured model stores `model_schema_id`, `provider_id`, optional `provider_model_id`, `name`, `type`, credentials, configs, properties, and optional fallback models.
- Chat models can declare properties such as function-call and streaming support. Assistant tools/retrieval-by-function-call require function-call support; streaming requests require streaming support.
- Text-embedding models must expose a valid `embedding_size`; collection creation fails if the embedding model is not `text_embedding` or lacks embedding size.
- Rerank models are optional and are used only when retrieval query/ranking asks for reranking.

Provider-specific schema catalogs, credential fields, network/provider failures, and inference execution details belong to `../inference-providers/`.

## Assistant, chat, message, and generation objects

### Assistant

Create/update assistant fields include:

- `model_id`: must point to a configured `chat_completion` model.
- `name`, `description`, `system_prompt_template`.
- `memory`: one of `zero`, `naive`, or `message_window`; `message_window` requires `max_messages` and can include `max_tokens`.
- `tools`: list of backend tool refs such as `{ "type": "action", "id": "..." }` or `{ "type": "plugin", "id": "..." }`.
- `retrievals`: currently collection refs such as `{ "type": "collection", "id": "..." }`.
- `retrieval_configs`: `top_k`, optional `max_tokens`, optional `score_threshold`, `method`, and optional `function_description`.
- `metadata`: small key/value metadata dictionary.

Validation points:

- The model must be chat-completion capable.
- Tools require the assistant model to support function calling and must resolve through backend tool verification.
- Retrieval refs must resolve to collections. Multiple retrieval collections must use the same embedding model.
- `retrieval_configs.method = function_call` also requires model function-call support.

### Chat and message

A chat belongs to an assistant. Chat creation initializes chat memory from the assistant's memory policy and increments the assistant's chat count. Chat deletion decrements that count.

A message belongs to an assistant and a chat. Message creation accepts:

```json
{
  "role": "user",
  "content": { "text": "Hello" },
  "metadata": {}
}
```

Only `user` and `assistant` roles are modeled for stored messages. The backend counts tokens and updates chat memory after message creation:

- `zero` memory stores user messages and clears memory after assistant responses.
- `naive` memory appends all messages.
- `message_window` trims by message count and token limit after assistant responses.

### Stateful generation

Call `POST /assistants/{assistant_id}/chats/{chat_id}/generate` after the user message has been created. Request fields:

```json
{
  "system_prompt_variables": { "name": "value" },
  "stream": false,
  "debug": false
}
```

Generation behavior:

1. Load assistant and chat.
2. Reject if the chat lock is active; generation locks the chat for the request and unlocks in a `finally` path.
3. Resolve the assistant model and verify streaming if requested.
4. Load chat memory messages.
5. Fetch assistant tools into chat-completion function definitions.
6. Resolve retrievals. If retrieval method is `user_message` or `memory`, query retrieval before model inference and inject retrieved content into the system prompt. If method is `function_call`, add a synthetic retrieval function to the function list.
7. Build the system prompt from the assistant template plus variables and retrieval content.
8. Run chat-completion inference. If the model returns function calls, run retrieval/tools and append function messages, with up to five use rounds per tool name.
9. Store the final assistant message and return it, or stream Server-Sent Events when requested.

Common generation errors come from missing chat/model/tools, unsupported streaming/function calls, chat lock contention, retrieval collection mismatch, provider errors, or backend dependency failures.

## Stateless chat completion and OpenAI-compatible endpoints

`POST /inference/chat_completion` accepts TaskingAI chat-completion requests. The `model_id` field is overloaded:

- If it is an 8-character model ID, the backend calls the configured model directly.
- If it is a 24-character assistant ID, the backend creates a stateless assistant session using the request messages and functions.
- Otherwise the backend raises a request-validation error.

`POST /chat/completions` adapts OpenAI-compatible payloads into the same TaskingAI chat-completion flow and adapts responses/chunks back to OpenAI-style JSON. It supports both direct model IDs and assistant IDs using the same length-based dispatch.

`POST /embeddings` adapts OpenAI-compatible embedding payloads into TaskingAI text-embedding requests.

When OpenAI-compatible calls fail, distinguish three layers:

1. OpenAI-shape adaptation error (messages/tools/functions/input format).
2. TaskingAI model/assistant validation error (ID length, model capability, route auth).
3. Provider execution error (credentials/network/provider behavior, routed to `../inference-providers/`).

## Retrieval collections, records, chunks, and queries

### Collection lifecycle

Create a collection before records or chunks. Required fields:

```json
{
  "name": "Knowledge",
  "description": "...",
  "capacity": 1000,
  "embedding_model_id": "8CharEmb",
  "metadata": {}
}
```

Source-backed validation currently allows capacity `1000`. The embedding model must be a configured `text_embedding` model with `embedding_size`. A collection owns a dynamic chunk table named from its collection ID; treat this as implementation detail unless debugging database state.

### Record lifecycle

A record belongs to a collection and can create many chunks by loading, splitting, embedding, and storing content. Record create/update fields include:

- `type`: `text`, `file`, or `web`.
- `file_id`: required for file records.
- `url`: required for web records.
- `title` and optional text `content` for text records.
- `text_splitter`: required for create and for content-changing update.
- `metadata`: string key/value metadata.

Text splitter modes:

- `token`: requires `chunk_size` and `chunk_overlap`.
- `separator`: requires non-empty `separators`; no separator can be empty, longer than the limit, or a substring of another separator.
- `chunk_overlap` must not exceed half of `chunk_size`.

Record creation checks remaining collection capacity, loads content, splits text, embeds chunks with the collection embedding model, then stores the record and chunks. File records cannot be updated; delete and recreate them.

### Chunk lifecycle

Chunks can also be created directly under a collection with `content` and `metadata`. Direct chunk creation embeds the content using the collection embedding model, counts tokens, checks collection capacity, and stores one chunk. Updating a chunk's content re-embeds it.

### Querying chunks and retrievals

`POST /collections/{collection_id}/chunks/query` accepts `top_k`, `query_text`, optional `max_tokens`, optional `score_threshold`, and optional `rerank_model_id`. The backend embeds the query using the collection embedding model, performs vector ranking, optionally reranks, and applies `max_tokens` to selected chunks.

Assistant retrievals call the same underlying retrieval services. When multiple collections are used in one assistant/retrieval query, they must share the same embedding model.

## Tools, actions, bundle instances, and assistant orchestration

TaskingAI assistants use tools through backend `ToolRef` values. There are two tool types:

- `action`: user-defined HTTP/OpenAPI actions created and executed through the backend.
- `plugin`: plugin bundle instances exposed as backend tools; plugin catalog and plugin execution internals belong to `../plugin-bundles/`.

### Actions

Bulk-create actions with `POST /actions/bulk_create` from an OpenAPI schema plus optional authentication. The action schema must:

- Be valid OpenAPI.
- Have exactly one server.
- Have paths and operations.
- Give every operation a string `description` or a usable `summary`.
- Give every operation a valid `operationId` matching an identifier pattern and length limit.

If multiple paths/methods are present, the backend splits them into multiple action objects. Updating an action expects a schema with exactly one path and one method. Running an action uses `POST /actions/{action_id}/run` with optional `parameters`.

Action authentication is encrypted before storage and displayed in redacted/display form in responses.

### Bundle instances as backend tools

Web-mode backend routes can create/update/list/delete bundle instances. The backend stores credentials and resolves bundle/plugin tools when assistants fetch tools. Use this sub-skill for the backend object lifecycle and assistant wiring; use `../plugin-bundles/` for bundle IDs, plugin IDs, plugin schema details, credential schemas, and plugin-service execution behavior.

### Tool execution during generation

During generation, the session fetches all assistant tools and exposes their function definitions to the chat model. If the model emits function calls:

1. The backend validates the called function name against known tools or the synthetic retrieval function.
2. It limits repeated use to avoid more than five rounds per tool name.
3. Retrieval function calls query collections and append a function message with retrieved content.
4. Action/plugin tool calls are converted into `ToolInput` objects, executed through backend tool services, and appended as function messages with JSON content.
5. The model is called again until no function calls remain, then the final assistant message is stored.

## Files and images

`POST /files` accepts multipart form fields:

- `purpose`: currently `record_file` for retrieval records.
- `file`: upload file.

Allowed file extensions for retrieval record files are `pdf`, `docx`, `md`, `txt`, `html`, and `htm`. The source-backed limit is 15 MB. The response returns a `file_id` used when creating a file-type record.

`POST /images` accepts:

- `purpose`: currently user-message image purpose.
- `image`: upload image.

Allowed image extensions are `jpg`, `jpeg`, and `png`. The source-backed limit is 5 MB. The response returns an image URL.

Storage behavior depends on deployment object-storage configuration. Route storage-mode and public URL setup to `../deployment-configuration/`; diagnose upload/runtime symptoms with [troubleshooting](troubleshooting.md).

## Integrated assistant + retrieval + tool order

For a user request such as "create an assistant that answers from one document and can call a weather action", use this order:

1. **Confirm service mode and prefix.** API mode `/v1` with API key is typical for programmatic use; web mode `/api/v1` with admin token is needed for admin/model/API-key management.
2. **Create or select models.** Need a `chat_completion` model for the assistant. Need a `text_embedding` model with `embedding_size` for retrieval. Optional: need `rerank` model for reranked chunk queries. Provider-specific credentials/schema details belong to `../inference-providers/`.
3. **Create retrieval collection.** Use capacity `1000` unless a running service documents additional allowed values. Store the `collection_id`.
4. **Load retrieval content.** For text records, create a record with `type: text`, `content`, and a valid text splitter. For file records, upload the file first, then create a record with `type: file` and `file_id`. For a small hand-authored chunk, create a direct chunk. Embedding happens at record/chunk creation.
5. **Create backend tool objects.** For HTTP actions, bulk-create actions from valid OpenAPI and capture created `action_id` values. For plugin tools, create/select a bundle instance and use plugin-specific details from `../plugin-bundles/`.
6. **Create assistant.** Include the chat model, memory policy, retrieval refs, retrieval config, and tool refs. If using retrieval or tools as function calls, verify the chat model supports function calling. Retrieval collections must share one embedding model.
7. **Create chat.** Store the `chat_id`.
8. **Create user message.** Use role `user` and content `{ "text": "..." }`.
9. **Generate assistant message.** Call generation with system prompt variables and optional streaming/debug flags. Expect retrieval/tool/model rounds internally before the final assistant message is returned.
10. **Troubleshoot by stage.** If create collection fails, inspect embedding model and capacity. If record/chunk creation fails, inspect loader/splitter/capacity/embedding. If assistant creation fails, inspect model/tool/retrieval validation. If generation fails, inspect chat lock, model capability, retrieval collection compatibility, tool execution, provider/service dependencies.
