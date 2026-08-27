# MCP and Hosted Tools Troubleshooting

Use this guide when local MCP servers, hosted MCP tools, approval flows, caching, or structured outputs behave unexpectedly.

## Quick Triage

| Symptom | Likely cause | First check | Fix |
| --- | --- | --- | --- |
| `Failed to import MCPServer... from agents.mcp` | Missing or incompatible MCP dependency. | Import `agents`, then `agents.mcp.MCPServerStdio` in the target environment. | Install/repair the package environment; use the verified base install or ensure the MCP Python package is present. |
| Stdio server fails immediately | `command` not found, wrong `args`, wrong `cwd`, or missing env. | Run the safe config helper with `--json`; check `command_found`. | Use a command on `PATH`, pass args as a list, and set required env/cwd in application config. |
| `Server not initialized` | `connect()` was not called or context manager exited. | Check server lifecycle around `Runner.run(...)`. | Wrap runs in `async with server:` or manage `connect()` / `cleanup()` explicitly. |
| HTTP connect/list/call raises `UserError` | Bad URL, auth, timeout, or server disconnect. | Inspect status code and endpoint transport. | Fix URL/auth, increase timeout, use retries for transient failures, or migrate SSE to Streamable HTTP. |
| Remote hosted MCP does not run | Model/provider does not support hosted MCP or server is not reachable by OpenAI. | Confirm the agent uses an OpenAI Responses-capable model/provider. | Route provider setup to `models-providers`; use local MCP for private/VPC servers. |
| Tool list is stale | `cache_tools_list=True` after server tool changes. | Check whether removed/renamed tools still appear. | Call `server.invalidate_tools_cache()` or disable caching for dynamic servers. |
| Sensitive tool appears | Filter missing or applied without context. | Inspect `tool_filter` and exposed tool names. | Add static/dynamic filter; ensure dynamic filter is used through agent/run context. |
| Tool call does not pause | Approval policy mismatch or tool filtered/renamed. | Check exact MCP tool name after filtering/server-prefixing. | Use valid `require_approval` form and match original tool names. |
| Structured output duplicated or missing | Wrong `use_structured_content` setting for server output shape. | Inspect server `CallToolResult` content and `structuredContent`. | Toggle `use_structured_content`; prefer default `False` unless server is structured-only. |
| Session resume fails | Missing/incorrect `Mcp-Session-Id` or server does not support resume. | Read `server.session_id` only while connected. | Persist supported session ids and pass them back in headers; otherwise start a fresh session. |

## Missing MCP Dependency or Import Failure

The verified package imports `agents` and MCP classes under the base install. If a target environment fails:

1. Run a minimal import check:
   ```bash
   python -c "from agents.mcp import MCPServerStdio, MCPServerStreamableHttp; print('ok')"
   ```
2. If the error mentions the MCP module, install or repair the environment so the SDK's MCP dependency is available.
3. If the error comes from an optional transport dependency or version conflict, recreate the environment from the package constraints instead of mixing old MCP packages.
4. Do not work around this by copying source files into the application; fix the environment.

## Server Command Not Found

For `MCPServerStdio`, the SDK launches `params["command"]` directly. It does not invoke an interactive shell.

Common fixes:

- Pass `params={"command": "python", "args": ["-m", "package.server"]}` instead of one shell string.
- Ensure the command is available on the runtime `PATH` or use an application-owned executable path.
- Set `cwd` only if the server needs relative files.
- Put required subprocess environment variables in `params["env"]`, not in public docs or skill files.
- Use [../scripts/check_mcp_config.py](../scripts/check_mcp_config.py) to report whether stdio commands are discoverable without launching them.

## Auth and Session ID Issues

For HTTP transports:

- Use `params["headers"]` for static headers such as tenant ids or bearer tokens.
- Use `params["auth"]` for `httpx.Auth` handlers, including `httpx.BasicAuth` or custom token refresh.
- Use `params["httpx_client_factory"]` for custom TLS, proxy, instrumentation, or test clients.
- For Streamable HTTP resume, capture `server.session_id` while the server is connected and pass it back through `params["headers"]`, commonly under `Mcp-Session-Id`.
- If a server rejects resume headers, remove the session id and start a fresh session; not every server supports resumable state.

Do not place secret values in examples, traces, config dumps, or generated skill content.

## Stale Cached Tool Lists

`cache_tools_list=True` improves latency but freezes the tool catalog until invalidated.

Use this sequence after a server deploy or capability change:

