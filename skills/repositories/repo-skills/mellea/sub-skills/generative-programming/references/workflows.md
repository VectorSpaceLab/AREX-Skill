# Generative-programming workflows

These recipes are provider-neutral. Replace `start_session()` with an explicit
backend only after reading the sibling `backends-and-models` route. The examples
show API shape and validation boundaries; model output is not deterministic.

## 1. Start a session and choose context

For independent extraction/classification calls, use the default stateless
context:

```python
from mellea import start_session

with start_session() as m:
    one = m.instruct("Classify this document.")
    two = m.instruct("Classify that document.")
```

For a conversation, opt in to history:

```python
from mellea import start_session
from mellea.stdlib.context import ChatContext

with start_session(ctx=ChatContext(window_size=10)) as m:
    m.chat("The project codename is Orion.")
    answer = m.chat("What is the codename?")
    print(str(answer))
```

`ChatContext` retains turns and may window or compact them. `SimpleContext`
forwards no prior history. `m.reset()` clears history while retaining the
session's backend/configuration. `m.clone()` creates a branch from the current
context, useful for independent continuations.

## 2. Define a reusable typed operation

Use a conventional Python signature and docstring rather than writing a prompt
inside the body:

```python
from typing import Literal
from mellea import generative, start_session

@generative
def classify_sentiment(text: str) -> Literal["positive", "negative", "mixed"]:
    """Classify the sentiment of the supplied text."""
    ...

with start_session() as m:
    sentiment = classify_sentiment(m, text="Support was excellent, but setup was slow.")
assert sentiment in {"positive", "negative", "mixed"}
```

The first argument is the session. Pass all decorated function arguments by
keyword. For dependency injection, use the alternative call shape
`classify_sentiment(context=ctx, backend=backend, text=...)`, which returns a
`(value, new_context)` pair for a synchronous stub.

For nested output:

```python
from pydantic import BaseModel
from mellea import generative

class Finding(BaseModel):
    label: str
    evidence: str

class Report(BaseModel):
    title: str
    findings: list[Finding]

@generative
def extract_report(document: str) -> Report:
    """Extract a title and evidence-backed findings from the document."""
    ...

report = extract_report(m, document=document)
for finding in report.findings:
    print(finding.label, finding.evidence)
```

Use a Pydantic schema for shape and a requirement for semantic rules such as a
minimum finding count or allowed labels.

## 3. Dynamic instruction with grounding and repair

Use `instruct` when the description, variables, or grounding documents are
assembled at runtime:

```python
from mellea.stdlib.requirements import req, simple_validate
from mellea.stdlib.sampling import RejectionSamplingStrategy

short = req(
    "Use at most 40 words.",
    validation_fn=simple_validate(
        lambda text: (len(text.split()) <= 40, "Output exceeds 40 words.")
    ),
)
with start_session() as m:
    result = m.instruct(
        "Answer the question using only the supplied document: {{question}}",
        user_variables={"question": question},
        grounding_context={"document": document},
        requirements=[short, "State uncertainty when the document is insufficient."],
        strategy=RejectionSamplingStrategy(loop_budget=3),
        return_sampling_results=True,
    )
if result.success:
    answer = str(result.result)
else:
    # Inspect result.sample_validations before selecting a fallback.
    answer = str(result.sample_generations[0].value) if result.sample_generations else ""
```

A plain string requirement is rendered as guidance and checked by the strategy.
Use `simple_validate` for deterministic checks and include a useful failure
reason so the repair attempt knows what to change.

## 4. Structured output with a dynamic prompt

```python
from pydantic import BaseModel

class ActionItems(BaseModel):
    owners: list[str]
    due_dates: list[str]

with start_session() as m:
    raw = m.instruct(
        "Extract action items from the meeting notes.",
        grounding_context={"notes": notes},
        format=ActionItems,
    )
    items = ActionItems.model_validate_json(str(raw))
```

`format=...` produces JSON text in the thunk. Use `@generative` when the
operation has a stable name/signature and direct typed return is more useful.
Use a backend that supports the formatter for live constrained decoding; do not
try to use `format` with the dummy backend.

## 5. Compose typed stages

Keep each stage small and gate nonsensical compositions with a typed guard:

```python
from typing import Literal
from mellea import generative

@generative
def summarize(transcript: str) -> str:
    """Summarize the transcript in a concise paragraph."""
    ...

@generative
def has_actionable_risk(summary: str) -> Literal["yes", "no"]:
    """Decide whether the summary contains an actionable business risk."""
    ...

@generative
def propose_mitigation(summary: str) -> str:
    """Propose mitigation for risks in the summary."""
    ...

summary = summarize(m, transcript=transcript)
if has_actionable_risk(m, summary=summary) == "yes":
    mitigation = propose_mitigation(m, summary=summary)
```

