# LangBot MCP Server

LangBot's own MCP server is mounted at `/mcp` on the same host and port as the
HTTP API. It uses streamable HTTP with API-key authentication.

## Current Tool Families

The server intentionally exposes a curated subset:

- `get_system_info`
- Bot tools: list/get/create/update/delete.
- Pipeline tools: list/get/create/update/delete.
- Model/provider reads: LLM models, embedding models, providers.
- Knowledge-base reads and retrieval.
- External MCP server listing; these are servers LangBot connects to as a
  client, not LangBot's own `/mcp` server.
- Installed skill listing and single skill lookup.

Mutating tools take JSON dictionaries shaped like the corresponding HTTP API
request bodies and rely on the authenticated Workspace context.

## Update Rule

When adding or changing an HTTP endpoint that should be agent-accessible:

1. Decide whether it belongs in the curated MCP surface. Do not expose internal
   routes merely because they exist.
2. Add a tool with a concise description and direct service-layer call.
3. Reuse existing permission checks through MCP request context.
4. Add or adjust tests for auth, tool listing, and representative tool calls.
5. Update agent-facing guidance so future agents know the new surface.

## Smoke Test Shape

The manual MCP smoke creates a mocked service graph, starts an MCP mount on a
local port, verifies unauthenticated requests get `401`, lists tools with a
global key, and calls representative tools. It is useful after transport,
auth-context, or tool-registration changes.
