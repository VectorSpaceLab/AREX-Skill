# Generative-programming API reference

Use this reference to check names and return contracts before writing code. The
contracts below are for Mellea `0.8.0.dev0` on Python 3.11+.

## Imports and session signatures

```python
from mellea import MelleaSession, generative, start_session
from mellea.stdlib.context import ChatContext, SimpleContext
from mellea.stdlib.functional import (
    aact, achat, ainstruct, aquery, atransform,
    act, chat, instruct, query, transform,
)
```

The main factory is:

```python
start_session(
    backend_name: Literal["ollama", "hf", "openai", "watsonx", "litellm"] = "ollama",
    model_id: str | ModelIdentifier = default_model,
    ctx: Context | None = None,
    *,
    context_type: Literal["simple", "chat"] | None = None,
    model_options: dict | None = None,
    plugins: list[Any] | None = None,
    **backend_kwargs: Any,
) -> MelleaSession
```

`ctx` and `context_type` are mutually exclusive. `context_type="simple"` creates
`SimpleContext`; `context_type="chat"` creates `ChatContext`. A requested
backend may require an optional package or service; route that setup to
`backends-and-models`.

`MelleaSession(backend: Backend, ctx: Context | None = None, *,
session_id: str | None = None)` wraps one backend and context. Its high-level
methods update `m.ctx` with the returned context. The context manager calls
cleanup and makes the session current for nested session-aware code.

## Session methods

The most-used synchronous methods are:

```python
m.instruct(
    description: str,
    *,
    requirements: list[Requirement | str] | None = None,
    icl_examples: list[str | CBlock] | None = None,
    grounding_context: dict[str, str | Span] | None = None,
    user_variables: dict[str, str] | None = None,
    prefix: str | CBlock | None = None,
    output_prefix: str | CBlock | None = None,
    strategy: SamplingStrategy | None = RejectionSamplingStrategy(loop_budget=2),
    return_sampling_results: bool = False,
    format: type[BaseModelSubclass] | None = None,
    model_options: dict | None = None,
    tool_calls: bool = False,
) -> ModelOutputThunk[str] | SamplingResult[str]

m.act(
    action: Component[S] | CBlock | ModelOutputThunk,
    *,
    requirements: list[Requirement] | None = None,
    strategy: SamplingStrategy | None = None,
    return_sampling_results: bool = False,
    format: type[BaseModelSubclass] | None = None,
    model_options: dict | None = None,
    tool_calls: bool = False,
) -> ModelOutputThunk[S] | SamplingResult[S]

m.chat(
    content: str,
    role: Message.Role = "user",
    *,
    images=None, audio=None, documents=None, user_variables=None,
    format: type[BaseModelSubclass] | None = None,
    model_options: dict | None = None,
    tool_calls: bool = False,
) -> Message
```

`m.query(obj, query, *, format=None, model_options=None, tool_calls=False)`
returns a computed `ModelOutputThunk`. `m.transform(obj, transformation, *,
format=None, model_options=None)` may return a thunk or the return value of a
selected exposed method when a tool call performs the transformation.

The async counterparts are `ainstruct`, `aact`, `achat`, `aquery`, and
`atransform`. They have the corresponding parameters plus `await_result=False`
where lazy evaluation is supported. `m.avalidate(...)` returns an awaitable list
of `ValidationResult` objects. An async method is not a reason to use
`ChatContext` concurrently: independent calls should use `SimpleContext`.

## Lower-level functional API

The functional API makes context and backend explicit:

```python
result, new_ctx = act(component, ctx, backend, strategy=None)
# `act` is synchronous and returns a computed thunk when sampling results are off.
result, new_ctx = await aact(
    component, ctx, backend, strategy=None, await_result=True
)
```

`act()` returns `(ComputedModelOutputThunk, Context)` when
`return_sampling_results=False`, or a `SamplingResult` when it is true.
`aact()` returns `(ModelOutputThunk, Context)` by default when no strategy is
used; `await_result=True` makes the thunk computed before return. Passing
`return_sampling_results=True` requires a strategy. Passing `requirements` to
`act`/`aact` without a strategy raises `ValueError`; requirements already
attached to an `Instruction` or generative stub still render into its prompt,
but are not validated without a strategy.

`instruct(description, ctx, backend, ...)` constructs an `Instruction` and then
uses `act`; `chat(content, ctx, backend, ...)` constructs a `Message`. These
functional methods return both the result and updated context. Use them when a
custom loop must thread context explicitly; otherwise use a session.

