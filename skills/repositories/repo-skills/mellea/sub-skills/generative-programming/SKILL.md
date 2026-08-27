---
name: generative-programming
description: "Use Mellea 0.8.0.dev0 to build typed, composable generative
  programs with sessions, contexts, validation repair, asynchronous thunks,
  streaming, and legacy MObjects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Generative programming

Use this route when the task mentions a typed LLM function, structured output,
`@generative`, a generative stub, `start_session`, `MelleaSession`, context,
validation retry, lazy computation, streaming, `mify`, or legacy integration.
This route covers the execution layer; it does not choose a provider, configure
credentials, design tool policies, or run evaluations.

## Read the smallest useful reference

- Public classes, signatures, return contracts, and imports: [api-reference.md](references/api-reference.md).
- End-to-end recipes and sync/async/streaming decisions: [workflows.md](references/workflows.md).
- Typed schemas, formatter output, thunks, and validation results: [data-and-output.md](references/data-and-output.md).
- Symptoms, likely causes, and recovery actions: [troubleshooting.md](references/troubleshooting.md).

## Choose the operating level

1. Prefer `@generative` for a named, reusable function with stable typed inputs
   and outputs.
2. Prefer `MelleaSession.instruct()` for a dynamic prompt, grounding context,
   user variables, requirements, or `format=...`.
3. Prefer `chat()` only for unvalidated conversational turns. Use
   `ChatContext` when history must persist; the default `SimpleContext` isolates
   calls.
4. Use `act()`/`aact()` when you already have an explicit Component such as
   `Instruction`, `SimpleComponent`, `Message`, a generative stub, or an MObject.
5. Use `stream()` only when partial output and early per-chunk validation are
   requirements. For ordinary incremental output, use `ModelOption.STREAM` and
   a single reader of the returned thunk.

Provider/model construction belongs to the sibling `backends-and-models`
route. Tool definitions, tool execution, ReAct loops, and safety policy belong
to `tools-and-agents`. Sampling presets and evaluator/LLM-judge workflows belong
to `sampling-and-evaluation`.

## Minimal typed program

```python
from pydantic import BaseModel
from mellea import generative, start_session

class Person(BaseModel):
    name: str
    age: int

@generative
def extract_person(text: str) -> Person:
    """Extract the person's name and age from the text."""
    ...

with start_session() as m:
    person = extract_person(m, text="Alice is 31 years old.")
assert isinstance(person, Person)
```

The decorated function body is a declaration. The function name, signature,
docstring, annotations, and keyword arguments become the generation contract.
The session is the first call argument; original function arguments should be
passed by keyword. An async decorated function returns an awaitable parsed
result.

## Required checkpoints

- **Before generation:** choose the context policy, validate untrusted inputs
  with `precondition_requirements` where applicable, and verify the provider
  route has the required optional dependency/service.
- **At the output boundary:** use Pydantic/`Literal` annotations for shape;
  use `requirements` and deterministic `simple_validate` functions for semantic
  constraints; do not confuse a schema-valid value with a task-correct value.
- **On repair:** provide a `SamplingStrategy`, normally
  `RejectionSamplingStrategy(loop_budget=N)`, whenever requirements must be
  evaluated and retried. Set `return_sampling_results=True` when fallback or
  per-attempt diagnostics matter.
- **Before concurrency:** use `SimpleContext` for independent concurrent calls;
  with `ChatContext`, await one call fully before starting the next.
- **Before streaming:** select one consumer per thunk, use `async with` around
  iterators, and decide whether a final full-output validation or per-chunk
  `stream()` validation is needed.

## Context and lifecycle quick choice

```python
from mellea import start_session
from mellea.stdlib.context import ChatContext

with start_session(ctx=ChatContext(window_size=10)) as m:
    m.chat("Remember that the project codename is Orion.")
    answer = m.chat("What is the codename?")
    print(str(answer))
```

`start_session(...)` returns a `MelleaSession` and can be used directly or as a
context manager. The manager makes the session available to nested convenience
code and performs cleanup. Use `m.reset()` to preserve backend configuration
while clearing history, `m.clone()` to branch a conversation, and
`m.ctx.last_output()`/`m.ctx.last_turn()` for inspection.

## Composition and legacy surface

Compose typed functions with ordinary Python, passing one parsed result into the
next. Use `Instruction` for a full prompt component, `SimpleComponent(**parts)`
for named ad-hoc spans, `Message` for chat turns, and `m.act(component)` when a
component must be executed explicitly. `@generative` is the canonical name;
`mellea.stdlib.components.genslot` is a deprecated compatibility shim whose
slot aliases should be migrated to `genstub`.

Use `@mify` or `mify(obj, ...)` to expose selected fields and documented methods
of an existing object. Then use `m.query(obj, question)` or
`m.transform(obj, instruction)`. Expose only the fields/functions needed by the
model; direct Python methods remain preferable when no generation is needed.

## Verification posture

Keep unit tests deterministic: assert types, schema fields, allowed `Literal`
values, validator reasons, context isolation, thunk state, and exact option
forwarding. Mark model-quality assertions as qualitative. Use a fake or dummy
backend for API/control-flow tests; never make a real model call merely to test
routing, parsing, or retry bookkeeping. For a safe installed-package signature
check, run:

```bash
cd sub-skills/generative-programming
python scripts/inspect_api.py --help
python scripts/inspect_api.py
```

If the task crosses into backend setup, tool execution, sampling/evaluation, or
serving, hand off rather than duplicating those routes.
