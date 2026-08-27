# Agent Core Troubleshooting

## Missing schema docstring

**Symptom:** `ValueError: <SchemaName> must have a non-empty docstring...`

**Cause:** `BaseIOSchema` validates the docstring at subclass creation time.

**Fix:** Add a non-empty docstring to every public schema, even when the class only has one field.

## Raw provider client used instead of Instructor

**Symptom:** agent construction succeeds but completion calls fail, or schema validation does not behave as expected.

**Cause:** `AgentConfig.client` must be an Instructor-wrapped client, not a raw provider SDK client.

**Fix:** Use `instructor.from_openai(...)`, `instructor.from_anthropic(...)`, or another Instructor factory before building the agent.

## Sync / async mismatch

**Symptom:** `run()` asserts on an async client, or `run_async()` asserts on a sync client.

**Cause:** the agent methods are intentionally split by client type.

**Fix:**
- sync client → `run()` / `run_stream()`
- async client → `run_async()` / `run_async_stream()`

## History reset loses backend state

**Symptom:** `reset_history()` returns a plain in-memory history or drops custom persistence state.

**Cause:** `BaseChatHistory.copy()` was not overridden in the custom backend.

**Fix:** implement `copy()` so it returns the same backend type and restores any database/session handles or other state.

## Gemini role remapping looks odd

**Symptom:** mid-conversation tool result or injected context messages are not handled like the OpenAI/Anthropic path.

**Cause:** Gemini-style backends use `assistant_role='model'`, so Atomic Agent remaps mid-conversation system-style messages to `user` by default.

**Fix:** accept the default remapping or override `tool_result_role` explicitly if the backend behavior requires it.

## Context trimming fails unexpectedly

**Symptom:** `max_context_tokens` causes a `ValueError`, or a turn is trimmed sooner than expected.

**Cause:** the agent trims whole turns and counts schema/tool overhead too.

**Fix:** raise the limit, shorten the prompt, or reduce per-turn content; do not assume individual messages will be removed.

## Token counter import errors

**Symptom:** `get_context_token_count()` fails around token counting.

**Cause:** `litellm` is required for the token counter backend.

**Fix:** keep the framework dependencies installed and rerun the smoke check.
