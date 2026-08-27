# Prebuilt Agent Workflows

This guide gives reusable patterns for LangGraph prebuilt agents and tool execution. Keep examples self-contained; do not depend on repository examples or local checkout paths.

## Build a Simple ReAct Agent

Use this when maintaining existing `langgraph.prebuilt.create_react_agent` code:

```python
from langgraph.prebuilt import create_react_agent


def search(query: str) -> str:
    """Return a deterministic fixture."""
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "60 degrees and foggy"
    return "90 degrees and sunny"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[search],
    prompt="Answer briefly and cite tool observations.",
    version="v2",
)

result = agent.invoke({"messages": [{"role": "user", "content": "weather in sf"}]})
```

Checklist:

- Confirm the model package and credentials are available; the prebuilt code does not bundle provider clients.
- Confirm each tool has a docstring and typed parameters so schema inference is useful.
- If the model is already bound with tools, verify names match the supplied `tools` list.
- Use `version="v2"` for new maintenance work that needs `post_model_hook` or per-tool-call distribution.
- Use a checkpointer for multi-turn memory and a store for cross-thread memory; see [../../persistence/SKILL.md](../../persistence/SKILL.md).

## Add a Pre-Model Hook for Message Trimming

`pre_model_hook` can change what the LLM sees without corrupting state history:

```python
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES


def trim_for_llm(state: dict) -> dict:
    recent = state["messages"][-8:]
    return {"llm_input_messages": recent}


def replace_history(state: dict) -> dict:
    recent = state["messages"][-8:]
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *recent]}
```

Use `llm_input_messages` for temporary prompt compaction. Use the `RemoveMessage(id=REMOVE_ALL_MESSAGES)` pattern only when you intentionally overwrite graph state.

## Add a Post-Model Hook for Guardrails

`post_model_hook` is available only with `create_react_agent(..., version="v2")`.

```python
from langchain_core.messages import AIMessage


def require_tool_for_prices(state: dict) -> dict:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and "price" in last.content.lower() and not last.tool_calls:
        return {"messages": [AIMessage(content="I need to call a pricing tool first.")]}
    return {}
```

Use post hooks for validation, handoff, review, or human interrupt routing. If the hook emits tool calls or commands, ensure the next node routing still preserves tool-call/tool-message consistency.

## Use ToolNode in a Custom StateGraph

```python
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def call_model(state: State) -> dict:
    # Replace this stub with a tool-calling chat model invocation.
    return {"messages": []}

builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode([add]))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": END})
builder.add_edge("tools", "agent")
graph = builder.compile()
```

Common variations:

- Set `ToolNode(..., messages_key="chat_history")` and route with `partial(tools_condition, messages_key="chat_history")` when your state uses another message field.
- Use direct tool-call input for unit tests: `ToolNode([add]).invoke([{"name": "add", "args": {"a": 1, "b": 2}, "id": "1", "type": "tool_call"}])`.
- Use `handle_tool_errors=False` in tests to fail fast on invalid schemas or tool exceptions.

## Customize Tool Error Handling

```python
from langchain_core.tools import ToolException
from langgraph.prebuilt import ToolNode


def user_safe_error(error: ValueError) -> str:
    return f"Invalid tool arguments: {error}"

node = ToolNode(
    [my_tool],
    handle_tool_errors=user_safe_error,
)

strict_node = ToolNode([my_tool], handle_tool_errors=False)

selective_node = ToolNode(
    [my_tool],
    handle_tool_errors=(ValueError, ToolException),
)
```

Guidance:

- Use a callable formatter to tell the model how to repair malformed arguments.
- Use `False` for security-sensitive tools when exceptions should not be converted into model-visible text.
- Do not catch graph control exceptions such as interrupts as ordinary tool failures.
- Test both success and malformed-call paths; malformed call results should keep the original `tool_call_id`.

## Intercept Tool Calls with Wrappers

```python
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode


def wrap_tool_call(request, execute):
    if request.tool_call["name"] == "blocked_tool":
        return ToolMessage(
            content="This tool is blocked by policy.",
            name=request.tool_call["name"],
            tool_call_id=request.tool_call["id"],
            status="error",
        )
    fixed_args = {**request.tool_call["args"]}
    if "count" in fixed_args:
        fixed_args["count"] = max(0, fixed_args["count"])
    return execute(request.override(tool_call={**request.tool_call, "args": fixed_args}))

node = ToolNode([safe_tool], wrap_tool_call=wrap_tool_call)
```

