# Testing and Debugging Agent Core

Use this reference for deterministic tests and common failures around `Agent`, `RunContext`, streaming, usage limits, message history, and specs.

## Deterministic Test Checklist

- Set `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` in tests that should never call live providers.
- Use `TestModel()` for fast schema-driven tool/output exercising.
- Use `FunctionModel(...)` when test assertions require exact model behavior, tool-call arguments, or streamed chunks.
- Use `Agent.override(model=..., deps=..., tools=..., toolsets=..., instructions=...)` around application code when the call site is not easy to parameterize.
- Use `capture_run_messages()` or `FunctionModel` message capture to assert the actual request/response history.
- Use `UsageLimits(request_limit=..., tool_calls_limit=..., total_tokens_limit=...)` to prove loops are bounded.
- For native provider tools configured through capabilities, override with `native_tools=[]` unless the test specifically checks native tool request parameters.

## `TestModel`

Current signature:

```python
TestModel(
    *,
    call_tools: list[str] | Literal['all'] = 'all',
    custom_output_text: str | None = None,
    custom_output_args: Any | None = None,
    seed: int = 0,
    model_name: str = 'test',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
)
```

Typical use:

```python
from pydantic_ai import Agent, models
from pydantic_ai.models.test import TestModel

models.ALLOW_MODEL_REQUESTS = False
agent = Agent('openai:gpt-5.2', defer_model_check=True)

with agent.override(model=TestModel(custom_output_text='deterministic')):
    result = agent.run_sync('ignored by TestModel')

assert result.output == 'deterministic'
```

Notes:

- `TestModel` is procedural, not an LLM. It tries to generate valid tool arguments and structured outputs from schemas.
- With default `call_tools='all'`, it will call registered function tools it can satisfy.
- `call_tools=['tool_name']` limits which tools it calls.
- `custom_output_text` is useful for text agents; `custom_output_args` is useful for structured/output-tool paths.
- It cannot emulate provider-executed native tools.

## `FunctionModel`

Current signature:

```python
FunctionModel(
    function: FunctionDef | None = None,
    *,
    stream_function: StreamFunctionDef | None = None,
    model_name: str | None = None,
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
)
```

Use it when the test must control exactly what the model returns:

```python
from pydantic_ai import Agent, ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel


def model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    if len(messages) == 1:
        assert any(tool.name == 'lookup' for tool in info.function_tools)
        return ModelResponse(parts=[ToolCallPart('lookup', {'query': 'pydantic'})])
    return ModelResponse(parts=[TextPart('done')])

agent = Agent(FunctionModel(model_function))
```

Streaming tests can pass `stream_function=` to emit model stream events. Use `FunctionModel` rather than monkeypatching internals when verifying history processors, event-stream behavior, or handoff message shape.

## Overrides

`agent.override(...)` temporarily changes agent configuration in a context manager:

```python
with agent.override(
    model=TestModel(),
    deps=test_deps,
    instructions='Test-only instructions.',
):
    result = agent.run_sync('prompt')
```

Supported override knobs include `name`, `deps`, `model`, `toolsets`, `tools`, `native_tools`, `instructions`, `metadata`, `model_settings`, `retries`, and `spec`.

Rules:

- Override `retries=N` means output retries only.
- Override `retries={'tools': N}` is invalid; tool retry budgets are construction-time or per-tool/toolset.
- `spec=` in `override()` supplies defaults; spec capabilities replace existing capabilities rather than merging. For additive per-run spec capabilities, pass `spec=` to `run()`/`iter()`.
- Override contexts are the safest way to test app functions that call a module-global agent.

## Capturing Messages

Use `capture_run_messages()` for high-level message assertions:

```python
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.models.test import TestModel

agent = Agent('openai:gpt-5.2', defer_model_check=True)

with capture_run_messages() as messages:
    with agent.override(model=TestModel(custom_output_text='ok')):
        agent.run_sync('hello')

assert messages
```

Use `FunctionModel` for provider-input assertions:

```python
received = []

def capture(messages, info):
    received[:] = messages
    return ModelResponse(parts=[TextPart('ok')])

agent = Agent(FunctionModel(capture))
agent.run_sync('hello')
assert received
```

For history processors, assert the exact messages received by `FunctionModel`, not just `result.all_messages()`.

## Testing Message History Continuation

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent(TestModel(custom_output_text='ok'))
first = agent.run_sync('first')
second = agent.run_sync('second', message_history=first.new_messages())

assert second.all_messages()[0] in first.new_messages()
assert first.conversation_id == second.conversation_id
```

Pitfalls:

- `new_messages()` excludes messages passed in via `message_history`.
- `StreamedRunResult` only includes final result messages after the stream has been fully consumed with `stream_text()`, `stream_output()`, `stream_response()`, or `get_output()`.
- If `stream_text(delta=True)` is the only consumer, the final output string is not built into result messages.
- If moving final output-tool histories between agents, route to `outputs-and-messages` to avoid passing the wrong output-tool call/return sequence.

## Usage-Limit Tests

```python
import pytest

from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits
from pydantic_ai.models.test import TestModel

