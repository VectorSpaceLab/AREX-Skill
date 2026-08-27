# giskard.agents workflows

## Purpose

Use these recipes to build async chat workflows, tools, templates, structured
outputs, middleware, optional LiteLLM generators, and embedding wrappers without
reopening the original repository. API details are in
[api-reference.md](api-reference.md); failure recovery is in
[troubleshooting.md](troubleshooting.md).

## Before a live provider call

`giskard.agents.Generator` delegates actual model calls to `giskard.llm`. Before
running any live completion or embedding:

1. Select and install the provider extra or SDK.
2. Configure provider aliases, base URLs, API versions, and credential
environment variables.
3. Run provider-routing checks from [llm-providers](../../llm-providers/SKILL.md).

Do not put provider SDK imports, API keys, or provider wire-format conversions
inside workflow or tool code. Put them in generator subclasses or in the
provider layer.

## Basic async chat

```python
import giskard.agents as agents

generator = agents.Generator(model="openai/gpt-4o-mini")

chat = await generator.chat("Hello, how are you?").run()
print(chat.last.content)
```

Run several independent completions concurrently:

```python
chats = await generator.chat("Give a one-sentence greeting.").run_many(n=3)
assert len(chats) == 3
```

Build a multi-message workflow. Plain string content is literal unless
`as_template=True`:

```python
chat = await (
    generator.chat("You are concise.", role="system")
    .chat("Say hello.", role="user")
    .chat("Hello.", role="assistant")
    .chat("Now say goodbye.", role="user")
    .run()
)
```

Use `ChatWorkflow` directly when a generator is constructed elsewhere:

```python
workflow = agents.ChatWorkflow(generator=generator)
chat = await workflow.chat("Summarize the policy.", role="user").run()
```

## Batch and stream inputs

For one workflow template over many input dictionaries:

```python
workflow = generator.chat(
    "Write a weather-safe answer for {{ city }}.", as_template=True
)

chats = await workflow.run_batch([
    {"city": "Paris"},
    {"city": "London"},
])

assert chats[0].context.inputs["city"] == "Paris"
```

If the caller wants results as soon as each finishes:

```python
async for chat in workflow.stream_batch([{"city": "Paris"}, {"city": "London"}]):
    print(chat.last.content)
```

`run_many` and `stream_many` clone the same workflow inputs for each parallel
run. Use `run_batch` or `stream_batch` when each run needs distinct inputs.

## No-provider local generator for tests and tools

Use a `BaseGenerator` subclass to test workflow logic without network calls.
This is also the pattern for implementing a new provider adapter: translate
messages/tools inside `_call_model`, not in workflows.

```python
from collections.abc import Sequence
from typing import Any, override

import giskard.agents as agents
from giskard.agents.generators import GenerationParams
from giskard.llm.types import AssistantMessage, ChatMessage, Choice, CompletionResponse


class StaticGenerator(agents.BaseGenerator):
    @override
    async def _call_model(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams,
        metadata: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        return CompletionResponse(
            choices=[
                Choice(
                    message=AssistantMessage(content="local response"),
                    finish_reason="stop",
                    index=0,
                )
            ]
        )

chat = await agents.ChatWorkflow(generator=StaticGenerator()).chat("hi").run()
assert chat.last.content == "local response"
```

Run [../scripts/run_agents_smoke.py](../scripts/run_agents_smoke.py) for a
complete deterministic tool-plus-workflow smoke check.

## Prompt templates

### Inline templates

```python
chat = await (
    generator.chat("Hello {{ name }}", as_template=True)
    .with_inputs(name="Test Bot")
    .run()
)
```

Security rule: only mark developer-authored strings as templates. User-supplied
strings should stay literal because Jinja2 expressions execute at render time.

### File templates and namespaces

Configure prompt paths once during application setup:

```python
import giskard.agents as agents

agents.set_default_prompts_path("prompts")
agents.add_prompts_path("prompts/evals", namespace="evals")
```

Then reference exact template names:

```python
chat = await (
    generator.template("evals::judge.j2")
    .with_inputs(answer="Paris", question="Capital of France?")
    .run()
)
```

A template with no message blocks renders as a single user message. Use message
blocks for few-shot or multi-role prompts:

```jinja
{% message system %}
You are a strict JSON formatter.
{% endmessage %}

{% message user %}
Question: {{ question | fence }}
{% endmessage %}
```

Use the `fence` filter when embedding untrusted text inside delimiters or judge
prompts; it escapes marker-breaking characters after Giskard's finalization.

### Structured-output prompt hint

When `.with_output(Model)` is set, the workflow injects `_instr_output` into the
template context. A file template can include it explicitly:

```jinja
{% message system %}
{{ _instr_output }}
{% endmessage %}
{% message user %}
Extract the action from: {{ text | fence }}
{% endmessage %}
```

The workflow also passes the Pydantic model as `response_format` in generation
parameters.

## Tools and RunContext

Define tools with type hints and docstrings. Use `RunContext` for per-run state;
that parameter is not exposed in the tool schema.

```python
from pydantic import BaseModel
import giskard.agents as agents


class Weather(BaseModel):
    city: str
    summary: str


@agents.tool
def get_weather(city: str, context: agents.RunContext) -> Weather:
    """Get deterministic weather.

    Parameters
    ----------
    city : str
        City name.
    context : RunContext
        Per-run state.
    """
    seen = context.get("seen_cities", [])
    context.set("seen_cities", [*seen, city])
    return Weather(city=city, summary="rain")

chat = await (
    generator.chat("What is the weather in Paris?")
    .with_tools(get_weather)
    .run(max_steps=4)
)
print(chat.context.get("seen_cities"))
```

