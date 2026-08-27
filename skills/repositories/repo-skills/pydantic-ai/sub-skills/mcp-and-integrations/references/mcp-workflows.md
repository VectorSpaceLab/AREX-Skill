# MCP Workflows

Use this reference when connecting Pydantic AI to Model Context Protocol servers, exposing an agent from inside an MCP server tool, or choosing between local MCP tool execution and provider-native MCP support.

## MCP Selection Matrix

| Need | Prefer | Why | Notes |
| --- | --- | --- | --- |
| Current MCP client for tools/resources/prompts/sampling | `pydantic_ai.mcp.MCPToolset` | Full protocol path built on FastMCP `Client`; accepts URL, script path, transport, in-process server, pre-built client, or config-derived toolsets. | Requires the MCP optional dependencies for local client execution. |
| Remote MCP server that may be executed natively by the provider | `pydantic_ai.capabilities.MCP` | Chooses provider-native `MCPServerTool` when supported and local `MCPToolset` fallback otherwise. | Be explicit with `native=` in new code because defaults are changing in v2. |
| Existing code using old MCP SDK wrappers | `MCPServerStdio`, `MCPServerSSE`, `MCPServerHTTP`, `MCPServerStreamableHTTP` | Compatibility with legacy code and tests. | Deprecated; migrate to `MCPToolset`. |
| Existing code using `FastMCPToolset` | `MCPToolset` | `MCPToolset` accepts the same broad input shapes and adds parity with legacy MCP server classes. | `FastMCPToolset` is deprecated and removed in v2. |
| Multiple MCP servers in JSON config | `load_mcp_toolsets(config_path)` | Expands one `MCPToolset` per server entry. | `load_mcp_servers()` returns deprecated classes; avoid in new code. |
| A Pydantic AI agent exposed as an MCP server tool | FastMCP server function that calls `agent.run()` | There is no separate `Agent.to_mcp()` API in this checkout; put the agent call inside an MCP server tool. | Requires a server process/runtime outside Pydantic AI. |

## Client-Executed MCP with `MCPToolset`

`MCPToolset` is an `AbstractToolset`, so attach it with `Agent(toolsets=[...])` and manage lifecycle with `async with agent:` or `async with toolset:` when a run block will call the server repeatedly.

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

agent = Agent('openai:gpt-5.2', toolsets=[MCPToolset('http://localhost:8000/mcp', id='calc')])
```

Practical choices:

- Use a streamable HTTP URL for a separately hosted MCP server.
- Use a script path or a `fastmcp.client.transports.StdioTransport` for a local stdio server command.
- Use a pre-built `fastmcp.Client` only when you need custom OAuth/auth, roots, handlers, timeouts, or transport control.
- Use an in-process `FastMCP` server for deterministic tests or same-process application wiring.
- Set `id=` for durable execution and for logs; use `.prefixed('name')` or wrapper toolsets when multiple servers expose colliding tool names.
- Set `include_instructions=True` only when the server instructions should be added to the agent instructions.
- Keep `cache_tools=True` for static catalogs; set `cache_tools=False` when the server mutates tools without sending list-change notifications.
- Set `tool_error_behavior='retry'` for model-correctable server tool errors and `'error'` when the application should fail immediately.
- Use `process_tool_call` for request metadata or telemetry wrappers that must surround every server tool call.

`MCPToolset` also exposes resource and prompt operations for application code. Guard calls with the server's advertised capabilities and handle `MCPError` when resources, prompts, or the requested identifier are unavailable.

## MCP Config Files

Use `load_mcp_toolsets()` for JSON config with an `mcpServers` object. Server keys become toolset IDs. URL entries infer streamable HTTP unless the endpoint clearly targets the deprecated SSE path. Stdio entries can include `command`, `args`, and `env`.

Keep config values safe:

- Use environment-variable placeholders for secrets in config files, but do not print resolved secret values.
- Prefer `${VAR:-default}` only for non-secret defaults.
- Treat missing `${VAR}` values as configuration errors to fix before runtime.
- Avoid inheriting the parent process environment into stdio servers unless the server actually needs it.

## Native-or-Local MCP Capability

`pydantic_ai.capabilities.MCP` is for adaptive integration with provider-native MCP support.

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP

agent = Agent(
    'openai:gpt-5.2',
    capabilities=[
        MCP(
            'https://example.com/mcp',
            id='docs-mcp',
            native=True,
            local=True,
            allowed_tools=['search_docs'],
            description='Documentation search server.',
        )
    ],
)
```

