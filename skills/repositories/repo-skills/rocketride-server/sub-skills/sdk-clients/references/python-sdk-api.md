# Python SDK API

This reference is self-contained for the RocketRide Python SDK public surface
verified from an installed `rocketride` 1.3.0 package. It focuses on client use,
not `.pipe` design or engine deployment.

## Imports and setup

```bash
pip install rocketride
```

```python
import asyncio
import os

from rocketride import RocketRideClient, Question, AuthenticationException

async def main():
    async with RocketRideClient(
        uri=os.environ.get("ROCKETRIDE_URI", "https://api.rocketride.ai"),
        auth=os.environ["ROCKETRIDE_APIKEY"],
    ) as client:
        result = await client.use(filepath="pipeline.pipe")
        token = result["token"]
        try:
            out = await client.send(token, "Hello", objinfo={"name": "input.txt"}, mimetype="text/plain")
            print(out)
        finally:
            await client.terminate(token)

asyncio.run(main())
```

Key points:

- Python is async-first. Prefer `async with RocketRideClient(...)` so
  `connect()` and `disconnect()` bracket the session.
- The constructor reads process environment and, when `env` is not supplied,
  may also read a `.env` file from the process working directory.
- `ROCKETRIDE_APIKEY` is the SDK credential environment variable. If a user only
  has `ROCKETRIDE_AUTH`, copy it into `ROCKETRIDE_APIKEY` or pass it as
  `auth=...`; the Python SDK does not rely on `ROCKETRIDE_AUTH` for ordinary
  client/CLI auth.
- `uri` is normalized to the WebSocket task service path. For Cloud use a secure
  `https://...` or `wss://...` URI. `http://`, `ws://`, and bare hosts normalize
  to plain `ws://` and are unsafe for Cloud.

## Constructor and connection signatures

The inspected Python package exposes these connection signatures:

```python
RocketRideClient(uri: str = "", auth: str = "", **kwargs)
connect(self, credential: Optional[str] = None, *, timeout: Optional[float] = None) -> ConnectResult
disconnect(self) -> None
attach(self, uri: Optional[str] = None, *, timeout: Optional[float] = None) -> None
detach(self) -> None
login(self, credential: Optional[str] = None, *, uri: Optional[str] = None, timeout: Optional[float] = None) -> ConnectResult
logout(self) -> None
is_connected(self) -> bool
is_attached(self) -> bool
is_authenticated(self) -> bool
get_connection_info(self) -> dict
get_apikey(self) -> Optional[str]
set_env(self, env: Dict[str, str]) -> None
```

Constructor `kwargs` of practical interest:

| Option | Use |
| --- | --- |
| `env` | Replaces process/`.env` variables for this client. `use()` forwards `ROCKETRIDE_*` keys for pipeline substitution. |
| `module` | Client name for logs/debugging. |
| `ws_path` | Custom WebSocket path; default is `/task/service`. Use only for specialized clients. |
| `request_timeout` | Default timeout in milliseconds for individual DAP requests. |
| `max_retry_time` | Maximum retry time in milliseconds for persistent connection attempts. |
| `persist` | Enables automatic reconnect behavior. |
| `on_event` | Async callback for server events. |
| `on_connected` / `on_disconnected` / `on_connect_error` | Lifecycle callbacks. |
| `on_protocol_message` / `on_debug_message` / `on_trace` | Debug/trace hooks; avoid logging secrets. |
| `client_name` / `client_version` | Friendly identity sent during auth. |
| `public` | Public unauthenticated mode for public `rrext_public_*` commands. |

Use `connect()` for ordinary scripts. Use `attach()` + `login()` when you need an
anonymous public attachment first, then authentication. The inspected Python API
does **not** expose a `set_connection_params()` method; to change endpoint or
credential, use `login(uri=..., credential=...)`, `detach()`/`attach()`, or
create a new client.

## Pipeline execution and token lifecycle

Inspected signatures:

