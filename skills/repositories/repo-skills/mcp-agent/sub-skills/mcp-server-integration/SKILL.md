---
name: mcp-server-integration
description: "Connect mcp-agent applications to MCP servers and expose MCPApp
  workflows as FastMCP servers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MCP Server Integration

Use this sub-skill when an agent needs to connect an `mcp-agent` app to upstream MCP servers or expose an `MCPApp` itself as an MCP server. It covers transport configuration, server registry behavior, connection lifecycle, MCP primitives, OAuth/authentication, roots, sampling, elicitation, and safe client-install preparation.

## Start Here

1. For app and agent construction, first read `../core-sdk/SKILL.md`, then return here for server wiring.
2. Choose the direction:
   - **Consume upstream MCP servers**: configure `mcp.servers`, attach agents with `server_names`, or use `gen_client`/`MCPAggregator` directly.
   - **Expose this app as an MCP server**: decorate tools/workflows on `MCPApp`, then call `create_mcp_server_for_app(app, **kwargs)`.
   - **Prepare client installation/deployment**: use the checks here, then follow `../cli-cloud-operations/SKILL.md` for CLI install/deploy commands.
3. Read the closest bundled reference:
   - `references/configuration.md` for `MCPServerSettings`, transports, roots, registry, and client install dry-runs.
   - `references/server-and-client-workflows.md` for `create_mcp_server_for_app`, workflow tools, decorators, primitives, aggregators, sampling, and elicitation.
   - `references/oauth-and-auth.md` for downstream OAuth servers, token storage, pre-authorization, and OAuth-protected app servers.
   - `references/troubleshooting.md` for common failure modes and fixes.
4. Use bundled scripts before running real services:
   - `scripts/validate_server_config.py --help`
   - `scripts/validate_server_config.py path/to/mcp_agent.config.yaml --check-executables`
   - `scripts/minimal_app_server.py --help`
   - `scripts/minimal_app_server.py --mode dry-run --json`

## Upstream Server Checklist

- Define every upstream server under `mcp.servers.<server_name>` and make sure the agent/workflow uses the same exact `server_name`.
- Use `transport: stdio` with `command` and `args`; use `sse`, `streamable_http`, or `websocket` with `url`.
- Put bearer/API tokens in `headers` or secrets-backed placeholders; use `auth.oauth` only for delegated OAuth flows.
- Set `roots` as `file://` URIs when a server needs declared filesystem access, and include `server_uri_alias` only when the server expects a different mounted URI.
- Use `allowed_tools` to restrict high-risk or collision-prone tool surfaces before exposing them to an LLM.
- Prefer `gen_client(server_name, app.context.server_registry, context=app.context)` for a direct client session and `MCPAggregator([...])` when an agent needs a combined tools/resources/prompts surface.

## App Server Checklist

- Register simple callable tools with `@app.tool` for synchronous results and `@app.async_tool` when callers should receive `workflow_id`/`run_id` and poll later.
- Register workflow classes with `@app.workflow` and `@app.workflow_run` when the workflow needs explicit workflow semantics or signals.
- Wrap the running app with `create_mcp_server_for_app(agent_app, **fastmcp_kwargs)` only after `async with app.run() as agent_app`.
- Expect generic workflow tools: `workflows-list`, `workflows-runs-list`, `workflows-run`, `workflows-get_status`, `workflows-resume`, `workflows-cancel`, and `workflows-store-credentials`.
- For explicit workflow classes, expect per-workflow tools named `workflows-<WorkflowName>-run`; decorator tools expose their declared names instead.
- Avoid starting public network transports during validation; use `scripts/minimal_app_server.py --mode dry-run` to inspect the expected surface first.

## MCP Primitives

- **Tools**: call with `agent.call_tool(...)`, `session.call_tool(...)`, or let an attached LLM invoke allowed tools.
- **Resources**: list/read with `list_resources()` and `read_resource(uri)`.
- **Prompts**: list/get with `list_prompts()` and `get_prompt(...)`; use agent prompt helpers when combining prompts with resource content.
- **Roots**: configure `roots` on the server entry; validate every URI starts with `file://`.
- **Sampling**: provide an `MCPApp` human-input callback when nested servers may request LLM sampling approval.
- **Elicitation**: provide an `MCPApp` elicitation callback when servers may call `elicitation/create`; schema fields must stay primitive (`str`, `int`, `float`, `bool`).

## When Not To Use This Sub-skill

- Use `../core-sdk/SKILL.md` for basic `MCPApp`, `Agent`, LLM, and workflow construction before server integration.
- Use `../durable-execution/SKILL.md` for Temporal worker operations and durable workflow runtime management.
- Use `../cli-cloud-operations/SKILL.md` for CLI command syntax, cloud deployment, and hosted app lifecycle operations.
