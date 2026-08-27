# MCP and Permissions

This reference covers human-in-the-loop tool approvals and optional MCP tool integration. Both features are agent/tool orchestration surfaces; provider model setup remains separate.

## Permission architecture

Core classes:

```python
from adalflow.apps.permission_manager import (
    PermissionManager,
    ApprovalOutcome,
    ApprovalResponse,
)
from adalflow.apps.cli_permission_handler import CLIPermissionHandler, AutoApprovalHandler
from adalflow.apps.fastapi_permission_handler import FastAPIPermissionHandler
```

`PermissionManager` constructor:

```python
PermissionManager(
    approval_callback=None,  # async callable receiving FunctionRequest
    approval_mode="default", # "default", "auto_approve", or "yolo"
    tool_manager=None,
)
```

Approval outcomes:

- `ApprovalOutcome.PROCEED_ONCE`: allow the current tool call once.
- `ApprovalOutcome.PROCEED_ALWAYS`: allow this tool name in future calls by adding it to `always_allowed_tools`.
- `ApprovalOutcome.CANCEL`: deny execution. Runner returns a cancelled `ToolOutput` for that step.

Approval modes:

| Mode | Behavior | Use |
|---|---|---|
| `default` | Respects blocked tools, always-allowed tools, and per-tool `require_approval`. | Production or user-facing workflows. |
| `auto_approve` | Automatically approves tools unless blocked. | Tests and trusted local demos. |
| `yolo` | Bypasses approval checks. | Only for throwaway, fully trusted development. |

## Marking tools for approval

Use `FunctionTool(..., require_approval=True)` for destructive, external, expensive, or credentialed operations:

```python
from adalflow.core.func_tool import FunctionTool
from adalflow.core.types import ToolOutput


def delete_candidate(path: str) -> ToolOutput:
    """Dry-run deletion candidate; caller must approve real deletion elsewhere."""
    return ToolOutput(
        output={"path": path, "would_delete": True},
        observation=f"Deletion candidate prepared for {path}",
        display=f"Needs approval: delete {path}",
    )

delete_tool = FunctionTool(delete_candidate, require_approval=True)
```

The runner registers approval requirements from the agent's tool manager during initialization. If you attach a permission manager later, call `runner.set_permission_manager(permission_manager)` so tools are registered.

## Custom approval callback

A callback receives `FunctionRequest(id, tool_name, tool, confirmation_details)` and returns an `ApprovalOutcome` or `ApprovalResponse`.

```python
async def deny_external_writes(request):
    if request.tool_name in {"delete_candidate", "send_email", "write_file"}:
        return ApprovalOutcome.CANCEL
    return ApprovalOutcome.PROCEED_ONCE

permission_manager = PermissionManager(
    approval_callback=deny_external_writes,
    approval_mode="default",
)
runner = Runner(agent=agent, permission_manager=permission_manager)
```

If a callback raises, permission checking denies the tool for safety.

## Pre-execution confirmation details

`FunctionTool(pre_execute_callback=...)` can prepare confirmation details before a streaming permission event is emitted:

```python
def confirm_delete(path: str):
    if not path or path == "/":
        return ToolOutput(output="Invalid path", observation="Refusing unsafe path", status="error")
    return {"message": f"Approve deletion candidate {path}?", "path": path}

safe_delete_tool = FunctionTool(
    delete_candidate,
    require_approval=True,
    pre_execute_callback=confirm_delete,
)
```

Rules for callbacks:

- Keep them fast and side-effect-free.
- Return a `ToolOutput(status="error")` to block unsafe parameters before user approval.
- Return small serializable confirmation details for frontends.
- Do not perform the destructive operation inside the callback.

## CLI and auto handlers

`CLIPermissionHandler(approval_mode="default", timeout=30.0)` prompts on the command line. It is useful for local development but unsuitable for non-interactive services.

`AutoApprovalHandler()` uses auto approval for tests. It is safe only when the tools themselves are safe/dry-run or the environment is trusted.

```python
from adalflow.apps.cli_permission_handler import CLIPermissionHandler, AutoApprovalHandler

permission_handler = CLIPermissionHandler(approval_mode="default", timeout=30.0)
# or for deterministic tests:
permission_handler = AutoApprovalHandler()
```

## FastAPI permission handler

`FastAPIPermissionHandler` creates or attaches approval endpoints to a FastAPI app:

```python
handler = FastAPIPermissionHandler(
    app=existing_app,
    approval_mode="default",
    timeout_seconds=None,
    api_prefix="/api/v1/approvals",
)
runner = Runner(agent=agent, permission_manager=handler)
```

Endpoint behavior:

- `GET {api_prefix}/pending`: list pending approval requests.
- `GET {api_prefix}/{request_id}`: inspect one request.
- `POST {api_prefix}/{request_id}/approve`: submit `proceed_once`, `proceed_always`, or `cancel`.
- `DELETE {api_prefix}/{request_id}`: cancel a pending request.
- `GET {api_prefix}/stats`: inspect counts and allow/block lists.

