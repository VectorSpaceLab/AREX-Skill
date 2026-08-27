# Background, Async, and WebSocket Callbacks

## When to read

Read this for `async def` callbacks, background callbacks, WebSocket callbacks,
progress updates, cancellation, and callback caching behavior.

## Async callbacks

Dash supports `async def` callbacks. The backend determines whether they are
native or require an extra:

- Flask requires `dash[async]`.
- FastAPI and Quart are natively async.

Example:

```python
import asyncio
from dash import Dash, html, Input, Output

app = Dash(__name__)
app.layout = html.Div([html.Button("Go", id="go"), html.Div(id="out")])

@app.callback(Output("out", "children"), Input("go", "n_clicks"))
async def update(n):
    await asyncio.sleep(1)
    return "done"
```

## Background callbacks

Background callbacks run outside the main request path when `background=True`.
Supported managers are `DiskcacheManager` and `CeleryManager`.

Core keywords:

- `progress=Output(...)` or a grouped output to receive progress updates.
- `progress_default` to set the non-running value.
- `running=[(Output(...), while_running, after_done), ...]` for UI state.
- `cancel=[Input(...)]` for cancel triggers.
- `cache_by`, `cache_args_to_ignore`, and `cache_ignore_triggered` for cache key
  control.
- `api_endpoint` is not a background-only setting, but it can coexist with
  background callbacks.

### Diskcache manager

Use `DiskcacheManager` for local development and simple deployments. It needs
`dash[diskcache]` and uses a diskcache result backend plus multiprocess/psutil.
It does not require an external broker.

### Celery manager

Use `CeleryManager` only when you have a configured Celery app with a result
backend. Installation alone is not enough; the app must be pointed at a real
broker/backend.

### Cache and progress shape

- Progress values are written by the injected `set_progress` helper.
- A background callback may return ordinary callback outputs or raise
  `PreventUpdate`.
- If a background callback updates props via `set_props`, that data is managed
  through the manager's result store.

## WebSocket callbacks

WebSocket callbacks are the low-latency runtime path for apps that need persistent
server/client communication.

Important facts:

- Global WebSocket callbacks require the FastAPI backend.
- A callback can opt into WebSocket mode with `websocket=True`.
- `persistent=True` is for persistent WebSocket callbacks that use `set_props`
  and typically no ordinary Output.
- `ctx.websocket` gives access to the WebSocket helper inside a callback.
- Long-running loops must check `ws.is_shutdown` to stop cleanly when the client
  disconnects.
- Browser support depends on `SharedWorker` availability.

### WebSocket helper methods

- `set_props(component_id, props)` streams prop updates to the client.
- `await ws.get_prop(component_id, prop_name)` fetches a current browser prop.
- `await ws.set_prop(component_id, prop_name, value)` sets a prop from the server.
- `await ws.close(code, reason)` closes the connection deliberately.

## Runtime checks and failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dash[async]` not installed | Flask async callback request | Install the extra or move the app to FastAPI/Quart. |
| Background manager import error | Missing `dash[diskcache]` or `dash[celery]` | Install only the needed extra. |
| Background callback never finishes | Broker/backend missing, worker absent, or callback error | Check the manager's runtime logs and backend configuration. |
| WebSocket callback never connects | Wrong backend, browser lacks `SharedWorker`, or app disabled WebSocket mode | Verify backend/runtime requirements and browser support. |
| `WebsocketDisconnected` or silent stop in a long loop | Loop does not check `ws.is_shutdown` | Break or raise `PreventUpdate` when shutdown is set. |

## Related references

- [backend workflows](backend-workflows.md)
- [MCP and hooks](mcp-and-hooks.md)
