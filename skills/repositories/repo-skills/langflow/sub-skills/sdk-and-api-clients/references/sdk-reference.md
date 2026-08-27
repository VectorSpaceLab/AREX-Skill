# SDK Reference

This reference distills the Langflow Python SDK surface for client code. It is grounded in the `langflow-sdk` package API and the SDK tests for models, serialization, streaming, push/pull, and environment config.

## Installation And Imports

Install the SDK package in the application environment that will call Langflow:

```bash
python -m pip install langflow-sdk
```

Common imports:

```python
from langflow_sdk import (
    AsyncClient,
    Client,
    FlowCreate,
    FlowUpdate,
    ProjectCreate,
    ProjectUpdate,
    RunRequest,
    RunResponse,
    StreamChunk,
)
from langflow_sdk.exceptions import (
    LangflowAuthError,
    LangflowConnectionError,
    LangflowHTTPError,
    LangflowNotFoundError,
    LangflowValidationError,
)
```

Verified public constructors:

- `Client(base_url, api_key=None, timeout=60.0, httpx_client=None)` is the preferred sync alias for `LangflowClient`.
- `AsyncClient(base_url, api_key=None, timeout=60.0, httpx_client=None)` is the preferred async alias for `AsyncLangflowClient`.
- `base_url` should be the server root such as `http://localhost:7860`, not `/api/v1`.
- `api_key` becomes the `x-api-key` header. Leave it unset only for local unauthenticated/dev servers.
- Inject `httpx.Client` or `httpx.AsyncClient` only when tests need custom transports or the application manages connection pooling.

## Client Lifetime

Use context managers when the SDK creates the HTTP client:

```python
from langflow_sdk import Client

with Client("http://localhost:7860", api_key="...") as client:
    flows = client.list_flows(get_all=True)
```

Async code:

```python
from langflow_sdk import AsyncClient

async with AsyncClient("http://localhost:7860", api_key="...") as client:
    projects = await client.list_projects()
```

Call `client.close()` or `await client.aclose()` if you do not use a context manager.

## Flow CRUD

Sync and async clients expose the same flow operations; async versions are awaited.

| Operation | SDK method | REST behavior |
| --- | --- | --- |
| List flows | `list_flows(folder_id=None, remove_example_flows=False, components_only=False, get_all=False, header_flows=False, page=1, size=50)` | `GET /api/v1/flows/` with query parameters |
| Read flow | `get_flow(flow_id)` | `GET /api/v1/flows/{flow_id}` |
| Create flow | `create_flow(FlowCreate(...))` | `POST /api/v1/flows/` |
| Patch flow | `update_flow(flow_id, FlowUpdate(...))` | `PATCH /api/v1/flows/{flow_id}` |
| Upsert flow | `upsert_flow(flow_id, FlowCreate(...))` | `PUT /api/v1/flows/{flow_id}` returning `(flow, created)` |
| Delete flow | `delete_flow(flow_id)` | `DELETE /api/v1/flows/{flow_id}` |

`FlowCreate` fields include `name`, `description`, `data`, `is_component`, `endpoint_name`, `tags`, `folder_id`, `icon`, `icon_bg_color`, `locked`, and `mcp_enabled`. `FlowUpdate` mirrors optional patchable fields. The SDK dumps models with `exclude_none=True`, so omitted fields are not sent.

Example:

```python
from langflow_sdk import Client, FlowCreate, FlowUpdate

with Client("http://localhost:7860", api_key="...") as client:
    created = client.create_flow(FlowCreate(name="SDK Demo", data={"nodes": [], "edges": []}))
    renamed = client.update_flow(created.id, FlowUpdate(name="SDK Demo Renamed"))
    print(renamed.name)
```

## Project CRUD And Archives

Langflow projects are folder-like containers for flows.