```python
use(self, *, token: str = None, filepath: str = None, pipeline: Optional[PipelineConfig] = None,
    source: str = None, threads: int = None, use_existing: bool = None,
    args: List[str] = None, ttl: int = None, pipelineTraceLevel: str = None,
    name: str = None, env: Dict[str, str] = None) -> Dict[str, Any]
terminate(self, token: str) -> None
restart(self, *, project_id: str, source: str, pipeline: PipelineConfig,
    token: Optional[str] = None, team_id: str = "") -> None
get_task_status(self, token: str) -> TASK_STATUS
get_task_token(self, project_id: str, source: str, *, team_id: str = "") -> str | None
get_task_pipeline(self, token: str) -> dict | None
```

Lifecycle:

1. `await client.use(filepath="...pipe")` or `await client.use(pipeline={...})`
   starts a task and returns a dict with at least `token`.
2. Pass that token to `send`, `send_files`, `pipe`, `chat`, `set_events`,
   `get_task_status`, and `terminate`.
3. Call `terminate(token)` when the work is done unless the task is intentionally
   long-lived (for example a webhook/dropper source).
4. If you need to address an already running dev/deployed run, resolve a token
   with `get_task_token(project_id, source, team_id=...)` when the server has
   that metadata.

`use()` behavior:

- Requires either `filepath` or `pipeline`.
- `.pipe` files wrapped as `{ "pipeline": { ... } }` are unwrapped before
  execution.
- `source` overrides the pipeline source.
- `env` values are merged over the client's filtered `ROCKETRIDE_*` environment
  and sent for server-side placeholder substitution.
- `pipelineTraceLevel` may be `'none'`, `'metadata'`, `'summary'`, or `'full'`
  when the server supports tracing. Keep deep trace interpretation with runtime
  diagnostics rather than `.pipe` authoring here.

## Data transfer signatures

```python
send(self, token: str, data: Union[str, bytes], objinfo: Dict[str, Any] = None,
    mimetype: str = None, on_sse=None) -> PIPELINE_RESULT
send_files(self, files: List[Union[str, Tuple[str, Optional[Dict[str, Any]]],
    Tuple[str, Optional[Dict[str, Any]], Optional[str]]]], token: str) -> UPLOAD_RESULT
pipe(self, token: str, objinfo: Dict[str, Any] = None, mime_type: str = None,
    provider: str = None, on_sse=None) -> DataPipe
```

Choose the method by payload shape:

| Method | Use when | Important details |
| --- | --- | --- |
| `send` | You have one string or `bytes` object in memory. | Internally opens a pipe, writes once, and closes it. Use `mimetype` such as `text/plain` or `application/json` when auto-detection is ambiguous. |
| `send_files` | You have one or more local files. | Each file can be a path string, `(path, objinfo)`, or `(path, objinfo, mimetype)`. Progress events use `apaevt_status_upload`. |
| `pipe` | You need chunked streaming, large payloads, incremental input, or pipe-scoped SSE. | Call `open()`, one or more `write(bytes)`, then `close()`. Use `async with await client.pipe(...)` for cleanup. |

`DataPipe` inspected methods:

```python
open(self) -> DataPipe
write(self, buffer: bytes) -> None
close(self) -> PIPELINE_RESULT
tool(self, *, tool: str, node_id: str = "", input: dict = None) -> Any
__aenter__(self)
__aexit__(self, exc_type, exc_val, exc_tb)
```

Streaming example with pipe-scoped SSE:

```python
async def on_sse(event_type: str, data: dict) -> None:
    print("SSE", event_type, data)

pipe = await client.pipe(
    token,
    objinfo={"name": "large.jsonl"},
    mime_type="application/jsonl",
    on_sse=on_sse,
)
async with pipe:
    for line in lines:
        await pipe.write(line.encode("utf-8"))
    result = await pipe.close()
```

## Chat, services, validation, events, and ping

```python
chat(self, *, token: str, question: Question, on_sse=None) -> PIPELINE_RESULT
validate(self, pipeline: PipelineConfig, *, source: Optional[str] = None) -> VALIDATION_RESULT
get_services(self) -> SERVICES_RESPONSE
get_service(self, service: str) -> SERVICE_DEFINITION
set_events(self, token: str, event_types: List[str], pipe_id: int = None) -> None
ping(self, token: str = None) -> None
```

