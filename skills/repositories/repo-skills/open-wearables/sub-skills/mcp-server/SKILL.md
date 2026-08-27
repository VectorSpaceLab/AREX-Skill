---
name: mcp-server
description: "Use for Open Wearables FastMCP server setup, assistant
  configuration, tool/API client extension, prompt formatting, MCP tests, and
  backend/API-key failure handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MCP Server

Use this sub-skill when the task is about the Open Wearables MCP package for AI assistants: FastMCP startup, Claude Desktop/Cursor/MCPJam connection templates, API-client configuration, MCP tool routing, prompt formatting, mocked MCP tests, or diagnosing API-key/backend failures surfaced through MCP tools.

## Route Here When

- The user mentions MCP, Model Context Protocol, FastMCP, Claude Desktop, Cursor MCP settings, MCPJam, or assistant access to wearable data.
- The task names MCP tools such as `get_users`, `get_activity_summary`, `get_sleep_summary`, `get_workout_events`, or `get_timeseries`.
- The task changes the MCP REST client, tool envelopes, typed error handling, date-range guidance, or the `present_health_data` prompt.
- The task asks how to run the MCP server locally, configure `OPEN_WEARABLES_API_URL` / `OPEN_WEARABLES_API_KEY`, or test tool calls without a live API.

## Route Elsewhere

- Backend API route behavior, API-key issuance, user CRUD, summaries/events/timeseries endpoint implementation, auth, database, migrations, Redis, or Celery belong in [backend-core](../backend-core/SKILL.md).
- Provider OAuth/import/webhook/coverage internals belong in [provider-integrations](../provider-integrations/SKILL.md).
- React portal pages, hooks, settings UI, and dashboard/device-pairing presentation belong in [frontend-portal](../frontend-portal/SKILL.md).

## Read Order

1. For available tools, client endpoint paths, response envelopes, prompt behavior, or adding a tool, read [references/tools-and-client.md](references/tools-and-client.md).
2. For local install, environment variables, assistant configuration templates, and non-live setup checks, read [references/setup-and-assistant-config.md](references/setup-and-assistant-config.md).
3. For missing key, connection refused, 401/404/5xx, no users, date-range defaults, or app-import confusion, read [references/troubleshooting.md](references/troubleshooting.md).
4. For a safe config/import diagnostic that never calls the live API by default, run or adapt [scripts/check_mcp_config.py](scripts/check_mcp_config.py).

## Operating Rules

- Keep MCP changes REST-client-driven. Do not bypass the Open Wearables backend by sharing database models or direct DB access from the MCP package.
- Treat the API key as a secret. Use placeholders in docs and assistant configs; never commit real keys or assistant-machine paths.
- MCP summary tools require explicit date arguments. When the user omits a period, follow the server instruction default of the last 2 weeks before calling the tool.
- Prefer mocked HTTP tests for MCP behavior. The native MCP test candidates use `pytest`, `pytest-asyncio`, and `pytest-httpx`; they do not require a live backend.
- If tool behavior depends on a backend endpoint contract change, coordinate with [backend-core](../backend-core/SKILL.md) and then update MCP client/tool tests.
