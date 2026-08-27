---
name: mcp-integrations
description: "Use the Atomic Agents MCP connector stack to discover tools,
  resources, and prompts over STDIO, SSE, or HTTP Stream."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MCP Integrations

Use this subskill when a task is about connecting Atomic Agents to MCP servers, transforming MCP schemas into Atomic Agent tools, or troubleshooting MCP transport and session behavior.

## Read first

- `references/api-reference.md` for `MCPFactory`, `MCPDefinitionService`, `SchemaTransformer`, and transport behavior.
- `references/workflows.md` for STDIO, SSE, HTTP Stream, and generated tool/resource/prompt recipes.
- `references/troubleshooting.md` for endpoint, session, and version-mismatch failures.
- `scripts/check_mcp_imports.py` for an offline MCP import/schema smoke check.

## Owns

- `MCPTransportType`, `MCPDefinitionService`, `MCPFactory`, and `SchemaTransformer`.
- `fetch_mcp_tools`, `fetch_mcp_resources`, `fetch_mcp_prompts`, and their async variants.
- `create_mcp_orchestrator_schema` and `fetch_mcp_attributes_with_schema`.
- STDIO, SSE, and HTTP Stream connection planning.
- Typed output extraction from MCP result payloads and generated dynamic tool/resource/prompt classes.

## Does not own

- Core agent construction, memory, hooks, or token counting; use `../agent-core/SKILL.md`.
- Base tool authoring and Atomic Forge / `atomic` CLI usage; use `../tooling-and-forge/SKILL.md`.
- Example project cataloging; use `../example-workflows/SKILL.md`.
- Repo maintenance; use `../repo-development/SKILL.md`.

## Common triggers

- "How do I connect to an MCP server?"
- "How do I turn MCP tools into Atomic Agent tools?"
- "Why does my MCP endpoint need `/mcp/` or `/sse`?"
- "Why is a persistent client session asking for an event loop?"
- "Why did the MCP import break after a dependency update?"
