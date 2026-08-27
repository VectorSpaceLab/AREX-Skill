---
name: mcp
description: "Expose LitServe LitAPI endpoints as Model Context Protocol tools
  with schema extraction, streamable HTTP mounting, and connection
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LitServe MCP sub-skill

Use this sub-skill when a user wants to expose a `LitAPI` as a Model Context Protocol (MCP) tool, build or debug the tool schema, mount the streamable HTTP MCP route, or connect an MCP client such as Claude Desktop to a LitServe app.

## Routing

- Start here for requests like “add MCP to my LitServe app”, “make a tool from `decode_request`”, “why does MCP say it is not connected”, “mount the streamable HTTP MCP route”, or “build the MCP schema from Pydantic/type hints”.
- Use the root LitServe router at `../../SKILL.md` when the request is broader than MCP.
- Use `../server-basics/SKILL.md` when the user needs the underlying `LitAPI`, `LitServer`, request/response, batching, streaming, auth, middleware, or deployment model first.
- Route OpenAI-compatible chat and embedding endpoint work to `../openai-specs/SKILL.md`.
- Do not cover benchmark-only, torch-heavy, parity-throughput, or accelerator-specific workflows here.

## Operating checklist

1. Confirm the runtime has `fastmcp` installed. LitServe MCP construction raises a runtime error when MCP support packages are unavailable.
2. Create an `MCP` object with at least a useful `description`; optionally set a unique `name` and a manual `input_schema`.
3. Pass the `MCP` object into the `LitAPI` constructor (`super().__init__(mcp=...)` or a base class that accepts `mcp`). This connects the MCP object to the `LitAPI`; do not call private connection methods in user code.
4. Prefer automatic schema extraction from `decode_request` when the endpoint accepts a Pydantic request model or well-annotated parameters. Use a manual `input_schema` only when it matches the actual LitServe endpoint handler arguments.
5. Build the server with `ls.LitServer(api)` and run it normally. LitServe registers the tool and mounts the streamable HTTP MCP app automatically when MCP support is available.
6. Tell MCP clients to connect to the same host and port with the `/mcp/` suffix, for example `http://localhost:8000/mcp/`.
7. If the client lists the tool but tool calls fail, debug the schema shape, tool name uniqueness, and endpoint path mapping before changing core server code.

## Reference map

- `references/api-reference.md` — exact MCP constructor behavior, schema helper behavior, connector internals, and streamable HTTP route details.
- `references/workflows.md` — copyable patterns for adding MCP to a `LitAPI`, using Pydantic/type-hint schemas, checking the tool object, connecting clients, and Claude Desktop setup.
- `references/troubleshooting.md` — common failures: missing `fastmcp`, disconnected MCP, missing name/description, malformed schema, endpoint collisions, missing mounted route, beta warning, and Claude Desktop confusion.
- `scripts/mcp_server.py` — safe bundled example adapted from LitServe MCP behavior; it can print the generated tool metadata or run a local MCP-enabled LitServe server.

## Facts to preserve

- `MCP(description=None, input_schema=None, name=None)` accepts `description`, `input_schema`, and `name`.
- `extract_input_schema(func) -> dict[str, Any]` is available from `litserve.mcp`.
- `_python_type_to_json_schema` and `_param_name_to_title` are available helper functions.
- `MCP.as_tool()` requires a connected `LitAPI` and returns a `ToolEndpointType` with `name`, `description`, `inputSchema`, and `endpoint`.
- The tool name is sanitized by removing a leading slash and replacing remaining slashes with underscores.
- The MCP streamable HTTP endpoint is `/mcp/` on the LitServe server.
- MCP support is beta and its APIs may change.
