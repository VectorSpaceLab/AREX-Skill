# API Reference: Agents, Tools, and HITL

This reference covers the public Haystack APIs needed to build agents, tools, tool catalogs, human confirmation, and tool-call debugging. It assumes `haystack-ai` 2.31.x and Python 3.10+.

## Public Imports

```python
from haystack import Pipeline, AsyncPipeline, SuperComponent, component
from haystack.components.agents import Agent, State
from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage, ToolCall
from haystack.dataclasses.breakpoints import AgentBreakpoint, Breakpoint, ToolBreakpoint
from haystack.human_in_the_loop import ConfirmationUIResult, ToolExecutionDecision
from haystack.human_in_the_loop import AlwaysAskPolicy, AskOncePolicy, NeverAskPolicy
from haystack.human_in_the_loop import BlockingConfirmationStrategy, SimpleConsoleUI, RichConsoleUI
from haystack.tools import (
    Tool,
    Toolset,
    SearchableToolset,
    ComponentTool,
    PipelineTool,
    create_tool_from_function,
    tool,
)
```

Provider chat generators live outside this sub-skill's responsibility. See `../generation-and-model-components/SKILL.md` for model setup and credentials.

## Agent

`Agent` is the preferred orchestration component for tool-calling applications.

```python
agent = Agent(
    chat_generator=chat_generator,
    tools=[tool_a, tool_b],
    system_prompt="Use tools when needed and answer concisely.",
    user_prompt=None,
    required_variables=None,
    exit_conditions=["text"],
    state_schema=None,
    max_agent_steps=20,
    streaming_callback=None,
    raise_on_tool_invocation_failure=False,
    tool_invoker_kwargs={"convert_result_to_json_string": True},
    confirmation_strategies=None,
)
```

Important parameters:

- `chat_generator`: must accept a `tools` parameter in `run`; otherwise initialization raises `TypeError`.
- `tools`: `list[Tool | Toolset]`, a single `Toolset`, or `None`. Runtime `run(..., tools=...)` can select tools from the agent's configured catalog.
- `system_prompt`, `user_prompt`, `required_variables`: prompt templates. Variables required by prompts become `run` inputs and must not collide with state keys or `run` parameters.
- `exit_conditions`: use `"text"` to stop on an assistant text response, or a tool name to stop after that tool executes.
- `state_schema`: maps state keys to type configs. Tool `inputs_from_state` and `outputs_to_state` read and write these keys.
- `max_agent_steps`: hard loop guard; reduce from the default for production tools.
- `raise_on_tool_invocation_failure`: `False` converts tool errors into tool messages for the model; `True` raises.
- `tool_invoker_kwargs`: forwarded to the internal `ToolInvoker`.
- `confirmation_strategies`: maps a tool name or tuple of tool names to a confirmation strategy.

Typical run:

```python
result = agent.run(messages=[ChatMessage.from_user("Find the weather and summarize it")])
last = result["last_message"]
history = result["messages"]
```

`run_async` mirrors `run` for async orchestration.

## Tool

`Tool` is the model-visible function abstraction.

```python
tool = Tool(
    name="lookup_order",
    description="Look up an order by id.",
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
    function=lookup_order,
    outputs_to_string=None,
    inputs_from_state=None,
    outputs_to_state=None,
)
```

Rules and behavior:

- `function` must be synchronous. Async functions raise `ValueError`.
- `parameters` must be a valid JSON Schema. Invalid schemas raise `ValueError`.
- `tool.tool_spec` returns `{"name", "description", "parameters"}` for chat generators.
- `tool.invoke(**kwargs)` executes the wrapped function and wraps failures in `ToolInvocationError`.
- Override `warm_up()` in subclasses for idempotent expensive setup.

## Function Tools

Use typed functions for most tools.

```python
from typing import Annotated, Literal
from haystack.tools import tool

@tool
def convert_temperature(
    value: Annotated[float, "Temperature value"],
    unit: Annotated[Literal["celsius", "fahrenheit"], "Input unit"],
) -> float:
    """Convert a temperature to the other unit."""
    return value * 9 / 5 + 32 if unit == "celsius" else (value - 32) * 5 / 9
```

`create_tool_from_function(function, name=None, description=None, inputs_from_state=None, outputs_to_state=None, outputs_to_string=None)` is equivalent when decoration is not practical.

Schema generation requirements:

- Every public parameter needs a type hint unless it is mapped from state, typed as `State`, or a skipped callable.
- Use `Annotated` metadata for parameter descriptions.
- Use `Literal` for enums.
- Function docstrings become tool descriptions unless overridden.

## Tool Output Controls

`outputs_to_string` controls what the LLM sees in the tool result message.

Single output style:

```python
outputs_to_string={"source": "documents", "handler": format_docs, "raw_result": False}
```

Multiple output style:

```python
outputs_to_string={
    "summary": {"source": "summary_text", "handler": str},
    "count": {"source": "count"},
}
```

`raw_result=True` is only valid in single-output style and is intended for multimodal content such as `TextContent` or `ImageContent` lists.

`inputs_from_state` maps state keys to tool parameters:

```python
inputs_from_state={"repository": "repo"}
```

`outputs_to_state` maps tool outputs into agent state keys:

```python
outputs_to_state={"documents": {"source": "docs", "handler": dedupe_docs}}
```

For `ComponentTool` and `PipelineTool`, Haystack validates `outputs_to_state.source` against known output sockets.

## Toolset and SearchableToolset

`Toolset([tool_a, tool_b])` groups related tools. It implements iteration, membership, `len`, indexing, `add`, `remove`, `filter`, serialization, and `warm_up`. Passing a single `Tool` directly to `Toolset` is invalid; use `Toolset([tool])`.

