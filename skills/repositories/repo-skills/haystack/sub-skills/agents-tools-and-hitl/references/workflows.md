# Workflows: Agents, Tools, and HITL

Use these recipes to implement common Haystack agent and tool tasks without reopening the source repository.

## Build a Function Tool

1. Write a synchronous function with complete type hints.
2. Use `typing.Annotated` for parameter descriptions and `Literal` for closed choices.
3. Add a docstring that tells the model when to use the tool.
4. Decorate with `@tool` or call `create_tool_from_function`.
5. Inspect `tool.tool_spec` and invoke it once with representative parameters.

```python
from typing import Annotated, Literal
from haystack.tools import create_tool_from_function


def shipping_quote(
    destination: Annotated[str, "Destination city or postal code"],
    weight_kg: Annotated[float, "Package weight in kilograms"],
    speed: Annotated[Literal["standard", "express"], "Shipping speed"],
) -> dict[str, float | str]:
    """Estimate shipping price for a package."""
    multiplier = 2.0 if speed == "express" else 1.0
    return {"destination": destination, "price": round(5 + weight_kg * 1.8 * multiplier, 2)}

quote_tool = create_tool_from_function(shipping_quote)
assert quote_tool.tool_spec["parameters"]["properties"]["speed"]["enum"] == ["standard", "express"]
```

If schema generation fails, check for missing annotations, unsupported custom classes, or `Callable` parameters. For custom validation not expressible from type hints, construct `Tool(...)` manually with JSON Schema.

## Add State to Tools

Use state when one tool should consume or update data from another tool call.

```python
from typing import Annotated
from haystack.components.agents import Agent
from haystack.tools import create_tool_from_function


def search(query: Annotated[str, "Search query"]) -> dict[str, list[str]]:
    """Search for matching document titles."""
    return {"documents": [f"doc about {query}"]}


def summarize(topic: Annotated[str, "Topic to summarize"], docs: list[str]) -> str:
    """Summarize previously retrieved docs for a topic."""
    return f"{topic}: " + "; ".join(docs)

search_tool = create_tool_from_function(
    search,
    outputs_to_state={"documents": {"source": "documents"}},
)
summarize_tool = create_tool_from_function(
    summarize,
    inputs_from_state={"documents": "docs"},
)

agent = Agent(
    chat_generator=chat_generator,
    tools=[search_tool, summarize_tool],
    state_schema={"documents": {"type": list}},
)
```

Validation checklist:

- State keys in `inputs_from_state` and `outputs_to_state` match `state_schema` intent.
- Tool parameter names on the right side of `inputs_from_state` exist in the wrapped function/component.
- `outputs_to_state.source` matches an output key for `ComponentTool` and `PipelineTool`.
- State values are serializable if snapshots or pipeline serialization are needed.

## Wrap a Component as a Tool

Use `ComponentTool` when the callable unit is one component.

```python
from haystack import component
from haystack.tools import ComponentTool

@component
class TextNormalizer:
    """Normalize input text for downstream processing."""

    @component.output_types(text=str)
    def run(self, text: str) -> dict[str, str]:
        return {"text": " ".join(text.lower().split())}

normalizer = TextNormalizer()
normalizer_tool = ComponentTool(
    component=normalizer,
    name="normalize_text",
    description="Normalize whitespace and lowercase input text.",
    outputs_to_string={"source": "text"},
)
```

Do not wrap a component that has already been added to a pipeline. Instantiate a separate component for the tool.

## Wrap a Pipeline as a Tool

Use `PipelineTool` when the tool should run a graph of components.

```python
from haystack import Pipeline, component
from haystack.tools import PipelineTool

@component
class KeywordResponder:
    @component.output_types(answer=str)
    def run(self, query: str) -> dict[str, str]:
        return {"answer": f"Known facts for {query}: ..."}

pipeline = Pipeline()
pipeline.add_component("responder", KeywordResponder())

qa_tool = PipelineTool(
    pipeline=pipeline,
    name="answer_known_fact",
    description="Answer questions from a curated internal fact source.",
    input_mapping={"query": ["responder.query"]},
    output_mapping={"responder.answer": "answer"},
    outputs_to_string={"source": "answer"},
)
```

Prefer explicit mappings so the LLM sees stable business-level parameter names instead of internal socket paths.

## Use ToolInvoker Manually

Use `ToolInvoker` when a chat generator prepares tool calls but the application owns the loop.

```python
from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage, ToolCall

invoker = ToolInvoker(tools=[quote_tool], raise_on_failure=False, convert_result_to_json_string=True)
message = ChatMessage.from_assistant(
    tool_calls=[ToolCall(tool_name="shipping_quote", arguments={"destination": "Berlin", "weight_kg": 2.5, "speed": "standard"})]
)
result = invoker.run(messages=[message])
for tool_message in result["tool_messages"]:
    print(tool_message.tool_call_result.result)
```

Use `raise_on_failure=False` while prototyping so tool errors become model-visible messages. Switch to `True` when upstream code should handle failures explicitly.

## Build an Agent Tool Loop

