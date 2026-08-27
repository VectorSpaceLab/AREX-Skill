# Agent Core Workflows

Use these recipes to implement common Pydantic AI agent patterns without reopening repository docs. Production examples use provider-prefixed model strings; deterministic tests should override them with `TestModel` or `FunctionModel`.

## Minimal Agent

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Answer in one short paragraph.')

result = agent.run_sync('What does Pydantic AI provide?')
print(result.output)
```

Checklist:

- Use a provider-prefixed model string for live providers, such as `openai:gpt-5.2`.
- If the model is chosen later, create `Agent()` or pass `model=` to `run*`.
- If tests should not require provider credentials, use `defer_model_check=True` and override with `TestModel`.

## Typed Dependencies and Dynamic Instructions

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

@dataclass
class Deps:
    user_name: str
    account_tier: str

agent = Agent(
    'openai:gpt-5.2',
    deps_type=Deps,
    instructions='Give practical advice.',
    defer_model_check=True,
)

@agent.instructions
def personalize(ctx: RunContext[Deps]) -> str:
    return f'Address {ctx.deps.user_name}; tier={ctx.deps.account_tier}.'

with agent.override(model=TestModel(custom_output_text='ok')):
    result = agent.run_sync('Hello', deps=Deps('Ada', 'pro'))

assert result.output == 'ok'
```

Guidance:

- `deps_type=Deps` is a type-checking contract; `deps=Deps(...)` is the runtime value.
- Use `@agent.instructions` for current-turn dynamic context; instructions are always reevaluated for the current run.
- Use `@agent.system_prompt` only when you intentionally want system prompt messages to persist in history across runs or across agents.
- Use `TemplateStr` or spec template strings only where a declarative config needs dependency values; Python callables give better IDE/type-checker support.

## Async Runs, Sync Runs, and Settings

```python
from pydantic_ai import Agent, ModelSettings, UsageLimits

agent = Agent(
    'openai:gpt-5.2',
    model_settings=ModelSettings(temperature=0.2),
)

async def answer(prompt: str) -> str:
    result = await agent.run(
        prompt,
        model_settings=ModelSettings(max_tokens=300),
        usage_limits=UsageLimits(request_limit=3, total_tokens_limit=2_000),
        retries={'output': 2},
    )
    return result.output
```

Precedence:

- Model-level settings are the base.
- Agent-level `model_settings` override model defaults.
- Run-time `model_settings` override both for that run.
- Construction `retries=N` sets tool and output budgets; run-time `retries=N` sets output retries only.

## Final-Output Streaming

Use `run_stream()` when you want easy final-output streaming:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

async def stream_text(prompt: str) -> list[str]:
    chunks: list[str] = []
    async with agent.run_stream(prompt) as result:
        async for text in result.stream_text(delta=True):
            chunks.append(text)
    return chunks
```

Important behavior:

- `stream_text(delta=False)` yields accumulated text snapshots; `delta=True` yields deltas.
- `stream_output()` streams validated structured outputs.
- `stream_text()` can only be used for text responses; structured outputs should use `stream_output()`.
- `run_stream()` considers the first output matching the output type final. If the model emits text before a tool call and `output_type` accepts text, later tool calls may not run with the default `end_strategy`.

## Raw Event Streaming

Use `run_stream_events()` when you need all model/tool events and the final result event:

```python
from pydantic_ai import Agent, AgentRunResultEvent

agent = Agent('openai:gpt-5.2')

async def collect_events(prompt: str):
    events = []
    async with agent.run_stream_events(prompt) as stream:
        async for event in stream:
            events.append(event)
            if isinstance(event, AgentRunResultEvent):
                final_output = event.result.output
    return events
```

Guidance:

- Always use `async with agent.run_stream_events(...) as stream:` so cleanup is deterministic.
- Expect raw `PartStartEvent`, `PartDeltaEvent`, `FunctionToolCallEvent`, `FunctionToolResultEvent`, `FinalResultEvent`, and final `AgentRunResultEvent` shapes depending on the model/tool flow.
- You must assemble partial text or structured output from raw events yourself.
- Use `run(event_stream_handler=...)` when the application wants the normal final result while a handler observes the event stream.

## Iterating the Agent Graph

Use `iter()` when graph nodes matter or you need to stream events/output from a model request node:

```python
from pydantic_ai import Agent
from pydantic_ai import ModelRequestNode

agent = Agent('openai:gpt-5.2')

async def inspect_nodes(prompt: str):
    node_names: list[str] = []
    async with agent.iter(prompt) as run:
        async for node in run:
            node_names.append(type(node).__name__)
            if isinstance(node, ModelRequestNode):
                async with node.stream(run.ctx) as request_stream:
                    async for text in request_stream.stream_text(delta=True):
                        print(text, end='')
        assert run.result is not None
        return node_names, run.result.output
```

Guidance:

- `iter()` returns an `AgentRun` context manager; inspect `run.next_node`, `run.result`, `run.ctx`, `run.all_messages()`, and `run.new_messages()` as needed.
- Bare `async for node in run` is fine for simple inspection. If capabilities use node hooks or enqueue idle messages, manually drive with `await run.next(node)` so hooks and queues are honored.
- Route complex standalone graph design to `evals-and-graph`.

## Message History Continuation

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Be concise.')

first = agent.run_sync('Who was Ada Lovelace?')
second = agent.run_sync(
    'What is she best known for?',
    message_history=first.new_messages(),
)

assert first.conversation_id == second.conversation_id
```