`SearchableToolset(catalog, top_k=3, search_threshold=8, search_tool_name="search_tools", search_tool_description=None, search_tool_parameters_description=None)` is for large catalogs:

- If the flattened catalog size is below `search_threshold`, all tools are exposed directly.
- Otherwise the model sees only a bootstrap search tool until it discovers matching tools by keyword.
- `warm_up()` first warms child toolsets, then flattens and indexes the catalog.
- `clear()` resets discovered tools between runs when reusing the same instance.
- `add` and concatenation are intentionally unsupported after initialization.

## ComponentTool

`ComponentTool` wraps one Haystack component instance as a tool.

```python
component_tool = ComponentTool(
    component=my_component,
    name="normalize_text",
    description="Normalize text before indexing.",
    parameters=None,
    outputs_to_string={"source": "text"},
    inputs_from_state=None,
    outputs_to_state=None,
)
```

Use it when a reusable component already has a stable `run` signature. Constraints:

- `component` must be a Haystack component instance.
- The component must not already be added to a pipeline.
- Default schema is generated from component input sockets.
- Default name is the component class name converted to snake case.
- Default description is the component docstring or name.

## PipelineTool

`PipelineTool` wraps a whole `Pipeline` or `AsyncPipeline` through `SuperComponent`.

```python
retrieval_tool = PipelineTool(
    pipeline=retrieval_pipeline,
    name="retrieve_documents",
    description="Retrieve documents relevant to a query.",
    input_mapping={"query": ["embedder.text", "prompt_builder.query"]},
    output_mapping={"retriever.documents": "documents"},
)
```

Use `input_mapping` to collapse many pipeline sockets into LLM-friendly parameters and `output_mapping` to expose only useful outputs. If omitted, mappings are inferred from pipeline inputs/outputs, which can expose confusing internal socket names.

## ToolInvoker

`ToolInvoker` executes prepared `ToolCall`s and returns tool-role `ChatMessage`s.

```python
invoker = ToolInvoker(
    tools=[weather_tool],
    raise_on_failure=True,
    convert_result_to_json_string=False,
    streaming_callback=None,
    enable_streaming_callback_passthrough=False,
    max_workers=4,
)

message = ChatMessage.from_assistant(
    tool_calls=[ToolCall(tool_name="weather", arguments={"city": "Berlin"})]
)
result = invoker.run(messages=[message])
tool_messages = result["tool_messages"]
```

Important behavior:

- `tools` can be a list of `Tool`/`Toolset` or a single `Toolset`.
- Duplicate names and empty tools are rejected.
- `raise_on_failure=False` returns error tool messages instead of raising.
- `convert_result_to_json_string=True` uses `json.dumps`; otherwise `str` conversion is used.
- `enable_streaming_callback_passthrough=True` passes the callback to tools that accept a `streaming_callback` parameter.
- `max_workers` controls concurrent tool invocations.

## Human-in-the-Loop

Core dataclasses:

```python
ConfirmationUIResult(action="confirm" | "reject" | "modify", feedback=None, new_tool_params=None)
ToolExecutionDecision(tool_name="tool", execute=True, tool_call_id=None, feedback=None, final_tool_params={})
```

Built-in policies:

- `AlwaysAskPolicy`: ask every time.
- `NeverAskPolicy`: proceed without UI.
- `AskOncePolicy`: ask once per tool name and exact parameter dict after a confirmation.

Built-in UIs:

- `SimpleConsoleUI`: standard input/output.
- `RichConsoleUI`: richer terminal UI; requires the optional `rich` package.

Blocking strategy:

```python
strategy = BlockingConfirmationStrategy(
    confirmation_policy=AlwaysAskPolicy(),
    confirmation_ui=SimpleConsoleUI(),
)

agent = Agent(
    chat_generator=chat_generator,
    tools=[dangerous_tool, safe_tool],
    confirmation_strategies={dangerous_tool.name: strategy},
)
```

Custom strategies implement `run(...) -> ToolExecutionDecision` and optionally `run_async(...)`. The `confirmation_strategy_context` parameter is available for request-scoped resources such as WebSocket queues or pub/sub clients.

## Breakpoints and Snapshots

Agent breakpoints pause before chat generation or tool execution:

```python
chat_bp = AgentBreakpoint(
    break_point=Breakpoint(component_name="chat_generator", visit_count=0),
    agent_name="my_agent",
)

tool_bp = AgentBreakpoint(
    break_point=ToolBreakpoint(component_name="tool_invoker", visit_count=0, tool_name="weather"),
    agent_name="my_agent",
)
```

Use `snapshot_callback` on `Agent.run()` or `Pipeline.run()` to handle snapshots in memory. File snapshot saving is disabled by default and controlled by `HAYSTACK_PIPELINE_SNAPSHOT_SAVE_ENABLED`. Load saved snapshots with `haystack.core.pipeline.breakpoint.load_pipeline_snapshot` and resume via `pipeline.run(data={}, pipeline_snapshot=snapshot)` when the agent runs inside a pipeline.

## OpenAPI and MCP Connectors

Core Haystack includes OpenAPI connector components under `haystack.components.connectors` for calling operations from OpenAPI specifications, and docs describe MCP tools/toolsets through integration packages. Treat these as optional connector layers:

- Check the package/import path for the installed integration before writing runtime code.
- Convert connector capabilities into ordinary Haystack `Tool` or `Toolset` objects before passing them to `Agent` or `ToolInvoker`.
- Filter large or risky external catalogs with tool-name allowlists or `SearchableToolset`.
- Keep credentials in environment variables or secret managers; never embed them in tool descriptions or serialized pipeline files.
