# Troubleshooting Outputs and Messages

Use this reference when structured output, output functions, multimodal content, or replayed message history behaves unexpectedly.

## Structured Output Returns Plain Text

Symptoms:

- `result.output` is a `str` when app code expected a Pydantic model.
- A model answers in prose instead of calling the output tool.

Checks:

- Remove `str` from `output_type` unless plain text is intentionally allowed.
- Replace `output_type=[MyModel, str]` with `output_type=MyModel` or `ToolOutput(MyModel)` when extraction must be structured.
- If using `TextOutput(...)`, remember text is still an accepted final response; the wrapped function changes the returned value but does not force JSON.
- Confirm the selected model supports the chosen output mode; route provider-native questions to `../models-and-providers/`.

## `NativeOutput` or `PromptedOutput` Fails at Construction

Symptoms:

- User errors such as ``NativeOutput` must be the only output type.``
- User errors about `DeferredToolRequests` or `BinaryImage` inside a native/prompted marker.

Checks:

- Use `NativeOutput([A, B])` or `PromptedOutput([A, B])` as the whole marker, not `[NativeOutput(A), B]`.
- Keep explicit image output or deferred tool request types as supported sibling output choices rather than nested inside the marker.
- Use default tool output or multiple `ToolOutput(...)` items when each output needs a custom tool name or per-output retry limit.

## Non-Object Schema Looks Wrapped

Symptoms:

- Output tool parameters contain a wrapper object for `int`, `bool`, `list[str]`, or another non-object output.
- Snapshot tests show a wrapper key around an otherwise scalar/list schema.

Explanation and fix:

- Output tools must expose object parameter schemas to model tool-calling APIs, so Pydantic AI wraps non-object schemas internally.
- App code still receives the semantic output such as `list[str]` or `int`.
- If wrapper shape is confusing the model, use a Pydantic model with named fields or `ToolOutput(..., name=..., description=...)` for clearer semantics.

## Type Checker Rejects Valid Output Choices

Symptoms:

- Pyright or mypy complains about `output_type=Foo | Bar`.
- Mypy complains about `output_type=[Foo, Bar]` or async output functions.
- `result.output` is inferred as too broad or too narrow.

Checks:

- Parameterize the agent explicitly with deps and output generic parameters on `Agent`.
- Prefer list choices, `output_type=[Foo, Bar]`, when a union expression only exists for output alternatives.
- Add the narrowest local ignore only when a known type-checker limitation remains; do not weaken runtime output types to `Any` just to satisfy a checker.
- For output functions, ensure the first parameter is either `RunContext[...]` plus data, or just data, and the function has a return type annotation.

## Invalid JSON Schema or `StructuredDict` Problems

Symptoms:

- `StructuredDict` rejects the schema.
- Output schema generation fails around `$defs` or recursion.
- The model ignores required fields from a dynamic schema.

Checks:

- `StructuredDict` requires an object JSON schema; top-level arrays/scalars are not valid here.
- Avoid recursive `$defs` with `StructuredDict`; use Pydantic models for recursive data.
- Remember `StructuredDict` returns `dict[str, Any]` and does not provide app-side typed validation beyond the model-facing schema. Add an output validator or convert the result into a Pydantic model if the app needs stronger guarantees.
- Use `agent.output_json_schema()` in a no-network test to inspect the final schema.

## Output Function Also Registered as Tool

Symptoms:

- The model calls a function during the conversation instead of using it as the final answer.
- The run continues after a call that was expected to end the run.
- The model sees duplicate or confusing function names.

Fix:

- Do not decorate an output function with `@agent.tool` and do not include it in `tools=[...]`.
- Put final-answer callables only in `output_type=...`.
- Put reusable mid-run capabilities in normal tools/toolsets and route design questions to `../tools-and-toolsets/`.

## Output Validation Retries Exhausted

Symptoms:

- `UnexpectedModelBehavior` or retry-limit errors after output validation.
- The model keeps returning the same invalid structured output.

Checks:

- Raise `ModelRetry` only for errors the model can realistically fix.
- Increase the output retry budget with `retries={'output': N}` or a specific `ToolOutput(max_retries=N)` when a model needs more attempts.
- Make output field descriptions/docstrings precise enough for the model.
- Prefer separate output functions for distinct alternatives instead of one broad `@agent.output_validator` with complex `isinstance` branches.
- In streaming paths, guard side effects and final-only checks with `ctx.partial_output`.

## Dropped or Dangling Output Tool Call During Handoff

Symptoms:

- A second agent errors after receiving another agent's history.
- Provider complains that a tool call has no matching tool result.
- A router output function hands off but the downstream model sees an irrelevant final-result tool call.

Fix:

- In an output function handoff, remove the final output-tool call before passing history onward: `message_history=ctx.messages[:-1]`.
- When trimming history, keep normal `ToolCallPart` and `ToolReturnPart` pairs together.
- Do not pass unresolved tool calls from a UI client unless deferred results are explicitly supplied.
- If the destination agent has different tool definitions, do not replay messages that require tools it does not expose unless those call/return pairs are already complete and provider-compatible.

## Replay Uses Wrong Agent Definitions

Symptoms:

- Replayed history refers to tool names, output tool names, system prompts, or structured outputs that no longer exist.
- A provider rejects tool-call history after an agent refactor.
- Continuing with a different agent produces semantically incoherent answers.

Checks:

- Keep persisted message history tied to an agent definition version, or migrate stored history when tool/output names change.
- Preserve or reinject the intended system prompt if storage did not round-trip the original leading instructions.
- When switching models/providers, inspect provider-specific parts such as `ThinkingPart`, `CompactionPart`, `UploadedFile`, and `provider_details`; strip or rewrite unsupported provider-bound state.
- Prefer storing app-level thread metadata alongside the serialized `ModelMessage` list so the app can detect stale agent definitions before replay.

## Multimodal Media Type Problems

Symptoms:

- `ValueError` for unknown media type or URL format.
- A provider rejects an image/audio/video/document part.
- An uploaded file works with one provider but fails with another.

Checks:

- Pass `media_type` explicitly for extensionless URLs or bytes.
- Use `BinaryContent.from_path()` only for local app-owned files; it defaults unknown extensions to `application/octet-stream`, which may still be rejected by a provider.
- `BinaryImage` requires an image media type.
- `UploadedFile` requires the correct `provider_name` and is not portable across providers.
- Check provider/model support in `../models-and-providers/` before promising image/audio/video/document support.
- For UI inputs, keep default file URL sanitization unless the backend has audited allowed schemes and download behavior.

## Message Serialization Does Not Round-Trip

Symptoms:

- Deserialized content becomes a plain dict instead of `ImageUrl`/`DocumentUrl`.
- Binary content changes type or loses identifiers.
- `conversation_id` or `run_id` disappears unexpectedly.

Checks:

- Use `ModelMessagesTypeAdapter.dump_json()` and `.validate_json()`, or `.dump_python(..., mode='json')` and `.validate_python()`.
- Preserve discriminators such as `kind: 'image-url'`, `kind: 'document-url'`, `kind: 'binary'`, message `kind`, and part `part_kind` if another system edits the JSON.
- Do not hand-roll partial message dictionaries unless tests cover `ModelMessagesTypeAdapter` round-tripping.
- Older histories may legitimately have `conversation_id=None`; app code should tolerate that.

## History Trimming Breaks Tools

Symptoms:

- Provider API rejects history after a summarization or recent-window processor.
- Model sees tool returns without calls or calls without returns.
- `new_messages()` includes or excludes unexpected messages after a processor.

Checks:

- Trim by complete turns and preserve tool-call/return pairs.
- If summarizing older messages, replace complete spans with a coherent summary request/response rather than cutting through a tool exchange.
- If a processor rebuilds the trailing `ModelRequest`, preserve its `parts`, `timestamp`, `instructions`, and `metadata`.
- If a processor inserts a message that belongs to the current run, use a context-aware processor and set the current `run_id`.