Wrapper rules:

- Use `request.override(...)`; direct attribute assignment is deprecated.
- The `execute` callable can be called multiple times for retry logic.
- For async tools, prefer `awrap_tool_call`; if absent, async execution falls back to the sync wrapper path where supported.
- Dynamic tools chosen inside wrappers can still receive `ToolRuntime` injection if their signature asks for it.

## Inject State and Store Safely

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState, InjectedStore, ToolNode
from langgraph.prebuilt.tool_node import ToolRuntime
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore


def remember_preference(
    key: str,
    value: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore()],
    runtime: ToolRuntime,
) -> str:
    """Save a user preference."""
    store.put(("preferences", user_id), key, {"value": value, "tool_call_id": runtime.tool_call_id})
    return "saved"

node = ToolNode([remember_preference])
store = InMemoryStore()
```

When compiling a graph that uses this node, pass the store to graph compilation/invocation according to the graph runtime API. If you invoke a `ToolNode` directly outside a graph, use a compiled graph for integration-level injection tests rather than relying on private runtime config keys.

Security checks:

- Confirm the generated tool schema exposes only model-controlled arguments such as `key` and `value`.
- Include a test where the LLM tries to pass `user_id` or `store`; the injected runtime value should override or strip the spoofed value.
- Avoid returning secrets or raw store records in tool messages.

## Return Commands from Tools

Use `Command` when a tool must update state or navigate:

```python
from typing import Annotated
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command


def set_status(status: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """Update status and terminate the tool call."""
    return Command(
        update={
            "status": status,
            "messages": [ToolMessage(f"status={status}", tool_call_id=tool_call_id)],
        }
    )
```

Validation rules:

- Dict-style `Command.update` requires dict state input and the configured `messages_key`.
- List-style `Command.update` requires message-list input.
- Current-graph commands must include a matching `ToolMessage` for the originating tool call.
- A list returned by one tool must contain exactly one terminating `ToolMessage` for the originating call.
- `Command(graph=Command.PARENT, ...)` can target a parent graph and follows parent graph routing semantics.

## Validate Malformed Tool Calls Without Executing Tools

```python
from pydantic import BaseModel, field_validator
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ValidationNode


class SelectNumber(BaseModel):
    a: int

    @field_validator("a")
    @classmethod
    def must_be_37(cls, value: int) -> int:
        if value != 37:
            raise ValueError("Only 37 is allowed")
        return value

node = ValidationNode([SelectNumber])
result = node.invoke({
    "messages": [
        AIMessage(
            content="",
            tool_calls=[{"name": "SelectNumber", "args": {"a": 42}, "id": "call-1"}],
        )
    ]
})
error_message = result["messages"][0]
assert error_message.additional_kwargs["is_error"] is True
assert error_message.tool_call_id == "call-1"
```

Re-prompt pattern:

1. Model emits a tool call for a Pydantic schema.
2. `ValidationNode` validates the call and returns tool messages.
3. Conditional route checks the latest validation messages.
4. If any has `additional_kwargs["is_error"]`, return to the model with the preserved tool-call IDs.
5. If none are errors, end or continue to the next graph node.

This is especially useful for extraction workflows where the schema is complex and executing a real tool would be wrong.

## Human Review with Interrupt Payloads

```python
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterrupt, HumanResponse


def review_action(tool_call: dict) -> HumanResponse:
    request: HumanInterrupt = {
        "action_request": {"action": tool_call["name"], "args": tool_call["args"]},
        "config": {
            "allow_ignore": True,
            "allow_respond": True,
            "allow_edit": True,
            "allow_accept": True,
        },
        "description": "Review this tool call before execution.",
    }
    return interrupt([request])[0]
```

Handle responses:

- `accept`: proceed with the original action.
- `ignore`: skip or replace with a safe no-op `ToolMessage`.
- `response`: use text feedback to re-prompt the model.
- `edit`: apply the edited `ActionRequest` after validation.

## Suggested Hard Usability Cases

- Malformed schema loop: route an invalid `SelectNumber` tool call through `ValidationNode`, preserve the original `tool_call_id`, re-prompt, then accept a corrected call.
- Injection and custom errors: create a `ToolNode` with a tool using `InjectedState("user_id")`, `InjectedStore()`, and `ToolRuntime`; include a wrapper or callable `handle_tool_errors` that converts only `ValueError` while allowing security-sensitive exceptions to propagate.
