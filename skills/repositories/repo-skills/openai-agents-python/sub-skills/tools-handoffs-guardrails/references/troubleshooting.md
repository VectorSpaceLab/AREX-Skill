# Troubleshooting: Tools, Handoffs, Approvals, and Guardrails

Use this when tool schema generation, handoff routing, guardrail timing, approvals, or hosted/local tool behavior is not doing what the application expects.

## Fast Diagnostic Table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tool schema misses argument descriptions | Docstring parser could not infer format or docstring has unsupported shape | Pass `docstring_style="google"`, `"sphinx"`, or `"numpy"`; use `description_override`; add Pydantic `Field(description=...)`; or set `use_docstring_info=False` and write explicit descriptions elsewhere. |
| `ModelBehaviorError: Invalid JSON input for tool ...` | Model emitted invalid JSON or schema-incompatible arguments | Keep `strict_mode=True`, simplify parameter types, add field descriptions, or return a recoverable error with `failure_error_function`. |
| Strict schema rejects optional/default fields unexpectedly | Strict structured-output schema conversion makes model contract narrower | Prefer explicit nullable types and required fields; inspect schema with `scripts/validate_function_tool_schema.py`; only use `strict_mode=False` after provider compatibility is verified. |
| `input_type` does not route to the requested specialist | `handoff(...)` always transfers to the fixed `agent` it wraps | Register one handoff per destination or do routing in code before the run. |
| Receiving handoff agent sees too much prior tool chatter | No handoff `input_filter` or nested-history setting | Use `handoff(..., input_filter=...)`, `agents.extensions.handoff_filters.remove_all_tools`, or `RunConfig(nest_handoff_history=True)`. |
| Input guardrail does not run after a handoff | Agent-level input guardrails run only for the first agent in a chain | Put checks on the starting agent or use function-tool guardrails around each tool call. |
| Output guardrail does not run on a manager before a handoff target answers | Agent-level output guardrails run only for the final-producing agent | Attach output guardrails to the agent that will produce final output, or keep manager control with `Agent.as_tool()`. |
| Tool guardrail does not run for `ShellTool`, `ComputerTool`, hosted tools, or handoff calls | Tool guardrails only wrap custom function tools made with `function_tool`/`FunctionTool` | Add checks in the local executor/harness, use approval callbacks, or wrap the behavior in a function tool if appropriate. |
| Approval pause appears before input tool guardrails reject secrets | Default flow pauses first, then runs input guardrails after approval | Set `RunConfig(tool_execution=ToolExecutionConfig(pre_approval_tool_input_guardrails=True))`; guardrails still run again after approval. |
| Resuming approval restarts the wrong workflow | Resumed nested or handoff agent instead of the original top-level run | Convert the paused result to `RunState`, approve/reject on that state, then call `Runner.run(original_top_level_agent, state)`. |
| `ShellTool` hosted configuration raises `UserError` about executor or approvals | Hosted container mode forbids local `executor`, `needs_approval`, and `on_approval` | Remove those fields for hosted environments; use local `ShellTool` if you need local approval callbacks. |
| Model calls a tool that is conditionally hidden or not present | Stale prompt/tool name, `is_enabled=False`, deferred tool not loaded, or no matching function tool | Fix prompt and tool names; use `ToolSearchTool()` for deferred surfaces; optionally set `tool_not_found_behavior="return_error_to_model"`. |
| `ComputerTool` payload uses preview shape unexpectedly | Effective Responses model is not explicit GA model, or prompt template owns the model | Set the run/agent model deliberately and use `ModelSettings(tool_choice="computer")` or `"computer_use"` when forcing GA selector. |

## Schema and Docstring Parsing

`@function_tool` uses Python `inspect`, Pydantic schema generation, and `griffe` docstring parsing. Problems usually come from ambiguous annotations or docstrings.

Checklist:

- Every parameter should have a type annotation; avoid untyped `dict` and broad `Any` unless the tool really accepts arbitrary JSON.
- Prefer small Pydantic models or `TypedDict` for nested objects.
- Put constraints and descriptions in `Field(...)` when docstring extraction is unreliable.
- Use `name_override` for stable public names when Python function names are implementation details.
- Use `description_override` when docstrings contain internal details that should not be shown to the model.
- Run `python scripts/validate_function_tool_schema.py` from this sub-skill to print generated schema and validation examples.

If automatic schema generation is still unsuitable, create a manual `FunctionTool` with a known `params_json_schema` and an `on_invoke_tool` function that validates `raw_json` itself.

## Strict Mode Validation

Strict mode is the safe default because it improves valid model arguments, but it can expose schema design issues.

Use this sequence:

1. Keep `strict_mode=True` and simplify the function signature.
2. Replace complex unions with Pydantic models that have explicit field descriptions.
3. Represent optional fields clearly as nullable values when the provider supports them.
4. Inspect the emitted schema locally.
5. Only set `strict_mode=False` when the target model/provider has been verified and your tool handles missing/default values robustly.

