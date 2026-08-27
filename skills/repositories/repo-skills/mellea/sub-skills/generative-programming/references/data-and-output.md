# Data, schemas, and output contracts

Read this reference whenever a task needs a typed value, Pydantic output, JSON,
requirements, repair diagnostics, or lazy/streaming result handling.

## Two structured-output paths

### Named typed function: `@generative`

Use a return annotation for reusable operations. Mellea generates a structured
response wrapper and parses the result before returning it.

```python
from pydantic import BaseModel
from mellea import generative

class Address(BaseModel):
    city: str
    country: str

class Company(BaseModel):
    name: str
    headquarters: Address

@generative
def extract_company(text: str) -> Company:
    """Extract the company name and headquarters from the text."""
    ...

company = extract_company(session, text="Acme is based in Springfield, USA.")
assert isinstance(company, Company)
print(company.headquarters.city)
```

`Literal["low", "medium", "high"]`, `list[str]`, nested Pydantic models, and
lists of models are useful return annotations. A successful call gives the
annotated Python value, not a JSON string. If parsing cannot succeed after the
active retry behavior, handle `ComponentParseError` or the backend exception as
an operational failure.

### Dynamic prompt: `format=Model`

Use `format=` on `m.instruct`, `m.act`, or `m.chat` when the prompt is assembled
at runtime or includes grounding/user variables.

```python
from pydantic import BaseModel

class Names(BaseModel):
    names: list[str]

raw_thunk = m.instruct(
    "Extract every person's name from the supplied document.",
    grounding_context={"document": text},
    format=Names,
)
parsed = Names.model_validate_json(str(raw_thunk))
```

The `format=` path returns a thunk whose `.value`/`str(...)` is a JSON string.
Do not use `cast(Names, raw_thunk.value)`. Parse explicitly with
`Names.model_validate_json(str(raw_thunk))`. When
`return_sampling_results=True`, parse `str(result.result)` after checking
`result.success`.

Schema-constrained decoding depends on backend support. A dummy backend is
intentionally not a formatter backend and rejects `format=`; use a backend
that supports constrained decoding for live structured generation, or test
formatting/validation at the component boundary with a fake response.

## Shape versus meaning

A schema proves that fields and primitive types are present; it does not prove
that the extracted facts are correct. Combine layers:

1. **Type/schema:** Pydantic, `Literal`, or typed containers.
2. **Deterministic semantics:** a `Requirement` with `simple_validate` that
   parses the output and checks a property such as minimum list length.
3. **Model-judged semantics:** a natural-language requirement or a dedicated
   evaluator when groundedness or style cannot be checked cheaply.

For dynamic JSON output, a validation-only requirement can avoid putting an
implementation detail into the prompt:

```python
from mellea.stdlib.requirements import check, simple_validate
from mellea.stdlib.sampling import RejectionSamplingStrategy

class Names(BaseModel):
    names: list[str]

def at_least_two(value: str) -> tuple[bool, str]:
    try:
        parsed = Names.model_validate_json(value)
    except Exception:
        return False, "Expected JSON matching Names."
    if len(parsed.names) >= 2:
        return True, ""
    return False, f"Found {len(parsed.names)} names; expected at least 2."

attempts = m.instruct(
    "Extract the names from the document.",
    format=Names,
    requirements=[check(None, validation_fn=simple_validate(at_least_two))],
    strategy=RejectionSamplingStrategy(loop_budget=4),
    return_sampling_results=True,
)
if attempts.success:
    names = Names.model_validate_json(str(attempts.result)).names
else:
    # Inspect attempts.sample_validations and choose an explicit fallback.
    names = []
```

`check(None, ...)` creates a check-only requirement. A normal `req("...")`
(or a plain string requirement) is both rendered as guidance and validated by
the strategy. `Requirement.validate(...)` returns `ValidationResult(result,
reason=...)`; preserve the reason because it is the repair feedback.

## Repair and sampling result contracts

`instruct` has a default `RejectionSamplingStrategy(loop_budget=2)`. Explicitly
set a strategy when the retry budget is part of the application contract:

```python
from mellea.stdlib.requirements import req, simple_validate
from mellea.stdlib.sampling import RejectionSamplingStrategy

lowercase = req(
    "Use lowercase text.",
    validation_fn=simple_validate(
        lambda value: (value == value.lower(), "Output is not lowercase.")
    ),
)
result = m.instruct(
    "Write a short status message.",
    requirements=[lowercase],
    strategy=RejectionSamplingStrategy(loop_budget=3),
    return_sampling_results=True,
)
if result.success:
    text = str(result.result)
else:
    for validations in result.sample_validations:
        for requirement, validation in validations:
            if not validation:
                print(requirement.description, validation.reason)
    fallback = str(result.sample_generations[0].value) if result.sample_generations else ""
```

`SamplingResult.success=False` is an expected exhausted-budget outcome, not a
Python exception. Decide whether to reject, relax/retry, escalate to another
provider, or return a clearly marked best effort. Never silently claim that a
failed result met the requirement.

For `@generative` output requirements, the parsed model is returned on success;
requirements operate on the generated structured representation during the
repair loop. For a precondition, use a deterministic validator over the bound
argument representation and catch `PreconditionException`; no model call is
made when the precondition fails.

## Thunks and laziness

A `ModelOutputThunk` is a handle for raw output plus parsed/tool metadata.
Important states and operations:

- `.is_computed()` tells whether generation and parsing have completed.
- `.value` reads the computed raw string; `.parsed_repr` is the typed/component
  representation when one exists.
- `await thunk.avalue()` resolves a lazy result and returns its string value.
- `await thunk.astream()` returns the next new delta when streaming is enabled;
  once complete, the final call returns the complete value.
- `async with thunk: async for delta in thunk:` is the preferred iterator form;
  leaving early releases/cancels the underlying generation.

A synchronous call is computed before it returns. An async call can return a
lazy thunk when no sampling strategy forces a final result and
`await_result=False`. Use `await_result=True` when downstream code needs a
fully resolved result immediately; leave it false when launching independent
requests or consuming a stream.

Only one coroutine may read a given thunk's stream. Do not call `astream()` and
iterate the same thunk from separate consumers.

## Streaming validation contract

`stream(action, backend, ctx, chunking=..., requirements=...)` returns a
`Streamer` after awaiting its creation. The stream validator is tri-state:

| Result | Meaning |
|---|---|
| `PartialValidationResult("unknown")` | insufficient evidence yet |
| `PartialValidationResult("pass")` | this chunk is acceptable so far |
| `PartialValidationResult("fail", reason="...")` | stop immediately and record failure |

A natural stream end still runs full `Requirement.validate` for requirements
that did not fail incrementally. A `pass` is not a replacement for final
validation. Inspect `streamer.completed_normally` and
`streamer.streaming_failures` after the loop.

## Testing output deterministically

Use a fake or canned backend to test control flow without a network or model.
Assert `isinstance`, schema validation, exact requirement reasons, retry count,
`SamplingResult.success`, context immutability, thunk computation state, and
stream terminal state. Keep model-dependent content assertions in a separately
marked qualitative test. The sibling `sampling-and-evaluation` route owns
large-scale or judge-model evaluation.
