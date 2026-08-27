---
name: prebuilt-agents
description: "Use LangGraph prebuilt ReAct agents, ToolNode, ValidationNode,
  injected state/store/runtime, tool error handling, and human interrupt
  schemas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangGraph Prebuilt Agents

Use this sub-skill when an agent task involves `langgraph.prebuilt`: ReAct-style agent graphs, `ToolNode`, `ValidationNode`, tool-call routing, injected state/store/runtime, custom tool error handling, or human-in-the-loop interrupt payloads.

## Start Here

- For API signatures and parameter behavior, read [references/api-reference.md](references/api-reference.md).
- For implementation recipes, graph patterns, and validation loops, read [references/workflows.md](references/workflows.md).
- For import failures, deprecations, malformed calls, injection failures, and async issues, read [references/troubleshooting.md](references/troubleshooting.md).
- For a safe local smoke check, run [scripts/smoke_tool_node.py](scripts/smoke_tool_node.py).
- For graph state, routing, and `StateGraph` mechanics, use sibling [graph-runtime](../graph-runtime/SKILL.md).
- For checkpointers and stores used by agents/tools, use sibling [persistence](../persistence/SKILL.md).
- For deployment and config, use sibling [cli-deployment](../cli-deployment/SKILL.md).
- For remote LangGraph API clients, use sibling [sdk-clients](../sdk-clients/SKILL.md).

## Choose the Right Prebuilt Component

| Goal | Use | Notes |
| --- | --- | --- |
| Build a quick tool-calling loop | `create_react_agent` | Deprecated in LangGraph in favor of `langchain.agents.create_agent`, but still present in `langgraph.prebuilt`. |
| Execute model tool calls in a custom graph | `ToolNode` | Supports dict state, message-list input, and direct tool-call input. |
| Route only when an AI message has tool calls | `tools_condition` | Returns `"tools"` or `"__end__"`; accepts a custom `messages_key`. |
| Validate tool-call args without executing tools | `ValidationNode` | Deprecated; useful for extraction/re-prompt patterns that must preserve tool IDs. |
| Hide state/store/runtime from model-visible tool schemas | `InjectedState`, `InjectedStore`, `ToolRuntime` | Values are injected by `ToolNode`, not supplied by the LLM. |
| Pause for human review | `HumanInterrupt`, `HumanResponse` schemas | Interrupt schemas moved toward `langchain.agents.interrupt`; expect deprecation warnings from old imports. |

## Minimal ToolNode Smoke

```bash
python skills/langgraph/sub-skills/prebuilt-agents/scripts/smoke_tool_node.py --help
python skills/langgraph/sub-skills/prebuilt-agents/scripts/smoke_tool_node.py
```

Expected smoke output includes a JSON object with a successful `add` tool result and an error `ToolMessage` for a malformed call. The script is self-contained and does not require credentials, network access, a checkpointer, or destructive writes.

## ReAct Agent Pattern

Prefer the newer LangChain `create_agent` when starting greenfield code. Use `langgraph.prebuilt.create_react_agent` when maintaining existing LangGraph code or when the task explicitly asks for this API.

```python
from langgraph.prebuilt import create_react_agent


def get_weather(city: str) -> str:
    """Return a small weather fixture."""
    return f"sunny in {city}"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt="You are concise.",
    version="v2",
)
result = agent.invoke({"messages": [{"role": "user", "content": "weather in sf"}]})
```

Important `create_react_agent` parameters:

- `prompt` may be `str`, `SystemMessage`, callable, async callable, or `Runnable`; it receives graph state and may use configured store when supported.
- `response_format` adds a final structured response under `structured_response` and requires model `.with_structured_output` support.
- `pre_model_hook` must return at least `messages` or `llm_input_messages`; use `RemoveMessage(id=REMOVE_ALL_MESSAGES)` when overwriting `messages`.
- `post_model_hook` is available only with `version="v2"` and is useful for validation, guardrails, or human review.
- `state_schema` must include `messages` and `remaining_steps`; add `structured_response` when `response_format` is used.
- `context_schema` is the run-scoped context schema; `config_schema` is deprecated.
- `checkpointer` persists per-thread conversation state; `store` provides cross-thread persistent data to prompts and injected tools.
- `interrupt_before` and `interrupt_after` support node names such as `"agent"` and `"tools"`.
- `version="v1"` executes all tool calls from one message inside one tool node; `version="v2"` distributes tool calls through `Send` and is the default.

