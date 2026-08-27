# Core Primitive Troubleshooting

Use this guide for failure modes owned by the `core-primitives` sub-skill.

## Message or Content-Block Translation Mismatches

Symptoms:

- Provider payload has the wrong content block shape.
- Image/file blocks lose data fields or source-type information.
- Tool calls or tool-call chunks fail to round-trip through message serialization.
- `merge_message_runs`, `filter_messages`, or conversion utilities unexpectedly mutate input messages.

Checks:

- Confirm whether the data belongs in chat message content blocks or retrieval `Document` objects.
- Preserve standard block `type` discriminators and keep provider-only fields in `extras` or `NonStandardContentBlock` when no standard field exists.
- Test both normalized `langchain_core.messages` objects and provider-shaped conversion output.
- Include round-trip tests using `message_to_dict`, `messages_to_dict`, and `messages_from_dict` when serialization compatibility is involved.
- Assert original message lists are unchanged after conversion, filtering, or merging unless mutation is explicitly documented.

Common fix pattern:

- Normalize early to standard content blocks.
- Convert late at provider boundary.
- Keep backward-compatible handling for older block shapes if existing tests cover them.

## Runnable Sync, Async, Stream, or Batch Misuse

Symptoms:

- `ainvoke` blocks the event loop or loses callbacks.
- `batch` returns outputs in the wrong order.
- `stream` yields a final object instead of chunks, or `astream` does not mirror sync streaming semantics.
- Child runnable calls drop `tags`, `metadata`, callbacks, run IDs, or configurable fields.

Checks:

- Ensure custom runnable classes implement `invoke` and only override async/batch/stream methods when they provide native behavior.
- Pass `RunnableConfig` through nested invocations; use existing helpers rather than hand-rolling config dictionaries.
- Preserve input order for batch outputs unless the API explicitly documents otherwise.
- Add tests for `invoke`, `ainvoke`, `batch`, `abatch`, `stream`, `astream`, and config propagation for custom primitives.
- Watch deprecated event/log paths; warnings can be expected while compatibility tests remain.

Common fix pattern:

- Implement a small sync core, then wrap async with `run_in_executor` only when native async is not available.
- For streaming, yield chunks from the underlying implementation and use existing chunk merge helpers in tests to verify final equivalence.

## Pydantic Model and Schema Issues

Symptoms:

- `model_json_schema()` differs unexpectedly.
- Tool or prompt input schemas omit fields or include internal callback/run-manager parameters.
- Pydantic v1 and v2 models are mixed in unsupported ways.
- Serializable objects include excluded fields or fail on deprecated serialization attributes.

Checks:

- Use Pydantic v2 `BaseModel`, `Field`, validators, and `ConfigDict` for new code.
- Preserve existing compatibility branches for Pydantic v1 where the package already supports them.
- For tool schemas, keep filtered arguments such as callbacks/run managers out of user-facing schemas.
- For prompts, validate reserved `stop`, missing variables, partial overlap, and optional variables.
- For serializable classes, prefer `is_lc_serializable`, `get_lc_namespace`, `lc_secrets`, and `lc_attributes`; do not reintroduce deprecated `lc_namespace` or `lc_serializable` attributes.

Common fix pattern:

- Add focused schema assertions rather than broad snapshots when possible.
- Normalize schema differences only where existing test utilities already do so.

## Tool Schema or Docstring Problems

Symptoms:

- `@tool` raises `ValueError` for invalid docstrings.
- Tool args schema has no parameter descriptions.
- A runnable cannot be converted to a tool.
- Tool message content/artifact format errors occur at runtime.

Checks:

- Ensure every tool function parameter has a type hint.
- When `parse_docstring=True`, ensure Google-style `Args:` entries exactly match function parameter names.
- Provide `description` explicitly when no usable function docstring or schema description exists.
- Pass a string name when converting a `Runnable` to a tool.
- For `response_format="content_and_artifact"`, return a two-item tuple matching content and artifact.
- Keep injected args and callback/run-manager parameters out of public schemas.

Common fix pattern:

- Prefer explicit `args_schema` for complex tools.
- Use `Annotated[..., "description"]` or Pydantic fields for parameter descriptions when docstring parsing is too brittle.

## Optional Dependency Import Failures

Symptoms:

- Importing a public core surface fails because an optional package is missing.
- A test unexpectedly requires a provider integration, vector backend, or graph-rendering package.
- Lazy imports mask the actual missing dependency until attribute access.

Checks:

- Core public imports should avoid importing optional heavy integrations at module import time.
- Use lazy imports or local imports for optional features.
- Unit tests should use fakes or in-memory primitives when possible.
- Skip tests requiring unavailable optional packages with an explicit reason rather than installing through non-`uv` tooling.

Common fix pattern:

- Keep the base interface importable with only core dependencies.
- Move optional dependency checks to the method or feature boundary and raise an actionable error message.

## Deprecation Warnings and API Compatibility

Symptoms:

- Tests fail under strict warning settings.
- Deprecated methods no longer emit expected `LangChainDeprecationWarning`.
- A public signature change breaks older usage patterns.
- `asdict`, `dict`, or serialization compatibility tests fail.

Checks:

- Use the package deprecation helpers rather than raw `warnings.warn` for public LangChain APIs.
- Include since/removal/alternative details when known and preserve warning stack levels.
- Keep compatibility wrappers until the documented removal version.
- Do not change public argument names or positions without explicit migration handling.
- Add tests for both the new path and the deprecated path when maintaining compatibility.

Common fix pattern:

- Add the new API first, keep the old API as a delegating wrapper with a warning, and update tests to assert both behavior and warning category.

## Serialization Compatibility

Symptoms:

- `dumpd`, `dumps`, or `loads` changes identifiers or leaks secrets.
- Deserialization cannot find a moved class.
- Serialized constructor kwargs no longer match the class constructor.

Checks:

- Keep `get_lc_namespace` stable for public serializable classes unless a mapping migration exists.
- Ensure `lc_attributes` names are accepted by the constructor or otherwise intentionally handled.
- Use `lc_secrets` to replace secret values with secret references.
- Confirm non-serializable classes return a not-implemented serialized shape instead of pretending to be serializable.

Common fix pattern:

- Preserve old IDs with mapping, add regression tests for old serialized payloads, and never include live credential values in expected serialized output.
