# MCP Reference

CrewAI supports MCP servers through two paths:

1. Native `Agent(mcps=[...])` configuration from `crewai.mcp` for normal agent use.
2. `MCPServerAdapter` from `crewai_tools` for advanced manual lifecycle control.

Prefer native `mcps` unless you need to open a server, inspect/filter tools manually, and pass the resulting tool collection into `tools=[...]` yourself.

## Installation Boundary

MCP support requires the `mcp` library. Advanced adapter usage also expects the MCP extras for `crewai-tools`.

```bash
uv add mcp
uv pip install 'crewai-tools[mcp]'
```

Do not install packages or start network/local server processes without user approval in restricted environments.

## Native Agent MCP DSL

### String References

`Agent.mcps` accepts strings for remote HTTPS servers or connected CrewAI catalog integrations.

```python
from crewai import Agent

agent = Agent(
    role="Research Analyst",
    goal="Use approved MCP tools for research.",
    backstory="Connects only to MCP servers authorized for this run.",
    mcps=[
        "https://mcp.example.com/mcp",
        "https://api.weather.example/mcp#get_forecast",
        "snowflake",
        "stripe#list_invoices",
    ],
)
```

String behavior:

- HTTPS URL without `#`: discover all tools from that server.
- HTTPS URL with `#tool_name`: use one specific tool.
- Bare slug: resolve a connected CrewAI catalog MCP integration.
- Bare slug with `#tool_name`: resolve one tool from that connected integration.

Connected catalog integrations require the user's CrewAI account/platform configuration and may need platform tokens. Treat them as credential-bound.

### Structured Configs

Use structured configs for transport selection, headers/env, filtering, and tool-list caching.

```python
from crewai import Agent
from crewai.mcp import MCPServerHTTP, MCPServerSSE, MCPServerStdio
from crewai.mcp.filters import create_static_tool_filter

agent = Agent(
    role="MCP Analyst",
    goal="Use a constrained set of MCP tools.",
    backstory="Prefers filtered, least-privilege tool access.",
    mcps=[
        MCPServerStdio(
            command="python",
            args=["server.py"],
            env={"API_KEY": "read_from_runtime_secret_store"},
            tool_filter=create_static_tool_filter(
                allowed_tool_names=["read_file", "list_directory"],
                blocked_tool_names=["delete_file"],
            ),
            cache_tools_list=True,
        ),
        MCPServerHTTP(
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer runtime_token"},
            streamable=True,
            cache_tools_list=True,
        ),
        MCPServerSSE(
            url="https://stream.example.com/mcp/sse",
            headers={"Authorization": "Bearer runtime_token"},
        ),
    ],
)
```

Config fields:

| Config | Fields | Use when |
| --- | --- | --- |
| `MCPServerStdio` | `command`, `args`, `env`, `tool_filter`, `cache_tools_list` | Local MCP server process over stdin/stdout. |
| `MCPServerHTTP` | `url`, `headers`, `streamable`, `tool_filter`, `cache_tools_list` | Remote HTTP or streamable HTTP MCP server. |
| `MCPServerSSE` | `url`, `headers`, `tool_filter`, `cache_tools_list` | Remote Server-Sent Events MCP server. |

`cache_tools_list` caches discovery metadata, not the underlying tool result. Use it when the server's tool list is stable for the run.

## Tool Filtering

Static filters are the default least-privilege option.

```python
from crewai.mcp.filters import create_static_tool_filter

filter_tools = create_static_tool_filter(
    allowed_tool_names=["read_file", "list_directory"],
    blocked_tool_names=["delete_file"],
)
```

Filtering rules:

- Blocked tool names take precedence over allowed names.
- If `allowed_tool_names` is set, only those names pass unless blocked.
- Dynamic filters can receive `ToolFilterContext` with agent and server details; keep them deterministic and side-effect free.

## Native Execution Behavior

