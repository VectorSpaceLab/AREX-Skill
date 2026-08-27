---
name: server-backends-and-async
description: "Use for Dash backend selection, async callbacks, WebSocket
  callbacks, background callbacks, hooks, and MCP server configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Dash Server Backends and Async Workflows

Use this sub-skill when a task depends on Dash's server runtime rather than the
layout/callback API alone: backend selection, async callbacks, background
callbacks, WebSocket callbacks, hooks, or MCP exposure.

## Start here

1. Read [references/backend-workflows.md](references/backend-workflows.md) for
   backend selection, adapters, and constructor/runtime facts.
2. Read [references/background-and-websocket-callbacks.md](references/background-and-websocket-callbacks.md)
   for async, background, and WebSocket behavior.
3. Read [references/mcp-and-hooks.md](references/mcp-and-hooks.md) for hooks and
   MCP configuration.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   backend import or optional-extra path fails.
5. Run [scripts/inspect_backends.py](scripts/inspect_backends.py) for a safe
   optional-backend diagnostic before promising backend coverage.

## Main routes

### Choose or inspect a backend

Dash defaults to Flask but can also run on FastAPI or Quart. Use this sub-skill
when you need to know which backend constructor to use, which extras are needed,
or how to create a Dash app around an existing server instance.

### Write async or background callbacks

Use this sub-skill for `async def` callbacks, `background=True`,
`DiskcacheManager`, `CeleryManager`, `progress`, `running`, `cancel`, and cache
keys.

### Use WebSocket callbacks

Route WebSocket tasks here when the callback depends on `websocket_callbacks`,
`websocket=True`, `persistent=True`, `ctx.websocket`, `set_props`, or browser/
server disconnect behavior. FastAPI is the backend surface that exposes the
WebSocket path in Dash.

### Expose hooks or MCP content

Use this sub-skill for `hooks.setup`, `hooks.layout`, `hooks.route`,
`hooks.error`, `hooks.callback`, `hooks.websocket_connect`,
`hooks.websocket_message`, `configure_mcp_server`, and `mcp_enabled`.

## Route elsewhere

- Plain callback, layout, page, asset, and clientside app behavior:
  [app callback workflows](../app-callback-workflows/SKILL.md).
- Component wrapper generation, `dash-renderer`, and resource loading:
  [component renderer development](../component-renderer-development/SKILL.md).
- Test selection and browser command strategy:
  [testing and maintenance](../testing-and-maintenance/SKILL.md).

## Validation checklist

Before marking a backend workflow solved:

- The installed extra or backend package is present.
- If the workflow requires Flask async, `dash[async]` is installed.
- If the workflow requires FastAPI or Quart, the relevant extra is installed and
  a safe app/backend construction check passes.
- If the workflow requires Diskcache or Celery, the corresponding dependency set
  is installed and the service requirement is called out when applicable.
- If the workflow uses WebSocket callbacks, the backend and browser/runtime
  prerequisites are explicitly named.
- If a hook or MCP change alters route exposure, the sub-skill references explain
  the request/session/content-type rules and the expected failure modes.
