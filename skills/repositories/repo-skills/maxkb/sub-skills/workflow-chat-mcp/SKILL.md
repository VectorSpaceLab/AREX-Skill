---
name: "workflow-chat-mcp"
description: "Covers MaxKB application workflows, chat streaming, and MCP
  JSON-RPC execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# workflow-chat-mcp

Use this sub-skill for application workflow, chat runtime, streaming-response, and MCP tasks.

## Owns
- `apps/application/flow/*` and the workflow engine.
- `apps/application/chat_pipeline/*` as the legacy comparison path.
- `apps/application/views/*` and `apps/chat/views/*` runtime behavior.
- `apps/chat/mcp/tools.py` and `apps/chat/views/mcp.py` JSON-RPC flow.
- Response framing via `apps/common/handle/*`.

## Do not own
- Knowledge vector search and provider catalogs -> `knowledge-models`.
- Vue workflow canvas UI -> `frontend-integration`.
- Tool CRUD / trigger management / admin pages -> `admin-access`.
- Generic service bootstrap -> `runtime-architecture`.

## Key files
- `references/workflow-and-chat.md`
- `references/troubleshooting.md`
- `scripts/workflow_node_catalog.py`

## Guidance
- Treat chat runtime, streaming shape, and MCP auth as separate concerns.
- Keep MCP answers JSON-RPC focused and do not expose tokens.
- Use the backend node registry as the source of truth for node families.
