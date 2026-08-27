# MCP and Hooks

## When to read

Read this for Dash hooks, custom route injection, WebSocket hook validation, and
MCP configuration/exposure.

## Hooks

Dash exposes a hook registry with these common routes:

- `setup` - run after app instantiation.
- `layout` - mutate the served layout.
- `routes` - add custom routes.
- `error` - add an error handler.
- `callback` - add callbacks at app setup time.
- `index` - customize the HTML index.
- `custom_data` - add namespaced data to callback context.
- `dev_tools` - add devtools components.
- `websocket_connect` - validate WebSocket connections.
- `websocket_message` - validate WebSocket messages.

Hook return rules for WebSocket validation:

- truthy => allow
- falsy => reject with the default close code
- `(code, reason)` tuple => reject with a custom reason

## MCP configuration

Use `configure_mcp_server` to decide which Dash content the MCP endpoint exposes.
The exposed surface includes layout resources, callback resources, clientside
callbacks, and page resources.

Useful toggles:

- `include_layout`
- `include_callbacks`
- `include_clientside_callbacks`
- `include_pages`
- `expose_callback_docstrings`

The `mcp_enabled` decorator marks ordinary Python functions as MCP tools. It can
be used bare or with arguments:

```python
from dash.mcp import mcp_enabled

@mcp_enabled

def my_tool(x):
    return x
```

```python
@mcp_enabled(name="custom_name", expose_docstring=True)
def my_tool(x):
    return x
```

## MCP route behavior

- The endpoint expects JSON-RPC style messages.
- POST requests require `application/json`.
- The server returns a session ID header for clients to reuse.
- GET requests return a lightweight stream-open response.
- DELETE is refused with a 405-style JSON response.

## Failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MCP endpoint returns 415 | POST did not use `application/json`. | Send JSON and set the correct Content-Type. |
| Session appears stale after restart | Client session ID no longer matches server session state. | Refresh the client session or restart the client after server reload. |
| Cannot configure MCP inside a callback | Configuration attempted from request context. | Configure MCP at setup time, not inside callback execution. |
| Hook validation blocks a connection | WebSocket hook returned false or a custom close tuple. | Re-evaluate the connection criteria and validate the cookie/origin/session. |
