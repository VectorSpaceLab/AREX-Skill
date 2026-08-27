---
name: mcp-and-hosted-tools
description: "Integrate local and hosted MCP tools in openai-agents-python,
  including stdio, SSE, Streamable HTTP, filtering, approvals, caching,
  metadata, retries, and structured content."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MCP and Hosted Tools

Use this sub-skill when a task mentions `MCPServerStdio`, `MCPServerSse`, `MCPServerStreamableHttp`, `HostedMCPTool`, `tool_filter`, `require_approval`, MCP auth, streamable HTTP, server managers, or hosted MCP connectors.

## Start Here

- Read [references/api-reference.md](references/api-reference.md) for constructor options, local transport differences, approval/filter forms, metadata hooks, and hosted MCP tool shape.
- Read [references/workflows.md](references/workflows.md) for copyable integration patterns: stdio, Streamable HTTP, server manager, filtering, approval, hosted MCP, metadata, caching, and fake-server tests.
- Read [references/troubleshooting.md](references/troubleshooting.md) for missing MCP imports, command failures, auth/session problems, stale cached tools, approval/structured-content surprises, and remote network restrictions.
- Run [scripts/check_mcp_config.py](scripts/check_mcp_config.py) to validate a JSON MCP config and import MCP classes without starting remote servers by default.

## Routing Boundaries

- Stay here for local MCP server lifecycle, stdio/SSE/Streamable HTTP params, `MCPServerManager`, `MCPUtil`, tool caching/filtering, MCP approvals, `_meta` resolvers, message handlers, structured content, hosted MCP `tool_config`, hosted approval callbacks, and MCP retry/error handling.
- Route generic `@function_tool`, function-tool guardrails, `handoff(...)`, and non-MCP approval declarations to [../tools-handoffs-guardrails/SKILL.md](../tools-handoffs-guardrails/SKILL.md).
- Route model/provider support, Responses versus Chat Completions compatibility, `OpenAIProvider`, websocket provider setup, and feature validation to [../models-providers/SKILL.md](../models-providers/SKILL.md).
- Route core runner semantics, `RunState` resume mechanics, sessions, streaming event interpretation, and `RunConfig` orchestration to [../core-runtime/SKILL.md](../core-runtime/SKILL.md).

## Fast Decisions

- Use local MCP servers in `Agent(mcp_servers=[...])` when the MCP server is local, private, needs custom auth/client behavior, or should execute tool calls in the application process.
- Use `HostedMCPTool` in `Agent(tools=[...])` when an OpenAI Responses model should call a public or connector-backed MCP server directly.
- Prefer Streamable HTTP for new HTTP MCP servers; keep SSE only for legacy servers, and use stdio when the server is a local subprocess.
- Enable `cache_tools_list=True` only when tool definitions are stable, and call `invalidate_tools_cache()` after capabilities change.
- Combine `tool_filter` with `require_approval` for least-privilege MCP exposure: hide irrelevant tools first, then approval-gate sensitive remaining calls.

## Safety Notes

- Do not put secrets, bearer tokens, local checkout paths, or machine-specific command paths in public skill content or logged config dumps.
- Do not start remote servers, invoke configured commands, or perform network checks just to validate configuration unless the user explicitly asks.
- Treat hosted MCP as Responses-only hosted-tool configuration; route provider/model feature questions before assuming a non-OpenAI provider supports it.
