# Generative-programming troubleshooting

Diagnose from the first failing boundary. Do not hide provider, credential, or
schema failures behind a generic retry.

## Installation and imports

**Symptom:** `ModuleNotFoundError: mellea`, `pydantic`, or an optional backend.

**Recovery:** install Mellea with Python 3.11 or newer using the project/package
manager's documented command. Install only the provider extra owned by
`backends-and-models`; do not assume the default Ollama route makes every
backend importable. Verify with:

```bash
python -c "import mellea; print(mellea.__version__)"
python sub-skills/generative-programming/scripts/inspect_api.py
```

**Symptom:** `genslot` emits a deprecation warning or an old slot class cannot
be imported.

**Recovery:** migrate imports from `mellea.stdlib.components.genslot` to
`mellea.stdlib.components.genstub` and use `generative`,
`GenerativeStub`, `SyncGenerativeStub`, or `AsyncGenerativeStub` as appropriate.
The compatibility shim is transitional.

## Session and context errors

**Symptom:** the backend cannot connect on the first call.

**Likely causes:** the selected provider package is absent, a local model
server is stopped, model identifier is unavailable, or credentials/base URL are
wrong. Run provider-specific setup through `backends-and-models`. Creating a
session does not prove that generation is reachable; probe the first call and
handle its exception.

**Symptom:** `ValueError` says both `ctx` and `context_type` were supplied.

**Recovery:** pass one policy only:
`start_session(ctx=ChatContext())` or `start_session(context_type="chat")`.
Use `context_type="simple"` for the default independent-call behavior.

**Symptom:** a follow-up chat ignores earlier turns.

**Cause:** `SimpleContext` is stateless by design.

**Recovery:** create the session with `ChatContext()` or
`context_type="chat"`; inspect `m.ctx.as_list()` and `m.ctx.last_turn()`. For
long histories use `window_size`, an explicit compactor, or `m.reset()` at a
natural boundary.

**Symptom:** concurrent async calls see stale or mixed chat history.

**Cause:** overlapping requests share `ChatContext`.

**Recovery:** use `SimpleContext` for independent concurrency, or await each
`achat`/`ainstruct` before starting the next when history is semantically
shared. Use `m.clone()` for independent branches from one known history.

## Typed output and parsing

**Symptom:** `ComponentParseError`, Pydantic `ValidationError`, or a `Literal`
value is rejected.

**Checks:**

1. Confirm the return annotation/schema is correct and not contradictory.
2. Make the function name/docstring explicit about fields and allowed values.
3. Check that the backend supports the requested formatter/constrained decoding.
4. Set an explicit repair strategy and inspect failure reasons.
5. Escalate provider/model capability only after ruling out a schema or prompt
   error.

**Symptom:** code expects `format=Model` to return a model instance, but receives
JSON text.

**Recovery:** use `Model.model_validate_json(str(thunk))`. With a
`SamplingResult`, check `.success` and parse `str(result.result)`. Do not
`cast()` a string to the model.

**Symptom:** `DummyBackend` rejects `format=`.

**Cause:** its documented purpose is predetermined raw responses and it does
not implement constrained decoding.

**Recovery:** test schema parsing separately or use a fake formatter-capable
backend in a unit test. Do not make the dummy backend a live structured-output
provider.

**Symptom:** nested Pydantic output has correct shape but wrong facts.

**Cause:** schema validity is not semantic correctness.

**Recovery:** add deterministic validators for cheap invariants, grounded
requirements for source adherence, and a separately owned evaluator for
quality. Do not turn a qualitative assertion into an unconditional unit test.

## Requirements, preconditions, and retries

**Symptom:** `ValueError` from `act`/`aact` when requirements are supplied.

**Cause:** requirements passed through the `requirements=` argument need a
`SamplingStrategy`; otherwise they cannot be validated.

**Recovery:** pass `strategy=RejectionSamplingStrategy(loop_budget=N)`, or attach
requirements to an `Instruction` only when prompt guidance without validation
is intentional. `instruct`/`ainstruct` handle the distinction internally.

**Symptom:** `return_sampling_results=True` raises `ValueError`.

**Recovery:** supply a strategy. On return, inspect `SamplingResult.success`,
`sample_generations`, and `sample_validations`; an exhausted budget is an
expected result, not proof that generation succeeded.

