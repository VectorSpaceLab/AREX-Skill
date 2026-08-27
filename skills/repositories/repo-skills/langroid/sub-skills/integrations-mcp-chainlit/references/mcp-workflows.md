# MCP workflows in Langroid

This reference covers Langroid's MCP bridge: converting MCP server tools into Langroid `ToolMessage` classes, enabling them on agents, and handling transport/event-loop details safely.

## Imports and entry points

Use the public MCP helpers from `langroid.agent.tools.mcp`:

```python
from langroid.agent.tools.mcp import (
    FastMCPClient,
    get_tool_async,
    get_tools_async,
    mcp_tool,
)
```

- `await get_tool_async(server, "tool_name")` returns one generated `ToolMessage` subclass.
- `await get_tools_async(server)` returns all generated `ToolMessage` subclasses with one tool-list round trip.
- `FastMCPClient(server)` exposes lower-level lifecycle control, resource forwarding, and `tool_model_from_mcp_tool()` for allow-listed bulk conversion.
- `@mcp_tool(server, "tool_name")` is declarative and copies user-defined methods onto the generated class, but it performs synchronous tool construction through `asyncio.run()`; only use it where no event loop is already running.

`FastMCP` is a base dependency in this repo, so in-memory server smoke tests do not need extra installation.

## Supported server specs and transports

Langroid accepts the same broad server specs expected by FastMCP clients:

- In-memory `FastMCP` server instance.
- Local MCP server script path.
- Network server URL supported by the installed FastMCP transport layer.
- A `ClientTransport`, such as `StdioTransport`, `NpxStdioTransport`, `UvxStdioTransport`, `SSETransport`, or streamable HTTP transport if available in the installed FastMCP version.
- A zero-argument factory returning one of the above.

Prefer a factory for stdio-style transports:

```python
from fastmcp.client.transports import StdioTransport
from langroid.agent.tools.mcp import get_tool_async

PingTool = await get_tool_async(
    lambda: StdioTransport(command="python", args=["server.py"]),
    "ping",
)
```

Why: subprocess transports are lifecycle-sensitive. A factory gives each connection a fresh process/session and avoids reusing closed pipes. Langroid internally clones plain `StdioTransport` instances when possible, while preserving stateful keep-alive behavior for `NpxStdioTransport` and `UvxStdioTransport`; the factory style is still the most explicit and portable.

## Programmatic pattern inside async code

Use this pattern in Chainlit callbacks, async examples, tests, notebooks, or any function where an event loop may already exist:

```python
import langroid as lr
import langroid.language_models as lm
from fastmcp.server import FastMCP
from pydantic import Field  # pydantic v2 for FastMCP server schemas
from langroid.agent.tools.mcp import get_tool_async


def make_server() -> FastMCP:
    server = FastMCP("MathServer")

    @server.tool()
    def add(
        a: int = Field(..., description="First integer"),
        b: int = Field(..., description="Second integer"),
    ) -> int:
        """Add two integers."""
        return a + b

    return server


async def make_task() -> lr.Task:
    AddTool = await get_tool_async(make_server(), "add")
    agent = lr.ChatAgent(
        lr.ChatAgentConfig(
            llm=lm.OpenAIGPTConfig(async_stream_quiet=False),
            system_message="Use the available tools when arithmetic is requested.",
        )
    )
    agent.enable_message(AddTool)
    return lr.Task(agent, interactive=False)
```

Do not call synchronous `get_tool()` / `get_tools()` or use `@mcp_tool` from inside this async function; those wrappers use `asyncio.run()`.

## Decorator pattern when no loop is running

The decorator is convenient for module-level tool declarations and custom `handle_async()` formatting:

```python
import langroid as lr
from fastmcp.client.transports import StdioTransport
from langroid.agent.tools.mcp import mcp_tool


@mcp_tool(lambda: StdioTransport(command="python", args=["server.py"]), "search")
class SearchTool(lr.ToolMessage):
    async def handle_async(self) -> str:
        raw = await self.call_tool_async()  # recent Langroid returns (content, files)
        content = raw[0] if isinstance(raw, tuple) else raw
        return f"<SearchResult>\n{content}\n</SearchResult>"
```

