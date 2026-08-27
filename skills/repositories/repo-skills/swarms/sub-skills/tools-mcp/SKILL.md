---
name: tools-mcp
description: "Guide Swarms tool schema conversion, BaseTool helpers, and MCP
  client/server workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Tools and MCP

Use this sub-skill when the user wants to turn Python callables into tools, reason about tool schemas, or connect Swarms to an MCP server.

## Owns these workflows

- Convert functions and Pydantic models into tool schemas.
- Use `BaseTool` to inspect, validate, and execute local tools.
- Configure `MCPManager`, `MCPConnection`, and `MCPOAuthConfig`.
- Use one or many MCP servers from an `Agent`.
- Build or smoke-test a small local MCP server.

## Does not own

- Single-agent prompt, memory, marketplace, or fallback behavior; use `single-agent`.
- CLI file loading or autoswarm generation; use `cli-loaders`.
- Multi-agent orchestration, routing, or swarm selection; use `multi-agent-workflows`.

## Read this sub-skill when the request mentions

- `BaseTool`, `tool_registry`, `func_to_dict`, `base_model_to_openai_function`, or `execute_tool_by_name`.
- `MCPManager`, `MCPConnection`, `MCPOAuthConfig`, `mcp_url`, `mcp_urls`, or `mcp_configs`.
- `streamable_http`, `sse`, `stdio`, auth headers, bearer tokens, OAuth, or tool routing.
- `Agent(..., mcp_url=...)` or local MCP server debugging.

## Working shape

1. Decide whether the user needs local tool schemas, a direct MCP client, or an MCP server.
2. Check auth style and transport before promising a live connection.
3. Use the bundled references for API shapes and recovery steps.
4. Prefer a local server smoke test before a remote MCP endpoint.

## What to read next

- `references/api-reference.md` for schema helpers and MCP config objects.
- `references/workflows.md` for function-schema, Agent+MCP, and local-server recipes.
- `references/troubleshooting.md` for auth, transport, and tool routing failures.
- `scripts/tool_schema_smoke.py` and `scripts/mcp_smoke.py` for safe offline checks.

## Typical user questions this sub-skill should answer

- How do I convert a function or Pydantic model into a tool schema?
- How do I route MCP tools from one or many servers?
- Why does the client say it cannot find a tool name?
- Why does a local MCP server work on one header but not another?
- How do I prove the tool path without talking to a remote service?

## Route boundaries

- If the task is mainly about one agent’s prompt or memory, route to `single-agent`.
- If the task is about command-line creation or file loaders, route to `cli-loaders`.
- If the task is about a swarm shape or router choice, route to `multi-agent-workflows`.

## Acceptance checklist

- The response should identify the right helper function or MCP config object.
- The response should state which transport and auth style are required.
- The response should provide a concrete smoke or validation step.
- The response should include a recovery path for missing dependencies, bad headers, or empty tool lists.
