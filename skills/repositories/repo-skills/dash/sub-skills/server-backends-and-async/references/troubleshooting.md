# Backend, Async, Background, WebSocket, and MCP Troubleshooting

## When to read

Read this when backend selection, async callbacks, background managers,
WebSocket callbacks, hooks, or MCP routes fail.

## Backend import and selection

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for FastAPI backend | `dash[fastapi]` not installed | Install the extra and rerun the backend inspection script. |
| `ImportError` for Quart backend | `dash[quart]` not installed | Install the extra and rerun the backend inspection script. |
| `Dash(__name__, backend='fastapi')` fails | Optional backend not installed or incompatible | Install the backend extra, then inspect `get_backend('fastapi')` and app construction again. |
| Flask async coroutine error | `dash[async]` not installed | Install the async extra or move the app to FastAPI/Quart. |

## Background callback failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `DiskcacheManager requires extra dependencies` | `dash[diskcache]` missing | Install the extra. |
| `CeleryManager requires extra dependencies` | `dash[celery]` missing | Install the extra and configure Celery with a broker and result backend. |
| Background callback never resolves | Worker process, broker, or backend missing | Verify the manager's runtime dependencies and the callback traceback. |
| Progress never updates | The callback never calls the injected `set_progress` helper or the progress Output does not match | Confirm the progress output shape and call order. |
| Cancellation does not work | Cancel Input is not wired or the manager is not started with the expected job | Check the cancel dependency and the background manager wiring. |

## WebSocket failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| WebSocket callbacks never activate | Wrong backend or WebSocket mode disabled | Use FastAPI and enable `websocket_callbacks=True` or `websocket=True` on the callback. |
| Connection drops during a long task | The task ignores `ws.is_shutdown` | Check `is_shutdown` in long loops and exit cleanly. |
| `set_props` updates disappear | Connection closed or helper used outside the WebSocket context | Confirm the callback has `ctx.websocket` and the connection is still alive. |
| Browser-side WebSocket support missing | No `SharedWorker` in the browser runtime | Use a compatible browser or fall back to HTTP callback behavior. |

## Hooks and MCP failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Hooking a route has no effect | Hook registered too late or on the wrong app | Register hooks before the app serves requests. |
| MCP POST returns 415 | Missing JSON Content-Type | Send JSON and the correct header. |
| MCP tool not visible | `configure_mcp_server` excluded the relevant content or the function was not decorated | Check the include toggles and `mcp_enabled` decoration. |
| Cannot change MCP config during a callback | Configuration attempted inside request context | Move it to application setup. |

## Safe diagnostic steps

1. Run `scripts/inspect_backends.py --json` to see which backend extras are
   actually installed and which app constructions succeed.
2. Confirm the selected workflow's required extra is present before debugging the
   callback implementation itself.
3. For async/background/WebSocket bugs, inspect the callback traceback and the
   manager/backend configuration before assuming a logic bug.
