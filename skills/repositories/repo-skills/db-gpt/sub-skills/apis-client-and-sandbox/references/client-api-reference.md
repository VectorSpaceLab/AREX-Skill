# Python client reference

This reference describes the public `dbgpt_client` surface in DB-GPT 0.8.1. All calls are asynchronous. The package root exports only `Client`, `ClientException`, and `__version__`; import CRUD functions from their submodules.

## Constructing and closing `Client`

```python
from dbgpt_client import Client

client = Client(
    api_base="http://localhost:5670/api/v2",
    api_key=None,          # or load DBGPT_API_KEY outside the source
    timeout=120,
)
try:
    result = await client.get("/datasources")
finally:
    await client.aclose()
```

Constructor signature:

```text
Client(api_base: str | None = None,
       api_key: str | None = None,
       version: str = "v2",
       timeout: httpx timeout type | None = 120)
```

- If `api_base` is omitted, `DBGPT_API_BASE` is read; otherwise the default is `http://localhost:5670/api/v2`.
- If `api_key` is omitted, `DBGPT_API_KEY` is read. A supplied key is sent as `Authorization: Bearer <key>`.
- The URL is syntactically checked for a scheme and network location. A bad value raises `ValueError` at construction; construction does not prove that the server is reachable.
- `close()` is a synchronous convenience that runs the async client close through DB-GPT's event-loop helper. In async applications prefer `await aclose()` and close explicitly in `finally`.
- A full `api_base` is expected. Do not give a host-only value or append `/serve` yourself when using the generic service methods.

## Transport method semantics

The methods intentionally expose raw `httpx.Response` objects for generic service calls:

| Method | Effective URL | Payload placement |
|---|---|---|
| `await client.get(path, **params)` | `<api_base>/serve<path>` | non-`None` kwargs become query parameters |
| `await client.post(path, body)` | `<api_base>/serve<path>` | JSON body |
| `await client.post_param(path, params)` | `<api_base>/serve<path>` | query parameters |
| `await client.put(path, body)` | `<api_base>/serve<path>` | JSON body |
| `await client.delete(path, ...)` | `<api_base>/serve<path>` | forwarded `httpx` args/kwargs |
| `await client.patch(path, ...)` | `<api_base>/serve<path>` | **implementation quirk:** returns the patch coroutine rather than awaiting it |
| `await client.head(path, ...)` | `<api_base><path>` | does not insert `/serve` |

Use `response.status_code`, `response.headers`, and `response.json()` (when the body is JSON) on raw responses. Generic methods do not call `raise_for_status()`.

`ClientException(status=None, reason=None, http_resp=None)` preserves optional response information, headers, and body. The CRUD wrappers catch all exceptions and re-raise a new `ClientException` with a failure message passed as its first positional argument; consequently, the message can appear in `.status` rather than `.reason`. Do not rely on `.status` being an HTTP integer for wrapper failures.

## Chat

`await client.chat(...)` accepts:

```text
model: str
messages: str | list[str]
temperature: float | None
max_new_tokens: int | None
chat_mode: str | None
chat_param: str | None
conv_uid: str | None
user_name: str | None
sys_code: str | None
span_id: str | None
incremental: bool = True
enable_vis: bool = True
```

It posts JSON to `<api_base>/chat/completions` with `stream=false`, using `ChatCompletionRequestBody`. The schema also accepts the inherited OpenAI-style fields (`max_tokens`, `top_p`, `stop`, and similar). `max_new_tokens` is copied to `max_tokens` when `max_tokens` is absent. Prefer `max_tokens` in new payloads.

`chat_stream(...)` uses the same request shape with `stream=true` and returns an async generator of `ChatCompletionStreamResponse`. It parses lines beginning with `data:` as JSON and stops on the exact `data: [DONE]` marker. A malformed SSE event raises a parsing error. A non-200 response is yielded as decoded JSON when possible rather than converted to a typed success response, so callers must check the result shape.

Supported `chat_mode` values represented by the client schema include:

- `chat_normal` (default)
- `chat_app`
- `chat_flow`
- `chat_knowledge`
- `chat_data`
- `chat_with_db_qa`
- `chat_dashboard`

The v2 server requires `model` and `messages`; a non-normal mode requires `chat_param`. `chat_app` requires streaming. `chat_flow` may be streamed or non-streamed. Data and knowledge modes need an existing datasource/space and are implementation-specific; route their construction details to the data/RAG skill.

## Datasource helpers

Import from `dbgpt_client.datasource`:

```text
create_datasource(client, datasource: DatasourceModel) -> DatasourceModel
update_datasource(client, datasource: DatasourceModel) -> DatasourceModel
delete_datasource(client, datasource_id: str) -> DatasourceModel
get_datasource(client, datasource_id: str) -> DatasourceModel
list_datasource(client) -> list[DatasourceModel]
```

`DatasourceModel` has required `db_type` and `db_name`, plus `db_path`, `db_host`, `db_port`, `db_user`, `db_pwd`, `comment`, and optional `id`. The helper paths are:

```text
POST   /serve/datasources
PUT    /serve/datasources
DELETE /serve/datasources/{datasource_id}
GET    /serve/datasources/{datasource_id}
GET    /serve/datasources
```