Use a transport factory rather than constructing a stdio transport as a module-level singleton. Module-level stdio construction may launch subprocesses during import and can later surface as closed-loop or closed-pipe errors.

## Subclassing a generated tool for custom handling

When code is already async, generate the base class first and subclass it:

```python
BaseSearch = await get_tool_async(server, "search")

class SearchTool(BaseSearch):  # type: ignore[misc, valid-type]
    async def handle_async(self) -> str:
        raw = await self.call_tool_async()
        content = raw[0] if isinstance(raw, tuple) else raw
        return f"Use this search evidence only:\n{content}"
```

This avoids the decorator's `asyncio.run()` while preserving generated MCP fields, schema, and `call_tool_async()`.

## Enabling MCP tools on agents

Generated MCP tools behave like Langroid `ToolMessage` classes:

```python
tools = await get_tools_async(server)
agent.enable_message(tools)
```

The generated tool class has:

- `request` set to the MCP tool name.
- `purpose` set to the MCP tool description, or a fallback if missing.
- Pydantic-backed fields derived from the MCP input schema.
- `call_tool_async()` for raw MCP invocation.
- Default `handle_async()` that returns text, or returns a `ChatDocument` with file attachments when files are forwarded and an agent is supplied.

If an MCP parameter name collides with reserved Langroid fields (`request`, `purpose`, `recipient`, `name`), Langroid renames the generated field with a `__` suffix. Instantiate with `request__=...`, `purpose__=...`, `recipient__=...`, or `name__=...` as needed.

## Schema and output behavior

Langroid preserves useful MCP schema details for LLM grounding and runtime validation:

- Scalar `enum` and `const` become `Literal` constraints.
- `anyOf` / `oneOf` become `Union`, with nullable branches mapped to `Optional`.
- Objects with properties become nested models.
- Arrays become lists.
- Local `$defs` references are resolved where possible; cyclic or malformed schema portions degrade to `Any` rather than blocking tool creation.

Newer MCP clients may validate tool outputs against declared output schemas. If a server supports an argument like `output_mode`, set it to a structured mode before calling `call_tool_async()`:

```python
class GrepTool(BaseGrep):  # type: ignore[misc, valid-type]
    async def handle_async(self) -> str:
        if hasattr(self, "output_mode"):
            self.output_mode = "structured"
        raw = await self.call_tool_async()
        return raw[0] if isinstance(raw, tuple) else str(raw)
```

## Resource forwarding

`FastMCPClient` can convert MCP content into text and Langroid file attachments:

```python
async with FastMCPClient(
    server,
    forward_images=True,
    forward_text_resources=True,
    forward_blob_resources=True,
) as client:
    ChartTool = await client.get_tool_async("get_chart")
```

- Images are forwarded by default when `forward_images=True`.
- Text resources are included only when `forward_text_resources=True`.
- Blob resources are attached only when `forward_blob_resources=True`.
- To receive file attachments from the default generated handler, call `await tool_msg.handle_async(agent)` so the handler can return `agent.create_agent_response(..., files=...)`.

## Persistent connections and bulk conversion

Use `persist_connection=True` when a server intentionally keeps state across multiple tool calls:

```python
async with FastMCPClient(server, persist_connection=True) as client:
    AddBeans = await client.get_tool_async("add_beans")
    Count = await client.get_tool_async("get_num_beans")
```

Always close persistent clients with `async with` or `await client.close()`.

For large servers, use one list call and convert only allow-listed tools:

```python
async with FastMCPClient(server) as client:
    raw_tools = await client.client.list_tools()
    wanted = [t for t in raw_tools if t.name in {"search", "fetch"}]
    tool_classes = [client.tool_model_from_mcp_tool(t) for t in wanted]
```

## Bounded local checks

Before contacting an external MCP server or search service:

1. Verify required Python imports locally.
2. Verify command availability with a local `--help` or version check when the server is a subprocess.
3. Verify required environment variables are set before launching network transports.
4. Use explicit timeouts around subprocess or network tool listing.
5. Keep the default smoke test no-network by using the bundled in-memory MCP script from this sub-skill.