```python
server.invalidate_tools_cache()
tools = await server.list_tools(run_context, agent)
```

If the model calls a removed tool after a deploy, check whether the agent used cached MCP tools converted earlier with `MCPUtil.get_all_function_tools(...)`. Rebuild the agent's prefetched `tools` list after invalidating and refetching.

## Approval Mismatches

Local MCP `require_approval` validates policy shape. Problems usually come from name mismatch or resume flow confusion.

Checks:

- Match the original MCP tool name, not a natural-language title.
- If `include_server_in_tool_names=True`, the model-visible function name may be server-prefixed, but approval mapping is based on the MCP tool as converted by the server policy.
- For grouped policy objects, do not put the same tool name under both `always` and `never`.
- For callable policies, confirm the run context contains the expected values.
- Approval interruptions resume through `result.to_state()`, approval/rejection on that state, and another `Runner.run(agent, state)` call with the same top-level agent.

If an approval-gated tool silently runs, tighten the policy to `require_approval="always"` temporarily to confirm the HITL path works, then reintroduce per-tool or callable logic.

## Tool Filtering Mismatches

Static filters are exact-name filters. Dynamic filters require context.

- If a static allow-list hides everything, inspect the names returned by `list_tools()` before filtering.
- If a dynamic filter raises, the SDK excludes that tool and logs an error; add defensive checks and tests.
- If filtering works in direct calls but not in a run, ensure the agent actually uses the filtered server instance.
- If multiple servers publish duplicate tool names, set `Agent.mcp_config["include_server_in_tool_names"] = True` or prefetch with `MCPUtil.get_all_function_tools(..., include_server_in_tool_names=True)`.

## Structured Content Mismatches

The default `use_structured_content=False` avoids duplicate content for servers that put structured data in both `content` and `structuredContent`.

- Enable `use_structured_content=True` when the server intentionally returns machine-readable `structuredContent` without equivalent text.
- Disable it if the model sees duplicate JSON, loses human-readable text, or downstream tests expected text entries.
- For custom data, ensure `custom_data_extractor` returns a JSON-compatible mapping or `None`.

## Error Handling and Retries

Local MCP failures can be converted to model-visible error text or raised.

- Set agent-level `mcp_config={"failure_error_function": None}` to fail fast for all local MCP servers unless a server overrides it.
- Set server-level `failure_error_function=None` when one server must fail fast even if the agent has a default formatter.
- Use `max_retry_attempts` and `retry_backoff_seconds_base` for transient list/call failures.
- `max_retry_attempts=-1` means unlimited retries; use only with an external timeout/cancellation policy.
- Streamable HTTP can retry selected transient shared-session call failures through an isolated session when retry budget remains.

## Remote and Network Restrictions

Hosted MCP is executed by OpenAI Responses infrastructure. It cannot reach private localhost, VPC-only, or workstation-only servers unless those are exposed through an approved public/connector path.

If a server is private:

- Use `MCPServerStreamableHttp` or `MCPServerStdio` locally instead of `HostedMCPTool`.
- Keep credentials in application config, not in generated skill files.
- If the environment disables network access, write tests around config shape, filtering, and fake servers rather than live remote calls.

## Message Handler Surprises

`message_handler` is passed into the MCP `ClientSession` for stdio, SSE, and Streamable HTTP servers. If it never fires:

- Confirm the server emits MCP notifications or requests that the client session delivers.
- Confirm the handler is async-callable if it performs async work.
- Make sure the server instance receiving the handler is the same instance passed to the agent or manager.

## Required Parameter Validation

When tools have been listed and cached on the server instance, `call_tool()` validates required input-schema parameters before making a remote call.

If a call fails locally with missing required parameters:

- Inspect the MCP tool schema's `required` list.
- Ensure the model-facing schema was converted correctly.
- Avoid bypassing tool-listing setup in tests unless the test intentionally bypasses validation.

## Hosted MCP Tool Search Issues

If using `HostedMCPTool(tool_config={..., "defer_loading": True})`:

- Add exactly one `ToolSearchTool()` to the agent.
- Use an OpenAI Responses model/provider that supports hosted tool search.
- Do not expect standard `Runner` to execute client-mode tool search calls automatically.
- Keep namespace/function-tool search troubleshooting in [../../tools-handoffs-guardrails/SKILL.md](../../tools-handoffs-guardrails/SKILL.md) and provider support in [../../models-providers/SKILL.md](../../models-providers/SKILL.md).
