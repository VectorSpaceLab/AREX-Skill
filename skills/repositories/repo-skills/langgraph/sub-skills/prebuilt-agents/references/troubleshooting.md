# Prebuilt Agents Troubleshooting

Use this guide when `create_react_agent`, `ToolNode`, `ValidationNode`, injected tool args, or human interrupt schemas fail.

## Install and Import Failures

### `ModuleNotFoundError: No module named 'langgraph'`

Fix:

```bash
python -m pip install -U langgraph
```

Notes:

- The prebuilt package is bundled with `langgraph`; most users do not need to install `langgraph-prebuilt` directly.
- Provider models require their own packages, such as `langchain-anthropic` or `langchain-openai`.
- If using stores/checkpointers from optional integrations, install the matching integration package and consult sibling [../../persistence/SKILL.md](../../persistence/SKILL.md).

### `ImportError` for provider models

`create_react_agent` accepts a model object, model string, or dynamic model function, but the provider client and credentials are not bundled by LangGraph.

Fix checklist:

- Install the provider package.
- Set required API keys outside code, using environment variables or your deployment secret manager.
- Confirm the selected model supports tool calling.
- Confirm structured output support before using `response_format`.

### Deprecation warnings

Current prebuilt compatibility APIs may warn:

- `create_react_agent` moved toward `langchain.agents.create_agent`.
- `ValidationNode` moved toward LangChain agent custom tool error handling.
- `HumanInterruptConfig`, `ActionRequest`, and `HumanInterrupt` moved toward `langchain.agents.interrupt`.
- `config_schema` is deprecated; use `context_schema`.

Do not suppress these warnings blindly. For maintenance tasks, keep existing behavior and document migration risk. For new agent construction, prefer the recommended replacement APIs unless the task explicitly requires LangGraph prebuilt compatibility.

## `create_react_agent` Misuse

### `create_react_agent() got unexpected keyword arguments`

Cause: passing removed or misspelled keyword arguments through `**deprecated_kwargs`.

Fix:

- Compare against the supported signature in [api-reference.md](api-reference.md).
- Replace `config_schema` with `context_schema`.
- Remove old aliases from older tutorials.

### `Missing required key(s) ... in state_schema`

Cause: custom `state_schema` does not include required keys.

Fix:

- Include `messages` and `remaining_steps`.
- If using `response_format`, include `structured_response`.
- Use `Annotated[..., add_messages]` for message accumulation when defining typed state.

### `post_model_hook` does not run

Common causes:

- `version="v1"` was used; `post_model_hook` requires `version="v2"`.
- The hook was added but conditional routing ends before the hook due to graph construction or custom commands.

Fix:

- Use `create_react_agent(..., version="v2", post_model_hook=...)`.
- Add assertions that `"post_model_hook"` appears in graph nodes when introspection is available.
- Keep hook return values as valid state updates or `Command` objects.

### Structured response is missing or fails

Causes:

- `response_format` is not set.
- The selected model lacks `.with_structured_output`.
- Custom state schema omits `structured_response`.
- The final structured-output call needs a different prompt/schema tuple.

Fix:

- Verify model capability first with a minimal structured-output call.
- Use a Pydantic model or JSON schema that matches expected output.
- Add `structured_response` to state when using a custom schema.

### Bound tool mismatch

Error resembles: number of tools in `model.bind_tools()` and tools passed to `create_react_agent` must match, or missing tool names in bound tools.

Fix:

- Bind tools once, not in multiple inconsistent places.
- If a dynamic model returns a bound model, ensure bound tools are a subset of the supplied `tools` parameter.
- Confirm tool function names match expected call names.

## ToolNode Input and Output Failures

### `No message found in input`

Cause: input is neither a message list, a dict/object containing the configured `messages_key`, nor direct tool-call input.

Fix:

```python
node.invoke({"messages": [ai_message]})
# or
node.invoke([ai_message])
# or
node.invoke([{"name": "add", "args": {"a": 1, "b": 2}, "id": "1", "type": "tool_call"}])
```