1. Choose a chat generator that supports Haystack tools.
2. Create tools/toolsets and smoke-test them independently.
3. Configure a short `max_agent_steps` and clear `exit_conditions`.
4. Add prompt instructions that describe when tools should be used and how to recover from tool failures.
5. Run with a simple user `ChatMessage` and inspect `result["messages"]` before relying on `last_message` only.

```python
from haystack.components.agents import Agent
from haystack.dataclasses import ChatMessage

agent = Agent(
    chat_generator=chat_generator,
    tools=[quote_tool],
    system_prompt="Use tools for shipping calculations. If a tool returns an error, ask for the missing field.",
    max_agent_steps=8,
    raise_on_tool_invocation_failure=False,
)

result = agent.run(messages=[ChatMessage.from_user("Quote express shipping to Paris for 3 kg")])
print(result["last_message"].text)
```

If the model never calls tools, verify provider support in `../generation-and-model-components/SKILL.md`, the tool descriptions, and whether runtime `tools` accidentally overrides the configured tools.

## Manage Large Tool Catalogs

Use `SearchableToolset` when many tools would overwhelm the model.

```python
from haystack.tools import SearchableToolset

toolset = SearchableToolset(
    catalog=all_tools,
    top_k=4,
    search_threshold=8,
    search_tool_description="Find available business tools by keywords from tool names and descriptions.",
)
agent = Agent(chat_generator=chat_generator, tools=toolset, max_agent_steps=12)
```

Operational notes:

- Teach the model in the system prompt to call the bootstrap search tool first for unknown capabilities.
- Call `toolset.clear()` between independent conversations if you reuse the same instance.
- For external toolsets that connect lazily, `SearchableToolset.warm_up()` warms children before indexing.

## Add HITL Confirmation

Use HITL for tools that write data, spend money, call external systems, or expose sensitive information.

```python
from haystack.human_in_the_loop import AlwaysAskPolicy, BlockingConfirmationStrategy, SimpleConsoleUI

strategy = BlockingConfirmationStrategy(
    confirmation_policy=AlwaysAskPolicy(),
    confirmation_ui=SimpleConsoleUI(),
)

agent = Agent(
    chat_generator=chat_generator,
    tools=[read_tool, write_tool],
    confirmation_strategies={write_tool.name: strategy},
)
```

For a shared policy across multiple tools:

```python
confirmation_strategies={("send_email", "create_ticket", "charge_card"): strategy}
```

For web applications, implement a custom strategy that returns `ToolExecutionDecision` and uses `confirmation_strategy_context` for request-scoped channels. Preserve `tool_call_id` in decisions when multiple tool calls can appear in one assistant message.

## Support Modify and Reject Paths

HITL confirmation can modify parameters or reject execution. Design the prompt and application for both outcomes:

- Rejection returns a tool-message-like explanation to the agent, not a final answer by itself.
- Modification replaces the tool call parameters with `final_tool_params`.
- `AskOncePolicy` only stops asking after a `confirm` action with the same parameters.
- If multiple tool calls share a name, include `tool_call_id` to avoid ambiguous decisions.

## Use Breakpoints and Snapshots for Tool Debugging

Use agent breakpoints when a tool call is malformed or risky and you need to inspect before execution.

```python
from haystack.dataclasses.breakpoints import AgentBreakpoint, ToolBreakpoint

breakpoint = AgentBreakpoint(
    break_point=ToolBreakpoint(component_name="tool_invoker", visit_count=0, tool_name="write_tool"),
    agent_name="agent",
)

result = agent.run(
    messages=[ChatMessage.from_user("Update the CRM record")],
    break_point=breakpoint,
    snapshot_callback=lambda snapshot: print(snapshot.break_point),
)
```

When an agent is inside a pipeline, resume from a loaded or in-memory pipeline snapshot via `pipeline.run(data={}, pipeline_snapshot=snapshot)`. Keep snapshot file saving disabled unless you intentionally need files; when enabled, avoid storing snapshots containing secrets.

## Expose External Tools

MCP and OpenAPI are optional connector patterns rather than required core runtime dependencies.

Recommended approach:

1. Verify the installed integration package and import path.
2. Load or construct the external tool/toolset.
3. Filter by allowlisted operation/tool names.
4. Wrap in `SearchableToolset` if the exposed catalog is large.
5. Add HITL for write or side-effect operations.
6. Run a deterministic dry-run or schema inspection before connecting to a real backend.

For OpenAPI connector components, wrap a connector or pipeline around a specific `operation_id` instead of exposing an entire broad API when the task only needs one operation.

## Multi-Agent Pattern

Wrap an `Agent` or specialist pipeline as a tool when a coordinator agent delegates work. Use `ComponentTool` if the specialist is a component-like object with a stable `run` method, or `PipelineTool` if delegation requires a graph. Keep specialist tool descriptions narrow so the coordinator chooses them only for the intended domain.

Cross-reference base pipeline wiring in `../pipelines-and-components/SKILL.md` and provider setup in `../generation-and-model-components/SKILL.md`.
