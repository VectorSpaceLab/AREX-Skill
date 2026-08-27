# MCP API Reference

## Core import surface

```python
from atomic_agents.connectors.mcp import (
    MCPFactory,
    MCPDefinitionService,
    MCPTransportType,
    MCPToolDefinition,
    MCPResourceDefinition,
    MCPPromptDefinition,
    SchemaTransformer,
    fetch_mcp_tools,
    fetch_mcp_resources,
    fetch_mcp_prompts,
    fetch_mcp_tools_async,
    fetch_mcp_resources_async,
    fetch_mcp_prompts_async,
    create_mcp_orchestrator_schema,
    fetch_mcp_attributes_with_schema,
)
```

## Transport types

| Transport | Meaning | Notes |
| --- | --- | --- |
| `STDIO` | spawn the MCP server as a subprocess and talk over stdio | endpoint is a command string; it is split with `shlex` |
| `SSE` | legacy Server-Sent Events transport | endpoint is typically `<server>/sse` |
| `HTTP_STREAM` | HTTP streaming transport | endpoint is typically `<server>/mcp/` |

## MCPDefinitionService

`MCPDefinitionService(endpoint=None, transport_type=MCPTransportType.HTTP_STREAM, working_directory=None)`

Responsibilities:

- connect to an MCP server or command
- list tools, resources, and prompts from a session
- apply transport-specific endpoint formatting
- raise clear errors when the endpoint is missing or the transport is invalid

Important behavior:

- `HTTP_STREAM` uses a `/mcp/` suffix.
- `SSE` uses a `/sse` suffix.
- `STDIO` requires a non-empty command string.

## MCPFactory

`MCPFactory(mcp_endpoint=None, transport_type=MCPTransportType.HTTP_STREAM, client_session=None, event_loop=None, working_directory=None)`

Responsibilities:

- fetch MCP definitions through a service or persistent session
- build dynamic tool/resource/prompt classes from MCP JSON schemas
- expose synchronous wrapper methods that internally call the async service

Important behavior:

- If `client_session` is provided, `event_loop` must also be provided.
- Generated tool/resource/prompt classes get an async `run`/`read`/`generate` path.
- Typed output schemas are used when MCP provides one; otherwise generic fallback schemas are used.

## SchemaTransformer

`SchemaTransformer.create_model_from_schema(schema, model_name, tool_name_literal, docstring=None, attribute_type="tool", is_output_schema=False)`

Responsibilities:

- convert JSON Schema into a Pydantic model
- preserve required/optional fields and nested unions
- add a `tool_name` literal field for tool-oriented input schemas
- optionally skip the `tool_name` field for output schemas

## Result extraction precedence for typed MCP outputs

When an MCP tool returns a typed output schema, the runtime tries the following in order:

1. `structuredContent` attribute
2. `content[0].text` parsed as JSON
3. `content[0].data` dict
4. dict with `structuredContent` or `content` keys
5. direct dict fallback

## Related workflows

- Use `workflows.md` for transport examples and orchestration patterns.
- Use `troubleshooting.md` for transport, session, and version failures.