If using a custom key:

```python
ToolNode([tool], messages_key="chat_history")
```

Route with the same key:

```python
tools_condition(state, messages_key="chat_history")
```

### `No AIMessage found in input`

Cause: the message history has no `AIMessage` with tool calls.

Fix:

- Ensure the model output is appended to state before `ToolNode` runs.
- Use `tools_condition` after the model node so `ToolNode` only runs when the last AI message has tool calls.
- In tests, construct `AIMessage(content="", tool_calls=[...])` explicitly.

### Invalid tool name

Symptom: `ToolMessage` content says the requested tool is not valid and lists available tools.

Fix:

- Align function/tool names with `tool_calls[*]["name"]`.
- If using `@tool(name=...)`, use the decorated tool name in model/tool-call fixtures.
- Inspect `ToolNode([...]).tools_by_name.keys()` in tests.

### Tool arguments fail validation

Symptoms:

- Error `ToolMessage` when handling is enabled.
- Raised exception when `handle_tool_errors=False`.

Fix:

- Add type annotations and docstrings to tools.
- Confirm tool-call `args` match the schema exactly.
- Use `ValidationNode` before real execution when re-prompting is better than executing.
- In tests, use `handle_tool_errors=False` to expose the original exception.

### Tool returns an unexpected type

`ToolNode` expects regular tools to return content that can become a `ToolMessage`, or explicit `ToolMessage`, `Command`, or a list of `Command`/`ToolMessage` values.

Fix:

- Return strings, JSON-serializable values, supported message content blocks, `ToolMessage`, or `Command`.
- Do not return arbitrary custom objects.
- If returning a list, ensure every element is a `Command` or `ToolMessage`; otherwise serialize the list as data.

### `Command.update` validation error

Typical message: expected a matching `ToolMessage` in `Command.update` for the tool.

Fix:

```python
from langchain_core.messages import ToolMessage
from langgraph.types import Command

return Command(update={"messages": [ToolMessage("done", tool_call_id=tool_call_id)]})
```

Rules:

- Current-graph commands that update messages need a matching `ToolMessage`.
- The `tool_call_id` must equal the originating call ID.
- Dict `Command.update` needs dict state input; list `Command.update` needs message-list input.
- For a list returned by one tool, include exactly one terminating `ToolMessage` for that call.

## Error Handling Confusion

### Errors are swallowed into model-visible messages

Cause: `handle_tool_errors=True`, a string, an exception tuple, or a callable formatter catches the exception.

Fix:

- Use `handle_tool_errors=False` for fail-fast tests or tools where exceptions must propagate.
- Narrow caught exceptions, for example `handle_tool_errors=(ValueError,)`.
- Keep security-sensitive details out of formatted error strings.

### Errors are not handled

Causes:

- `handle_tool_errors=False`.
- Callable handler type annotations do not match the thrown exception type.
- The exception is a graph control exception that bubbles up intentionally.

Fix:

- Check the handler configuration.
- Broaden the exception tuple only if safe.
- Do not catch `GraphInterrupt`/bubble-up control flow as a normal tool error.

## Injected State, Store, and Runtime Failures

### `Cannot inject store into tools with InjectedStore annotations`

Cause: tool requested `InjectedStore()` but no store is present in graph runtime.

Fix:

- Compile or run the graph with a store appropriate for your application.
- For local examples, use `InMemoryStore`.
- For persistence integrations, see [../../persistence/SKILL.md](../../persistence/SKILL.md).

### Missing injected state field

Symptoms: `KeyError`, `AttributeError`, or a message saying the graph state should contain required fields.

Fix:

- Ensure the graph state schema includes the field named in `InjectedState("field")`.
- If using object/Pydantic/dataclass state, ensure it exposes an attribute with that name.
- If invoking a node with list state, only full-state or message-field injection can be adapted automatically.

### Model tries to pass hidden injected args

Behavior: `ToolNode` strips model-supplied values for injected arg names and replaces them with trusted runtime values.