Selection rules:

- `native=True` creates a provider-native `MCPServerTool` when the model supports it.
- `local=True` builds a local `MCPToolset` from the capability URL when the MCP extra is installed.
- `native=True, local=False` is native-only and avoids local client dependencies, but fails on models without native MCP support.
- `native=False` is local-only and requires the MCP optional dependencies.
- `authorization_token`, `headers`, and `allowed_tools` are applied to both native and local paths where possible.
- A non-URL local client, script path, in-process server, or pre-built client belongs in `local=MCPToolset(...)`, not in the serializable `local='...'` path.
- Pass a stable explicit `id` when the capability is deferred or when message history may be persisted and resumed.

Avoid confusion: provider-native MCP means the model provider calls the MCP server; client-executed MCP means Pydantic AI calls the server through `MCPToolset` and reports tool results back to the model. Authorization, network reachability, latency, and observability differ between those two paths.

## Deferred MCP

`MCP` is a capability, so it can be hidden behind on-demand loading:

```python
from pydantic_ai.capabilities import MCP

analytics = MCP(
    'https://analytics.example.com/mcp',
    id='analytics-mcp',
    native=True,
    local=True,
    defer_loading=True,
    description='Analytics queries and reports.',
)
```

Rules for deferred MCP:

- Always set `id=` explicitly; URL-derived IDs can drift between environments and break history replay.
- Treat the server instructions returned by a deferred capability as message-history-visible content after loading.
- Native tools or native MCP definitions may affect provider prompt-cache prefixes when loaded.
- On resume, the new agent must be constructed with a matching capability ID; history records loaded IDs, not capability definitions.

## Agent Inside an MCP Server

To expose a Pydantic AI agent through MCP, create an MCP/FastMCP server and call the agent from a server tool. The MCP server owns process startup, transport, auth, and lifecycle; Pydantic AI owns the internal agent run.

```python
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent

server = FastMCP('support-agent')
agent = Agent('openai:gpt-5.2', instructions='Answer support questions concisely.')

@server.tool()
async def answer_support_question(question: str) -> str:
    result = await agent.run(question)
    return result.output
```

If the MCP client should provide sampling instead of the server holding provider credentials, use an MCP sampling model in the server-side agent and ensure the client supports sampling callbacks. A plain MCP client without sampling support cannot satisfy server-side sampling requests.

## Migration Notes

- Replace `MCPServerStdio('python', ['server.py'])` with `MCPToolset('server.py')` when FastMCP can infer the stdio transport, or with a `StdioTransport` for arbitrary commands.
- Replace `MCPServerSSE`/`MCPServerHTTP`/`MCPServerStreamableHTTP` with `MCPToolset(url, ...)` for new code.
- Replace `load_mcp_servers()` with `load_mcp_toolsets()` for config-based loading.
- Replace `FastMCPToolset(...)` with `MCPToolset(...)`; the old class lacks some current MCP parity and is deprecated.
- Replace `agent.run_mcp_servers()` with `async with agent:`; use `agent.set_mcp_sampling_model()` only when legacy MCP server wrappers need a common sampling model.

## Safe Validation Without Servers

Before a live integration run, use the bundled import diagnostic script. It checks imports, constructor signatures, and optional group hints only; it does not start stdio servers, connect to URLs, fetch OAuth metadata, or validate credentials.