Native MCP resolution discovers tool definitions, converts schemas into CrewAI `BaseTool` wrappers, and creates fresh MCP clients for each invocation. This design prevents parallel calls to the same MCP tool from sharing mutable client state. Discovery and execution have bounded timeouts and retry behavior in CrewAI's resolver.

When no tools are discovered, CrewAI logs a warning and returns an empty tool list. For a specific `#tool` reference, a missing tool also logs a warning.

## MCPServerAdapter

Use `MCPServerAdapter` when you need manual lifecycle control or want a list-like `ToolCollection` to pass into `Agent(tools=...)`.

### Stdio Adapter

```python
from crewai import Agent
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env={"API_KEY": "read_from_runtime_secret_store"},
)

with MCPServerAdapter(server_params, "read_file", connect_timeout=30) as tools:
    agent = Agent(
        role="Local MCP User",
        goal="Use only the approved local MCP read tool.",
        backstory="Treats local server tools as privileged actions.",
        tools=tools,
    )
```

### SSE or Streamable HTTP Adapter

```python
from crewai_tools import MCPServerAdapter

server_params = {
    "url": "https://api.example.com/mcp",
    "transport": "streamable-http",
}

with MCPServerAdapter(server_params, connect_timeout=30) as tools:
    approved_tools = [tool for tool in tools if tool.name.startswith("safe_")]
```

Adapter details:

- Constructor accepts `StdioServerParameters` or a dict for remote transports.
- Positional tool names filter the discovered tool collection.
- `connect_timeout` defaults to `30` seconds.
- The adapter starts during initialization; context manager cleanup is the safest lifecycle pattern.
- If manually managed, always call `stop()` in `finally`.

```python
adapter = None
try:
    adapter = MCPServerAdapter(server_params, "safe_tool", connect_timeout=45)
    tools = adapter.tools
finally:
    if adapter is not None:
        adapter.stop()
```

## Transport Selection

| Transport | Best for | Security notes |
| --- | --- | --- |
| Stdio | Local server script or executable under user control | Validate command, args, working directory, env, and file-system permissions. Avoid passing broad secrets. |
| HTTP / Streamable HTTP | Remote MCP server over HTTPS | Prefer HTTPS, set auth headers at runtime, and confirm data exfiltration boundaries. |
| SSE | Remote real-time server stream | Use authentication. Local SSE servers should bind to `127.0.0.1`; server implementations should validate `Origin` headers. |

## Migrating a Stdio Server Into an Agent

1. Confirm the server command is installed and trusted.
2. Replace hardcoded paths and secrets with runtime configuration.
3. Use `MCPServerStdio(command=..., args=..., env=...)` in `Agent(mcps=[...])`.
4. Add `create_static_tool_filter(...)` to allow only necessary tools.
5. Set `cache_tools_list=True` if the server's tool list is stable.
6. Use task descriptions that constrain tool usage and data boundaries.
7. If using `MCPServerAdapter`, wrap it in `with` or call `stop()` in `finally`.

## Failure Modes

- Missing `mcp` package: install `mcp` or `crewai-tools[mcp]` before using MCP.
- Local command not found: verify executable availability and use explicit command names.
- Authentication failure: inspect headers/env without logging secrets.
- Timeout during discovery: reduce tool list, check server startup time, or increase adapter `connect_timeout` when using `MCPServerAdapter`.
- Empty tool list: verify server exposes tools and filters are not too restrictive.
- Specific tool not found: check sanitized tool names and `#tool` suffix spelling.
- Local process remains alive: prefer context managers; otherwise call `stop()` in `finally`.
- SSE DNS rebinding risk: bind local development servers to loopback and require server-side origin checks.

## Boundary Links

- Agent/task assignment and kickoff: [`core-runtime`](../../core-runtime/SKILL.md)
- RAG storage or knowledge retrieval architecture behind an MCP tool: [`memory-knowledge-and-rag`](../../memory-knowledge-and-rag/SKILL.md)
- LLM provider credentials used by an MCP server: [`llm-and-providers`](../../llm-and-providers/SKILL.md)
