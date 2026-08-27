# Agents And Workflows API Reference

This reference captures high-value imports, constructors, and behaviors for LlamaIndex agent work. Prefer repo-local signatures over older examples when behavior conflicts.

## Imports

```python
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent, ReActAgent
from llama_index.core.agent.workflow import AgentInput, AgentOutput, AgentStream, ToolCallResult
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.core.memory import ChatMemoryBuffer, Memory
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent
```

`llama-index-workflows` is installed as a dependency and provides workflow machinery used by `AgentWorkflow` and agent `run()` handlers.

## FunctionAgent

```python
FunctionAgent(
    name="Agent",
    description="An agent that can perform a task",
    system_prompt=None,
    tools=None,
    tool_retriever=None,
    can_handoff_to=None,
    llm=None,
    initial_state=None,
    output_cls=None,
    structured_output_fn=None,
    streaming=True,
    early_stopping_method="force",
    allow_parallel_tool_calls=True,
)
```

Important behavior:

- Requires `llm.metadata.is_function_calling_model`; otherwise `take_step()` raises `ValueError("LLM must be a FunctionCallingLLM")`.
- Uses `llm.achat_with_tools()` for non-streaming and `llm.astream_chat_with_tools()` for streaming.
- `allow_parallel_tool_calls=True` lets compatible providers call multiple tools in a step; set `False` for ordered side-effectful tools.
- `initial_tool_choice` can force a first tool call when provided by the class field.
- Maintains a `scratchpad` in workflow context and writes it to memory during `finalize()`.

## ReActAgent

```python
ReActAgent(
    name="Agent",
    description="An agent that can perform a task",
    system_prompt=None,
    tools=None,
    tool_retriever=None,
    can_handoff_to=None,
    llm=None,
    streaming=True,
    reasoning_key="current_reasoning",
    output_parser=ReActOutputParser(),
    formatter=ReActChatFormatter(...),
)
```

Important behavior:

- Formats tools and chat history into ReAct prompt messages.
- Parses responses as either an action (`Thought`, `Action`, `Action Input`) or final answer (`Thought`, `Answer`).
- Emits retry messages for empty output or parser failures so the LLM can correct its format.
- Stores reasoning steps under `reasoning_key` until finalization.

## AgentWorkflow

```python
AgentWorkflow(
    agents=[...],
    initial_state=None,
    root_agent=None,
    handoff_prompt=None,
    handoff_output_prompt=None,
    state_prompt=None,
    timeout=None,
    output_cls=None,
    structured_output_fn=None,
    early_stopping_method="force",
)
```

Validation and routing:

- At least one agent is required.
- Multi-agent workflows require unique non-default `name` and useful non-default `description` values.
- Multi-agent workflows require `root_agent`; single-agent workflows infer it.
- `root_agent` must match one supplied agent name.
- Per-agent `initial_state` is rejected; use workflow-level `initial_state`.
- `handoff_prompt` must include `{agent_info}` when passed as a string.
- `handoff_output_prompt` must include `{to_agent}` and `{reason}` when passed as a string.
- `state_prompt` must include `{state}` and `{msg}` when passed as a string.

Run parameters:

```python
handler = workflow.run(
    user_msg="...",
    chat_history=[...],
    memory=ChatMemoryBuffer.from_defaults(),
    max_iterations=20,
    early_stopping_method="force",  # or "generate"
)
```

`max_iterations` defaults to 20. With `early_stopping_method="force"`, max iterations raise `WorkflowRuntimeError`. With `"generate"`, the active agent receives one final prompt to generate a response.

## Handoff Tool

`AgentWorkflow` creates a reserved `handoff` tool automatically when there are multiple agents and at least one valid destination. Do not define your own tool named `handoff`; agent validation rejects it.

Handoff inputs:

- `to_agent`: exact target agent `name`.
- `reason`: why control should move.

If the target name is invalid, the tool returns an error string listing valid agents. If `can_handoff_to` blocks the destination, the tool returns a denial string and the workflow remains with the current agent.

## FunctionTool

```python
FunctionTool.from_defaults(
    fn=None,
    name=None,
    description=None,
    return_direct=False,
    fn_schema=None,
    async_fn=None,
    tool_metadata=None,
    callback=None,
    async_callback=None,
    partial_params=None,
)
```

Behavior:

- Requires either `fn` or `async_fn`.
- Auto-infers `name` from the function name when omitted.
- Auto-builds `description` from function signature plus docstring when omitted.
- Auto-creates a Pydantic function schema unless `fn_schema` or `tool_metadata` is supplied.
- Filters `self`, `Context` parameters, and `partial_params` out of generated schema.
- Supports sync and async functions; sync functions are wrapped into async execution.
- `metadata.get_parameters_dict()` shows the schema sent to tool-calling LLMs.

Use `ToolMetadata` directly when full metadata control is required:

```python
metadata = ToolMetadata(
    name="safe_lookup",
    description="Look up one approved item by id.",
    fn_schema=LookupInput,
    return_direct=True,
)
tool = FunctionTool(fn=lookup, metadata=metadata)
```

## QueryEngineTool

```python
QueryEngineTool.from_defaults(
    query_engine,
    name=None,
    description=None,
    return_direct=False,
    resolve_input_errors=True,
)
```

Behavior:

- Calls `query_engine.query(query_str)` in sync mode and `query_engine.aquery(query_str)` in async mode.
- Accepts the query as positional argument, keyword `input`, or stringified kwargs if `resolve_input_errors=True`.
- Returns `ToolOutput(content=str(response), raw_output=response)`.
- Useful for exposing a RAG pipeline, a query engine, or another query-engine-compatible component to an agent.

## Memory

Default agent memory is `ChatMemoryBuffer.from_defaults(...)` unless a `memory` argument is passed at run time.

```python
memory = ChatMemoryBuffer.from_defaults(token_limit=40000)
response = await agent.run(user_msg="...", memory=memory)
```

The newer `Memory` class supports short-term FIFO memory and memory blocks:

```python
memory = Memory(token_limit=30000, token_flush_size=3000, memory_blocks=[])
```

Important fields:

- `token_limit`: overall memory budget, default 30000.
- `token_flush_size`: amount flushed when pressure exceeds the limit, default 3000.
- `chat_history_token_ratio`: minimum ratio reserved for chat history, default 0.7.
- `memory_blocks`: long-lived memory modules that can accept flushed short-term messages.
- `insert_method`: inject memory blocks into system or user messages.

## Events To Watch

Common event classes emitted through `handler.stream_events()`:

| Event | Use |
| --- | --- |
| `AgentInput` | Inspect exact messages sent to the active agent. |
| `AgentStream` | Token deltas, accumulated response text, current agent name, raw provider data, tool-call deltas for function agents. |
| `ToolCall` | Tool name and kwargs before execution. |
| `ToolCallResult` | Tool output, errors, raw input/output, and `return_direct`. |
| `AgentOutput` | Final or intermediate agent model output. |
| `AgentStreamStructuredOutput` | Structured response emitted when `output_cls` or `structured_output_fn` succeeds. |
| `InputRequiredEvent` | Human input is needed by a context-aware tool. |

Always await the handler after consuming events:

```python
handler = agent.run(user_msg="...")
async for event in handler.stream_events():
    ...
result = await handler
```

## Chat Engine API

```python
chat_engine = index.as_chat_engine()
response = chat_engine.chat("Tell me a joke.")
streaming_response = chat_engine.stream_chat("Explain slowly.")
for token in streaming_response.response_gen:
    print(token, end="")
```

Chat engines are stateful query-engine analogues. Use them for conversations over one knowledge source; use agents for tool choice and handoff.