## Components

```python
from mellea.stdlib.components import Instruction, Message, SimpleComponent, mify
from mellea.stdlib.components.genstub import generative
from mellea.stdlib.components.react import ReactInitiator, ReactThought
```

- `Instruction(description=None, requirements=None, icl_examples=None,
  grounding_context=None, user_variables=None, prefix=None, output_prefix=None,
  images=None, audio=None)` is the full instruction component. Its
  `requirements` are resolved to `Requirement` objects. Jinja variables apply to
  string instruction fields; `output_prefix` is currently unsupported when
  variables are used.
- `SimpleComponent(**kwargs)` accepts strings, `CBlock`s, components, or thunks
  as named spans and renders them as a JSON representation.
- `Message(role, content, *, images=None, audio=None, documents=None,
  tool_calls=None, tool_call_id=None, thinking=None)` represents a chat turn.
- `ReactInitiator(goal, tools)` seeds a ReAct component and internally reserves
  the `final_answer` tool. `ReactThought()` represents a thinking step. Use the
  sibling `tools-and-agents` route for tool approval, execution, and loop policy.

## `@generative` and stubs

```python
@generative
def classify(text: str) -> Literal["yes", "no"]:
    """Classify the text."""
    ...

answer = classify(m, text="...")
```

The decorator returns a `SyncGenerativeStub` for a normal function and an
`AsyncGenerativeStub` for an `async def`. The generated output is parsed into
the declared return type. Call original function parameters by keyword; the
first positional argument is the session, or pass `context=...` and
`backend=...` explicitly. Reserved stub-control names include `m`, `context`,
`backend`, `requirements`, `precondition_requirements`, `strategy`, and
`model_options`; do not reuse them as decorated function parameter names.

A call accepts `precondition_requirements`, `requirements`, `strategy`, and
`model_options`. A failed precondition raises `PreconditionException` before
model generation and exposes validation results. Output requirements are only
forwarded into the repair loop when a strategy is supplied.

`mellea.stdlib.components.genslot` is a deprecated compatibility module. It
re-exports the genstub implementation and old aliases such as
`GenerativeSlot`; import from `genstub` and use `generative` for new code.

## Context and result objects

- `SimpleContext()` does not forward previous history to the model.
- `ChatContext(*, compactor=None, window_size=None,
  token_context_length_limit=None, model_id=None)` accumulates history.
  `compactor` and `window_size` are mutually exclusive. `add()` is persistent
  and returns a new context; it does not mutate the old one.
- `ctx.as_list()`, `ctx.view_for_generation()`, `ctx.last_output()`, and
  `ctx.last_turn()` are useful inspection methods.
- `m.reset()` creates a fresh context preserving context configuration;
  `m.clone()` branches from the current context and shares the backend.

`ModelOutputThunk` exposes `.value`, `.parsed_repr`, `.is_computed()`,
`await .avalue()`, and async iteration/`astream()` for a stream-enabled result.
A sync session returns a computed thunk. Async generation may return an
uncomputed thunk so callers can launch several requests before awaiting their
values.

## Streaming signature

```python
from mellea.stdlib.streaming import stream

streamer = await stream(
    action, backend, ctx,
    chunking=None | "word" | "sentence" | "paragraph" | ChunkingStrategy,
    requirements=None,
    validation_backend=None,
)
```

Consume a `Streamer` with `async with` and `async for`. It owns the lifecycle,
tracks `completed_normally` and `streaming_failures`, and performs final
validation after a natural end. A `Requirement.stream_validate()` result is
`PartialValidationResult("unknown" | "pass" | "fail")`; `"fail"` terminates
an invalid stream early. For simple display, do not use `stream()`; enable
`ModelOption.STREAM` and iterate one thunk.

## `mify` and object execution

```python
@mify(fields_include={"table"}, template="{{ table }}")
class TableView:
    table: str = "..."

answer = m.query(TableView(), "What does the table show?")
```

`mify` may be used as `@mify(...)`, `@mify` on a class, or `mify(obj, ...)` on
an instance. Important controls are `fields_include`, `fields_exclude`,
`funcs_include`, `funcs_exclude`, `template`, `template_order`, and
`stringify_func`. Include and exclude controls are intentionally narrow: expose
only the data and documented methods needed by the operation.
