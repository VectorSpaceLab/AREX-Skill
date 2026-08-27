# Workflow, chat, and MCP

## Backend workflow stack
- The older `chat_pipeline/` path is a linear comparison point.
- The newer `flow/` engine uses `WorkflowManage`, `Workflow`, `Node`, and `Edge` objects plus a thread-pool-backed executor.
- Node families are registered through `apps/application/flow/step_node/__init__.py` and the `node_list`/`node_map` lookup.
- Flow execution supports stream and block styles and has interruption-aware logic for looping and form-style nodes.

## Chat runtime surfaces
- `apps/application/views/application.py` and the related chat/key/token views expose application management and runtime access.
- `apps/chat/api/chat_api.py`, `chat_authentication_api.py`, and `chat_embed_api.py` expose chat-facing APIs.
- Streaming responses are built through `BaseToResponse` and the `system`, `openai`, and `loop` response strategies.
- SSE chunk formatting uses the `data: ...\n\n` pattern.

## MCP surfaces
- `apps/chat/views/mcp.py` handles JSON-RPC methods `initialize`, `tools/list`, and `tools/call`.
- `chat.mcp.tools.MCPToolHandler` authenticates through an active `ApplicationApiKey` and requires a published application.
- Missing `id` returns HTTP 204; unknown methods return JSON-RPC `-32601`.
- Tool calls are transformed into chat requests and streamed back into MCP-compatible content.

## Practical routing
- Use this sub-skill when the request is about workflow semantics, chat behavior, or MCP runtime.
- Route tool management to `admin-access` and frontend node canvas questions to `frontend-integration`.

## Validation notes
- Static node-catalog checks are usually enough for structure questions.
- Live MCP checks need an application key and a published application, so note that dependency if it is not available.
