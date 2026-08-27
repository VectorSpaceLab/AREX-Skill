# Output API

This reference covers final output contracts for Pydantic AI agents. It focuses on public identifiers exposed from `pydantic_ai` and `pydantic_ai.output`.

## Core Contract

`Agent(..., output_type=...)` and per-run `agent.run(..., output_type=...)` accept an output spec made from a single type, a callable output function, a sequence of choices, or marker classes.

| Need | Use | Notes |
| --- | --- | --- |
| Plain text | default `output_type=str` | A run can end on any text response. |
| Typed structured data | Pydantic model, dataclass, `TypedDict`, scalar, collection, or union/list | Pydantic AI builds JSON schema and validates returned data. |
| Provider-portable structured output | default tool output or `ToolOutput(...)` | Uses special output tools and works across most tool-capable models. |
| Provider-native JSON schema output | `NativeOutput(...)` | Uses a model's native structured-output mode; check provider compatibility first. |
| Schema injected into prompt | `PromptedOutput(...)` | Broad compatibility but weaker enforcement than tool/native output. |
| Text post-processing | `TextOutput(function)` | Lets plain text terminate the run, then applies a text output function. |
| External JSON schema | `StructuredDict(schema, name=..., description=...)` | Produces a `dict[str, Any]` subclass; app code remains responsible for defensive reads. |
| App-side final action | output function | Model supplies arguments; function returns the final run output and is not sent back to the model. |

## Marker Signatures

Verified public signatures in this repository generation:

- `TextOutput(output_function)` wraps a function accepting `str`, or `RunContext` plus `str`, to process plain text output.
- `ToolOutput(type_, *, name=None, description=None, max_retries=None, strict=None)` customizes one output tool.
- `NativeOutput(outputs, *, name=None, description=None, strict=None, template=None)` requests native structured output.
- `PromptedOutput(outputs, *, name=None, description=None, template=None)` requests JSON via schema instructions.
- `StructuredDict(json_schema, name=None, description=None)` creates a dict output type from an object JSON schema.

`NativeOutput` and `PromptedOutput` are mode markers for the whole structured output schema. Do not mix them with ordinary output types in the same list. If you need image output or deferred tool requests alongside them, keep those as explicit sibling output choices supported by the framework rather than embedding them inside the marker.

## Choosing an Output Mode

### Default Tool Output / `ToolOutput`

Start here for most applications that need structured data and provider portability. Pydantic AI registers output types or functions as special output tools. The model must call one of those output tools unless `str` or `TextOutput` also permits plain text.

Use `ToolOutput` when you need to tune the output tool:

```python
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput

class Invoice(BaseModel):
    invoice_id: str
    total: float

agent = Agent(
    'test',
    output_type=ToolOutput(
        Invoice,
        name='return_invoice',
        description='Return the extracted invoice fields.',
        max_retries=2,
        strict=True,
    ),
)
```

Important details:

- Each output type in a union/list becomes a separate output tool when using tool output, which keeps schemas simpler for the model.
- Non-object output schemas such as `int` or `list[str]` are wrapped internally so output tools still receive object parameters.
- `ToolOutput(max_retries=N)` overrides the per-tool retry limit for that output tool; otherwise the output side of the agent retry budget applies.
- `end_strategy` controls what happens when normal tools are called in parallel with output tools; see `../agent-core/` for run-loop behavior.

### `NativeOutput`

Use `NativeOutput` when a selected provider supports native structured outputs and your task benefits from provider-level JSON schema enforcement.

```python
from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput

class Person(BaseModel):
    name: str
    role: str

agent = Agent(
    'test',
    output_type=NativeOutput(Person, name='person', description='Extract one person.'),
)
```

Tradeoffs:

- Native structured output support is provider- and model-specific; route to `../models-and-providers/` before claiming compatibility.
- Some providers restrict native structured output when tools are present.
- `template` can inject schema instructions when a model profile requires or benefits from them; `template=False` disables that schema prompt.

### `PromptedOutput`

Use `PromptedOutput` for models that need schema instructions in the prompt or lack reliable tool/native structured output.

```python
from pydantic_ai import Agent, PromptedOutput

agent = Agent('test', output_type=PromptedOutput(Person, template='Return JSON matching: {schema}'))
```

