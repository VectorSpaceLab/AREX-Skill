# Backend Workflows

## When to read

Read this for backend selection, app construction around existing servers, and
core adapter facts.

## Backend model

Dash's backend layer normalizes different server frameworks behind a shared
interface. The key abstraction is `BaseDashServer`, with request/response
adapters for framework-specific behavior.

Verified public paths:

- `dash.backends.get_backend(name)` returns the backend wrapper class.
- `dash.backends.get_server_type(server)` detects `flask`, `fastapi`, or `quart`
  from a server instance.
- `Dash(..., backend=...)` can accept a backend name or backend class.
- `Dash(..., server=existing_server)` can wrap an existing server instance.

## Supported backend families

| Backend | Typical use | Install |
| --- | --- | --- |
| Flask | Default WSGI server path | `pip install dash` |
| FastAPI | ASGI, WebSocket callbacks, modern Python service integration | `pip install "dash[fastapi]"` |
| Quart | ASGI, async Flask-like service integration | `pip install "dash[quart]"` |

## Runtime facts

- `Dash(__name__)` creates a Flask-backed app by default.
- `Dash(__name__, backend='fastapi')` and `Dash(__name__, backend='quart')`
  create backend-specific app wrappers when the optional dependencies are
  installed.
- FastAPI/Quart backends expose async request handling and async-aware routes.
- Flask remains the default sync path; install `dash[async]` when you need Flask
  callback coroutines.
- `Dash` constructor parameters related to backend/runtime include `server`,
  `backend`, `use_async`, `websocket_callbacks`, `websocket_allowed_origins`,
  `websocket_inactivity_timeout`, `websocket_heartbeat_interval`, and
  `websocket_batch_delay`.

## Request and response adapters

Dash normalizes request/response access through adapters that provide:

- request args, headers, cookies, URL, path, and JSON access;
- response creation, cookies, and header mutation;
- backend-specific response wrappers for callback results.

Use the adapter methods instead of framework-specific request globals when code
needs to remain backend-agnostic.

## Safe inspection script

Use the bundled script to check imports and backend creation without starting a
server:

```bash
python path/to/server-backends-and-async/scripts/inspect_backends.py --json
```

The script reports missing optional extras explicitly so you can see whether a
backend is unavailable because the package is absent or because runtime service
support is missing.
