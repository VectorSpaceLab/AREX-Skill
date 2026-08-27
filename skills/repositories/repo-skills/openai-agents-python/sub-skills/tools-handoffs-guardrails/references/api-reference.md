# API Reference: Tools, Handoffs, Approvals, and Guardrails

This reference summarizes the `openai-agents` 0.17.6 surfaces that future agents most often need when building tool-heavy workflows.

## Selection Guide

| Need | Use | Notes |
| --- | --- | --- |
| Wrap Python code with JSON arguments | `@function_tool` | Best default for app-local capabilities; supports schema generation, strict mode, approval, timeouts, deferred loading, and tool guardrails. |
| Expose a custom raw JSON invoker | `FunctionTool` | Use only when decorator schema generation is not enough; you own parsing, validation, and error handling. |
| Let a manager call a specialist | `Agent.as_tool()` | Manager keeps control and sees the nested result as a tool output. |
| Transfer the conversation to a specialist | `handoff(...)` or `Agent(handoffs=[...])` | Specialist becomes active; use one handoff per destination. |
| Gate sensitive function work | `needs_approval` plus `RunState` | Manual approvals pause via `result.interruptions`; Shell and apply-patch can also use `on_approval`. |
| Validate every function-tool call | `tool_input_guardrail`, `tool_output_guardrail` | Applies to `function_tool` tools, not hosted tools, built-in shell/computer/apply-patch tools, or handoff calls. |
| Validate initial input or final output | `input_guardrail`, `output_guardrail` | Input guardrails run only for the first agent; output guardrails only for the final-producing agent. |
| Hide large tool surfaces | `defer_loading=True`, `tool_namespace(...)`, `ToolSearchTool()` | Responses-model feature; include exactly one `ToolSearchTool()` for deferred function surfaces. |
| Use OpenAI-hosted tools | `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool`, `ImageGenerationTool`, `ToolSearchTool` | Requires Responses-compatible OpenAI model/provider. Route MCP depth to the MCP sub-skill. |
| Run shell/computer/patch locally | `ShellTool`, `ComputerTool`, `ApplyPatchTool` | You must provide local executors/implementations except hosted-container `ShellTool`. |

## `@function_tool`

Decorator signature highlights:

| Option | Purpose | Guidance |
| --- | --- | --- |
| `name_override`, `description_override` | Override model-visible tool identity | Prefer clear verbs like `lookup_invoice` or `create_refund_draft`. |
| `docstring_style`, `use_docstring_info` | Control docstring parsing | Supported styles are `google`, `sphinx`, and `numpy`; disable parsing when docstrings are not model-safe. |
| `failure_error_function` | Convert tool crashes into model-visible output | Default returns a generic tool error. Pass `None` to re-raise failures. |
| `strict_mode` | Generate strict JSON schema | Keep `True` unless provider compatibility or optional fields require otherwise. |
| `is_enabled` | Hide/show tool at runtime | Can be a bool or callable receiving run context and current agent. |
| `needs_approval` | Pause before execution | Bool or async callable `(run_context, parsed_params, call_id) -> bool`. |
| `tool_input_guardrails`, `tool_output_guardrails` | Validate before/after function execution | Use for secrets, policy checks, output redaction, and tool-specific safety. |
| `timeout`, `timeout_behavior`, `timeout_error_function` | Bound async tool runtime | Timeouts are for async handlers; default returns a model-visible timeout string. |
| `defer_loading` | Hide schema until tool search loads it | Pair function tools with `ToolSearchTool()` under Responses models. |
| `custom_data_extractor` | Attach SDK-only metadata to emitted tool output item | Data is not sent to the model; useful for observability or app state. |

Function-tool schema facts:

- Tool names default to the Python function name; descriptions come from docstrings unless overridden.
- The first parameter may be `RunContextWrapper[...]` or `ToolContext[...]` when the tool needs run context.
- Function signatures become Pydantic models; Pydantic models, dataclasses, `TypedDict`, primitives, `Annotated`, and `Field(...)` constraints are supported.
- Strict schemas are passed through `ensure_strict_json_schema`; defaults and optional fields may be rewritten to satisfy strict structured-output requirements.
- Sync handlers run through `asyncio.to_thread`; async handlers run directly.
- Return values may be strings, stringable objects, `ToolOutputText`, `ToolOutputImage`, `ToolOutputFileContent`, their TypedDict variants, or lists of supported outputs.

## `FunctionTool`

Manual `FunctionTool` fields:

| Field | Purpose |
| --- | --- |
| `name`, `description` | Model-visible identity. |
| `params_json_schema` | JSON schema exposed to the model. |
| `on_invoke_tool` | Async callable `(ToolContext, raw_json_string) -> output`. |
| `strict_json_schema` | Applies strict conversion to `params_json_schema` in `__post_init__`. |
| `is_enabled` | Runtime tool visibility. |
| `tool_input_guardrails`, `tool_output_guardrails` | Function-tool guardrails. |
| `needs_approval` | Bool or callable approval gate. |
| `timeout_seconds`, `timeout_behavior`, `timeout_error_function` | Invocation timeout behavior. |
| `defer_loading` | Tool-search loading behavior. |
| `custom_data_extractor` | SDK-only output metadata. |

Use manual `FunctionTool` when you already have a trusted schema or need unusual JSON parsing. If you only need a custom name, description, approval, timeout, or guardrails, use `@function_tool(...)` instead.

## Hosted and Local Tool Classes

| Class | Runtime | Key configuration | Guardrail/approval notes |
| --- | --- | --- | --- |
| `WebSearchTool` | OpenAI hosted | `user_location`, `filters`, `search_context_size`, `external_web_access` | No function-tool guardrails. |
| `FileSearchTool` | OpenAI hosted | `vector_store_ids`, `max_num_results`, `filters`, `ranking_options`, `include_search_results` | No function-tool guardrails. |
| `CodeInterpreterTool` | OpenAI hosted | `tool_config` with container settings | No function-tool guardrails. |
| `HostedMCPTool` | OpenAI hosted remote MCP | `tool_config`; `on_approval_request` for hosted MCP approval callbacks | Route detailed MCP setup to `mcp-and-hosted-tools`. |
| `ImageGenerationTool` | OpenAI hosted | `tool_config` | No function-tool guardrails. |
| `ToolSearchTool` | OpenAI hosted search | Loads deferred tools/namespaces/hosted MCP surfaces | Include once when deferred function tools are configured. |
| `ShellTool` | Local or hosted container | Local: `executor`; hosted: `environment={"type":"container_auto"}` or `container_reference` | Local supports `needs_approval` and `on_approval`; hosted rejects `executor`, `needs_approval`, and `on_approval`. |
| `LocalShellTool` | Legacy local | `executor` | Prefer `ShellTool` for new code. |
| `ComputerTool` | Local harness mapped to Responses computer tool | `Computer`, `AsyncComputer`, callable factory, or `ComputerProvider`; optional `on_safety_check` | Wire selector depends on model; see troubleshooting. |
| `ApplyPatchTool` | Local editor/harness | `ApplyPatchEditor`; optional `needs_approval`, `on_approval`, `custom_data_extractor` | Good for model-suggested file edits with explicit review. |
| `CustomTool` | Responses custom raw-string tool | `name`, `description`, `on_invoke_tool`, optional `format`, `needs_approval`, `on_approval`, `defer_loading` | Uses raw string input, not JSON schema arguments. |

## `Agent.as_tool()`

`Agent.as_tool(...)` returns a `FunctionTool` that starts a nested agent run. Important options:

| Option | Purpose |
| --- | --- |
| `tool_name`, `tool_description` | Model-visible specialist tool identity. |
| `custom_output_extractor` | Extract or transform the nested `RunResult` before returning to the manager. |
| `is_enabled` | Runtime specialist availability. |
| `on_stream` | Receive nested stream events while the tool drains the nested run. |
| `run_config`, `max_turns`, `hooks` | Configure nested run behavior. |
| `previous_response_id`, `conversation_id`, `session` | Use only when the nested run needs its own conversation/session state. |
| `failure_error_function` | Convert nested failures into model-visible tool output; `None` re-raises. |
| `needs_approval` | Pause before the specialist tool runs. |
| `parameters`, `input_builder`, `include_input_schema` | Expose structured tool input and convert it to nested agent input. |

Decision boundary:

- Use `Agent.as_tool()` for bounded expert subtasks where the manager composes the final answer.
- Use `handoff(...)` for user-facing specialist takeover, focused specialist instructions, or routing where the target should own the next response.
- Nested approvals from an agent-as-tool execution surface on the outer run; approve/reject via the outer `RunState` and resume the original top-level agent.

## `handoff(...)`

`handoff(agent, ...)` creates a `Handoff` tool for a fixed target agent.

| Option | Purpose | Common pitfall |
| --- | --- | --- |
| `agent` | Destination agent | The helper always transfers to this agent. |
| `tool_name_override`, `tool_description_override` | Model-visible transfer tool identity | If omitted, name is `transfer_to_<agent_name>`. |
| `on_handoff` | Side effects/bookkeeping when invoked | Do not use for routine destination selection. |
| `input_type` | Schema for model-generated handoff metadata passed to `on_handoff` | Does not replace the next agent input and does not dynamically route. |
| `input_filter` | Rewrite what the receiving agent sees | Use for transcript trimming, tool-call removal, or custom summaries. |
| `nest_handoff_history` | Per-handoff override for run-level collapsed history | Ignored for server-managed conversations. |
| `is_enabled` | Hide/show handoff at runtime | Can be bool or callable receiving run context and current agent. |