**Symptom:** retries never pass.

**Checks:**

- The validator returns a real `bool` or `(bool, reason)` via
  `simple_validate`.
- The requirement is not contradictory with the instruction/schema.
- The failure reason is specific enough to be useful as repair feedback.
- The loop budget is finite and appropriate for cost/latency.
- The model can express the required output format.

Use a fallback, a relaxed contract, or provider escalation deliberately. Do not
silently return an invalid sample.

**Symptom:** `PreconditionException` occurs before a model call.

**Cause:** a `precondition_requirements` validator rejected the bound decorated
function arguments.

**Recovery:** catch the exception, inspect `.validation` and each
`ValidationResult.reason`, then sanitize/reject the input. Preconditions are
for fail-fast input contracts and do not retry generation.

**Symptom:** a generative stub's requirements appear in the prompt but do not
retry.

**Cause:** output requirements are only forwarded to the repair loop when a
non-`None` strategy is supplied.

**Recovery:** pass an explicit strategy. Keep check-only requirements separate
from natural-language prompt guidance when needed.

## Async, lazy, and streaming failures

**Symptom:** downstream code reads `.value` before async generation completes.

**Recovery:** use `await thunk.avalue()` or set `await_result=True` on the async
operation. Test `.is_computed()` before relying on `.value`.

**Symptom:** stream hangs or raises `TimeoutError`.

**Likely causes:** slow first token, slow CPU inference, dead provider stream,
or an unsuitable timeout.

**Recovery:** set `ModelOption.STREAM_TIMEOUT` to a suitable finite value; use
`None` only when unbounded waiting is intentional. Check provider connectivity
and model load time before increasing the timeout indefinitely.

**Symptom:** stream deltas are duplicated, missing, or a second iterator fails.

**Cause:** a thunk supports one reader and each `astream()` call advances the
same cursor.

**Recovery:** use exactly one `async for` consumer or one `astream()` loop. Keep
`async with thunk` around consumption so `break`/exceptions release the stream.

**Symptom:** early validation does not stop invalid content.

**Checks:** use `stdlib.streaming.stream`, not only `ModelOption.STREAM`; pass a
Requirement implementing `stream_validate`; choose a chunking strategy that
creates meaningful units. Return `PartialValidationResult("fail", reason=...)`
for early exit. Remember that `"pass"`/`"unknown"` still receive final full
validation after a natural end.

## Components, MObjects, and tools

**Symptom:** `SimpleComponent` asserts that a value is not a span.

**Recovery:** pass strings, `CBlock`, `Component`, or `ModelOutputThunk` values
as keyword fields. Normalize arbitrary Python objects first; use `mify` for a
controlled object representation.

**Symptom:** `m.query` exposes too much object state or the model cannot render
an MObject.

**Recovery:** use `fields_include`/`fields_exclude`, a `template`, or a
`stringify_func`; verify the object's rendered representation before generation.
For methods, use `funcs_include` and require docstrings. Use direct Python calls
for deterministic transforms.

**Symptom:** `m.transform` chooses the wrong method or returns a raw thunk.

**Recovery:** expose fewer methods, make method docstrings distinct, inspect
returned tool calls, and route tool execution/approval issues to
`tools-and-agents`. `transform` is not a replacement for an explicit safe tool
loop.

## Testing and quality gates

**Symptom:** tests flake across models or temperatures.

**Recovery:** in the marker-free unit tier, assert type, schema, allowed values,
context behavior, validation state, and option forwarding. Mark expected content
quality checks qualitative. Patch or inject a deterministic fake backend and
avoid credentials, local servers, downloads, and model weights.

**Symptom:** a fake backend fails inside the full `act` path with a missing
`GenerateLog` or incompatible output metadata.

**Recovery:** make the test double satisfy the public backend result contract,
including a generation log and a `ModelOutputThunk`/updated context, or patch
at the backend boundary. Do not weaken production assertions to accommodate an
incomplete fake.

For large sampling studies, judge-model tests, majority voting, or CLI
`m eval`, route to `sampling-and-evaluation`. For provider import, model IDs,
credentials, and backend-specific streaming, route to `backends-and-models`.
