# Server and Client Workflows

This reference covers the two main directions for MCP integration in `mcp-agent`:

- consuming upstream MCP servers from agents, workflows, and direct clients;
- exposing an `MCPApp` as a FastMCP server with tools and workflow control endpoints.

## Consume Upstream MCP Servers

### Agent-attached servers

Use `server_names` on an `Agent` when an LLM or workflow should use server tools naturally.

```python
from mcp_agent.agents.agent import Agent

agent = Agent(
    name="researcher",
    instruction="Use the configured MCP servers to gather and summarize evidence.",
    server_names=["fetch", "docs_api"],
)

async with agent:
    tools = await agent.list_tools()
    resources = await agent.list_resources("docs_api")
```

Checklist:

- Every name in `server_names` must match a key under `mcp.servers`.
- Use `allowed_tools` in config before connecting servers with broad or unsafe tool surfaces.
- Call primitive listing methods during startup checks to confirm the server surface before asking an LLM to use it.

### Direct `gen_client`

Use `gen_client` inside tools/workflows when code needs explicit MCP calls.

```python
from mcp_agent.mcp.gen_client import gen_client

async with gen_client("docs_api", app.context.server_registry, context=app.context) as session:
    tools = await session.list_tools()
    result = await session.call_tool("search_docs", {"query": "oauth"})
```

`gen_client` is the right level when:

- a workflow task needs one deterministic server call;
- a decorated app tool proxies a nested MCP server;
- you need custom `MCPAgentClientSession` callbacks for logs, progress, or notifications.

### Aggregated servers

Use `MCPAggregator` to combine multiple servers into one namespaced surface.

```python
from mcp_agent.mcp.mcp_aggregator import MCPAggregator

aggregator = MCPAggregator(
    server_names=["fetch", "docs_api"],
    connection_persistence=True,
    context=app.context,
    name="research",
)

async with aggregator:
    tools = await aggregator.list_tools()
```

The aggregator keeps maps for namespaced tools, prompts, and resources. This helps when different servers expose the same primitive name. If collisions remain hard for the caller, narrow the config with `allowed_tools`.

## MCP Primitives

### Tools

```python
tools = await agent.list_tools("docs_api")
result = await agent.call_tool("search_docs", arguments={"query": "routing"})
```

When using a direct session:

```python
tools = await session.list_tools()
result = await session.call_tool("search_docs", {"query": "routing"})
```

### Resources

```python
resources = await agent.list_resources("docs_api")
content = await agent.read_resource("docs://guide/configuration")
```

### Prompts

```python
prompts = await agent.list_prompts("docs_api")
messages = await agent.create_prompt(
    prompt_name="summarize",
    arguments={"topic": "MCP transports"},
    resource_uris="docs://guide/transports",
    server_names=["docs_api"],
)
```

### Roots

Configure roots in `mcp.servers.<name>.roots`, then list them from an agent/session when the server supports roots.

```python
roots = await agent.list_roots("project_tools")
```

Roots are declaration metadata; they do not replace server-side sandboxing. Keep root sets narrow and validate `file://` URIs.

### Sampling

Some nested MCP servers ask the client to perform LLM sampling. In `mcp-agent`, sampling can be proxied upstream to a connected MCP client or handled locally through the app’s human-input callback.

Skeleton:

```python
from mcp_agent.app import MCPApp
from mcp_agent.human_input.console_handler import console_input_callback

app = MCPApp(
    name="sampling_client",
    human_input_callback=console_input_callback,
)
```

If a sampling request fails:

- confirm the app has a human-input callback when no upstream client is connected;
- inspect the requested model preferences and provide a compatible LLM provider;
- avoid silently auto-approving sampling in production flows.

### Elicitation

Servers can call `elicitation/create` to ask for structured user input. Configure an elicitation callback on the app:

```python
from mcp_agent.app import MCPApp
from mcp_agent.elicitation.handler import console_elicitation_callback

app = MCPApp(
    name="elicitation_client",
    elicitation_callback=console_elicitation_callback,
)
```

Elicitation schemas should use primitive fields only: `str`, `int`, `float`, and `bool`. Handle accepted, declined, and cancelled responses explicitly in server tools.

## Expose an MCPApp as a FastMCP Server

### Minimal pattern