| Operation | SDK method | Notes |
| --- | --- | --- |
| List | `list_projects()` | Returns `Project` objects. |
| Read | `get_project(project_id)` | Returns `ProjectWithFlows`. |
| Create | `create_project(ProjectCreate(...))` | `flows_list` and `components_list` can move existing flows/components into the project. |
| Patch | `update_project(project_id, ProjectUpdate(...))` | Only sent fields update. |
| Delete | `delete_project(project_id)` | Removes the project by ID. |
| Download | `download_project(project_id)` | Returns `{filename: raw_json_bytes}` from a ZIP with safety limits. |
| Upload | `upload_project(zip_bytes)` | Uploads a ZIP and returns created flows. |

The SDK protects project archive extraction by rejecting archives over 500 entries and skipping entries larger than 50 MB.

## Running Flows

For most application code, call `run`:

```python
from langflow_sdk import Client

with Client("http://localhost:7860", api_key="...") as client:
    response = client.run(
        "my-endpoint-or-flow-id",
        input_value="Tell me a short joke.",
        input_type="chat",
        output_type="chat",
        tweaks={"OpenAIModel-abc123": {"temperature": 0.2}},
    )
    print(response.first_text_output())
```

Use `run_flow` with an explicit `RunRequest` when you want model validation around the full request:

```python
from langflow_sdk import Client, RunRequest

request = RunRequest(input_value="Hello", input_type="chat", output_type="chat", tweaks=None)
with Client("http://localhost:7860", api_key="...") as client:
    response = client.run_flow("my-endpoint-or-flow-id", request)
```

`RunRequest` defaults are `input_value=""`, `input_type="chat"`, `output_type="chat"`, `tweaks=None`, and `stream=False`. The simple `run` wrapper intentionally does not set `stream=True`.

Useful `RunResponse` helpers:

- `first_text_output()` returns the first chat/message text found in outputs.
- `all_text_outputs()` returns every extracted text string.
- `get_chat_output()`, `get_text_outputs()`, and `get_all_outputs()` mirror WorkflowResponse-style naming.
- `has_errors()`, `is_completed()`, and `is_failed()` inspect component output errors and empty responses.
- `is_in_progress()` is always `False` for synchronous v1 runs.

## Streaming Runs

`stream` sends a run request with `stream=True` and yields `StreamChunk` objects parsed from newline-delimited JSON/SSE lines. Blank lines and malformed lines are skipped.

Sync example:

```python
from langflow_sdk import Client
from langflow_sdk.exceptions import LangflowAuthError, LangflowConnectionError, LangflowHTTPError

try:
    with Client("http://localhost:7860", api_key="...") as client:
        final_response = None
        for chunk in client.stream("my-endpoint-or-flow-id", input_value="Hello"):
            if chunk.is_token and chunk.text:
                print(chunk.text, end="", flush=True)
            elif chunk.is_error:
                raise RuntimeError(chunk.data.get("error") or "Langflow stream reported an error")
            elif chunk.is_end:
                final_response = chunk.final_response()
        if final_response is not None and final_response.has_errors():
            raise RuntimeError("Langflow run completed with component errors")
except LangflowAuthError as exc:
    raise SystemExit(f"Authentication failed: {exc.detail}") from exc
except LangflowConnectionError as exc:
    raise SystemExit(str(exc)) from exc
except LangflowHTTPError as exc:
    raise SystemExit(f"Langflow HTTP failure {exc.status_code}: {exc.detail}") from exc
```

Async example:

```python
from langflow_sdk import AsyncClient

async with AsyncClient("http://localhost:7860", api_key="...") as client:
    async for chunk in client.stream("my-endpoint-or-flow-id", input_value="Hello"):
        if chunk.is_token and chunk.text:
            print(chunk.text, end="", flush=True)
        elif chunk.is_end:
            response = chunk.final_response()
            if response:
                print(response.first_text_output())
```

Known event names include `token`, `add_message`, `end_vertex`, `end`, and `error`.

`StreamChunk` helpers:

- `chunk.text` returns `data["chunk"]` for `token`, or message text for `add_message`.
- `chunk.is_token`, `chunk.is_end`, and `chunk.is_error` classify common events.
- `chunk.final_response()` parses `data["result"]` into `RunResponse` only for `end` events.

