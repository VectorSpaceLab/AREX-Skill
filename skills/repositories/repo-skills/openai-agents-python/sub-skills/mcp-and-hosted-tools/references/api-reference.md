# MCP and Hosted Tools API Reference

This reference summarizes the OpenAI Agents Python MCP surfaces that are safe to rely on from the verified package and repository evidence.

## Selection Matrix

| Need | Use | Attach to agent | Execution location |
| --- | --- | --- | --- |
| Launch a local MCP subprocess | `MCPServerStdio` | `Agent(mcp_servers=[server])` | Local application process |
| Connect to a current HTTP MCP endpoint | `MCPServerStreamableHttp` | `Agent(mcp_servers=[server])` | Local application process |
| Connect to a legacy HTTP/SSE MCP endpoint | `MCPServerSse` | `Agent(mcp_servers=[server])` | Local application process |
| Let OpenAI Responses call a public/connector MCP server | `HostedMCPTool` | `Agent(tools=[HostedMCPTool(...)])` | OpenAI-hosted Responses tool call |
| Manage multiple local MCP connections | `MCPServerManager` | `Agent(mcp_servers=manager.active_servers)` | Local application process |

Use local MCP classes for private network servers, local filesystem processes, custom `httpx` auth/client behavior, server-side sessions, local message handlers, and SDK-side filtering/approval. Use `HostedMCPTool` for public hosted MCP or connector-backed surfaces where the Responses API performs tool listing and calling without a local round trip.

## Imports

```python
from agents import Agent, HostedMCPTool, Runner
from agents.mcp import (
    MCPServerManager,
    MCPServerSse,
    MCPServerStdio,
    MCPServerStreamableHttp,
    MCPToolMetaContext,
    ToolFilterContext,
    create_static_tool_filter,
)
```

The base install imports `agents` and the MCP classes successfully for the verified package version. If `agents.mcp` fails to import, check the missing MCP dependency guidance in [troubleshooting.md](troubleshooting.md).

## Agent MCP Configuration

`Agent` accepts `mcp_servers=[]` and `mcp_config={...}`. Server objects are converted to callable function tools during a run.

Common `mcp_config` keys:

| Key | Meaning | Notes |
| --- | --- | --- |
| `convert_schemas_to_strict` | Best-effort conversion of MCP tool schemas to strict JSON schema. | Use when target models prefer strict schemas; unconvertible schemas fall back to original. |
| `failure_error_function` | Converts MCP tool failures to model-visible text. | Set to `None` for fail-fast exceptions; server-level setting overrides agent-level setting. |
| `include_server_in_tool_names` | Prefixes local MCP tool names with a server-derived name. | Helps avoid duplicate tool names across servers while invoking the original tool name on the server. |

Example:

```python
agent = Agent(
    name="Assistant",
    mcp_servers=[server],
    mcp_config={
        "convert_schemas_to_strict": True,
        "include_server_in_tool_names": True,
        "failure_error_function": None,
    },
)
```

## Local MCP Base Behavior

`MCPServerStdio`, `MCPServerSse`, and `MCPServerStreamableHttp` share these constructor options:

| Option | Type / values | Behavior |
| --- | --- | --- |
| `cache_tools_list` | `bool`, default `False` | Caches `list_tools()` results after first fetch; refresh with `invalidate_tools_cache()`. |
| `name` | `str | None` | Human-readable server name; defaults to transport-derived value. |
| `client_session_timeout_seconds` | `float | None`, default `5` | Read timeout passed to the MCP `ClientSession`. |
| `tool_filter` | static dict, callable, or `None` | Filters tools before conversion to function tools. Dynamic filters require run context and agent. |
| `use_structured_content` | `bool`, default `False` | Prefer MCP `structuredContent`; enable only when the server does not duplicate it in textual content. |
| `max_retry_attempts` | `int`, default `0` | Retries `list_tools()` / `call_tool()` failures; `-1` means unlimited retries. |
| `retry_backoff_seconds_base` | `float`, default `1.0` | Exponential backoff base delay. |
| `message_handler` | MCP session message handler or `None` | Receives server messages through the MCP client session. |
| `require_approval` | policy, mapping, bool, object, callable, or `None` | Converts local MCP tools to approval-aware function tools. |
| `failure_error_function` | callable, `None`, or unset | Overrides agent-level MCP failure formatting for this server. |
| `tool_meta_resolver` | callable or `None` | Produces per-call MCP `_meta` payload. |
| `custom_data_extractor` | callable or `None` | Adds SDK-only custom data to emitted MCP tool output items. |

