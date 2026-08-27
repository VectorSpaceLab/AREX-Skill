# Troubleshooting Agents, Tools, Streaming, Permissions, and MCP

Use this guide when an AdalFlow agent/tool workflow fails, stalls, emits confusing events, or behaves unsafely. Start with the safe bundled scripts before connecting live providers or services.

## Quick triage

1. Is the failure before any model call? Run `python scripts/function_tool_smoke.py` to isolate tool wrapping and `ToolManager` execution.
2. Is the failure in the runner loop? Run `python scripts/agent_runner_fake_planner_smoke.py` to isolate `Agent` + `Runner` without a provider.
3. Is the failure provider-specific? Route model-client/generator setup elsewhere before changing agent code.
4. Is the tool destructive, external, expensive, or credentialed? Add `require_approval=True` and test permission denial before approving real execution.
5. Is MCP involved? First verify that MCP dependencies import and that the server can list tools outside the agent loop.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Planner calls a tool with wrong parameters. | Tool has missing type hints, vague docstring, or a complex unsupported signature. | Add parameter annotations and a clear docstring; consider an explicit `FunctionDefinition`. |
| `FunctionTool.definition.func_name` is not the Python function name. | Bound methods are prefixed with the class name. | Use `tool.definition.func_name` in `Function` objects and tests. |
| `FunctionOutput.output` is a generator object. | Wrapped function is a sync or async generator. | Iterate the generator; in streaming runners, yield `ToolCallActivityRunItem` for progress and a final non-activity value. |
| Tool returned data but agent step observation is wrong. | Tool returned plain data when separate observation/display was needed. | Return `ToolOutput(output=..., observation=..., display=...)`. |
| Tool exception did not crash, but agent seems confused. | `FunctionTool` captured the exception in `FunctionOutput.error`. | Inspect `.error`; return a clearer recoverable `ToolOutput(status="error")` for expected validation failures. |
| Runner stops with `No output generated after ...`. | Planner never emitted a final `Function(_is_answer_final=True, _answer=...)`. | Update planner prompt/parser/fake planner to emit a final action within `max_steps`; raise `max_steps` only if necessary. |
| Final answer parsing fails. | `_answer` does not match `answer_data_type`. | For Pydantic or AdalFlow dataclasses, pass a dict or JSON object string; for built-ins, pass a value castable to the target type. |
| `RuntimeError: asyncio.run() cannot be called from a running event loop`. | Sync wrapper called inside an existing async loop. | Use `await runner.acall(...)`, `await tool.acall(...)`, or call `Runner.astream(...)` inside the running loop. |
| `Runner.astream` fails or never starts. | Called without a running event loop or stream not consumed. | Call `astream` inside an async function and drain `stream_events()` or `wait_for_completion()`. |
| Streaming loop hangs. | Consumer waits for a custom sentinel or ignores `agent.execution_complete`. | Break when `stream_events()` ends, or when a `RunItemStreamEvent` named `agent.execution_complete` is seen. |
| Permission event appears but tool never executes. | Approval callback is waiting, denied, timed out, or raised. | Inspect pending approvals; return `ApprovalOutcome.PROCEED_ONCE` for a safe test; handle callback exceptions. |
| Denied tool still appears in step history. | Denial is represented as a completed cancelled tool output. | Check `ToolOutput.status == "cancelled"` and observation `Tool execution cancelled by user`. |
| Importing MCP tools fails. | Optional `mcp` dependency is not installed. | Install the package's MCP optional extra or skip MCP features. |
| MCP tool list is empty or server times out. | Server command/URL is wrong, server failed to start, or network/service unavailable. | Test server startup and `list_tools()` before adding tools to an agent; reduce to one server. |
| Duplicate tool name warning. | Two tools map to the same `definition.func_name`. | Rename one function or provide explicit `FunctionDefinition(func_name=...)`. |

## Unsafe tool patterns

Avoid exposing these directly to a planner:

- Raw `eval`, `exec`, shell command execution, arbitrary file read/write/delete, package installation, network mutation, payment/billing APIs, credential stores, or email/message sending.
- Tools that accept unrestricted paths, URLs, SQL, shell fragments, or Python expressions.
- Tools that silently mutate external state and return only `True`/`False`.

Safer replacements:

- Split destructive actions into a dry-run planner tool and a separately approved execution tool.
- Require structured inputs: `path`, `operation`, `reason`, `max_bytes`, `allowlist_key` rather than raw commands.
- Return `ToolOutput` with `status`, `observation`, and `display` so users and the planner see what happened.
- Use `require_approval=True` and a `pre_execute_callback` for confirmation details.
- Add allowlists and path normalization inside the tool itself; permissions are not a substitute for input validation.

## Missing annotations or descriptions

Symptoms:

- Tool schema has empty or unclear parameter descriptions.
- Planner chooses wrong argument names or passes strings for structured objects.
- Function expression parsing fails because planner guessed a parameter name.

Fix checklist:

```python
# Weak: no docstring, no hints
def search(q, k=5): ...

# Better
def search_documents(query: str, top_k: int = 5) -> list[str]:
    """Search local documents for query and return up to top_k snippets."""
    ...
```

For complex objects, prefer simple serializable parameters or a dataclass/schema workflow from the structured-I/O sub-skill. If automatic schema generation is still poor, pass a custom `FunctionDefinition` with a clear `func_name`, `func_desc`, and `func_parameters`.

## Async loop issues