Use ordinary Python for branching, data normalization, and deterministic
checks. Add requirements at each boundary rather than allowing uncertainty to
compound through a long chain.

## 6. Async, lazy computation, and concurrency

Every session generation has an async form. For independent work, use
`SimpleContext` and resolve in parallel:

```python
import asyncio
from mellea import start_session
from mellea.backends import ModelOption

async def run(topics: list[str]) -> list[str]:
    m = start_session()
    thunks = [
        await m.ainstruct(
            "Write one sentence about {{topic}}.",
            user_variables={"topic": topic},
            strategy=None,
        )
        for topic in topics
    ]
    return await asyncio.gather(*(thunk.avalue() for thunk in thunks))

answers = asyncio.run(run(["rain", "snow", "wind"]))
```

`strategy=None` plus `await_result=False` allows a lazy thunk. Set
`await_result=True` on `aact`/`ainstruct` when the call must be resolved before
return. A non-`None` sampling strategy generally requires computation to inspect
validation and retry.

With `ChatContext`, never launch overlapping requests that depend on shared
history. Await the first call before the next:

```python
async def sequential_chat():
    from mellea import start_session
    from mellea.stdlib.context import ChatContext
    m = start_session(ctx=ChatContext())
    await m.achat("Remember the number 7.")
    response = await m.achat("What number should you remember?")
    return str(response)
```

## 7. Incremental streaming

For display-only streaming:

```python
import asyncio
from mellea import start_session
from mellea.backends import ModelOption

async def display():
    m = start_session()
    thunk = await m.ainstruct(
        "Write a short explanation of lazy computation.",
        strategy=None,
        model_options={ModelOption.STREAM: True},
    )
    async with thunk:
        async for delta in thunk:
            print(delta, end="", flush=True)
    print()

asyncio.run(display())
```

Use one reader. Configure `ModelOption.STREAM_TIMEOUT` for slow or remote
backends; `None` disables the timeout. An early `break` or exception should be
inside `async with` so generation is released.

For per-chunk enforcement, construct an `Instruction`, a `Requirement` that
implements `stream_validate`, and call `stdlib.streaming.stream(...)` with
`chunking="word"`, `"sentence"`, or `"paragraph"`. Consume the returned
`Streamer` with `async with`; inspect `streaming_failures` after early exit.

## 8. Components and explicit `act`

Use components when a program needs explicit composition or dependency
injection:

```python
from mellea.stdlib.components import Instruction, SimpleComponent

instruction = Instruction(
    "Summarize the supplied text.",
    grounding_context={"text": source_text},
)
result = m.act(instruction)

parts = SimpleComponent(
    task="classify",
    input=source_text,
)
result = m.act(parts)
```

`Instruction` owns requirements, variables, grounding, examples, and media.
`SimpleComponent` accepts named string/component spans. `Message` is the
component for a conversational turn. For explicit lower-level loops, use
`act`/`aact` with `(context, backend)` and thread the returned context.

`react(goal, context=ChatContext(), backend=..., tools=..., loop_budget=...)`
owns a tool-using ReAct loop; route tool registration, execution approval, and
agent policy to `tools-and-agents` rather than expanding this route.

## 9. Mify an existing object

Expose a narrow representation and documented methods:

```python
from mellea.stdlib.components import mify

@mify(fields_include={"table"}, template="{{ table }}")
class SalesView:
    table = "North: 250\nSouth: 80"

with start_session() as m:
    answer = m.query(SalesView(), "Which region has higher sales?")
```

Use `mify(obj, stringify_func=...)` when the class cannot be changed. Use
`funcs_include` for methods intended as model tools, and `m.transform` only when
the model must select an exposed method. Direct Python calls are safer and
cheaper for deterministic transformations.

## 10. Safe tests without a real model

Separate deterministic checks from qualitative model checks. For a fake backend,
return canned `ModelOutputThunk` values and attach a generation log if testing
the full `act` path; or patch the backend/session boundary and assert forwarded
components/options. Test:

- `@generative` function metadata and keyword-only original arguments.
- Pydantic schema parsing and nested fields.
- precondition failure and `PreconditionException.validation` reasons.
- `SamplingResult.success`, retry count, and validation feedback.
- `SimpleContext` isolation versus `ChatContext` history.
- lazy thunk `.is_computed()` before/after `.avalue()`.
- one-reader streaming and terminal failure state.

Avoid using a real provider for API tests. Provider-specific smoke and model
quality checks belong to the backend/evaluation routes.