Use `Question` for `chat()`:

```python
question = Question()
question.addQuestion("Summarize the uploaded document in three bullets.")
answer = await client.chat(token=token, question=question)
```

Use `validate()` before `use()` when the pipeline object is already in memory
and a server is available. Use the pipeline-authoring sub-skill for offline
schema/lane repair.

`set_events(token, event_types, pipe_id=None)` subscribes events to the client's
`on_event` callback. Common useful event types include upload and processing
status events such as `apaevt_status_upload`, `apaevt_status_processing`, and
pipe-scoped `SSE` when supported by the pipeline node.

## File store (`fs_*`) signatures

All Python SDK store paths are relative to the account store root. Do not pass
leading `/` or `\\` paths to SDK `fs_*` methods.

```python
fs_open(self, path: str, mode: str = "r") -> Dict[str, Any]
fs_read(self, handle: str, offset: int = 0, length: int = 4194304) -> bytes
fs_write(self, handle: str, data: bytes) -> int
fs_close(self, handle: str, mode: str = "r") -> None
fs_delete(self, path: str) -> None
fs_list_dir(self, path: str = "") -> Dict[str, Any]
fs_mkdir(self, path: str) -> None
fs_rmdir(self, path: str, *, recursive: bool = False) -> None
fs_stat(self, path: str) -> Dict[str, Any]
fs_rename(self, old_path: str, new_path: str) -> None
fs_get_url(self, path: str, expires_in: int = 3600, download_name: str = None) -> str
fs_read_many(self, paths: List[str]) -> List[Dict[str, Any]]
fs_read_string(self, path: str, encoding: str = "utf-8") -> str
fs_write_string(self, path: str, text: str, encoding: str = "utf-8") -> None
fs_read_json(self, path: str) -> Any
fs_write_json(self, path: str, obj: Any) -> None
```

Patterns:

```python
await client.fs_write_string("notes/todo.txt", "buy milk")
text = await client.fs_read_string("notes/todo.txt")

await client.fs_write_json("configs/job.json", {"debug": True})
cfg = await client.fs_read_json("configs/job.json")

info = await client.fs_open("uploads/video.mp4", "w")
try:
    with open("video.mp4", "rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            await client.fs_write(info["handle"], chunk)
finally:
    await client.fs_close(info["handle"], "w")
```

`fs_get_url(path, expires_in=3600, download_name=None)` returns a time-limited
HTTP(S) URL. Pass `download_name` when you need a cross-origin browser download
filename; otherwise Cloud storage URLs may ignore an HTML `<a download>` hint.

## Namespaced APIs

These APIs are available through properties on `RocketRideClient`; keep their
use focused on SDK tasks and route deployment/runtime planning to the runtime
sub-skill.

| Namespace | Examples |
| --- | --- |
| `client.database` | `query`, `begin_transaction`, `commit`, `rollback`, `dialect` for database-capable pipeline nodes. |
| `client.deploy` | `publish`, `deploy`, `list`, `get`, `versions`, `run`, `artifact`, `history`, schedule enable/disable/pause/resume/preview. |
| `client.log` | `open_event_stream`, `chapters`, `read`, `segment`, `delete` for run-log access. |
| `client.account` / `client.billing` | Profile, organization, team, API-key, environment-key, billing, and credit operations. |

## Exceptions and error handling

Important public exceptions:

```python
from rocketride import AuthenticationException, RocketRideException
from rocketride.core.exceptions import ConnectionException, PipeException, ExecutionException, ValidationException
```

Handle auth separately from transport/pipeline errors:

```python
try:
    await client.connect()
except AuthenticationException:
    # API key is missing, invalid, or expired.
    raise
except ConnectionException:
    # Server unreachable, WebSocket upgrade failed, proxy issue, etc.
    raise
```

Never log `get_apikey()` or raw auth values in troubleshooting output.