All local server classes are async context managers. Use `async with` when possible; otherwise call `connect()` before `list_tools()` or `Runner.run(...)`, and `cleanup()` afterward.

## `MCPServerStdio`

Use `MCPServerStdio(params={...})` for subprocess-backed servers.

`params` fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `command` | Yes | Executable to launch, such as `python`, `node`, or `npx`. |
| `args` | No | Command arguments. |
| `env` | No | Environment variables for the subprocess. |
| `cwd` | No | Working directory for the subprocess. |
| `encoding` | No | Text encoding, default `utf-8`. |
| `encoding_error_handler` | No | One of `strict`, `ignore`, or `replace`; default `strict`. |

Minimal pattern:

```python
async with MCPServerStdio(
    name="local-files",
    params={"command": "python", "args": ["-m", "my_mcp_server"]},
    cache_tools_list=True,
) as server:
    agent = Agent(name="Assistant", mcp_servers=[server])
    result = await Runner.run(agent, "List available MCP tools.")
```

## `MCPServerStreamableHttp`

Use `MCPServerStreamableHttp(params={...})` for current HTTP MCP servers.

`params` fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `url` | Yes | Streamable HTTP MCP endpoint URL. |
| `headers` | No | Request headers, commonly auth or session headers. |
| `timeout` | No | HTTP request timeout, default `5`. |
| `sse_read_timeout` | No | Stream read timeout, default `300`. |
| `terminate_on_close` | No | Whether to terminate the server session on close, default `True`. |
| `httpx_client_factory` | No | Custom `httpx.AsyncClient` factory for SSL, proxies, test clients, or instrumentation. |
| `auth` | No | `httpx.Auth` instance such as `httpx.BasicAuth` or a refresh-capable custom auth class. |
| `ignore_initialized_notification_failure` | No | Ignore best-effort initialized-notification HTTP failures and continue. |

`MCPServerStreamableHttp.session_id` returns the current MCP session id after connection when the server issues one. To resume a server-side session in another worker, pass it back in `params["headers"]`, usually as `{"Mcp-Session-Id": session_id}`. The property is `None` before connect, after cleanup, or when the transport provides no session id.

Streamable HTTP serializes shared-session requests and can retry selected transient call failures through an isolated session when retry budget remains. Configure `max_retry_attempts` and backoff deliberately for production servers.

## `MCPServerSse`

Use `MCPServerSse(params={...})` only for legacy SSE MCP servers. The MCP project deprecated this transport in favor of Streamable HTTP and stdio, but the SDK keeps equivalent local-server options.

`params` fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `url` | Yes | SSE endpoint URL. |
| `headers` | No | Request headers. |
| `timeout` | No | HTTP request timeout, default `5`. |
| `sse_read_timeout` | No | SSE read timeout, default `300`. |
| `auth` | No | `httpx.Auth` handler. |
| `httpx_client_factory` | No | Custom HTTP client factory. |

## Tool Filtering

Static filters use allow and block lists:

```python
server = MCPServerStdio(
    params={"command": "python", "args": ["-m", "my_mcp_server"]},
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["read_file", "list_directory"],
        blocked_tool_names=["delete_file"],
    ),
)
```

The SDK applies `allowed_tool_names` first, then removes `blocked_tool_names`. Dynamic filters receive `ToolFilterContext(run_context, agent, server_name)` and the MCP tool object; they may be sync or async. If a dynamic filter raises, the SDK logs the error and excludes that tool for safety.

```python
async def role_filter(context: ToolFilterContext, tool) -> bool:
    if context.agent.name == "ReadOnly Assistant":
        return tool.name.startswith("read_") or tool.name.startswith("list_")
    return True
```

## Local MCP Approval Policies

`require_approval` supports these forms:

| Form | Example | Meaning |
| --- | --- | --- |
| Global string | `"always"` or `"never"` | Require or skip approval for every tool. |
| Boolean | `True` or `False` | Equivalent to always/never. |
| Tool-name mapping | `{"delete_file": "always", "read_file": "never"}` | Per-tool policy; literal tool names may be `always` or `never`. |
| Tool-list object | `{"always": {"tool_names": ["delete_file"]}, "never": {"tool_names": ["read_file"]}}` | TypeScript-style grouped policy. |
| Callable | `def policy(run_context, agent, tool) -> bool: ...` | Sync or async dynamic decision per MCP tool. |

Invalid policy values raise `UserError` instead of silently failing open. Callable policies fail closed when converted without an agent context.