`HandoffInputData` includes `input_history`, `pre_handoff_items`, `new_items`, optional `input_items`, and `run_context`. Set `input_items` when you want to filter model input while preserving `new_items` for session history.

Run-level controls:

- `RunConfig.handoff_input_filter` applies globally only when a handoff does not define its own filter.
- `RunConfig.nest_handoff_history=True` collapses prior transcript into a single assistant message when no explicit filter is set.
- `RunConfig.handoff_history_mapper` customizes the collapsed-history payload.

## Guardrail Decorators

| Decorator/class | Function signature | Runs when | Result behavior |
| --- | --- | --- | --- |
| `@input_guardrail` / `InputGuardrail` | `(RunContextWrapper, Agent, str | list[TResponseInputItem]) -> GuardrailFunctionOutput` | Initial run input for first agent only | `tripwire_triggered=True` raises `InputGuardrailTripwireTriggered`. |
| `@output_guardrail` / `OutputGuardrail` | `(RunContextWrapper, Agent, agent_output) -> GuardrailFunctionOutput` | Final output of final-producing agent | `tripwire_triggered=True` raises `OutputGuardrailTripwireTriggered`. |
| `@tool_input_guardrail` / `ToolInputGuardrail` | `(ToolInputGuardrailData) -> ToolGuardrailFunctionOutput` | Before each `function_tool` invocation | `allow`, `reject_content`, or `raise_exception`. |
| `@tool_output_guardrail` / `ToolOutputGuardrail` | `(ToolOutputGuardrailData) -> ToolGuardrailFunctionOutput` | After each `function_tool` invocation | `allow`, `reject_content`, or `raise_exception`. |

Agent input guardrails support `run_in_parallel=True` by default or `run_in_parallel=False` for blocking preflight checks. Blocking mode prevents model/tool execution when the tripwire fires; parallel mode can be lower latency but may consume tokens or start side effects before cancellation.

Tool guardrail outcomes:

- `ToolGuardrailFunctionOutput.allow(output_info=None)` continues normally.
- `ToolGuardrailFunctionOutput.reject_content(message, output_info=None)` skips or replaces model-visible content with the message while continuing the run.
- `ToolGuardrailFunctionOutput.raise_exception(output_info=None)` raises a tool guardrail tripwire exception and halts execution.

## `ToolExecutionConfig` and Tool Error Controls

`RunConfig(tool_execution=ToolExecutionConfig(...))` controls SDK-side function-tool execution:

| Field | Meaning |
| --- | --- |
| `max_function_tool_concurrency` | `None` starts all emitted local function-tool calls; an integer caps concurrent execution and must be at least 1. |
| `pre_approval_tool_input_guardrails` | `False` runs input tool guardrails after approval; `True` also runs them before the pending approval interruption is emitted, then re-runs them after approval. |

Related run-level controls:

- `RunConfig.tool_not_found_behavior="raise_error"` is the default for unresolved function tool calls.
- `RunConfig.tool_not_found_behavior="return_error_to_model"` appends a model-visible function-call output and lets the model recover.
- `RunConfig.tool_error_formatter` can customize model-visible approval rejection and tool-not-found messages.

## Approval-Capable Surfaces

| Surface | Approval option | Auto-approval callback | Pause/resume path |
| --- | --- | --- | --- |
| `@function_tool` / `FunctionTool` | `needs_approval` | No | `result.interruptions` -> `RunState.approve/reject` -> resume original run. |
| `Agent.as_tool()` | `needs_approval` | No | Same outer-run interruption flow. |
| Nested tools inside `Agent.as_tool()` | Tool-specific approval | Depends on nested tool type | Interruptions still surface on the outer run. |
| Local `ShellTool` | `needs_approval` | `on_approval` | Manual interruption or callback. |
| `ApplyPatchTool` | `needs_approval` | `on_approval` | Manual interruption or callback. |
| Hosted `ShellTool` container mode | Not supported | Not supported | Hosted config rejects approval fields. |
| Local MCP servers | `require_approval` | Server/tool dependent | Route details to MCP sub-skill. |
| Hosted MCP | `tool_config={"require_approval": "always"}` | `on_approval_request` | Route details to MCP sub-skill. |

## Evidence Notes

Primary source evidence: `docs/tools.md`, `docs/handoffs.md`, `docs/guardrails.md`, `docs/human_in_the_loop.md`, `docs/multi_agent.md`, `docs/running_agents.md`, `src/agents/tool.py`, `src/agents/agent.py`, `src/agents/handoffs/`, `src/agents/guardrail.py`, `src/agents/tool_guardrails.py`, `src/agents/run_config.py`, and related tests under `tests/test_function_tool*.py`, `tests/test_guardrails.py`, `tests/test_tool_guardrails.py`, `tests/test_handoff*.py`, and `tests/test_tool_choice_reset.py`.
