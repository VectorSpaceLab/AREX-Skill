# Prebuilt Agents API Reference

This reference summarizes the `langgraph.prebuilt` APIs most often needed by coding agents. Prefer public package imports and avoid depending on repository source paths.

## Imports

```python
from langgraph.prebuilt import (
    ToolNode,
    ValidationNode,
    create_react_agent,
    tools_condition,
    InjectedState,
    InjectedStore,
)
from langgraph.prebuilt.tool_node import ToolRuntime
from langgraph.prebuilt.interrupt import HumanInterrupt, HumanResponse
```

Deprecation note: `create_react_agent`, `ValidationNode`, and several interrupt schemas are compatibility APIs in current LangGraph and emit deprecation guidance toward LangChain agents. Maintain existing code carefully, but prefer `langchain.agents.create_agent` for new general-purpose agents unless the task requires LangGraph prebuilt APIs.

## `create_react_agent`

Signature facts:

```python
create_react_agent(
    model,
    tools,
    *,
    prompt=None,
    response_format=None,
    pre_model_hook=None,
    post_model_hook=None,
    state_schema=None,
    context_schema=None,
    checkpointer=None,
    store=None,
    interrupt_before=None,
    interrupt_after=None,
    debug=False,
    version="v2",
    name=None,
    **deprecated_kwargs,
)
```

Behavior:

- Returns a compiled graph runnable that loops through an `agent` model node and `tools` node until the model stops requesting tool calls.
- `tools` may be a sequence of callables/BaseTool/dict tool specs or a preconfigured `ToolNode`.
- With no tools, the graph is a single LLM node.
- If a model is already bound with `.bind_tools(...)`, the bound tool names/count must match the supplied tools, except for allowed built-ins.
- `version="v1"` runs tool calls from a message in parallel inside one tool node.
- `version="v2"` distributes individual tool calls with `Send`; this is required for `post_model_hook`.
- `remaining_steps` prevents runaway loops; when too few steps remain and tool calls are present, the agent returns a polite final AI message instead of raising a recursion error.

Prompt forms:

- `None`: pass `state["messages"]` to the model.
- `str`: prepend a `SystemMessage`.
- `SystemMessage`: prepend it.
- sync/async callable: receives state and returns model input messages.
- `Runnable`: invoked with state.

Structured response:

- `response_format` accepts JSON schema, OpenAI-style function/tool schema, `TypedDict`, Pydantic model, or `(prompt, schema)`.
- The graph makes a separate model call after the tool loop and writes the result to `structured_response`.
- The model must support `.with_structured_output`.
- A custom `state_schema` used with structured response must include the `structured_response` key.

Hooks:

- `pre_model_hook` runs before the LLM node and must return at least `messages` or `llm_input_messages`.
- To overwrite message history in `pre_model_hook`, return `{"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}`.
- `llm_input_messages` changes only the LLM input and does not update stored graph messages.
- `post_model_hook` runs after the LLM node in `version="v2"` and can return a state update or `Command` for guardrails, human review, or validation routing.

State and context:

- Default state has `messages` and `remaining_steps`.
- Custom `state_schema` must provide `messages` and `remaining_steps`.
- `context_schema` describes run-scoped context accessible through `Runtime.context`.
- `config_schema` is deprecated; use `context_schema`.

Persistence:

- `checkpointer` persists per-thread graph state, usually keyed by `configurable.thread_id`.
- `store` persists cross-thread data and is also used by prompts/tools that request store injection.
- See sibling [persistence](../../persistence/SKILL.md) for saver/store setup details.

Interrupts:

- `interrupt_before=["agent"]` or `["tools"]` pauses before those nodes.
- `interrupt_after=["agent"]` or `["tools"]` pauses after those nodes.
- Use sibling [graph-runtime](../../graph-runtime/SKILL.md) for resume mechanics.

## `ToolNode`

Signature facts:

```python
ToolNode(
    tools,
    *,
    name="tools",
    tags=None,
    handle_tool_errors=..., 
    messages_key="messages",
    wrap_tool_call=None,
    awrap_tool_call=None,
)
```

Input forms:

- `{"messages": [AIMessage(...tool_calls=[...])]}` or a custom state dict with `messages_key`.
- `[AIMessage(...tool_calls=[...])]` for message-list input.
- `[{"name": "tool", "args": {...}, "id": "call-1", "type": "tool_call"}]` for direct tool-call input.

Output forms:

- Dict input returns `{messages_key: [ToolMessage(...)]}` for normal tools.
- Message-list input returns `[ToolMessage(...)]`.
- Direct tool-call input returns a dict with the configured messages key for normal tools.
- Tools may return `Command`, `ToolMessage`, or a list containing `Command`/`ToolMessage` values.

Tool registration:

- Plain functions are converted to tools using inferred schemas.
- `BaseTool` instances keep their schemas and metadata.
- Tool names must match `AIMessage.tool_calls[*]["name"]`.
- Unknown tool names return an error `ToolMessage` with content like `Error: requested_tool is not a valid tool, try one of [...]`.

Error handling:

