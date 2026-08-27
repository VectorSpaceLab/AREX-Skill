# Agent API Reference

This reference captures current public signatures and parameter choices for core `pydantic_ai.Agent` work. It is distilled from the source and live API inspection for this generated skill.

## Constructor

```python
Agent(
    model: Model | KnownModelName | str | None = None,
    *,
    output_type: OutputSpec[OutputDataT] = str,
    instructions: AgentInstructions[AgentDepsT] = None,
    system_prompt: str | Sequence[str] = (),
    deps_type: type[AgentDepsT] = NoneType,
    name: str | None = None,
    description: TemplateStr[AgentDepsT] | str | None = None,
    model_settings: AgentModelSettings[AgentDepsT] | None = None,
    retries: int | AgentRetries | None = None,
    validation_context: Any | Callable[[RunContext[AgentDepsT]], Any] = None,
    tools: Sequence[Tool[AgentDepsT] | ToolFuncEither[AgentDepsT, ...]] = (),
    toolsets: Sequence[AgentToolset[AgentDepsT]] | None = None,
    defer_model_check: bool = False,
    end_strategy: EndStrategy = 'early',
    metadata: AgentMetadata[AgentDepsT] | None = None,
    tool_timeout: float | None = None,
    max_concurrency: AnyConcurrencyLimit = None,
    capabilities: Sequence[AgentCapability[AgentDepsT]] | None = None,
)
```

### Constructor Decisions

| Need | Use | Notes |
|---|---|---|
| Default model | `model='provider:model-name'` | Provider-prefixed strings are normal for production. Route model/extras/provider errors to `models-and-providers`. |
| Late test override | `Agent(..., defer_model_check=True)` plus `agent.override(model=TestModel())` | Useful when production model needs credentials that tests do not have. |
| Final output contract | `output_type=MyModel`, `str`, or output classes | Route structured-output mode decisions to `outputs-and-messages`. |
| Agent prompt | `instructions=...` or `@agent.instructions` | Preferred for most new code; current instructions are always included when history is passed. |
| Preserved prompt history | `system_prompt=...` or `@agent.system_prompt` | Use only when previous system prompt messages should remain part of `message_history`. |
| Typed dependencies | `deps_type=MyDeps` and per-run `deps=MyDeps(...)` | `deps_type` is for static typing; pass an instance at run time. |
| Retry budgets | `retries={'tools': 3, 'output': 1}` or `retries=1` | Construction-time `int` sets both tool and output budgets. |
| Tool timeout | `tool_timeout=seconds` | Per-tool timeouts can override it; route tool behavior to `tools-and-toolsets`. |
| Tool final-output collisions | `end_strategy='early'`, `'graceful'`, or `'exhaustive'` | Matters when model returns final output and tool calls together; streaming defaults can stop early. |
| Run metadata | `metadata=dict` or callable using `RunContext` | Metadata appears on run results and instrumentation spans. |
| Concurrency | `max_concurrency=int` or limiter | Limits concurrent runs on the same agent. |
| History/capability hooks | `capabilities=[...]` | Use for `ProcessHistory`, event processing, hooks, instrumentation, and advanced integrations. |

## Run Methods

```python
await agent.run(
    user_prompt: str | Sequence[UserContent] | None = None,
    *,
    output_type: OutputSpec[RunOutputDataT] | None = None,
    message_history: Sequence[ModelMessage] | None = None,
    deferred_tool_results: DeferredToolResults | None = None,
    conversation_id: str | None = None,
    model: Model | KnownModelName | str | None = None,
    instructions: AgentInstructions[AgentDepsT] = None,
    deps: AgentDepsT = None,
    model_settings: AgentModelSettings[AgentDepsT] | None = None,
    usage_limits: UsageLimits | None = None,
    usage: RunUsage | None = None,
    metadata: AgentMetadata[AgentDepsT] | None = None,
    retries: int | AgentRetries | None = None,
    infer_name: bool = True,
    toolsets: Sequence[AbstractToolset[AgentDepsT]] | None = None,
    event_stream_handler: EventStreamHandler[AgentDepsT] | None = None,
    capabilities: Sequence[AgentCapability[AgentDepsT]] | None = None,
    spec: dict[str, Any] | AgentSpec | None = None,
) -> AgentRunResult[Any]
```

`run_sync(...)` accepts the same core parameters and returns `AgentRunResult[Any]` synchronously.

```python
async with agent.run_stream(...) as result:  # same run args plus event_stream_handler
    async for text in result.stream_text(delta=False, debounce_by=0.1): ...
    async for output in result.stream_output(debounce_by=0.1): ...
```

```python
async with agent.run_stream_events(...) as stream:  # no event_stream_handler parameter
    async for event in stream: ...
```

```python
async with agent.iter(...) as agent_run:  # same run args except event_stream_handler
    async for node in agent_run: ...
```

### Run Method Decisions

| Method | Choose When | Avoid When |
|---|---|---|
| `run()` | Async application code wants a complete `AgentRunResult`. | Caller is purely synchronous. |
| `run_sync()` | CLI scripts, notebooks, or sync tests need a complete result. | Already inside an event loop where blocking would be wrong. |
| `run_stream()` | UI needs streamed final text or structured output via `stream_text()`/`stream_output()`. | You must guarantee all tool calls execute after early text or final output. |
| `run_stream_events()` | You need raw `AgentStreamEvent` and final `AgentRunResultEvent` for model/tool event timelines. | You only need final text streaming; `run_stream()` is simpler. |
| `iter()` | You need graph-node control, to stream at selected nodes, or to inspect/drive model/tool phases manually. | Basic applications where `run()` is enough. |