Choices:

- Use `new_messages()` to continue from just the current run's additions.
- Use `all_messages()` when the next run needs the entire accumulated transcript.
- Use `all_messages_json()` or `new_messages_json()` for persistence, then deserialize using message adapters covered by `outputs-and-messages`.
- Pass `conversation_id='new'` to fork from a history while starting a fresh conversation identifier.
- If a UI/database/history compactor loses leading system prompts and you rely on `system_prompt`, use `ReinjectSystemPrompt`; prefer `instructions` in new agents to avoid relying on preserved system prompt messages.

## History Processing

Use `ProcessHistory` capability for history filtering or compaction:

```python
from pydantic_ai import Agent, ModelMessage, ModelRequest
from pydantic_ai.capabilities import ProcessHistory


def keep_requests(messages: list[ModelMessage]) -> list[ModelMessage]:
    return [message for message in messages if isinstance(message, ModelRequest)]

agent = Agent('openai:gpt-5.2', capabilities=[ProcessHistory(keep_requests)])
```

Warnings:

- History processors replace the message history used for the model call; copy data first if you need the original list.
- Keep tool-call/tool-return pairs intact when slicing or summarizing history.
- Use a context-aware processor `def fn(ctx: RunContext[Deps], messages: list[ModelMessage]) -> list[ModelMessage]` when filtering depends on deps, usage, run ID, or model.
- Do not use deprecated `history_processors=` in new agents.

## Multi-Agent Delegation

Use an agent as a tool when the parent agent should regain control after delegation:

```python
from pydantic_ai import Agent, RunContext, UsageLimits

selector = Agent(
    'openai:gpt-5.2',
    instructions='Use joke_factory, then return only the best joke.',
)
generator = Agent('google:gemini-3-flash-preview', output_type=list[str])

@selector.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    result = await generator.run(f'Generate {count} short jokes.', usage=ctx.usage)
    return result.output

result = selector.run_sync(
    'Tell me a joke.',
    usage_limits=UsageLimits(request_limit=5, total_tokens_limit=500),
)
```

Guidance:

- Pass `usage=ctx.usage` to delegate runs so the parent result includes delegate usage and usage limits can bound the whole operation.
- Pass `deps=ctx.deps` when parent and delegate share dependency objects.
- Keep agents global/reusable; do not put the delegate agent itself inside deps unless you have a strong application reason.
- If the first agent should hand off permanently rather than return to itself, consider an output function and route final-output contract/history details to `outputs-and-messages`.

## Programmatic Handoff

Use application code to sequence agents when a human or deterministic branch controls which agent runs next:

```python
from pydantic_ai import Agent, RunUsage, UsageLimits

planner = Agent('openai:gpt-5.2')
executor = Agent('openai:gpt-5.2')
limits = UsageLimits(request_limit=8)

async def run_workflow(task: str) -> str:
    usage = RunUsage()
    plan = await planner.run(task, usage=usage, usage_limits=limits)
    execution = await executor.run(
        'Execute this plan.',
        message_history=plan.new_messages(),
        usage=usage,
        usage_limits=limits,
    )
    return execution.output
```

Guidance:

- Share `RunUsage()` when one user operation spans multiple agent runs.
- Share `message_history` only if the next agent should see prior conversation context; otherwise pass structured outputs directly.
- Route complex finite-state control flow to `evals-and-graph`.

## AgentSpec Loading

YAML example:

```yaml
model: openai:gpt-5.2
instructions: "You are assisting {{user_name}}."
model_settings:
  max_tokens: 500
retries:
  output: 2
```

Python loading:

```python
from dataclasses import dataclass

from pydantic_ai import Agent, AgentSpec

@dataclass
class UserDeps:
    user_name: str

spec = AgentSpec.from_file('agent.yaml')
agent = Agent.from_spec(spec, deps_type=UserDeps)
result = agent.run_sync('Hello', deps=UserDeps('Ada'))
```

Use `Agent.from_file('agent.yaml', deps_type=UserDeps)` for the common one-line load. Use `AgentSpec.from_text(text, fmt='yaml')` or `AgentSpec.from_dict(data)` when specs come from a config service.

Spec gotchas:

- A spec or keyword argument must provide `model` before constructing an agent from a spec.
- Template variables are validated when `deps_type` or `deps_schema` is available.
- `output_schema` creates a `StructuredDict` output unless an explicit `output_type` kwarg is supplied.
- `tool_retries`, `output_retries`, and `instrument` fields are deprecated; prefer `retries` and capability-based instrumentation.
- YAML requires the package's spec/YAML support to be installed.

## Direct Model Requests Adjacent to Agents

Use `pydantic_ai.direct` only when you do not need agent features such as tool execution, retries, structured output parsing, dependencies, history processors, or capabilities:

```python
from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_sync

response = model_request_sync(
    'anthropic:claude-haiku-4-5',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
)
```

For most application code, prefer `Agent`; use direct requests for low-level model wrappers or custom abstractions.