HTTP status handling happens before parsing stream lines. `401` and `403` raise `LangflowAuthError`; `404` raises `LangflowNotFoundError`; `422` raises `LangflowValidationError`; other non-success statuses, including `500`, raise `LangflowHTTPError`.

## File Push/Pull Helpers

Use file helpers to version flows as JSON and synchronize them with a server.

```python
from langflow_sdk import Client

with Client("http://localhost:7860", api_key="...") as client:
    flow, created = client.push("flows/my-flow.json")
    normalized = client.pull(flow.id, output="flows/my-flow.normalized.json")
```

Details:

- `push(path)` reads a JSON flow file, requires an embedded top-level `id`, removes `id` from the request body, and calls `PUT /api/v1/flows/{id}`. It returns `(Flow, created)` where `created` is true for HTTP 201.
- `push_project(directory)` pushes sorted `*.json` files only; non-JSON files are ignored.
- `pull(flow_id, output=None)` downloads a flow, normalizes it, optionally creates parent directories, and writes deterministic JSON.
- `pull_project(project_id, output_dir=...)` downloads a project ZIP, normalizes each flow, and writes `<flow-name>.json`; duplicate flow names overwrite earlier files and indicate a server-side data problem.

For offline normalization without a server, use the bundled helper described in the root `SKILL.md` or import `normalize_flow_file` directly.

## Flow Normalization API

```python
from pathlib import Path
from langflow_sdk.serialization import flow_to_json, normalize_flow, normalize_flow_file

flow = normalize_flow_file(Path("flow.json"), code_as_lines=True)
Path("flow.normalized.json").write_text(flow_to_json(flow), encoding="utf-8")
```

`normalize_flow` defaults:

- `strip_volatile=True` removes top-level `updated_at`, `created_at`, `user_id`, `folder_id`, `access_type`, and `gradient`.
- `strip_secrets=True` clears template field `value` when `password=True` or `load_from_db=True`.
- `sort_keys=True` recursively sorts dictionaries.
- `code_as_lines=False` leaves code field strings as strings unless opted in.
- `strip_node_volatile=True` removes node UI keys `positionAbsolute`, `dragging`, and `selected`.

Use `code_as_lines=True` for readable code diffs in pull requests. Use `strip_secrets=False` only for local debugging and never for committed output.

## Environment Config

The SDK can load named environments from TOML through `get_client`, `get_async_client`, `get_environment`, and `load_environments`.

Lookup order:

1. Explicit `config_file` argument.
2. `LANGFLOW_ENVIRONMENTS_FILE`.
3. `langflow-environments.toml` in the current working directory.
4. `~/.config/langflow/environments.toml`.

Example:

```toml
[environments.local]
url = "http://localhost:7860"
api_key_env = "LANGFLOW_LOCAL_API_KEY"

[defaults]
environment = "local"
```

```python
from langflow_sdk import get_client

with get_client() as client:
    print(client.list_projects())
```

Prefer `api_key_env` over literal `api_key`; literal keys trigger a warning and are unsafe for shared files.

## Typed Exceptions

Catch specific exceptions when mapping failures to user messages:

| Exception | Typical cause | Recommended response |
| --- | --- | --- |
| `LangflowConnectionError` | Server URL wrong, server down, blocked network | Ask user to start Langflow or fix `base_url`. |
| `LangflowAuthError` | Missing/bad API key or forbidden account | Re-check `x-api-key`, auth settings, and user permissions. |
| `LangflowNotFoundError` | Flow/project ID or endpoint name missing | Re-list flows/projects and confirm ID vs endpoint name. |
| `LangflowValidationError` | Request body fails server validation (`422`) | Inspect `RunRequest`, `FlowCreate`, tweaks shape, and required component inputs. |
| `LangflowHTTPError` | Other non-2xx statuses such as conflicts or server errors | Surface status/detail; inspect server logs for 5xx. |
| `EnvironmentConfigError` | Missing/malformed environment TOML | Fix TOML structure and required `url`. |
| `EnvironmentNotFoundError` | Requested environment absent | Choose an existing environment or add the named table. |