```python
import asyncio
from mcp_agent.app import MCPApp
from mcp_agent.server.app_server import create_mcp_server_for_app

app = MCPApp(name="agent_server", description="Example MCPApp server")

@app.tool(name="echo", structured_output=True)
async def echo(message: str) -> dict[str, str]:
    return {"message": message}

async def main():
    async with app.run() as agent_app:
        mcp_server = create_mcp_server_for_app(agent_app, host="127.0.0.1", port=8000)
        await mcp_server.run_sse_async()

if __name__ == "__main__":
    asyncio.run(main())
```

Use `scripts/minimal_app_server.py` for a safe bundled skeleton that supports dry-run inspection before starting stdio or SSE mode.

### Decorator behavior

`MCPApp` decorators register app logic and `create_mcp_server_for_app(...)` publishes it through FastMCP.

| Decorator | Use | Exposed tool behavior |
| --- | --- | --- |
| `@app.tool` | Sync-style tool result, even if implemented as async Python | Tool name is the declared function/tool name and waits for completion. |
| `@app.async_tool` | Start work and return IDs | Tool name is the declared name and returns `workflow_id` plus `run_id`; poll with `workflows-get_status`. |
| `@app.workflow` + `@app.workflow_run` | Explicit workflow classes | Per-workflow endpoint `workflows-<WorkflowName>-run` plus generic workflow controls. |
| `@app.workflow_task` | Reusable task/activity | Used by workflows; not automatically exposed as a standalone tool. |
| `@app.workflow_signal` | Resume/wait signal handling | Use with `workflows-resume` or engine-specific signal support. |

### Generic workflow tools

The app server registers these generic tools:

| Tool | Purpose |
| --- | --- |
| `workflows-list` | List workflow types, descriptions, tool endpoints, and run parameter schemas. |
| `workflows-runs-list` | List workflow instances/runs, with pagination when supported. |
| `workflows-run` | Start a workflow by name and return `workflow_id`/`run_id`. |
| `workflows-get_status` | Fetch status/result/error for a run. |
| `workflows-resume` | Send a signal payload to a paused or waiting workflow. |
| `workflows-cancel` | Cancel a running workflow. |
| `workflows-store-credentials` | Store OAuth tokens for a workflow before it runs. |

Important distinction:

- Decorated `@app.tool` and `@app.async_tool` entries expose their declared names, not `workflows-<name>-run` aliases.
- Explicit workflow classes expose `workflows-<WorkflowName>-run`.
- `workflows-list` is the best runtime way to discover the actual surface and parameter schemas.

### FastMCP settings

`create_mcp_server_for_app(app, **kwargs)` forwards optional FastMCP settings. Common safe development settings are:

```python
mcp_server = create_mcp_server_for_app(
    agent_app,
    host="127.0.0.1",
    port=8000,
    debug=True,
    log_level="DEBUG",
)
```

Security notes:

- Bind to loopback for local testing.
- Do not expose a public network listener until auth, scopes, secrets, and allowed tools have been reviewed.
- Use OAuth-protected app-server settings when remote clients should authenticate.

## Verify Tool Surface Without Public Service

Use the bundled script:

```bash
python sub-skills/mcp-server-integration/scripts/minimal_app_server.py --mode dry-run --json
```

Expected output includes the generic workflow tools plus the skeleton’s declared tools and explicit workflow endpoint. This is a safe check because dry-run mode initializes the app and records tool registration without binding a public port.

## Client Session Callbacks

For clients that connect to an app server, `MCPAgentClientSession` can receive server logs and non-logging notifications. A factory can be passed to `gen_client(...)`:

```python
from datetime import timedelta
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession
from mcp.types import LoggingMessageNotificationParams
from mcp_agent.mcp.mcp_agent_client_session import MCPAgentClientSession

async def on_server_log(params: LoggingMessageNotificationParams) -> None:
    print(f"[{params.level}] {params.logger}: {params.data}")

def make_session(
    read_stream: MemoryObjectReceiveStream,
    write_stream: MemoryObjectSendStream,
    read_timeout_seconds: timedelta | None,
    context=None,
) -> ClientSession:
    return MCPAgentClientSession(
        read_stream=read_stream,
        write_stream=write_stream,
        read_timeout_seconds=read_timeout_seconds,
        logging_callback=on_server_log,
        context=context,
    )
```

After connecting, call `set_logging_level("info")` when the server advertises logging support.
