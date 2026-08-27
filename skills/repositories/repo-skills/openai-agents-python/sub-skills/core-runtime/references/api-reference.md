# Core Runtime API Reference

This reference summarizes the core runtime surfaces verified from repository docs, source, tests, and installed-package facts for `openai-agents` 0.17.6.

## Imports

```python
from agents import Agent, RunConfig, Runner
from agents.run_state import RunState
```

Common result and event types are available from `agents.result`, `agents.items`, and `agents.stream_events` when explicit type checks are needed.

## Agent

`Agent` is the central object passed to `Runner`. Its verified constructor shape is:

```text
Agent(
    name,
    handoff_description=None,
    tools=[],
    mcp_servers=[],
    mcp_config=...,
    instructions=None,
    prompt=None,
    handoffs=[],
    model=None,
    model_settings=...,
    input_guardrails=[],
    output_guardrails=[],
    output_type=None,
    hooks=None,
    tool_use_behavior="run_llm_again",
    reset_tool_choice=True,
)
```

Use the fields this sub-skill owns as follows:

| Field | Runtime role | Notes |
| --- | --- | --- |
| `name` | Human-readable agent name. | Required and used in logs, stream agent updates, handoffs, and debug output. |
| `instructions` | System prompt or dynamic instruction callback. | Preferred for plain agents; dynamic callbacks receive the run context and agent. |
| `prompt` | OpenAI Responses prompt template or callback. | Useful when prompt configuration lives in OpenAI platform prompts. |
| `model` | Agent-specific model or model object. | A `RunConfig.model` can override it for a run. |
| `model_settings` | Agent-level generation/tool settings. | A `RunConfig.model_settings` overlays non-null global values. |
| `output_type` | Structured final output adapter. | When set, `final_output` should be an instance of this type after a successful run. |
| `tools`, `handoffs`, `input_guardrails`, `output_guardrails` | Capabilities and safety controls. | Route detailed design to sibling sub-skills. |
| `tool_use_behavior`, `reset_tool_choice` | Core loop behavior after tool calls. | Keep default unless deliberately changing whether tools end or continue the loop. |

`Agent` is generic over context type. Pass an application context object to `Runner.run(..., context=...)` when tools, guardrails, or dynamic instructions need dependencies or per-run state.

## Runner Entry Points

All `Runner` entry points take a starting agent, input, and the same core options:

```text
Runner.run(starting_agent, input, *, context=None, max_turns=10, hooks=None,
           run_config=None, error_handlers=None, previous_response_id=None,
           auto_previous_response_id=False, conversation_id=None, session=None)
Runner.run_sync(starting_agent, input, *, ...same options...)
Runner.run_streamed(starting_agent, input, *, ...same options...)
```

| Method | Use when | Returns | Important caveat |
| --- | --- | --- | --- |
| `await Runner.run(...)` | Application already runs in async code. | `RunResult` | Preferred in FastAPI, notebooks with event loops, async CLIs, and services. |
| `Runner.run_sync(...)` | Caller is purely synchronous. | `RunResult` | Wraps async execution and is not suitable inside an already-running event loop. |
| `Runner.run_streamed(...)` | UI or service needs incremental events. | `RunResultStreaming` | You must consume `stream_events()` until it finishes before relying on final fields. |

The `input` may be a user string, a list of Responses API input items, or a `RunState` created by `result.to_state()` when resuming a paused run.

## Core Loop Semantics

A Runner call represents one logical user turn, even if the SDK makes multiple model calls. The loop is:

1. Call the model for the current agent.
2. If the model produced final output and no tool calls, finish.
3. If the model requested a handoff, switch current agent and continue.
4. If the model emitted tool calls, execute them, append outputs, and continue.
5. If `max_turns` is exceeded, raise `MaxTurnsExceeded` unless an error handler handles it.

Input guardrails run only on the first turn for the starting agent. Resuming an interrupted `RunState` continues the interrupted turn rather than treating approval resume as a new first turn.

## RunConfig

`RunConfig` configures a single run without mutating the agent definitions. Its verified fields include:

| Field | Purpose | Core-runtime guidance |
| --- | --- | --- |
| `model` | Global model override. | Overrides every agent model for the run. |
| `model_provider` | Resolves string model names. | Route provider setup details to ../models-providers/SKILL.md. |
| `model_settings` | Global model settings overlay. | Use for run-wide temperature, tool choice, usage inclusion, etc. |
| `handoff_input_filter` | Edits input sent to handoff target. | Unsupported with server-managed conversation state. |
| `nest_handoff_history`, `handoff_history_mapper` | Optional nested handoff transcript rewriting. | Leave default unless explicitly shaping handoff history. |
| `input_guardrails`, `output_guardrails` | Run-wide guardrails. | Route guardrail authoring to ../tools-handoffs-guardrails/SKILL.md. |
| `tracing_disabled`, `tracing`, `trace_include_sensitive_data`, `workflow_name`, `trace_id`, `group_id`, `trace_metadata` | Trace controls. | Route detailed observability to ../tracing-observability/SKILL.md. |
| `session_input_callback` | Customizes session-history merge before model input. | Route persistent session design to ../sessions-memory/SKILL.md. |
| `call_model_input_filter` | Edits fully prepared model input immediately before the model call. | Must return `ModelInputData(input=list_items, instructions=...)`. |
| `tool_error_formatter` | Formats model-visible approval/tool-not-found errors. | Useful with `tool_not_found_behavior="return_error_to_model"` and HITL rejection text. |
| `session_settings` | Per-run session retrieval overrides. | Do not combine sessions with `conversation_id` / `previous_response_id`. |
| `reasoning_item_id_policy` | Keeps or omits reasoning item IDs when building follow-up input. | Use `"omit"` to avoid Responses API errors about orphaned reasoning items. |
| `sandbox` | Sandbox runtime configuration. | Route to ../sandbox-agents/SKILL.md. |
| `tool_execution` | SDK-side local function tool execution controls. | Route deeper tool behavior to ../tools-handoffs-guardrails/SKILL.md. |
| `tool_not_found_behavior` | Handles unresolved function tool calls. | Default `"raise_error"`; opt into `"return_error_to_model"` for recoverable model-visible errors. |

### ModelInputData and CallModelData

`call_model_input_filter` receives `CallModelData` containing:

| Attribute | Meaning |
| --- | --- |
| `model_data.input` | Prepared input items that will be sent to the model. |
| `model_data.instructions` | Prepared instructions for the model call. |
| `agent` | Current agent. |
| `context` | Application context object or `None`. |

It must return `ModelInputData(input=<list>, instructions=<str or None>)`. Returning a bare list, dict, or mutating the original input in place is a misuse.

## Result Surfaces

Both `RunResult` and `RunResultStreaming` inherit these shared surfaces:

| Surface | Meaning | Typical use |
| --- | --- | --- |
| `final_output` | Final answer or structured output, or `None` if paused before final output. | Show user result after successful completion. |
| `new_items` | Rich `RunItem` wrappers from this run. | Audit messages, tools, handoffs, approvals, and reasoning. |
| `raw_responses` | Raw model response objects. | Provider diagnostics and response IDs. |
| `last_agent` | Last agent that ran. | Continue after handoff in manual chat loops. |
| `last_response_id` | Response ID from the last model response. | Pass as `previous_response_id` in Responses API chaining. |
| `to_input_list(mode="preserve_all")` | Converts input plus `new_items` into plain Responses input items. | Client-managed next-turn history. |
| `to_input_list(mode="normalized")` | Prefers canonical continuation input when handoff/input filtering rewrote history. | Manual continuation after filtered handoffs or graceful streaming cancellation. |
| `interruptions` | Pending `ToolApprovalItem` values. | Build a `RunState`, approve/reject, and resume. |
| `to_state()` | Creates a durable `RunState`. | Resume interrupted runs. |
| `input_guardrail_results`, `output_guardrail_results` | Guardrail diagnostics. | Audit safety decisions. |
| `tool_input_guardrail_results`, `tool_output_guardrail_results` | Tool guardrail diagnostics. | Debug blocked or transformed tool execution. |
| `context_wrapper` | Runtime wrapper for app context, usage, approvals, and nested tool input. | Access usage and context metadata. |

`RunResult.final_output_as(MyType, raise_if_incorrect_type=True)` can enforce a runtime type check on structured outputs.

## RunItem Types

`new_items` contains rich `RunItem` wrappers. Common types include:

| Item type | Meaning |
| --- | --- |
| `MessageOutputItem` | Assistant message output. |
| `ReasoningItem` | Reasoning item emitted by the model. |
| `ToolCallItem` | Tool call requested by the model. |
| `ToolCallOutputItem` | Tool execution result returned to the model. |
| `ToolApprovalItem` | Tool call paused for approval; never send it directly as model input. |
| `HandoffCallItem` | Handoff request. |
| `HandoffOutputItem` | Completed handoff transfer. |
| `ToolSearchCallItem`, `ToolSearchOutputItem` | Hosted tool-search request and loaded search results. |
| `MCPApprovalRequestItem`, `MCPApprovalResponseItem`, `MCPListToolsItem` | MCP-specific approval/listing events. |
| `CompactionItem` | History compaction item. |

Use `ItemHelpers.text_message_output(item)` and related helpers when extracting display text from message items.

## Streaming Events

`RunResultStreaming.stream_events()` yields a union of:

| Event type | Fields | Use |
| --- | --- | --- |
| `RawResponsesStreamEvent` | `type="raw_response_event"`, `data` | Token deltas and raw OpenAI Responses stream events. |
| `RunItemStreamEvent` | `type="run_item_stream_event"`, `name`, `item` | Semantic progress when complete messages, tool calls, outputs, or handoffs are created. |
| `AgentUpdatedStreamEvent` | `type="agent_updated_stream_event"`, `new_agent` | Detect active-agent changes after handoffs. |

`RunItemStreamEvent.name` values are:

- `message_output_created`
- `handoff_requested`
- `handoff_occured` (misspelled for compatibility)
- `tool_called`
- `tool_search_called`
- `tool_search_output_created`
- `tool_output`
- `reasoning_item_created`
- `mcp_approval_requested`
- `mcp_approval_response`
- `mcp_list_tools`

Streaming-specific result fields include `current_agent`, `current_turn`, `is_complete`, `run_loop_exception`, `cancel(mode="immediate" | "after_turn")`, and `stream_events()`.

## RunState

`RunState` is the durable pause/resume snapshot for interrupted runs. Its verified constructor shape is:

```text
RunState(context, original_input, starting_agent, max_turns=10, *,
         conversation_id=None, previous_response_id=None,
         auto_previous_response_id=False)
```

Most applications should not construct `RunState` manually. Prefer `result.to_state()` because it preserves generated items, model responses, current turn, approvals, trace state, server-managed conversation IDs, sandbox resume payloads, and schema version metadata.

Core methods and helpers:

| Surface | Use |
| --- | --- |
| `get_interruptions()` | Return pending approval items stored in the state. |
| `approve(approval_item, always_approve=False)` | Approve a pending tool call before rerunning. |
| `reject(approval_item, always_reject=False, rejection_message=None)` | Reject a pending tool call, optionally with model-visible text. |
| `to_json(...)` / `to_string(...)` | Serialize a paused run for durable storage. |
| `RunState.from_json(agent, payload, ...)` / `RunState.from_string(agent, text, ...)` | Recreate state for the matching agent graph. |

The source tracks a schema version and supported schema summaries. Newer SDK snapshots can fail fast in older SDKs, so store an SDK or agent-definition version with long-lived approval tasks.

## Conversation State Options

Pick one strategy per conversation turn unless deliberately reconciling layers:

| Strategy | Next turn input | Owned by | Notes |
| --- | --- | --- | --- |
| `result.to_input_list()` | Full local item history plus new user message. | Application. | Works with any provider and gives full manual control. |
| `session=...` | New user turn plus same session object/store. | SDK plus app storage. | Route backend details to ../sessions-memory/SKILL.md. |
| `conversation_id=...` | Only the new user turn plus same conversation ID. | OpenAI Conversations API. | Do not combine with `session`. |
| `previous_response_id=...` | Only the new user turn plus `result.last_response_id`. | OpenAI Responses API. | Lightweight response chaining. |
| `auto_previous_response_id=True` | Only new turns; SDK tracks chaining across server-managed runs. | OpenAI Responses API via SDK. | Preserved when resuming from `RunState`. |

`conversation_id` and `previous_response_id` are mutually exclusive. Session persistence cannot be combined with server-managed conversation settings in the same run.