## Result and Stream Objects

- `AgentRunResult.output` is the final output, already validated against `output_type`.
- `AgentRunResult.usage` and `StreamedRunResult.usage` expose accumulated `RunUsage` with requests, tool calls, and token totals.
- `all_messages()` returns prior plus current messages; `new_messages()` returns only messages produced by the current run.
- `all_messages_json()` and `new_messages_json()` serialize messages for persistence; route deep message-format decisions to `outputs-and-messages`.
- `StreamedRunResult` messages include the final response only after `stream_text()`, `stream_output()`, `stream_response()`, or `get_output()` completes. If `stream_text(delta=True)` is the only consumer, the final string is not built into result messages.
- `AgentRun` from `iter()` exposes `next_node`, `result`, `all_messages()`, `new_messages()`, and manual `next(...)` driving; use `next()` rather than bare async iteration when capability node hooks must fire.

## Dependencies and `RunContext`

Use a dependency container when prompts/tools/output validators need runtime services or request state:

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

@dataclass
class Deps:
    user_name: str

agent = Agent('openai:gpt-5.2', deps_type=Deps, instructions='Be concise.')

@agent.instructions
def add_user(ctx: RunContext[Deps]) -> str:
    return f'The user is {ctx.deps.user_name}.'

result = agent.run_sync('Say hello', deps=Deps('Ada'))
```

Rules:

- Pass the dependency type to `deps_type`, not an instance.
- Pass the dependency instance to `run*`/`iter` with `deps=...`.
- Parameterize `RunContext[Deps]` with the same dependency type to keep type checkers useful.
- `RunContext` provides `deps`, `agent`, `model`, `usage`, `retry`, `messages`, `prompt`, `run_id`, `conversation_id`, `metadata`, and model settings context depending on the call site.
- Sync context functions are run in an executor; prefer `async def` when dependencies do IO.

## Retry and Usage API

`AgentRetries` is a `TypedDict` with optional keys:

```python
retries={'tools': 3, 'output': 1}
```

Semantics:

- `Agent(retries=N)` sets both tool and output retry budgets to `N`.
- `Agent(retries={'tools': T, 'output': O})` sets separate construction-time budgets.
- `agent.run(..., retries=N)` or `agent.run(..., retries={'output': N})` overrides only output validation retries.
- Per-run or `override()` calls cannot set tool retries; configure tool retries at construction or per tool/toolset.
- Deprecated `tool_retries=` and `output_retries=` are still accepted in 1.x but should not be used in new code.

`UsageLimits` current constructor:

```python
UsageLimits(
    *,
    request_limit: int | None = 50,
    tool_calls_limit: int | None = None,
    input_tokens_limit: int | None = None,
    output_tokens_limit: int | None = None,
    total_tokens_limit: int | None = None,
    count_tokens_before_request: bool = False,
)
```

Use `request_limit` to stop runaway loops, `tool_calls_limit` to cap successful tool execution, and token limits to cap provider usage. `input_tokens_limit` and `output_tokens_limit` are current names; `request_tokens_limit` and `response_tokens_limit` are deprecated aliases.

## AgentSpec APIs

```python
AgentSpec(
    *,
    json_schema_path: str | None = None,
    model: str | None = None,
    name: str | None = None,
    description: TemplateStr[Any] | str | None = None,
    instructions: TemplateStr[Any] | str | list[TemplateStr[Any] | str] | None = None,
    deps_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    model_settings: dict[str, Any] | None = None,
    retries: int | AgentRetries | None = None,
    tool_retries: int | None = None,  # deprecated
    output_retries: int | None = None,  # deprecated
    end_strategy: Literal['early', 'graceful', 'exhaustive'] = 'early',
    tool_timeout: float | None = None,
    instrument: bool | None = None,  # deprecated in favor of Instrumentation capability
    metadata: dict[str, Any] | None = None,
    capabilities: list[CapabilitySpec] = [],
)
```

Loading and construction:

- `AgentSpec.from_file(path, fmt=None)` loads YAML/JSON by extension unless `fmt` is provided.
- `AgentSpec.from_text(text, fmt='yaml')` parses text.
- `AgentSpec.from_dict(data)` validates a dict.
- `Agent.from_spec(spec, deps_type=..., tools=..., toolsets=..., capabilities=...)` constructs an agent; explicit kwargs override scalar spec fields, merge after spec instructions/capabilities, and override matching `model_settings` keys.
- `Agent.from_file(path, deps_type=...)` is equivalent to loading the spec then calling `from_spec`.
- Per-run `spec=` is additive and can provide model fallback, instructions, settings, capabilities, and output retries for a specific run.
- `AgentSpec.to_file(path, fmt=None, schema_path='./{stem}_schema.json')` writes YAML/JSON and optionally a companion JSON schema.

If YAML loading fails because `yaml` is unavailable, install the spec extra for the package. If a spec has template variables, provide `deps_type` or `deps_schema` so variable names can be validated.

## Deprecation and Compatibility Warnings

- Prefer `instructions` over `system_prompt`; use `system_prompt` only when preserved system prompt messages across history are intentional.
- Replace legacy `history_processors=` with `capabilities=[ProcessHistory(...)]`.
- Replace deprecated `mcp_servers=` with `toolsets=`.
- Replace deprecated direct event-stream handler construction patterns with run-time `event_stream_handler` or capability-based event processing; route advanced event processing to `mcp-and-integrations`.
- Replace `stream_responses()` with `stream_response()` and `stream()` with `stream_output()` on streamed result objects.