Fix/check:

- Write a regression test where a tool call includes spoofed `user_id`, `store`, or `runtime` args.
- Assert the tool observes the graph/runtime value, not the spoofed model value.
- Do not expose sensitive injected values in returned tool content.

### `ToolRuntime` is missing in a direct test

Cause: direct `ToolNode.invoke(...)` outside a compiled graph may not have the same runtime context as graph execution.

Fix:

- Prefer compiled `StateGraph` tests for `ToolRuntime`, store, stream writer, and context behavior.
- For simple direct tests, avoid injection-sensitive tools or use the smoke script pattern that does not require runtime internals.

## Sync vs Async Confusion

### Async tools are not awaited or event loop errors occur

Fix:

- Use `await node.ainvoke(...)` for async tools in async code.
- Use `node.invoke(...)` for synchronous tests and synchronous tools.
- In pytest, mark async tests appropriately for the configured async backend.
- Provide `awrap_tool_call` for async wrapper behavior; do not perform blocking I/O in async wrappers.

### Mixed sync and async wrappers behave unexpectedly

Fix:

- If both sync and async execution paths are needed, implement both `wrap_tool_call` and `awrap_tool_call`.
- Keep wrapper logic pure and deterministic where possible.
- Test `.invoke` and `.ainvoke` separately if the graph can run in both modes.

## ValidationNode Failures

### `Last message is not an AIMessage`

Cause: `ValidationNode` validates tool calls from the last AI message only.

Fix:

- Append or pass the model `AIMessage` as the last message.
- Do not pass a trailing `ToolMessage` or `HumanMessage` into `ValidationNode` unless routing first removes or bypasses it.

### Unsupported schema input

Accepted schema inputs:

- Pydantic model classes.
- BaseTool instances with Pydantic `args_schema`.
- Callable functions with type-annotated signatures.

Fix:

- Wrap complex schemas in a Pydantic model.
- Ensure decorated tools have valid `args_schema`.
- Avoid passing instances or arbitrary classes that are not supported schema types.

### Re-prompt loop loses tool IDs

Fix:

- Preserve each `ToolMessage.tool_call_id` from the invalid `AIMessage.tool_calls[*].id`.
- Route validation errors back to the model using the returned `ToolMessage` objects.
- Assert `additional_kwargs["is_error"]` on malformed calls.

## Human Interrupt Issues

### Interrupt payload has wrong shape

Expected shape:

```python
{
    "action_request": {"action": "tool_name", "args": {...}},
    "config": {
        "allow_ignore": True,
        "allow_respond": True,
        "allow_edit": False,
        "allow_accept": True,
    },
    "description": "Human-readable review request",
}
```

Fix:

- Include all four `allow_*` booleans.
- Keep `action_request.args` JSON-like and reviewable.
- Treat `description` as optional but useful for UI/human context.

### Edited human response bypasses validation

Fix:

- Route `type="edit"` responses through the same schema validation used for model tool calls.
- Keep an audit trail in graph state if the application requires reviewability.
- Do not execute edited args directly for destructive tools without additional confirmation.

## Service, Backend, and Security Notes

- Tool-calling models are provider-specific; verify model support before blaming LangGraph routing.
- Structured output is provider/model-specific; test a minimal schema first.
- Stores/checkpointers can persist sensitive data; avoid returning secrets in `ToolMessage.content`.
- Human interrupt flows are not a sandbox; they pause execution but do not make unsafe tools safe by themselves.
- Do not run destructive tools from model-generated args without validation, authorization, and human confirmation.

## Source Script Adaptation Record

No original repository example or script is required at runtime for this sub-skill. The bundled [../scripts/smoke_tool_node.py](../scripts/smoke_tool_node.py) is a self-contained smoke check adapted from public API behavior and focused test patterns: direct `ToolNode` invocation, successful tool execution, malformed argument handling, and `ValidationNode` error reporting. Expensive notebooks, benchmark-only code, maintainer release tooling, and source repository path dependencies are intentionally excluded.