Use this decision table:

| Context | Correct call |
|---|---|
| Plain script, sync tool | `tool.call(...)`, `runner.call(...)` |
| Plain script, async tool | `asyncio.run(tool.acall(...))` or `asyncio.run(runner.acall(...))` |
| Already inside `async def` | `await tool.acall(...)`, `await runner.acall(...)` |
| Streaming agent in async app | `streaming = runner.astream(...); async for event in streaming.stream_events(): ...` |
| Sync test of streaming | Put streaming code inside `async def main()` and call `asyncio.run(main())` once at top level. |

Do not call `asyncio.run` from inside a notebook, web server, or any already-running event loop. Use native `await` or framework task creation instead.

## Tool result formatting

Use plain return values for tiny pure functions. Use `ToolOutput` when any of the following are true:

- The agent should see a concise observation but the application needs richer data.
- A frontend needs a display string.
- The tool can fail in an expected way and should return `status="error"` without raising.
- The output is streaming or contains metadata.

Example recoverable error:

```python
def divide(a: float, b: float) -> ToolOutput:
    """Divide a by b."""
    if b == 0:
        return ToolOutput(
            output=None,
            observation="Cannot divide by zero; ask for a non-zero divisor.",
            display="Division failed",
            status="error",
        )
    value = a / b
    return ToolOutput(output=value, observation=f"Division result: {value}")
```

## Max-step exhaustion

Symptoms:

- `RunnerResult.answer` starts with `No output generated after`.
- Step history shows repeated tool calls or repeated parser errors.

Fixes:

1. Lower test complexity and reproduce with a fake planner.
2. Confirm the planner output parser can produce `Function(_is_answer_final=True, _answer=...)`.
3. Add a prompt instruction that the last allowed step must finalize.
4. Increase `max_steps` only after the loop is making useful progress.
5. If a tool result is too verbose, return a concise `ToolOutput.observation` so the next step can finalize.

## Answer finalization failures

`Runner` does not require the final function name to be a real tool if `_is_answer_final=True`; it uses `_answer`. However, the final answer must match `answer_data_type`.

Examples:

```python
Function(name="finish", _is_answer_final=True, _answer="done")  # for answer_data_type=str
Function(name="finish", _is_answer_final=True, _answer={"ok": True})  # for answer_data_type=dict
Function(name="finish", _is_answer_final=True, _answer='{"label": "ok"}')  # for structured model/dataclass
```

If finalization fails:

- Inspect the raw `_answer` type.
- For structured types, validate JSON/dict shape before running a live provider.
- Avoid returning a `ToolOutput` as the final `_answer` unless the answer type expects that object.

## Permission denials

Expected denied output:

- Sync/async runner step observation: `Tool execution cancelled by user`.
- Tool output status: `cancelled`.
- Streaming may first emit `agent.tool_permission_request`, then `agent.tool_call_complete` with a cancelled output.

Debug checklist:

1. Confirm the tool name in `PermissionManager.tool_require_approval` matches `FunctionTool.definition.func_name`.
2. Confirm the runner was constructed with the permission manager or `set_permission_manager` was called.
3. Confirm callback returns `ApprovalOutcome.PROCEED_ONCE`, `PROCEED_ALWAYS`, or `CANCEL`.
4. If using FastAPI, inspect pending requests and ensure the approval response uses exactly `proceed_once`, `proceed_always`, or `cancel`.
5. If a pre-execution callback returns `ToolOutput(status="error")`, fix the unsafe arguments before asking for approval.

## Streaming event consumption problems

Common mistakes:

- Assuming every event is a `RunItemStreamEvent`; raw model chunks are `RawResponsesStreamEvent`.
- Assuming every `RunItemStreamEvent.item.data` has the same type.
- Ignoring `agent.execution_complete`, causing UI spinners to continue.
- Consuming an async generator output once for logging and trying to consume it again later.

Robust switch:

```python
async for event in streaming.stream_events():
    if getattr(event, "type", None) == "raw_response_event":
        handle_raw(event.data, event.error)
    elif getattr(event, "type", None) == "run_item_stream_event":
        if event.name == "agent.execution_complete":
            handle_final(event.item.data)
        elif event.name == "agent.step_complete":
            handle_step(event.item.data)
        elif event.name == "agent.tool_call_complete":
            handle_tool_output(event.item.data)
```

## Missing MCP extra or server

Symptoms:

- `ImportError` when importing `adalflow.core.mcp_tool`.
- `No servers added` from `MCPToolManager`.
- `Error getting tools from server` during discovery.
- Tool call returns no content or an MCP protocol exception.

Fixes:

1. Install the package's MCP optional extra in the target environment.
2. Verify the MCP server command, args, working directory, and environment independently.
3. For HTTP/SSE servers, verify URL, headers, timeout, and network reachability.
4. Call `await manager.list_all_tools(server_names=[...])` before `get_all_tools`.
5. If schemas are surprising, inspect the generated `MCPFunctionTool.definition` before giving it to the agent.
6. Add approval gates around MCP tools that mutate state or call external services.

## When to stop and reroute

Stop changing agent code and reroute when:

- The error is missing provider SDK, API key, model name, model kwargs, or provider streaming behavior.
- The task is actually about building a retriever/RAG tool before agent wrapping.
- The issue is tracing/log persistence, MLflow, or span instrumentation rather than event semantics.
- The user needs training/optimization of prompts or agent components rather than runtime execution.