agent = Agent(TestModel())

with pytest.raises(UsageLimitExceeded):
    agent.run_sync('hello', usage_limits=UsageLimits(request_limit=0))
```

Guidance:

- `request_limit` is checked before the next model request.
- Token limits are checked after responses unless `count_tokens_before_request=True` and the provider supports token counting.
- `tool_calls_limit` is checked before executing a batch of tool calls; if parallel calls would exceed the limit, none of that batch executes.
- Prefer low `request_limit` in tests for retry-loop and delegation failures.

## Troubleshooting Matrix

| Symptom | Likely Cause | Fix |
|---|---|---|
| Missing provider prefix or unknown model | Model string is not provider-prefixed or the provider package is unavailable. | Use strings like `openai:gpt-5.2`; route install/provider diagnosis to `models-and-providers`. |
| Credential error during unit tests | Agent inferred a real provider before override or model requests were allowed. | Use `defer_model_check=True`, `Agent.override(model=TestModel())`, and `models.ALLOW_MODEL_REQUESTS = False`. |
| `RunContext` type checker error | `RunContext[X]` does not match `Agent(..., deps_type=Y)`. | Use the same dependency type and pass an instance with `deps=...` at run time. |
| `ctx.deps` is `None` | `deps_type` was set but `deps=` was omitted for the run, or the agent really uses `None` deps. | Pass `deps=Deps(...)` or make the context handle `None`. |
| Tool retries not changing per run | Per-run `retries` only affects output retries. | Configure tool retries on `Agent(retries={'tools': ...})`, a tool, or a toolset. |
| `UsageLimitExceeded` before expected output | Request, token, or tool-call cap is too low for the loop. | Inspect `result.usage` or captured messages, then raise only the intended limit. |
| `stream_text()` fails for structured output | `stream_text()` is text-only. | Use `stream_output()` for structured output or route output-mode design to `outputs-and-messages`. |
| Tool call appears after streamed text but did not run | `run_stream()` accepted early text/final output as the final result. | Use `run_stream_events()` or `iter()` when all tool calls/events must be observed/executed; consider `end_strategy` only for final-output/tool-call collision behavior. |
| Raw stream event handling misses final output | `run_stream_events()` yields raw events plus `AgentRunResultEvent`; code ignored the final result event. | Check `isinstance(event, AgentRunResultEvent)` and read `event.result.output`. |
| History processor drops tool returns | Processor sliced messages without preserving tool-call/tool-return pairs. | Keep pairs together or summarize safely; route serialization details to `outputs-and-messages`. |
| `new_messages()` unexpected after processing | Processor mutated/replaced trailing prior messages or added messages without current run ID. | Preserve prior message fields, or use a context-aware processor and set `run_id=ctx.run_id` for new current-run messages. |
| Invalid `AgentSpec` YAML/JSON | Missing `model`, bad capability syntax, unknown template variable, or no YAML support. | Validate with `AgentSpec.from_file/from_text`; provide `deps_type`/`deps_schema`; install spec/YAML extra if needed. |
| Deprecated warnings for `system_prompt`, history, retries, stream methods | Code uses legacy surfaces. | Prefer `instructions`, `capabilities=[ProcessHistory(...)]`, `retries=...`, and `stream_response()`/`stream_output()` current names. |

## Difficult Case: Deps, Instructions, Override, History

Goal: prove a user-facing workflow can use typed deps, dynamic instructions, `TestModel` override, and message-history continuation without provider credentials.

Recipe:

1. Define a `@dataclass` deps object and `Agent(..., deps_type=Deps, instructions=..., defer_model_check=True)`.
2. Add `@agent.instructions def dyn(ctx: RunContext[Deps]) -> str` and assert it reads `ctx.deps`.
3. Set `models.ALLOW_MODEL_REQUESTS = False`.
4. Run once inside `with agent.override(model=TestModel(custom_output_text='first')):`.
5. Run again with `message_history=first.new_messages()` inside another override.
6. Assert both outputs, `conversation_id` continuity, and non-empty `all_messages()`.
7. If the task asks for persisted JSON, route to `outputs-and-messages` for adapter details.

## Difficult Case: Streaming Text Before Tool Call

Diagnosis path:

1. Ask whether the code used `run_stream()` and `stream_text()`/`stream_output()`.
2. If a model emitted text that matched the output contract before a tool call, explain that `run_stream()` can treat that first matching output as final.
3. If all events/tool calls must be observed, switch to `run_stream_events()` and process `FunctionToolCallEvent`, `FunctionToolResultEvent`, and `AgentRunResultEvent`.
4. If graph-node control or mixed event-plus-output streaming is needed, switch to `iter()` and stream from `ModelRequestNode`.
5. Route output contract ambiguity, especially `str` fallback in output unions, to `outputs-and-messages`.

## Smoke Script Expectations

The bundled `scripts/agent_smoke.py` performs only local imports and `TestModel` runs. It does not read credentials, contact providers, mutate user files, or rely on the source repository. Use it to quickly prove the installed package exposes current core APIs before deeper debugging.