Call `Tool.run` directly for deterministic unit checks and schema/coercion
validation:

```python
ctx = agents.RunContext()
result = await get_weather.run({"city": "Paris"}, ctx=ctx)
# result is a JSON string, because Tool.run serializes non-string outputs.
```

By default, `@agents.tool` catches exceptions and serializes a Giskard `Error`.
Use `@agents.tool(catch=None)` if tool errors should propagate to
`ChatWorkflow.on_error(...)`.

## Structured outputs

Use Pydantic models for typed assistant responses:

```python
from pydantic import BaseModel, Field


class Classification(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)

chat = await (
    generator.chat("Classify the input: {{ text }}", as_template=True)
    .with_inputs(text="This is great")
    .with_output(Classification, strict=True, num_retries=2)
    .run()
)

result = chat.output
assert isinstance(result, Classification)
```

Strict mode validates every non-tool assistant response against the model. The
workflow attempts `1 + num_retries` completions when parsing fails. Set
`strict=False` only when the workflow should return raw assistant content and
let the caller decide whether `chat.output` should be attempted.

If the provider reports `finish_reason="refusal"` or an assistant refusal field
while strict structured output is active, the workflow raises a `WorkflowError`
whose `.exception` is `ModelRefusalError`.

## Error policy

```python
from giskard.agents import ErrorPolicy

# Raise the default WorkflowError.
await workflow.run()

# Return a failed Chat with chat.failed == True and chat.error populated.
chat = await workflow.on_error(ErrorPolicy.RETURN).run()

# For run_many/run_batch/stream_many/stream_batch, discard failed chats.
chats = await workflow.on_error(ErrorPolicy.SKIP).run_many(n=3)
```

For a single `.run()`, `ErrorPolicy.SKIP` behaves like `RETURN` and returns a
failed `Chat` instead of an empty result.

## Steps API for tool traces

Use `.steps()` to inspect intermediate completions and tool results:

```python
from giskard.agents import StepType

async with workflow.with_tools(get_weather).steps(max_steps=10) as step_gen:
    async for step in step_gen:
        if step.step_type == StepType.TOOL_RESULT:
            print("tool result", step.message.content)
        elif step.step_type == StepType.COMPLETION:
            print("assistant/model step", step.message.role)
```

The tool loop stops when a completion has no tool calls or when `max_steps` is
reached.

## Retries and rate limiting

Configure retry policy on the generator, not on tools or workflow loops:

```python
from giskard.agents.generators.middleware import RetryPolicy

generator = agents.Generator(
    model="openai/gpt-4o-mini",
    retry_policy=RetryPolicy(max_attempts=5, base_delay=2.0, max_delay=30.0),
)
# Equivalent convenience copy:
generator = generator.with_retries(5, base_delay=2.0, max_delay=30.0)
```

Limit provider request rate with a core limiter:

```python
from giskard.core import MinIntervalRateLimiter

limiter = MinIntervalRateLimiter.from_rpm(60, max_concurrent=5, id="shared-openai")
generator = agents.Generator(
    model="openai/gpt-4o-mini",
    rate_limiter=limiter,
)
```

Use the same limiter instance or id when several generators must share a global
quota. Instances with the same id and the same limiter fields share state;
using the same id for a different config is an error unless duplicate warnings
are explicitly disabled.

## Custom completion middleware

Use custom middleware for logging, caching, or tracing around completions. It
must call `next_fn` to continue the chain.

```python
from typing import Any
from collections.abc import Sequence

from giskard.agents.generators import GenerationParams
from giskard.agents.generators.middleware import CompletionMiddleware, NextFn
from giskard.llm.types import ChatMessage, CompletionResponse


@CompletionMiddleware.register("audit_log")
class AuditLogMiddleware(CompletionMiddleware):
    async def call(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams | None,
        metadata: dict[str, Any] | None,
        next_fn: NextFn,
    ) -> CompletionResponse:
        response = await next_fn(messages, params, metadata)
        # Store safe metadata or metrics here; do not print secrets.
        return response
```

Built-in ordering is retry, then rate limiter, then custom middlewares.

## Optional LiteLLM generator backend

Install the optional extra before importing the backend:

```bash
pip install "giskard-agents[litellm]"
# or from the root distribution:
pip install "giskard[litellm]"
```

Then construct it explicitly:

```python
from giskard.agents.generators import LiteLLMGenerator

generator = LiteLLMGenerator(model="gemini/gemini-3.5-flash")
chat = await generator.chat("Say hello").run()
```

Use LiteLLM when its routing/model syntax is desired. Use the default
`agents.Generator` when you want Giskard's native `giskard.llm` provider
configuration, error mapping, and provider support.

## Embedding model wrapper

`agents.EmbeddingModel` is an async wrapper over `giskard.llm.aembedding`. It
batches locally and returns NumPy arrays; the actual embedding call still needs
an embedding-capable configured provider.

```python
from giskard.agents.embeddings import EmbeddingParams

embedding_model = agents.EmbeddingModel(
    model="google/gemini-embedding-001",
    params=EmbeddingParams(dimensions=768),
)

vectors = await embedding_model.embed(
    ["first document", "second document"],
    max_batch_size=32,
    max_total_chars=20_000,
)
```

If this wrapper is used to support scan knowledge bases or eval generation,
route the broader scan/eval workflow to [scan-redteam](../../scan-redteam/SKILL.md)
or [checks-evals](../../checks-evals/SKILL.md), and keep provider setup in
[llm-providers](../../llm-providers/SKILL.md).