Tradeoffs:

- It can work with broad model classes but relies on the model obeying prompt text.
- Pydantic AI still validates the parsed result and can ask the model to retry.
- `template=False` disables schema prompt injection and should only be used when another layer supplies equivalent instructions.

### `TextOutput`

Use `TextOutput` when the model should produce ordinary text but application code should transform that text into the final run output.

```python
from pydantic_ai import Agent, TextOutput

def split_words(text: str) -> list[str]:
    return text.split()

agent = Agent('test', output_type=TextOutput(split_words))
```

When streaming, `stream_text()` streams raw text and does not apply the `TextOutput` function. Use `stream_output()` when callers need the transformed value. Output functions and validators may be called repeatedly for partial streamed output; check `RunContext.partial_output` before side effects.

### `StructuredDict`

Use `StructuredDict` when the schema is dynamic or comes from another system and cannot conveniently be represented as a Pydantic model.

```python
from pydantic_ai import Agent, StructuredDict

Decision = StructuredDict(
    {
        'type': 'object',
        'properties': {'approved': {'type': 'boolean'}, 'reason': {'type': 'string'}},
        'required': ['approved', 'reason'],
    },
    name='Decision',
)
agent = Agent('test', output_type=Decision)
```

The JSON schema must be an object schema. Recursive `$defs` are not supported by `StructuredDict`; use a Pydantic model when recursion or stronger app-side validation is required.

## Output Functions

Output functions look like tools to the model, but they end the run. Their return value is the final `result.output`; it is not passed back to the model.

Use output functions when:

- arguments need extra validation or transformation that belongs outside the model;
- failures should raise `ModelRetry` to ask for corrected output;
- a router agent should hand off to another agent and return that result;
- each output alternative needs distinct validation logic, avoiding `isinstance` branching in a single output validator.

Do not also register the same callable as a normal tool with `@agent.tool` or `tools=[...]`. That gives the model two different meanings for one function and can cause it to call the wrong surface.

When an output function receives `RunContext`, `ctx.messages` includes the current run messages. If handing off to another agent, drop the final output-tool call before replaying history to the next agent:

```python
messages_for_handoff = ctx.messages[:-1]
next_result = await other_agent.run(query, message_history=messages_for_handoff)
```

## Unions, Lists, and Plain Text Fallback

`output_type=[A, B]` and `output_type=A | B` are functionally similar for runtime behavior. A list is often easier for static type checkers, especially when including marker instances such as `ToolOutput(...)`.

Be deliberate about `str`:

- Include `str` only when a plain text answer is an acceptable final result.
- Exclude `str` when structured extraction must not silently fall back to prose.
- `TextOutput(...)` also permits text termination, but the final value is the wrapped function's return.

Static typing caveats:

- For `output_type=Foo | Bar`, explicitly parameterize the agent, for example with `Agent` generic parameters for deps and output; some type checkers still need a local ignore at the `output_type` expression.
- Mypy may need help for list output choices and async output functions even when runtime behavior is correct.
- Prefer `output_type=[Foo, Bar]` when a list is enough and avoids a type-checker fight.

## Validation and Retries

Structured outputs and output function arguments are validated with Pydantic. Validation errors and `ModelRetry` can cause the model to retry within the output retry budget.

Use these levers:

- `validation_context=...` on `Agent(...)` to pass Pydantic validation context for both output validation and tool-argument validation. This context is not sent to the model.
- `@agent.output_validator` for final output validation that should return the same output type or raise `ModelRetry`.
- Output functions for per-output validation that can return a different final type and avoid a broad validator with many `isinstance` checks.
- `retries={'output': N}` at agent or run time to tune output retries; `ToolOutput(max_retries=N)` can override a specific output tool.

During streaming, output validators and output functions can see partial values. Use `ctx.partial_output` to skip side effects or complete-only checks until the final value.

## Schema Introspection

Use `agent.output_json_schema()` in tests, diagnostics, or smoke scripts to inspect the effective output schema without making a network call. This is useful for catching non-object schemas, unexpected `anyOf`, missing descriptions, and `StructuredDict` schema mistakes.