The service also exposes `POST /serve/datasources/test-connection`, `GET /serve/datasource-types`, and `POST /serve/datasources/{id}/refresh`; use raw HTTP for those. The service accepts a newer dynamic form (`type`, `params`, optional `description`, `id`) as well as the legacy `db_type`/`db_name` form. Do not assume a remote connector is installed merely because its type is listed.

The helper expects a DB-GPT `Result` object such as `{"success": true, "data": ...}`. An unsuccessful envelope becomes `ClientException`; a transport exception is wrapped as described above.

## Knowledge helpers

Import from `dbgpt_client.knowledge`:

```text
create_space(client, space_model: SpaceModel) -> SpaceModel
update_space(client, space_model: SpaceModel) -> SpaceModel
delete_space(client, space_id: str) -> SpaceModel
get_space(client, space_id: str) -> SpaceModel
list_space(client) -> list[SpaceModel]
create_document(client, doc_model: DocumentModel) -> DocumentModel
delete_document(client, document_id: str) -> DocumentModel
get_document(client, document_id: str) -> DocumentModel
list_document(client) -> list[DocumentModel]
sync_document(client, sync_model: SyncModel) -> list
```

`SpaceModel` uses `id`, `name`, `vector_type`, `desc`, `owner`, and `context`. A successful create accepts either a mapping response or a scalar primary key and fills that key into the submitted model.

Space helper paths are:

```text
POST   /serve/knowledge/spaces
PUT    /serve/knowledge/spaces
DELETE /serve/knowledge/spaces/{space_id}
GET    /serve/knowledge/spaces/{space_id}
GET    /serve/knowledge/spaces
```

List responses are expected to have `data.items`. Document list responses also expect `data.items`. `SyncModel` contains `doc_id`, `space_id`, optional `model_name`, and optional chunk parameters; `sync_document` sends a JSON list to `/serve/knowledge/documents/sync`.

**Important client/server boundary:** the client’s `create_document` calls `post_param("/knowledge/documents", ...)`, which puts fields in the query string. The server’s document-create route is a multipart form route requiring `doc_name`, `doc_type`, and `space_id` (with optional `content` or `doc_file`). Treat this helper as a legacy compatibility surface and verify it against the actual server version; for reliable document upload use a multipart HTTP request matching [service-endpoints.md](service-endpoints.md). Do not put a local file path in JSON and expect the server to read it.

## Flow helpers

Import from `dbgpt_client.flow`:

```text
create_flow(client, flow: FlowPanel) -> FlowPanel
update_flow(client, flow: FlowPanel) -> FlowPanel
delete_flow(client, flow_id: str) -> FlowPanel
get_flow(client, flow_id: str) -> FlowPanel
list_flow(client, name: str | None = None, uid: str | None = None) -> list[FlowPanel]
run_flow_cmd(client, name=None, uid=None, data=None,
             non_streaming_callback=None, streaming_callback=None) -> None
```

The intended create/list/get/delete paths are `/serve/awel/flows` and `/serve/awel/flows/{uid}`. `list_flow` sends optional `name` and `uid` as query parameters. `run_flow_cmd` first resolves exactly one flow, reads its metadata, and supports only an HTTP trigger; it selects the first trigger method and invokes the trigger path from the service base URL. It rejects no metadata, no triggers, multiple flows, multiple triggers, and non-HTTP trigger types.

There is a version-specific mismatch to check before using `update_flow`: the installed helper sends `PUT /serve/awel/flows` with the serialized panel, while the 0.8.1 v2 service route is `PUT /serve/awel/flows/{uid}`. Prefer a raw request with the UID path (or confirm a compatibility route exists) rather than assuming the helper updates a flow.

For flow chat, the OpenAI-compatible endpoint is `/api/v2/chat/completions` with `chat_mode="chat_flow"` and `chat_param=<flow uid>`. Streaming output may be SSE; non-streaming flow execution returns a typed chat response or a 400 error envelope.

## App helpers

Import from `dbgpt_client.app`:

```text
get_app(client, app_id: str) -> AppModel
list_app(client) -> list[AppModel]
```

These call `/serve/apps/{app_id}` and `/serve/apps`. The service additionally supports app create/update/delete at the same collection, but the Python client has no corresponding helpers. `AppModel` includes `app_code`, `app_name`, `app_describe`, `team_mode`, `language`, `team_context`, `user_code`, `sys_code`, collection state, icon, timestamps, and details.

Chatting with an app uses `/api/v2/chat/completions`, `chat_mode="chat_app"`, `chat_param=<app code>`, and streaming. Listing an app does not prove its agent, model, datasource, knowledge, or provider dependencies are available.

## Safe mock contract

A useful no-network test double should implement `post(path, body)`, `put(path, body)`, `get(path, **params)`, `post_param(path, params)`, and `delete(path)`, return a response with `.json()`, and record method/path/body/params. Cover:

1. success envelope and model decoding;
2. unsuccessful envelope, preserving the error code in diagnostic output;
3. transport exception and timeout;
4. 404 for a missing ID;
5. 409 for duplicate datasource/space/flow;
6. dependency ordering: datasource → knowledge space → document/sync → chat;
7. client/server mismatches for multipart document creation and flow update.

Use placeholders for all IDs, URLs, and keys. Never make a live call from a fixture test.
