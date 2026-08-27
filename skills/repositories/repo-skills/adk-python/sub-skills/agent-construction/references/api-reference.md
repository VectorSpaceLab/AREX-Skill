# Agent Construction API Reference

This reference covers ADK Python `google-adk` 2.3.0 agent-construction surfaces that can be used without reopening source docs.

## Imports And Version Assumptions

- Base package: `google-adk` 2.3.0 with Python 3.10+.
- Public import root: `google.adk`.
- Common imports:
  - `from google.adk import Agent, Runner`
  - `from google.adk.agents import LlmAgent, RunConfig, SequentialAgent, LoopAgent, ParallelAgent`
  - `from google.adk.tools.function_tool import FunctionTool`
  - `from google.genai import types` for `GenerateContentConfig`, `Content`, and `Part` objects.
- `google.adk.Agent` is an alias for `google.adk.agents.llm_agent.LlmAgent`.
- Base installs may not include optional extras such as database services, MCP, extensions, or cloud integrations; missing optional imports are normal and route to the integration/runtime sub-skills.

## `Agent` / `LlmAgent` Constructor

Use `Agent(...)` for most LLM-backed agents. Important fields include:

| Field | Purpose | Notes |
| --- | --- | --- |
| `name` | Agent identifier | Must be a Python identifier and cannot be `user`. |
| `description` | Capability summary | Used by parent agents to decide delegation; keep it short and specific. |
| `model` | Model name or `BaseLlm` | Empty string inherits from an ancestor or falls back to the default model. |
| `instruction` | Dynamic behavior prompt | May be a string or callable provider; placeholders can be resolved from state/context. |
| `static_instruction` | Literal static content | Useful for content caching; does not itself enable caching. |
| `tools` | Tool callables, `BaseTool`, or `BaseToolset` | Plain callables are wrapped like `FunctionTool`. Toolset/auth details route to `tools-and-integrations`. |
| `generate_content_config` | Model generation settings | Use for fields such as temperature/safety; do not put tools, system instructions, or response schema here. |
| `mode` | `chat`, `task`, or `single_turn` | Root LLM agents must run as `chat`; child task/single-turn modes become tools. |
| `include_contents` | `default` or `none` | `single_turn` helpers usually use `none`; set `default` only when history is required. |
| `input_schema` | Pydantic model type | Used when the agent is exposed as a tool. |
| `output_schema` | Pydantic/list/dict/GenAI schema | Validates final structured output and task return values. |
| `output_key` | Session state key | Saves final text or parsed structured output into session state. |
| `planner` | Planner object | Planner thinking config takes precedence over `generate_content_config.thinking_config`. |
| `code_executor` | Code execution backend | Route executor service/safety details to `runtime-services`. |
| `sub_agents` | Child agents | Each child gets `parent_agent`; one agent instance cannot be reused under multiple parents. |
| `before_agent_callback` / `after_agent_callback` | Agent lifecycle hooks | Accept `callback_context`; can short-circuit or append content/state. |
| `before_model_callback` / `after_model_callback` / `on_model_error_callback` | Model lifecycle hooks | Accept `CallbackContext`, request/response/error objects; first non-`None` callback wins. |
| `before_tool_callback` / `after_tool_callback` / `on_tool_error_callback` | Tool lifecycle hooks | Accept tool, args, `ToolContext`, and response/error as applicable. |

The installed signature contains additional fields such as `rerun_on_resume`, `wait_for_output`, schemas, callback collections, model/tool callbacks, planner, and executor options. Run `scripts/inspect_agent_api.py` to print the exact signature in the active environment.

## Constructor Validation Rules

- `name` must satisfy `str.isidentifier()` and cannot equal `user`.
- Pydantic config forbids unknown extra fields; typos become validation errors rather than ignored options.
- `sub_agents` names should be unique. Duplicate child names are warned about and confuse routing.
- A sub-agent receives a `parent_agent` during construction. Reuse requires cloning or creating a second agent instance with a distinct name.
- `generate_content_config` is normalized to a `types.GenerateContentConfig` even when omitted.
- `generate_content_config.tools` raises `ValueError`: set tools through `LlmAgent.tools`.
- `generate_content_config.system_instruction` raises `ValueError`: set prompt text through `LlmAgent.instruction` or `static_instruction`.
- `generate_content_config.response_schema` raises `ValueError`: set response structure through `LlmAgent.output_schema`.
- If both planner thinking config and `generate_content_config.thinking_config` are set, the planner takes precedence and ADK warns.

## Modes And Delegation Semantics

| Mode | Use | Delegation behavior |
| --- | --- | --- |
| `chat` | Ongoing conversational root or transfer target | Standard chat agent reachable through ADK transfer behavior. |
| `task` | Delegated self-contained job that may ask clarifying questions | Parent sees it as a tool; task agent runs until it calls built-in `finish_task`. |
| `single_turn` | Isolated helper that processes immediate input | Parent sees it as a tool; no direct transfer target; defaults to no history in tool/node contexts. |

Important constraints:

- A root `LlmAgent` run by `Runner` must be `mode="chat"`; if `mode` is unset, the runner sets it to chat.
- A root `LlmAgent` with `mode="task"` or `mode="single_turn"` raises a `ValueError` in the runner path.
- `task` and `single_turn` sub-agents are exposed to the parent as tools, not direct `transfer_to_agent` targets.
- `task` mode automatically appends a `finish_task` tool. The output passed to `finish_task` is validated against `output_schema` when present.
- `single_turn` sub-agents run in isolated sub-branches. They only see immediate inputs unless `include_contents="default"` is set intentionally.
- Task mode is for sub-agent delegation, not workflow graph node execution.