- Default handling catches invocation errors from bad model arguments and turns them into error `ToolMessage` content.
- Execution errors from the tool itself may be re-raised depending on the configured handler.
- `handle_tool_errors=True` catches broadly and returns default formatted error messages.
- `handle_tool_errors=False` disables conversion and lets exceptions propagate.
- A string handler returns that fixed string for handled errors.
- Exception classes or tuples catch only matching exceptions.
- Callable handlers return a formatted string and may infer handled exception types from type annotations.

Wrappers:

- `wrap_tool_call(request, execute)` intercepts sync execution.
- `awrap_tool_call(request, execute)` intercepts async execution.
- `request` is a `ToolCallRequest` with `tool_call`, `tool`, `state`, and `runtime`.
- Use `request.override(tool_call=..., state=...)` instead of mutating fields.
- Wrappers can retry, cache, rewrite arguments, route dynamic tools, or return custom `ToolMessage`/`Command` values.
- Dynamic tools supplied by wrappers still receive `ToolRuntime` injection when their signature requests it.

## `tools_condition`

```python
tools_condition(state, messages_key="messages") -> "tools" | "__end__"
```

- Reads a list state, dict state, or model-like state with the configured messages attribute.
- Returns `"tools"` if the last message has non-empty `tool_calls`.
- Returns `"__end__"` otherwise.
- Raises `ValueError` if no messages are found.
- In custom graphs, map return values to the `ToolNode` name and `END`/`__end__`.

## Injected Tool Arguments

### `InjectedState`

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState


def tool_name(query: str, state: Annotated[dict, InjectedState()]) -> str: ...
def field_tool(query: str, user_id: Annotated[str, InjectedState("user_id")]) -> str: ...
```

- `InjectedState()` injects the full state object.
- `InjectedState("field")` injects one dict key or object attribute.
- Hidden injected args are excluded from the model-visible tool schema.
- Missing required state fields raise `KeyError` or `AttributeError` depending on state type.
- List state can be converted to `{messages_key: state}` only when the tool needs the whole state or the messages field.

### `InjectedStore`

```python
from typing import Annotated
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore


def memory_tool(key: str, store: Annotated[BaseStore, InjectedStore()]) -> str: ...
```

- Injects the graph/store instance into the tool.
- Requires a compiled graph or invocation context with a store.
- Raises `ValueError` if a tool requires store injection and no store is available.
- Useful for user memories, profiles, and cross-thread data.

### `ToolRuntime`

```python
from langgraph.prebuilt.tool_node import ToolRuntime


def runtime_tool(x: int, runtime: ToolRuntime) -> str:
    return runtime.tool_call_id
```

`ToolRuntime` includes:

- `state`: current graph state for this tool call.
- `tool_call_id`: originating tool-call ID.
- `config`: runnable config for this execution.
- `context`: run-scoped context.
- `store`: persistent store if configured.
- `stream_writer`: stream output writer.
- `tools`: available tool instances.
- `execution_info` and `server_info` when provided by the runtime.

Security property: any model-supplied values for injected argument names are stripped before tool invocation, then trusted injected values are added.

## `Command` Returns from Tools

Tools can return `Command` to update state or navigate. When targeting the current graph, a `Command.update` that updates messages must include a `ToolMessage` whose `tool_call_id` matches the originating call. This preserves the invariant that every assistant tool call has a matching tool response.

Valid patterns:

```python
from langchain_core.messages import ToolMessage
from langgraph.types import Command


def update_state(tool_call_id: str) -> Command:
    return Command(update={"messages": [ToolMessage("ok", tool_call_id=tool_call_id)]})
```

When returning a list containing `Command` and `ToolMessage` values, exactly one terminating `ToolMessage` must match the tool-call ID, either top-level or inside `Command.update[messages_key]`.

## `ValidationNode`

```python
ValidationNode(schemas, *, format_error=None, name="validation", tags=None)
```

Schemas may be:

- Pydantic v2 `BaseModel` subclasses.
- Pydantic v1 `BaseModel` subclasses where supported by the Python/Pydantic version.
- `BaseTool` instances with Pydantic `args_schema`.
- Callables, where a schema is created from the function signature.

Behavior:

- Reads the last `AIMessage` from a message list or `{"messages": [...]}` dict.
- Validates each tool call in parallel.
- Returns `ToolMessage` objects with JSON content for valid calls.
- On validation errors, returns `ToolMessage(..., additional_kwargs={"is_error": True})`.
- Does not execute any tool side effects.
- Raises `ValueError` if the input has no message or the last message is not an `AIMessage`.

## Human Interrupt Schemas

```python
request: HumanInterrupt = {
    "action_request": {"action": "send_email", "args": {"to": "user@example.com"}},
    "config": {
        "allow_ignore": True,
        "allow_respond": True,
        "allow_edit": False,
        "allow_accept": True,
    },
    "description": "Review the email before sending.",
}
```

- `HumanInterruptConfig` controls allowed human actions.
- `ActionRequest` describes the action and arguments under review.
- `HumanInterrupt` is sent through `interrupt([request])` style flows.
- `HumanResponse` returns `type` and `args`: `accept`/`ignore` use `None`, `response` uses a string, and `edit` uses an updated action request.
