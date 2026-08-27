# Core Runtime Troubleshooting

Use this matrix when a plain `Agent` / `Runner` workflow fails or behaves unexpectedly.

## Quick Triage

| Symptom | Likely cause | First checks |
| --- | --- | --- |
| Import fails for `agents` | Package not installed or wrong environment. | Run `python scripts/inspect_core_runtime.py --json`; verify distribution `openai-agents` is installed. |
| First model call fails before items stream | Missing OpenAI API key or provider configuration. | Check environment/provider setup; route model transport details to ../models-providers/SKILL.md. |
| Run loops until `MaxTurnsExceeded` | Tool/handoff cycle or too-low `max_turns`. | Inspect `new_items`, semantic stream events, and repeated tool/handoff names. |
| Raw stream shows tool argument deltas but no final output | UI is reading raw provider deltas but not SDK semantic events, or run paused before final output. | Drain `stream_events()`, inspect `run_item_stream_event`, `interruptions`, and `run_loop_exception`. |
| `final_output` is `None` | Run paused for approval, stream not drained, or error/cancellation occurred. | Check `interruptions`, `is_complete`, `run_loop_exception`, and whether `stream_events()` finished. |
| Tool call raises tool-not-found behavior | Model emitted an unresolved function tool call. | Verify tool names; consider `RunConfig(tool_not_found_behavior="return_error_to_model")`. |
| Session plus `previous_response_id` fails | Mixed local session and server-managed state. | Pick one state strategy for the turn. |
| Resume replays the wrong turn | `RunState` not used correctly or new user input appended during approval resume. | Pass `state` as the input and resume the original top-level agent. |

## Missing API Key or Provider Configuration

Typical error source:

- The SDK imports successfully, but the first model call fails because no OpenAI API key or compatible provider configuration is available.
- Base installation does not expose console scripts; runtime use is through Python imports.

Resolution:

1. Confirm import surfaces without network calls:

   ```bash
   python scripts/inspect_core_runtime.py --json
   ```

2. Confirm the application is setting provider credentials before calling `Runner`.
3. For OpenAI defaults, ensure `OPENAI_API_KEY` is available to the process or an explicit provider/client is configured.
4. For non-default providers, route setup and transport details to ../models-providers/SKILL.md.
5. Do not hardcode API keys in skill content, `RunState.context`, logs, or serialized state.

## MaxTurnsExceeded

`max_turns` counts model invocations, not user messages. A single user turn may need multiple model invocations when tools or handoffs are involved.

Common causes:

- The model repeatedly calls a tool because `tool_choice` forces it or `reset_tool_choice=False` keeps forcing it.
- Tool output does not satisfy the model, causing another tool/model cycle.
- A handoff graph loops between agents.
- `max_turns` is set too low for a legitimate multi-step workflow.

Diagnosis:

1. Inspect `exc.run_data.new_items` for repeated `ToolCallItem`, `ToolCallOutputItem`, `HandoffCallItem`, or `HandoffOutputItem` patterns.
2. In streaming, check `run_item_stream_event.name` for repeated `tool_called` or `handoff_requested` events before the exception.
3. Check agent `tool_use_behavior`, `reset_tool_choice`, and model settings such as `tool_choice`.
4. If the loop is legitimate, raise the limit or set `max_turns=None` only when the host app has an independent timeout/loop guard.
5. For a graceful fallback, pass `error_handlers={"max_turns": handler}` and decide whether fallback text should be included in history.

Route tool-use behavior depth to ../tools-handoffs-guardrails/SKILL.md.

## Tool Not Found

Default behavior: unresolved function tool calls raise `ModelBehaviorError`.

Likely causes:

- Tool name in the prompt differs from the exposed `FunctionTool.name`.
- Tool is disabled by an `is_enabled` predicate.
- Handoff or MCP tool names collide with local function tool names.
- The model hallucinated a tool name not provided in the tool list.

Resolution:

1. Verify the current agent actually exposes the intended function tool.
2. Check stream semantic events for the exact emitted tool name.
3. If the task should be recoverable, set:

   ```python
   RunConfig(tool_not_found_behavior="return_error_to_model")
   ```

4. Optionally provide `tool_error_formatter` to make the model-visible message clearer.
5. Keep default `"raise_error"` when an unexpected tool name should fail fast.

This option only covers unresolved function tool calls; other malformed tool payloads keep their existing error behavior.

## Streaming Cancellation and Incomplete Streams

Problems:

- UI stops reading after the visible text delta and misses tool output or final bookkeeping.
- `cancel()` is called but `stream_events()` is not drained.
- `result.final_output` is read before the stream completes.

Rules:

- Always drain `async for event in result.stream_events(): ...` until it exits.
- After `result.cancel()`, keep consuming the iterator so cleanup, cancellation, session persistence, and error propagation can settle.
- Use `cancel(mode="after_turn")` when you need the current turn to finish cleanly.
- After draining, inspect `result.run_loop_exception` and raise/log it if present.
- If continuation is manual after a graceful cancel, use `result.to_input_list(mode="normalized")` and `result.last_agent` rather than starting a fresh unrelated user turn.

## Raw Tool-Call Deltas But No Final Output