## ToolNode Essentials

```python
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

node = ToolNode([add])
state = {
    "messages": [
        AIMessage(content="", tool_calls=[{"name": "add", "args": {"a": 2, "b": 3}, "id": "call-1"}])
    ]
}
output = node.invoke(state)
```

Accepted inputs:

- Dict state with `messages` or a custom `messages_key` containing messages.
- A message list whose last AI message has `tool_calls`.
- A direct list of tool-call dicts with `name`, `args`, `id`, and `type="tool_call"` for programmatic tests.

Outputs:

- Dict input returns `{messages_key: [ToolMessage(...)]}` for ordinary tools.
- Message-list input returns `[ToolMessage(...)]`.
- Tools returning `Command` may update graph state, navigate, or send messages; current-graph `Command.update` must include a matching `ToolMessage` for the tool-call ID unless it removes all messages.

## Error Handling

`ToolNode(..., handle_tool_errors=...)` accepts:

- `True`: catch errors and return an error `ToolMessage`.
- `False`: re-raise errors; use this in tests when failures should be visible.
- `"message"`: catch errors and return the fixed message.
- `ValueError` or `(ValueError, ToolException)`: catch only matching exception types.
- `callable`: format handled exceptions as a string; type annotations can narrow which exception types are handled.

`GraphInterrupt` and other bubble-up graph control exceptions should not be swallowed as ordinary tool errors.

## Injected State, Store, and Runtime

Use injected arguments for data the model must not control:

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState, InjectedStore
from langgraph.prebuilt.tool_node import ToolRuntime
from langgraph.store.base import BaseStore


def lookup_user(
    query: str,
    user_id: Annotated[str, InjectedState("user_id")],
    store: Annotated[BaseStore, InjectedStore()],
    runtime: ToolRuntime,
) -> str:
    """Use hidden graph context while exposing only query to the model."""
    item = store.get(("users",), user_id)
    return f"{query}: {item.value if item else 'missing'} via {runtime.tool_call_id}"
```

Rules:

- `InjectedState()` injects the entire state; `InjectedState("field")` injects one state key or attribute.
- `InjectedStore()` requires compiling or invoking the graph with a store; otherwise `ToolNode` raises an injection error.
- `ToolRuntime` is injected by type annotation without `Annotated` and includes `state`, `config`, `context`, `store`, `stream_writer`, `tool_call_id`, `tools`, execution info, and server info.
- LLM-supplied values for injected args are stripped before execution; trusted runtime values win.
- For direct `ToolNode` invocation outside a compiled graph, injection-sensitive tests may need a runnable config that includes graph runtime context; prefer compiled graph tests when possible.

## ValidationNode for Re-Prompting

`ValidationNode` validates tool calls from the last `AIMessage` against Pydantic models, BaseTool arg schemas, or function signatures, and returns `ToolMessage` objects. It does not execute tools.

Use it when a model should be re-prompted until generated tool-call args conform to a schema and existing tool-call IDs must be preserved for chat history consistency. On validation failure, the returned `ToolMessage` has `additional_kwargs={"is_error": True}` by default.

## Human Interrupt Schemas

`langgraph.prebuilt.interrupt` exposes typed payloads for Agent Inbox style human review:

- `HumanInterruptConfig`: booleans `allow_ignore`, `allow_respond`, `allow_edit`, `allow_accept`.
- `ActionRequest`: `action` string plus `args` dict.
- `HumanInterrupt`: `action_request`, `config`, and optional `description`.
- `HumanResponse`: `type` of `"accept"`, `"ignore"`, `"response"`, or `"edit"`, with matching `args`.

Treat old prebuilt interrupt imports as compatibility support and expect deprecation warnings that point to `langchain.agents.interrupt`.

## Validate Your Work

- Run `python skills/langgraph/sub-skills/prebuilt-agents/scripts/smoke_tool_node.py` for a dependency-light local check.
- For direct tool execution tests, assert every `ToolMessage.tool_call_id` matches the originating `AIMessage.tool_calls[*].id`.
- For `Command`-returning tools, assert exactly one terminating `ToolMessage` is present for the tool call.
- For injected args, assert the tool schema does not expose hidden parameters to the model and that spoofed LLM args do not override runtime-injected values.
- For `ValidationNode`, assert malformed calls return `additional_kwargs["is_error"]` and preserve the original tool-call ID.
