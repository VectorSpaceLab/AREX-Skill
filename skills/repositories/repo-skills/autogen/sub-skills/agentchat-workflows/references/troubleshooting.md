# AgentChat Troubleshooting

Use this matrix for high-level AgentChat failures. Route provider/client/executor installation and credentials to `../../extensions-integrations/SKILL.md`, low-level runtime internals to `../../core-runtime/SKILL.md`, and Studio/bench/CLI compatibility to `../../tools-studio-bench/SKILL.md`.

## Hangs or Runs Never Stop

Symptoms:
- `team.run(...)` or `Console(team.run_stream(...))` never returns.
- A nested team/tool keeps talking after the task is complete.
- Tests hang unless manually cancelled.

Likely causes:
- `RoundRobinGroupChat` or `SelectorGroupChat` was created without `termination_condition` and without `max_turns`.
- A semantic termination such as `TextMentionTermination("TERMINATE")` is configured, but agents never emit the exact text.
- A nested `TeamTool` or nested team lacks its own bounds.

Fixes:
- Add `max_turns` to every team and `MaxMessageTermination` to every multi-agent workflow.
- Combine semantic and hard bounds: `TextMentionTermination("TERMINATE") | MaxMessageTermination(8)`.
- For human or external handoff workflows, use `HandoffTermination(target)` to stop at the boundary.
- In tests, prefer replay/mock clients and small message bounds.

## Selector Failures

Symptoms:
- `ValueError` about invalid speaker name.
- `ValueError` that candidate function returned an empty list.
- Selector retries repeatedly or chooses the wrong participant.

Likely causes:
- `selector_func` returns a display label rather than exact participant `name`.
- `candidate_func` returns names not present in the team or filters out all participants.
- `allow_repeated_speaker=False` conflicts with a candidate list containing only the previous speaker.
- `selector_prompt` does not constrain the model to return only a role name.

Fixes:
- Validate hook outputs against `{participant.name for participant in participants}` before constructing the team.
- Let `selector_func` return `None` when it wants model-based selection.
- Ensure `candidate_func` always returns at least one valid name.
- Keep `max_selector_attempts` finite and add `max_turns` to the team.

## Async and Streaming Misuse

Symptoms:
- `TypeError` from awaiting an async generator.
- Stream appears empty until the final result.
- UI code loses the final `TaskResult`.

Likely causes:
- Calling `await team.run_stream(...)` instead of iterating it or passing it to `Console`.
- Forgetting that the final stream item is the `TaskResult`.
- Enabling `model_client_stream=True` but not handling `ModelClientStreamingChunkEvent` events.

Fixes:
- Use `await Console(team.run_stream(task="..."))` for terminal display.
- For custom UIs, use `async for event in team.run_stream(...): ...` and preserve the final `TaskResult`.
- Handle both chat messages and agent events; chunks are not the final response.

## Tool Summary and Structured Output Confusion

Symptoms:
- Final response is a `ToolCallSummaryMessage` instead of natural language.
- Tool output is concatenated or missing expected fields.
- Structured output works until a tool call occurs.

Likely causes:
- `reflect_on_tool_use=False`, so tool results are summarized directly.
- `tool_call_summary_format` omits fields needed by the next agent.
- `output_content_type` changes final message type and defaults `reflect_on_tool_use` differently.
- `tool_call_summary_formatter` was expected to survive serialization.

Fixes:
- Set `reflect_on_tool_use=True` when the model should synthesize after tools.
- Use `tool_call_summary_format` placeholders deliberately: `{tool_name}`, `{arguments}`, `{result}`, `{is_error}`.
- Test final message types when using `output_content_type`.
- Reattach non-serializable formatters in Python code after loading config.

## Code Executor Approval and Safety

Symptoms:
- Warning that no approval function is set.
- Code executes automatically from a model-produced markdown block.
- Execution fails due to missing Docker/Jupyter/local environment.

Likely causes:
- `CodeExecutorAgent(..., approval_func=None)` was accepted in a risky context.
- The app confuses AgentChat orchestration with concrete executor setup.
- Generated code block language is not in `supported_languages`.

Fixes:
- Add `approval_func` for any environment where model-generated code could be unsafe.
- Restrict `sources` and `supported_languages` where possible.
- Route executor installation/runtime failures to `../../extensions-integrations/SKILL.md`.
- Use no-provider and no-execution smoke tests before enabling real executors.

## State, Resume, and Schema Issues

Symptoms:
- `load_state` fails validation.
- Restored team resumes with wrong speaker or old termination state.
- Serialized component config loads but custom hooks are missing.

Likely causes:
- State is loaded into a different team structure or changed participant names.
- Termination condition fired before save and was not reset.
- Custom message types were not supplied.
- Non-serializable callables were expected to round-trip.

Fixes:
- Rebuild the exact same logical team before `load_state`: same names, participant order, and team class.
- Reset agents/teams/termination conditions for independent sessions.
- Include `custom_message_types` for custom message classes.
- Store Python hook wiring in code and reattach after component loading.

## Provider Credential or Model Client Failures

Symptoms:
- Import errors for provider packages.
- Missing API key or Azure endpoint errors.
- Model lacks tool calling, JSON output, or structured output capability.
- Selector model behaves differently across OpenAI-compatible endpoints.

Likely causes:
- Optional `autogen-ext` extras are missing.
- Credentials or endpoint fields are absent.
- `model_info` is incomplete for an OpenAI-compatible provider.
- The chosen model does not support required capabilities.

Fixes:
- Keep AgentChat code provider-neutral where possible.
- Verify model-client construction and capability flags through `../../extensions-integrations/SKILL.md`.
- For selector teams, test a deterministic `selector_func` path before using model-based selection.
- Do not install Magentic-One CLI or Studio into the same environment as 0.7.x libraries unless compatibility has been explicitly reviewed in `../../tools-studio-bench/SKILL.md`.

## Agent Concurrency and History Bugs

Symptoms:
- Interleaved conversations across users.
- Assistant repeats or grows context unexpectedly.
- Random state from an earlier task appears in a new run.

Likely causes:
- One agent/team instance is shared across concurrent sessions.
- Full transcript is passed back into a stateful agent on each call.
- `reset()` was not called before a logically independent task.

Fixes:
- Create one agent/team instance per session or protect access so calls are not concurrent.
- Pass only new messages/tasks to stateful AgentChat APIs.
- Save/load per-session state explicitly in web apps.