This is the difficult streamed-run case where raw provider events include tool-call argument deltas, but the app never sees final text.

Diagnosis path:

1. Confirm the code does not ignore all non-raw events. `raw_response_event` may show argument deltas, while completion state is reflected by `run_item_stream_event`.
2. Look for `run_item_stream_event` with `name="tool_called"`; this confirms the SDK created a tool call item.
3. Look for `name="tool_output"`; if absent, the tool may be awaiting approval, failing, canceled, or not found.
4. If `result.interruptions` is non-empty after drain, convert to `RunState`, resolve approvals, and resume.
5. If `result.run_loop_exception` is set, handle that exception; it may explain why no final output appeared.
6. If a final message item exists but no displayed text appears, use `ItemHelpers.text_message_output(...)` instead of manually parsing provider payloads.

Avoid treating tool-call argument deltas as assistant output. They are model instructions to the SDK/tool layer.

## Server-Managed Conversation and Session Incompatibility

The SDK supports several state strategies, but mixing them can duplicate history or raise errors.

Do not combine these in one `Runner` call:

- `session=...` with `conversation_id=...`
- `session=...` with `previous_response_id=...`
- `session=...` with `auto_previous_response_id=True`
- `conversation_id=...` with `previous_response_id=...`

Use:

- `to_input_list()` for fully client-managed local history.
- `session=...` when the SDK should load/save local or app-backed history.
- `conversation_id=...` for named OpenAI server-side conversation resources.
- `previous_response_id=result.last_response_id` for lightweight Responses API chaining.

When resuming from `RunState`, server-managed IDs saved in the state continue the same server-managed conversation. Do not add local replay history unless the application deliberately migrates state strategies.

## RunState and Schema Issues

Possible failures:

- Deserializing a `RunState` produced by a newer SDK with an older SDK.
- Loading state with a changed or incompatible agent graph.
- Failing to serialize a custom context object.
- Leaking secrets because context was serialized.

Resolution:

1. Prefer `result.to_state()` over manual `RunState(...)` construction.
2. Store SDK version and application agent-definition version next to long-lived state.
3. Use `context_serializer` and `context_deserializer` for custom context objects, or use `context_override` when reloading.
4. Keep secrets out of `RunContextWrapper.context` unless intentionally persisted.
5. Resume with the same original top-level agent graph so tool, handoff, and duplicate-name identities can be resolved.
6. If schema compatibility fails, load the state with a compatible SDK version and migrate at the application boundary rather than editing serialized state by hand.

## Resume Approval Without Creating a New First Turn

Correct pattern:

```python
state = result.to_state()
state.approve(result.interruptions[0])
result = await Runner.run(agent, state)
```

Incorrect patterns:

- Passing a new user string like `"approved"` instead of the `RunState`.
- Resuming a nested agent instead of the original top-level agent.
- Rebuilding conversation history manually from `new_items` while also using the `RunState`.
- Calling `to_state()` on a streamed result before `stream_events()` has completed.

Why this matters:

- `RunState` preserves `_current_turn`, `_last_processed_response`, generated items, approval decisions, server-managed IDs, and trace state.
- The runner has explicit resumed-state paths that continue the interrupted turn, then treats later turns normally.
- Input guardrails are first-turn checks; approval resume should not be transformed into a new first user turn.

## call_model_input_filter Errors

Common error: returning the wrong shape from the hook.

Required shape:

```python
from agents.run import ModelInputData

return ModelInputData(input=trimmed_items, instructions=data.model_data.instructions)
```

Checklist:

- `input` must be a list of Responses input items.
- Return a new `ModelInputData`, not a tuple, dict, or bare list.
- Preserve instructions unless deliberately changing them.
- Avoid mutating `data.model_data.input` in place; work from a copy or slice.
- With server-managed conversation state, the returned items are the sent delta tracked by the SDK.

## run_sync in an Active Event Loop

`Runner.run_sync()` wraps async execution. In environments that already run an event loop, use `await Runner.run(...)` instead.

Symptoms:

- Runtime errors about an event loop already running.
- Deadlocks or cancellation behavior in notebooks, FastAPI, async test runners, or GUI loops.

Resolution:

- Convert the caller to async and call `await Runner.run(...)`.
- For synchronous application entry points, keep `Runner.run_sync(...)` at the outermost boundary.

## `final_output` Type Surprises

Possible causes:

- A handoff changed the final agent, so output type differs from the starting agent's `output_type`.
- The run paused for approval, so `final_output` is `None`.
- Streaming is not complete yet.
- The model refused or failed structured output validation.

Resolution:

- Check `result.last_agent` before assuming output type.
- Use `result.final_output_as(ExpectedType, raise_if_incorrect_type=True)` when a runtime check is appropriate.
- Inspect `raw_responses`, guardrail results, and errors when structured output is absent.

## Reasoning Item ID Errors

If a follow-up Responses API call fails with an error about a reasoning item ID missing its required following item, use:

```python
RunConfig(reasoning_item_id_policy="omit")
```

This strips reasoning item IDs from SDK-built follow-up input while preserving reasoning content. It does not rewrite user-supplied initial input items, and a custom `call_model_input_filter` can still reintroduce IDs.