## Model Configuration

- `model` accepts a provider/model string or `BaseLlm` instance.
- If `model` is empty, an agent inherits the nearest ancestor LLM model; otherwise ADK resolves a default model.
- Built-in defaults can change; specify `model` explicitly for reproducible apps.
- Model calls require provider credentials or a local provider configured outside the agent object. Construction can succeed without credentials; execution may fail later.
- Use `types.GenerateContentConfig(...)` only for provider generation options such as `temperature`, `safety_settings`, `response_modalities`, or similar GenAI fields that are not agent-owned.

## Tools And `FunctionTool`

`FunctionTool(func, require_confirmation=False)` wraps a callable as an ADK tool.

- The tool name comes from the function name or callable class name.
- The tool description comes from the callable docstring.
- Typed parameters become model-visible function declaration parameters.
- Parameters named or typed as `ToolContext` are hidden from the model and injected at execution time.
- Missing mandatory args return a structured error response so the model can retry.
- `require_confirmation` may be a boolean or callable; confirmation/HITL details route to `tools-and-integrations` and `workflow-orchestration` when graph-based.

Tool callback order during function execution:

1. Plugin `before_tool_callback`.
2. Agent `before_tool_callback` list, in order, until a truthy response.
3. Actual tool call if no before-callback response exists.
4. Plugin `on_tool_error_callback`, then agent `on_tool_error_callback`, if the tool raises.
5. Plugin `after_tool_callback`.
6. Agent `after_tool_callback` list, in order, until a truthy replacement response.

## Callback APIs

Agent-level callbacks:

- `before_agent_callback(callback_context)` returns optional `types.Content`; a returned content skips the run.
- `after_agent_callback(callback_context)` returns optional `types.Content`; a returned content appends an additional agent response event.
- State changes made through callback context can yield state-only events.

Model callbacks:

- `before_model_callback(callback_context, llm_request)` may mutate the request or return `LlmResponse` to skip the model call.
- `after_model_callback(callback_context, llm_response)` may return a replacement `LlmResponse`.
- `on_model_error_callback(callback_context, llm_request, error)` may return a fallback `LlmResponse`.
- Plugin callbacks run before agent callbacks.
- For a list of callbacks, ADK calls in list order and stops when one returns a non-`None` value.

Tool callbacks:

- `before_tool_callback(tool, args, tool_context)` may return a dict to skip the tool.
- `after_tool_callback(tool, args, tool_context, tool_response)` may return a replacement dict.
- `on_tool_error_callback(tool, args, tool_context, error)` may return a fallback dict; if it returns `None`, the original tool error propagates.
- Prefer returning explicit dicts such as `{"error": "..."}` or `{"result": "..."}` so downstream function responses are predictable.

## Structured Output And State

- `input_schema` is a Pydantic model type used when the agent is represented as a tool.
- `output_schema` can be a Pydantic model type, a list type such as `list[MyModel]` or `list[str]`, a raw schema dict, or a GenAI schema object.
- ADK 2.3.0 supports `output_schema` and `tools` together by using tools during the thought loop and enforcing structure on final output.
- When `output_key` is set, a final response authored by that agent writes to `event.actions.state_delta[output_key]`.
- If `output_schema` is set with `output_key`, ADK parses final response text as structured JSON before saving to state.
- Empty final streaming chunks are ignored to avoid overwriting state.
- State from sub-agent tool runs can be forwarded to the parent tool context.

## `RunConfig` And Runner Invocation Shape

`RunConfig` controls runtime behavior for an invocation. Agent-specific configuration may override run-level defaults.

Common fields:

- `streaming_mode`: `StreamingMode.NONE`, `StreamingMode.SSE`, or `StreamingMode.BIDI`; use `run_live()` for actual bidirectional live execution.
- `max_llm_calls`: positive values enforce a bound; `0` or negative values allow unbounded calls.
- `custom_metadata`: merged into generated events.
- `tool_thread_pool_config`: optional thread pool config for live tool execution.
- Live/audio fields such as speech configs, transcription configs, realtime input, proactivity, session resumption, and history config are available but require matching runtime/model support.
- Deprecated fields such as `save_input_blobs_as_artifacts` and `save_live_audio` should be replaced with plugin or current runtime alternatives.

`Runner.run` has a keyword-only shape:

```python
runner.run(
    user_id="user-1",
    session_id="session-1",
    new_message=types.Content(role="user", parts=[types.Part.from_text(text="Hi")]),
    state_delta=None,
    run_config=RunConfig(),
)
```

Runner notes:

- The sync `run` method is for local testing and convenience; production code should prefer `run_async`.
- Sessions must exist unless the runner is configured with `auto_create_session=True`.
- `new_message` must be a `types.Content` object; `run_async` can fill role `user` if omitted on a provided message.
- Runner/service persistence, session creation, plugins, telemetry, and artifacts route to `runtime-services`.

## Safe Validation Checks

- Construct the agent object without executing it.
- Print signatures with `scripts/inspect_agent_api.py`.
- Instantiate callbacks and tools with no network side effects.
- For execution tests, use in-memory services and mock or local models where possible; credential-dependent model calls are not required to validate constructor structure.
