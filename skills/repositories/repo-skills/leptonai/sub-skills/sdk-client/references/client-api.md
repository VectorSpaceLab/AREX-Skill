# Client API for deployed endpoint calls

This reference covers the dynamic endpoint caller in `leptonai.client`. It is for Python scripts and notebooks that call an already-running endpoint. It is not the workspace-login or workload-creation route.

## Public entry points

```python
from leptonai.client import Client, local, current
```

Important signatures:

```python
from typing import Optional

Client(
    workspace_or_url: str,
    deployment: Optional[str] = None,
    token: Optional[str] = None,
    stream: Optional[bool] = None,
    chunk_size: Optional[int] = None,
    timeout = None,
    no_check: bool = False,
    http2: bool = True,
)
local(port: int = 8080) -> str
current() -> str
```

`Client.local(port)` and `Client.current()` are aliases of the module-level helpers.

## Construction modes

### Full URL or local URL

If `workspace_or_url` is already a URL, `Client` strips trailing slashes and treats that URL as the root of a deployment. It will check health at `/healthz` or `/health`, then fetch `<root>/openapi.json`, then build dynamic methods for OpenAPI paths.

```python
from leptonai.client import Client, local

client = Client(local(port=8080), timeout=60, no_check=True)
print(list(client.paths()))
```

Use `local(port)` only to build the URL string; constructing `Client(...)` still contacts that local service.

### Workspace id plus deployment name

If `workspace_or_url` is not a URL, `deployment` is required. The endpoint URL is built as:

```text
https://<workspace_id>-<deployment_name>.xenon.lepton.run
```

```python
import os
from leptonai.client import Client

client = Client(
    "workspace-id",
    "deployment-name",
    token=os.environ.get("LEPTON_WORKSPACE_TOKEN"),
    timeout=None,
)
```

The constructor only attaches an `Authorization: Bearer ...` header when `token` is not `None`. For private endpoints, pass a token explicitly or route to workspace/auth guidance first. Do not print tokens in notebooks or logs.

### Current workspace helper

`current()` reads the current workspace id from the local workspace record and raises `RuntimeError("No current workspace is set.")` if none is selected.

```python
from leptonai.client import Client, current

client = Client(current(), "deployment-name", token="...")
```

Use this only after workspace context has already been configured. Authentication setup belongs to the `workspace-and-auth` route.

## Initialization behavior and options

- `timeout=None` means the SDK uses an `httpx.Timeout(None)` for endpoint calls instead of httpx's short default timeout. Passing a float such as `timeout=60` sets seconds.
- `stream=True` makes `_get`/`_post` use streaming requests. JSON responses are still materialized as one JSON object; chunked non-JSON responses yield bytes from a generator.
- `chunk_size` is passed to streaming byte iteration.
- `no_check=True` suppresses the warning emitted when health/OpenAPI/path setup records debug issues. It does not suppress exceptions raised for connection failures.
- `http2` is part of the public signature for compatibility. In this package version, the constructor builds an `httpx.Client` with headers and timeout; do not rely on toggling HTTP/2 behavior unless you verify the installed SDK implementation.

## OpenAPI-derived method behavior

On construction, `Client` fetches `openapi.json` and iterates over its `paths` mapping.

- A `post` path becomes a Python method that sends keyword arguments as JSON: `json=jsonable_encoder(kwargs)`.
- A `get` path becomes a Python method that sends keyword arguments as query params.
- Positional arguments are rejected with a runtime message that tries to suggest the equivalent keyword call from the OpenAPI schema.
- The generated method docstring is derived from OpenAPI description/summary, input schema, examples, parameters, and response schema when present.
- `client.paths()` returns the OpenAPI path keys when the spec has a `paths` object; use `list(client.paths())` for display.
- `dir(client)` includes static helpers (`debug_record`, `paths`, `healthz`, `openapi`) plus dynamic path names.
- `help(client.<method>)` or `print(client.<method>.__doc__)` shows the generated documentation when the OpenAPI schema contains enough metadata.

Example:

```python
print(list(client.paths()))
print(client.run.__doc__)
print(client.run(inputs="hello"))
```

## PathTree naming rules

Dynamic endpoint attributes are backed by a `PathTree`.

| OpenAPI path component | Python member behavior |
| --- | --- |
| `predict` | `client.predict` |
| `my-path` | `client.my_path` |
| `foo.bar` | `client.foo_bar` |
| Python keyword such as `class` | suffix `_`, e.g. `client.class_` |
| invalid identifier such as `{item_id}` | ignored for dynamic attribute creation; see `debug_record()` |
| both `get` and `post` on same path | wrapper object with a default method and method-specific accessors such as `.get` / `.post` |
| a path that is both a leaf and a prefix | the attribute becomes a subtree; the preserved leaf callable is available with bracket lookup of `""` |

Examples with a real client:

```python
print(dir(client))              # dynamic top-level names
print(client.debug_record())    # warnings about invalid or unsupported paths

# If OpenAPI exposes both GET and POST on /run:
client.run(inputs="x")          # default method
client.run.get(q="x")           # explicit GET
client.run.post(inputs="x")     # explicit POST

# If both /branch and /branch/leaf exist:
client.branch.leaf(...)
client.branch[""](...)          # the original /branch leaf callable
```

If dynamic lookup is impossible because the OpenAPI path contains unsupported identifiers, use direct `_get`/`_post` only as a controlled fallback:

```python
# Fallback for a path that cannot be represented as a Python attribute.
raw = client._post("/items/{item_id}", json={"item_id": "123"})
print(client._get_proper_res_content(raw))
```

Direct `_get`/`_post` bypass the OpenAPI-derived argument help, so prefer dynamic methods when available.

## Health and OpenAPI diagnostics

`Client.healthz()` tries `/healthz` then `/health`; not every mounted framework exposes those endpoints, so `False` is a hint rather than proof that the endpoint is unusable.

`client.debug_record()` prints and returns initialization/debug messages such as:

- health endpoint missing or returning an error;
- `openapi.json` missing, corrupt, 404, or rate-limited;
- unsupported HTTP method for an OpenAPI path;
- invalid path component ignored by `PathTree`.

When you own the deployed service, prefer fixing the OpenAPI schema and endpoint names. When you only consume someone else's service, use `paths()`, `debug_record()`, and direct `_get`/`_post` fallbacks narrowly.

## Return values

Dynamic methods call `_get_proper_res_content(...)`:

- JSON response (`content-type: application/json`) returns `res.json()`.
- Streaming chunked response with `stream=True` yields byte chunks.
- Other non-streaming responses return `res.content` bytes.
- HTTP errors are raised with a detailed status message that includes response detail when available.

Design caller code to handle the endpoint's documented response shape rather than assuming every endpoint returns JSON.