Use this for web applications where the model execution task waits while a user or frontend approves tool execution.

## Permission events during streaming

During `Runner.astream`, tools requiring approval can emit:

```python
RunItemStreamEvent(
    name="agent.tool_permission_request",
    item=ToolCallPermissionRequest(data=FunctionRequest(...)),
)
```

A frontend should render `FunctionRequest.tool_name`, `tool.args`, `tool.kwargs`, and any `confirmation_details`, then resolve the approval callback. If permission is denied, the step completes with `ToolOutput(status="cancelled")` and observation `Tool execution cancelled by user`.

## Allow/block lists

`PermissionManager` exposes imperative allow/block helpers:

```python
permission_manager.add_to_always_allowed("safe_lookup")
permission_manager.add_to_blocked("delete_candidate")
permission_manager.remove_from_always_allowed("safe_lookup")
permission_manager.remove_from_blocked("delete_candidate")
pending = permission_manager.get_pending_approvals()
```

Blocked tools still require approval in auto-approve mode. Avoid `yolo` mode when blocked tools matter.

## MCP integration scope

MCP support is optional. Importing MCP tools requires the package to be installed with MCP dependencies. If importing `adalflow.core.mcp_tool` fails because `mcp` is missing, install the package's MCP optional extra in the target environment or skip MCP features.

Core imports:

```python
from adalflow.core.mcp_tool import (
    MCPServerStdioParams,
    MCPServerSseParams,
    MCPServerStreamableHttpParams,
    MCPFunctionTool,
    MCPToolManager,
    mcp_session_context,
)
```

Server parameter dataclasses:

```python
MCPServerStdioParams(
    command="python",
    args=["server.py"],
    env=None,
    cwd=None,
    encoding="utf-8",
    encoding_error_handler="strict",
)

MCPServerSseParams(
    url="https://your-mcp-server/sse",
    headers=None,
    timeout=5,
    sse_read_timeout=300,
)

MCPServerStreamableHttpParams(
    url="https://your-mcp-server/mcp",
    headers=None,
    timeout=timedelta(seconds=30),
    sse_read_timeout=timedelta(seconds=300),
    terminate_on_close=True,
)
```

MCP server parameters may include credentials in `env` or headers. Do not log secrets. Prefer short-lived tokens and least-privilege server processes.

## Single MCP tool pattern

```python
async with mcp_session_context(server_params, name="tools") as session:
    listed = await session.list_tools()
    first_tool = listed.tools[0]

mcp_tool = MCPFunctionTool(server_params, first_tool)
result = await mcp_tool.acall(param_name="value")
```

`MCPFunctionTool` wraps the remote tool as a `FunctionTool`. It uses the MCP tool's name, description, and input schema for `FunctionDefinition`. MCP tool calls are asynchronous; use `acall` in async code. The sync `call` helper wraps `acall` with `asyncio.run`, so avoid it inside an existing event loop.

## MCPToolManager pattern

```python
manager = MCPToolManager(
    cache_tools_list=True,
    client_session_timeout_seconds=30.0,
)
manager.add_server("local_tools", MCPServerStdioParams(command="python", args=["server.py"]))
# Optionally add several servers before discovery.
await manager.list_all_tools()
tools = await manager.get_all_tools()

agent = Agent(
    name="MCPAgent",
    tools=tools,
    model_client=model_client,
    model_kwargs={"model": "provider-model"},
)
```

Operational guidance:

- Start with one server and one known tool before aggregating many servers.
- Use `server_names=[...]` with `list_all_tools` or `get_all_tools` to limit discovery.
- Treat server startup failure, missing tools, schema mismatches, and network timeouts as optional integration failures unless MCP is required for the task.
- Cache discovered tools during one run, but refresh if server code or configuration changes.
- Do not run untrusted local MCP servers; stdio servers are processes with the privileges of the current user.

## JSON MCP server config

`MCPToolManager.add_servers_from_json_file(json_path)` reads a structure like:

```json
{
  "mcpServers": {
    "local_tools": {
      "command": "python",
      "args": ["server.py"],
      "env": null
    }
  }
}
```

Use a config file only when it is already trusted by the application. Do not include secrets in examples, generated logs, or shared artifacts.

## Safe approval + MCP composition

When exposing MCP tools to an agent:

1. Discover tools with `MCPToolManager`.
2. Wrap or mark sensitive MCP tools as requiring approval when they mutate files, send messages, call external APIs, or spend money.
3. Use a `PermissionManager` with default mode in production.
4. Consume `agent.tool_permission_request` events in streaming UIs.
5. Keep MCP server errors visible in `FunctionOutput.error` or `ToolOutput(status="error")` so the planner can recover or finish with a useful failure message.