Approval interruptions are resumed through the core runner `RunState` flow. Keep detailed resume mechanics in [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md); this sub-skill owns choosing and configuring the MCP approval policy.

## Per-Call Metadata and Custom Data

Use `tool_meta_resolver` when an MCP server expects `_meta` on `call_tool()`:

```python
def resolve_meta(context: MCPToolMetaContext) -> dict[str, str] | None:
    tenant_id = (context.run_context.context or {}).get("tenant_id")
    if tenant_id is None:
        return None
    return {"tenant_id": str(tenant_id), "source": "agents-sdk"}

server = MCPServerStreamableHttp(
    params={"url": "https://mcp.example.test/mcp"},
    tool_meta_resolver=resolve_meta,
)
```

Use `custom_data_extractor` only for SDK-internal metadata attached to MCP output items; it must return a JSON-compatible mapping or `None`.

## Tool Metadata and Output Content

For local MCP tools, the SDK exposes MCP tools as function tools. It uses the MCP `description`, or falls back to explicit/annotation `title`, so model-facing tool descriptions are not blank when the server only supplies display titles.

For hosted MCP list-tools payloads, `agents._mcp_tool_metadata.collect_mcp_list_tools_metadata(...)` can collect title/description metadata from raw `mcp_list_tools` items or run items. This is primarily useful when analyzing hosted MCP traces/results.

MCP tool outputs may include text, images, `_meta`, `structuredContent`, and `isError`. `use_structured_content=True` makes the SDK prefer `structuredContent` over textual content; leave it false if the server duplicates structured data into text.

## `MCPUtil`

`MCPUtil.get_all_function_tools(...)` converts one or more connected MCP servers to `FunctionTool` objects. Use this when you need to prefetch MCP tools and pass them through `Agent(tools=[...])` rather than `Agent(mcp_servers=[...])`.

Important arguments:

| Argument | Meaning |
| --- | --- |
| `servers` | Connected local MCP server instances. |
| `convert_schemas_to_strict` | Whether to strictify MCP input schemas. |
| `run_context`, `agent` | Required for dynamic filters and approval mapping. |
| `failure_error_function` | Effective MCP tool failure formatter. |
| `include_server_in_tool_names` | Prefix tools to avoid collisions. |
| `reserved_tool_names` | Names already used by local tools or handoffs. |

`MCPUtil` raises on duplicate exposed tool names unless server-prefixing resolves them.

## `MCPServerManager`

`MCPServerManager(servers, ...)` connects and cleans up multiple local MCP servers.

| Option | Default | Meaning |
| --- | --- | --- |
| `connect_timeout_seconds` | `10.0` | Per-server connect timeout. |
| `cleanup_timeout_seconds` | `10.0` | Per-server cleanup timeout. |
| `drop_failed_servers` | `True` | Expose only connected servers through `active_servers`. |
| `strict` | `False` | Raise on first connection failure instead of recording it. |
| `suppress_cancelled_error` | `True` | Suppress cancellation during cleanup when appropriate. |
| `connect_in_parallel` | `False` | Connect concurrently while preserving task affinity for cleanup. |

Key properties and methods: `active_servers`, `all_servers`, `failed_servers`, `errors`, `connect_all()`, `reconnect(failed_only=True)`, and `cleanup_all()`.

## Hosted MCP Tool

`HostedMCPTool` is a dataclass with:

| Field | Meaning |
| --- | --- |
| `tool_config` | MCP tool config sent to the OpenAI Responses API. |
| `on_approval_request` | Optional sync/async callback for hosted MCP approval requests. |
| `name` | Always returns `"hosted_mcp"`. |

Typical `tool_config` fields:

| Field | Meaning |
| --- | --- |
| `type` | Must be `"mcp"`. |
| `server_label` | Stable label used in hosted MCP tool events and metadata. |
| `server_url` | Public MCP server URL for hosted remote servers. |
| `connector_id` | OpenAI connector identifier for connector-backed MCP. |
| `authorization` | Connector/server authorization material. Prefer environment variables or secret stores. |
| `require_approval` | `"always"`, `"never"`, or tool-specific policy supported by Responses. |
| `defer_loading` | `True` to expose the hosted MCP server through `ToolSearchTool`. |

Hosted MCP belongs in `Agent(tools=[...])`, not `mcp_servers=[...]`:

```python
agent = Agent(
    name="Assistant",
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
```

Hosted MCP tools currently require an OpenAI Responses model with hosted MCP support. Route provider compatibility and feature-validation questions to [../../models-providers/SKILL.md](../../models-providers/SKILL.md).
