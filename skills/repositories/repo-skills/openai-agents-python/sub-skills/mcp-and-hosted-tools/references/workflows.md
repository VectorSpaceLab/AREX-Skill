# MCP and Hosted Tools Workflows

These workflows distill repository examples and tests into self-contained patterns. Replace placeholder URLs, commands, and tool names with application-owned values.

## 1. Choose the Transport

1. If the MCP server is a local command, use `MCPServerStdio`.
2. If the server is HTTP and current, use `MCPServerStreamableHttp`.
3. If the server is HTTP/SSE only, use `MCPServerSse` for legacy compatibility.
4. If OpenAI Responses should call a public or connector-backed MCP server directly, use `HostedMCPTool`.
5. If multiple local servers may fail independently, wrap them in `MCPServerManager` and pass `manager.active_servers` to the agent.

Keep local MCP servers in `mcp_servers=[...]`; keep hosted MCP in `tools=[...]`.

## 2. Local Stdio Server

Use this for subprocess servers such as Python modules, Node packages, or app-owned binaries.

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="workspace-files",
    params={
        "command": "python",
        "args": ["-m", "my_app.mcp_server"],
        "env": {"MCP_MODE": "readonly"},
    },
    cache_tools_list=True,
) as server:
    agent = Agent(
        name="Assistant",
        instructions="Use the MCP tools when they help answer workspace questions.",
        mcp_servers=[server],
    )
    result = await Runner.run(agent, "Which MCP tools are available?")
```

Checklist:

- Confirm the executable is on `PATH` or provide an application-controlled absolute command outside public docs.
- Avoid shell strings; pass `command` and `args` separately.
- Set `cwd` only when the server expects a working directory.
- Use `cache_tools_list=True` only for stable tool catalogs.
- Add `tool_filter` and `require_approval` before letting the agent see sensitive tools.

## 3. Streamable HTTP Server With Auth

Use this for private or remote HTTP MCP servers controlled by your app.

```python
import httpx

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

server = MCPServerStreamableHttp(
    name="tenant-mcp",
    params={
        "url": "https://mcp.example.test/mcp",
        "headers": {"X-Client": "agents-sdk"},
        "auth": httpx.BasicAuth("user", "password"),
        "timeout": 10,
        "sse_read_timeout": 300,
    },
    max_retry_attempts=2,
    retry_backoff_seconds_base=0.5,
)

async with server:
    agent = Agent(name="Assistant", mcp_servers=[server])
    result = await Runner.run(agent, "Use the tenant MCP tools to answer the request.")
```

For bearer tokens, inject headers from the application runtime instead of hard-coding them. For OAuth refresh, use a custom `httpx.Auth` implementation. For custom TLS/proxy/test clients, pass `httpx_client_factory` in `params`.

## 4. Resume Streamable HTTP Sessions

Some Streamable HTTP servers issue an MCP session id. Capture it after connect and send it in a later worker via headers.

```python
async with MCPServerStreamableHttp(params={"url": url}) as server:
    session_id = server.session_id

headers = {"Mcp-Session-Id": session_id} if session_id else {}
async with MCPServerStreamableHttp(params={"url": url, "headers": headers}) as server:
    ...
```

Use this only when the remote server documents that `Mcp-Session-Id` resumes server-side state. After `cleanup()`, `server.session_id` returns `None`.

## 5. Legacy SSE Server

Use `MCPServerSse` when a server still exposes HTTP with Server-Sent Events.

```python
from agents.mcp import MCPServerSse

async with MCPServerSse(
    name="legacy-sse",
    params={"url": "https://mcp.example.test/sse", "headers": {"X-App": "demo"}},
) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
```

Prefer migrating new servers to Streamable HTTP or stdio.

## 6. Server Manager for Multiple Local Servers

Use `MCPServerManager` when an app owns several local servers and should continue with the connected subset.

```python
from agents import Agent, Runner
from agents.mcp import MCPServerManager, MCPServerStreamableHttp

servers = [
    MCPServerStreamableHttp(name="calendar", params={"url": "https://calendar.example.test/mcp"}),
    MCPServerStreamableHttp(name="docs", params={"url": "https://docs.example.test/mcp"}),
]

async with MCPServerManager(
    servers,
    drop_failed_servers=True,
    strict=False,
    connect_timeout_seconds=5,
) as manager:
    agent = Agent(name="Assistant", mcp_servers=manager.active_servers)
    result = await Runner.run(agent, "Which connected MCP tools can help?")
```

If `manager.failed_servers` is non-empty, inspect `manager.errors` and decide whether to call `await manager.reconnect(failed_only=True)` before a later run. Use `strict=True` when every server is required.

## 7. Static Tool Filtering Plus Approval

A safe least-privilege pattern is to filter first, then require approval for sensitive remaining tools.

```python
from agents.mcp import MCPServerStdio, create_static_tool_filter

server = MCPServerStdio(
    name="files",
    params={"command": "python", "args": ["-m", "my_file_mcp"]},
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["read_file", "write_file", "delete_file"],
        blocked_tool_names=["delete_file"],
    ),
    require_approval={"write_file": "always", "read_file": "never"},
)
```

The allow list runs before the block list. If both lists mention the same name, the block list wins. Approval policies apply only to tools that remain exposed.

## 8. Dynamic Tool Filtering

Use a dynamic filter when available tools depend on agent identity or run context.

```python
from agents.mcp import ToolFilterContext

async def filter_by_role(context: ToolFilterContext, tool) -> bool:
    role = (context.run_context.context or {}).get("role", "reader")
    if role == "admin":
        return True
    return tool.name.startswith("read_") or tool.name.startswith("list_")