Avoid using loose strict-mode settings to mask a confusing tool contract. The model-visible schema should describe the real operation accurately.

## Guardrail Boundary Surprises

Guardrail timing is intentionally narrow:

- Agent input guardrails: only the first agent in the chain.
- Agent output guardrails: only the final-producing agent.
- Function-tool input guardrails: every `function_tool` invocation before execution, plus optionally before approval interruption.
- Function-tool output guardrails: every `function_tool` invocation after execution.
- Handoff calls, hosted tools, `ShellTool`, `ComputerTool`, `ApplyPatchTool`, and `Agent.as_tool()` do not expose function-tool guardrail hooks directly.

For manager/specialist workflows:

- Use manager input guardrails for initial user policy.
- Use tool guardrails for each sensitive function call.
- Use specialist output guardrails when handoff targets produce final answers.
- Use `Agent.as_tool()` rather than handoff when the manager must enforce final output policy centrally.

## Approval Pauses

Approval flow is run-wide. A pending approval may come from the current agent, a handoff target, a nested agent-as-tool run, a local shell/apply-patch tool, or MCP tooling.

Debug checklist:

- Inspect every `result.interruptions` item: `tool_name`, `arguments`, `call_id`, and agent metadata.
- Resolve decisions on `result.to_state()` with `state.approve(...)` or `state.reject(...)`.
- Resume the original top-level agent with the updated state.
- Keep passing the same session/backing store if the run also uses sessions.
- Use `state.to_json()` or `state.to_string()` for long-running approval queues.
- Use `always_approve=True` or `always_reject=True` only when repeated decisions are safe for the rest of the same run.

For secret or policy checks before a human sees an approval item, enable pre-approval tool input guardrails with `ToolExecutionConfig(pre_approval_tool_input_guardrails=True)`.

## Tool Not Found

Unresolved function tool calls default to an error. This can happen when:

- A prompt names an old tool after refactoring.
- `is_enabled` hides a tool for the current context.
- Deferred-loading tools are configured without `ToolSearchTool()`.
- `tool_namespace(...)` changed qualified names.
- `tool_choice` targets a deferred-only tool or namespace name.

Fix root causes first. For recoverable workflows, add `RunConfig(tool_not_found_behavior="return_error_to_model")` and optionally customize `RunConfig.tool_error_formatter` so the model can choose another listed tool.

## Hosted/Local Execution Mismatch

Hosted and local tools have similar names but different responsibilities.

- Hosted OpenAI tools run alongside the model and do not use local function-tool guardrails.
- Local `ShellTool` requires an `executor`; hosted-container `ShellTool` rejects `executor`, `needs_approval`, and `on_approval`.
- `ComputerTool` and `ApplyPatchTool` always need local harnesses/editors.
- `LocalShellTool` is legacy; use `ShellTool` for new shell integrations.
- MCP server lifecycle and approval details belong in the MCP sub-skill; sandbox workspace lifecycle belongs in the sandbox sub-skill.

When migrating code, identify where execution actually occurs before adding guardrails, approvals, or secrets.

## ComputerTool Model Selector Migration

`ComputerTool.name` preserves the preview-era runtime name `computer_use_preview` for hooks and persisted run-state compatibility, while tracing displays `computer`. The Responses wire payload depends on the effective model:

- Explicit `gpt-5.5` requests use the GA built-in `computer` tool payload.
- Explicit `computer-use-preview` keeps the preview `computer_use_preview` payload.
- If a prompt template owns the model and the request omits `model`, the SDK keeps preview-compatible serialization unless you force a GA selector.
- `ModelSettings(tool_choice="computer")`, `"computer_use"`, and `"computer_use_preview"` are accepted when a `ComputerTool` is present and normalize to the effective model.

If a `ComputerProvider` factory is unresolved, GA serialization can still proceed without dimensions/environment; preview-compatible serialization needs a resolved `Computer` or `AsyncComputer` instance so those fields can be sent.

## Handoff Input Filtering and Server-Managed Conversations

Handoff input filters and nested handoff history are not supported with server-managed conversations (`conversation_id`, `previous_response_id`, or `auto_previous_response_id`). If a workflow needs both server-managed conversation state and heavily customized specialist inputs, route the design through the core-runtime and models-provider sub-skills before implementing.

## When to Ask for a Design Change

Ask for clarification or propose a refactor when:

- One handoff is expected to dynamically choose among many destinations.
- A hosted tool is expected to run local guardrails or local approval callbacks.
- A function tool needs to pass secrets through model-visible arguments.
- A manager with shared final-output policy is implemented with handoffs that bypass the manager final answer.
- A local shell/computer/patch harness lacks a clear trust boundary or approval UX.