server.tool_filter = filter_by_role
```

Dynamic filters need `run_context` and `agent`, so use them through `Agent.get_mcp_tools(...)`, `Agent.get_all_tools(...)`, normal runner execution, or `MCPUtil.get_all_function_tools(...)` with explicit context and agent. If the filter raises, the SDK excludes that tool.

## 9. Dynamic Approval Policy

Use callable `require_approval` when policy depends on the active run or tool metadata.

```python
from agents import RunContextWrapper

async def require_for_writes(run_context: RunContextWrapper, agent, tool) -> bool:
    role = (run_context.context or {}).get("role")
    if role == "admin":
        return False
    return tool.name.startswith(("write_", "delete_", "send_"))

server = MCPServerStreamableHttp(
    params={"url": "https://mcp.example.test/mcp"},
    require_approval=require_for_writes,
)
```

A tool call that needs approval pauses as a runner interruption. Resume with the core `RunState` approval flow; do not re-create a new agent with different tools midway through the approval resume.

## 10. Per-Call `_meta` for Multi-Tenant Servers

Use `tool_meta_resolver` to send server-required metadata on every MCP `call_tool()`.

```python
from agents.mcp import MCPToolMetaContext

def resolve_meta(context: MCPToolMetaContext) -> dict[str, str] | None:
    run_context = context.run_context.context or {}
    tenant = run_context.get("tenant_id")
    if not tenant:
        return None
    return {
        "tenant_id": str(tenant),
        "tool_name": context.tool_name,
        "source": "agents-sdk",
    }

server = MCPServerStreamableHttp(
    params={"url": "https://mcp.example.test/mcp"},
    tool_meta_resolver=resolve_meta,
)
```

Keep secrets out of `_meta` unless the MCP server explicitly requires them and your logging/tracing policy protects them.

## 11. Hosted MCP Tool

Use hosted MCP when OpenAI Responses should perform the MCP round trip.

```python
from agents import Agent, HostedMCPTool, Runner

agent = Agent(
    name="Repository assistant",
    instructions="Use the hosted documentation MCP server when repository facts are needed.",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "docs",
                "server_url": "https://mcp.example.test/mcp",
                "require_approval": "never",
            }
        )
    ],
)

result = await Runner.run(agent, "Summarize the repository language mix.")
```

Hosted MCP notes:

- The hosted server is not added to `mcp_servers`.
- The server must be reachable by OpenAI Responses infrastructure or be connector-backed.
- Use `connector_id` plus `authorization` for OpenAI connector-backed MCP.
- Use `tool_config["defer_loading"] = True` with `ToolSearchTool()` when a hosted MCP surface should be loaded lazily.
- Route provider support questions to [../../models-providers/SKILL.md](../../models-providers/SKILL.md).

## 12. Hosted MCP Approval Callback

Use `on_approval_request` to programmatically approve or reject hosted MCP calls.

```python
from agents import HostedMCPTool, MCPToolApprovalFunctionResult, MCPToolApprovalRequest

SAFE_TOOLS = {"read_wiki_structure", "read_wiki_contents"}

def approve_hosted(request: MCPToolApprovalRequest) -> MCPToolApprovalFunctionResult:
    if request.data.name in SAFE_TOOLS:
        return {"approve": True}
    return {"approve": False, "reason": "Requires human review"}

hosted_tool = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "docs",
        "server_url": "https://mcp.example.test/mcp",
        "require_approval": "always",
    },
    on_approval_request=approve_hosted,
)
```

If no hosted approval callback is provided, the application must handle approval items and resume the run.

## 13. Structured Content

Enable `use_structured_content=True` only when the MCP server returns meaningful `structuredContent` that is not duplicated in `content`.

```python
server = MCPServerStreamableHttp(
    params={"url": "https://mcp.example.test/mcp"},
    use_structured_content=True,
)
```

If outputs suddenly contain duplicate JSON/text or missing natural-language summaries, toggle this setting and inspect the server's `CallToolResult` shape.

## 14. Cache Invalidation After Tool Catalog Changes

When `cache_tools_list=True`, the SDK returns cached tools until invalidated.

```python
server.invalidate_tools_cache()
updated_tools = await server.list_tools(run_context, agent)
```

Call this after deploying a server version that adds, removes, renames, or changes schemas for tools. For high-change servers, leave caching disabled.

## 15. Testing Without Starting Remote Servers

Use a fake MCP server in unit tests when the test only needs filtering, approval mapping, conversion, or runner interruption behavior.

```python
from mcp import Tool as MCPTool

class FakeServer:
    name = "fake"
    cache_tools_list = False
    tool_filter = None

    def __init__(self):
        self.tools = [MCPTool(name="read_file", inputSchema={}), MCPTool(name="write_file", inputSchema={})]

    async def list_tools(self, run_context=None, agent=None):
        return self.tools

    async def call_tool(self, tool_name, arguments, meta=None):
        raise AssertionError("unit test should not call remote MCP server")
```

For tests that need real SDK filtering behavior, subclass or reuse a test fake that delegates to `_MCPServerWithClientSession._apply_tool_filter(...)` and avoids network/process startup. Avoid running credentialed examples in unit tests; test config shape and approval/filter decisions separately from server integration smoke tests.

## 16. Safe Config Preflight

Before handing MCP configuration to runtime code, validate shape and imports without connecting:

```bash
python skills/openai-agents-python/sub-skills/mcp-and-hosted-tools/scripts/check_mcp_config.py mcp-config.json --json
```

The helper accepts `stdio`, `streamable_http`, `sse`, and `hosted` server entries. It imports SDK MCP classes and reports configured stdio commands without launching them unless `--list-commands` is set.
