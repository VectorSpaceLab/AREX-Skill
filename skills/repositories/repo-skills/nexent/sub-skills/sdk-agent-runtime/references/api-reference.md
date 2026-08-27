# SDK Runtime API Reference

This reference distills verified SDK runtime behavior from the SDK agent/model/tool/skills/scheduler/monitoring modules, SDK Basic Usage/Overview/Features/Monitoring documentation, and focused SDK/backend tests. It is self-contained: do not treat original repository docs or test artifacts as required runtime reading.

## Runtime ownership map

| Area | Primary APIs | Runtime ownership |
| --- | --- | --- |
| Agent data models | `ModelConfig`, `ToolConfig`, `AgentConfig`, `AgentRunInfo`, `AgentVerificationConfig` | SDK object contracts for direct runtime execution and backend-created run payloads. |
| Agent factory and loop | `NexentAgent`, `CoreAgent`, `agent_run` | Builds models/tools/sub-agents, runs SmolAgents-based code-agent loop, streams `MessageObserver` JSON chunks. |
| Models | `OpenAIModel` | OpenAI-compatible streaming adapter, provider extras, prompt cache, W1/W2 capacity and monitoring integration. |
| Tools | `ToolConfig`, SDK tool classes, `NexentAgent.create_tool` | Creates local, MCP, LangChain, and builtin tools; wraps visible tool calls for observer/monitoring. |
| MCP and A2A | `_normalize_mcp_config`, `ExternalA2AAgentConfig`, `A2AAgentInfo`, A2A proxy/wrapper classes | MCP hosts are normalized before `ToolCollection.from_mcp`; A2A agents are surfaced as managed-agent tools. |
| Sandbox | `SandboxConfig`, `build_python_executor`, `release_python_executor` | Optional local/Docker/WASM code-execution isolation injected into the SDK by the application boundary. |
| Verification | `AgentVerificationConfig`, `GuardrailConfig`, `GuardrailRule`, `VerificationController` | Step and final-answer verification plus regex guardrail checkpoints for input, tool args, and tool output. |
| Monitoring | `MonitoringConfig`, `AgentRunMetadata`, `MonitoringManager` | OTLP/OpenInference spans for agent runs, LLMs, tools, retrievers, token and context metrics. |
| Scheduler | `ScheduleSpec`, `compute_next_fire_at`, `LeaseScheduler` | Pure trigger calculation plus durable lease scheduler primitives. |
| Skill manager | `SkillManager`, `SkillLoader` | Tenant-isolated local skill CRUD, script execution, and `SKILL.md` parsing. |

## Core data model signatures

Signatures below were verified by runtime inspection.

### `ModelConfig`

```python
ModelConfig(
    *, cite_name: str, api_key: str = '', model_name: str, url: str,
    temperature: float | None = 0.1, top_p: float | None = 0.95,
    ssl_verify: bool | None = True, model_factory: str | None = None,
    extra_body: dict[str, Any] | None = None,
    max_output_tokens: int | None = None, max_tokens: int | None = None,
    context_window_tokens: int | None = None, max_input_tokens: int | None = None,
    default_output_reserve_tokens: int | None = None,
    tokenizer_family: str | None = None, capacity_source: str | None = None,
    capability_profile_version: str | None = None,
    timeout_seconds: float | None = None, concurrency_limit: int | None = None,
    prompt_cache: dict[str, Any] | None = None,
) -> None
```

Important semantics:

- `cite_name` is the model alias used by `AgentConfig.model_name`.
- `model_name` is the provider model id passed to the OpenAI-compatible client.
- `url` is the provider base URL. The SDK does not read provider URLs from environment variables.
- `extra_body` is merged into OpenAI-compatible request bodies for provider-specific switches.
- `max_output_tokens` is preferred. Legacy `max_tokens` backfills `max_output_tokens`; very large legacy context-window values are bounded conservatively.
- Capacity fields (`context_window_tokens`, `max_input_tokens`, `default_output_reserve_tokens`, `tokenizer_family`, `capacity_source`, `capability_profile_version`) are used by capacity/budget resolution and monitoring.
- `prompt_cache` stores selected provider cache capabilities; unknown/absent support disables provider cache directives while still allowing deterministic metrics.

### `ToolConfig`

```python
ToolConfig(
    *, class_name: str, name: str | None,
    description: str | None = None, inputs: str | None = None,
    output_type: str | None = None, params: dict[str, Any] = None,
    source: str = 'local', usage: str | None = None,
    metadata: dict[str, Any] | None = None, labels: list[str] | None = None,
) -> None
```

`source` routing:

| `source` | Runtime behavior |
| --- | --- |
| `local` | `class_name` is looked up among SDK tool imports and constructed with `params`; selected excluded/runtime-only objects are injected from `metadata`. |
| `mcp` | `class_name` must match a tool exposed by the active MCP `ToolCollection`. |
| `langchain` | `metadata` carries the LangChain tool object and is wrapped with `Tool.from_langchain`. |
| `builtin` | Builtin SDK tools such as skill-file readers/writers, plan tools, and scheduled-task proposal tools are constructed by explicit branches. |

`inputs` may be a JSON string; `NexentAgent.create_local_tool` parses it and assigns a dict to tool instances that expose `inputs`.

### `AgentVerificationConfig`, `GuardrailConfig`, `GuardrailRule`

```python
AgentVerificationConfig(
    *, enabled: bool = False, step_verification_enabled: bool = True,
    final_verification_enabled: bool = True, llm_verification_enabled: bool = True,
    max_final_rounds: int = 2, strictness: Literal['lenient','balanced','strict'] = 'balanced',
    fail_policy: Literal['repair_then_controlled_summary','warn'] = 'repair_then_controlled_summary',
    pass_score: float = 0.75,
    critical_events: list[Literal['tool_precheck','tool_result','retrieval','code_execution','handoff','final_answer']] = ...,
    guardrail_config: GuardrailConfig | None = None,
) -> None

GuardrailRule(*, name: str, pattern: str, severity: Literal['block','mask','pass'] = 'block', description: str | None = None) -> None
GuardrailConfig(*, enabled: bool = False, rules: list[GuardrailRule] = ..., default_action: Literal['block','mask','pass'] = 'pass') -> None
```

Guardrail checkpoints:

- New input: `block` becomes terminal refusal; `mask` redacts and continues.
- History and tool output: `block` is downgraded to masking because the data already exists in context/output.
- Tool input: `block` prevents the tool call from running.
- Verification emits `ProcessType.VERIFICATION` messages only when verification is enabled.

### `AgentConfig`

```python
AgentConfig(
    *, name: str, description: str,
    prompt_templates: dict[str, Any] | None = None,
    tools: list[ToolConfig], max_steps: int = 15,
    requested_output_tokens: int | None = None,
    model_name: str, provide_run_summary: bool | None = False,
    instructions: str | None = None,
    managed_agents: list[AgentConfig] = [],
    external_a2a_agents: list[ExternalA2AAgentConfig] = [],
    context_manager_config: Any | None = None,
    context_items: list[ContextItemInput] | None = None,
    pre_run_tool_events: list[dict[str, Any]] = ...,
    capacity_snapshot: dict[str, Any] | None = None,
    safe_input_budget_snapshot: dict[str, Any] | None = None,
    verification_config: AgentVerificationConfig = ...,
    enable_planning: bool = False,
    sandbox_policy: dict[str, Any] | None = None,
) -> None
```

Key points:

- `model_name` must equal a `ModelConfig.cite_name` in `AgentRunInfo.model_config_list`.
- `managed_agents` recursively construct local sub-agents that share the parent executor.
- `external_a2a_agents` are converted to A2A wrappers and added as managed-agent tools.
- `context_manager_config` and `context_items` feed the context runtime; direct SDK callers can still pass `context_items` when no run-scoped `context_input` is present.
- `enable_planning=True` wires plan tools to a `PlanRepo`; no eager planning step is emitted before the first tool action.
- `sandbox_policy` is a serializable intent. The backend/application boundary resolves it to `SandboxConfig` and places it on `AgentRunInfo.sandbox_config`.

### `AgentRunInfo`

```python
AgentRunInfo(
    query: str,
    model_config_list: list[ModelConfig],
    observer: MessageObserver,
    agent_config: AgentConfig,
    stop_event: threading.Event,
    mcp_host: list[str | dict[str, Any]] | None = None,
    history: list[AgentHistory] | None = None,
    conversation_id: int | None = None,
    user_id: str | None = None,
    context_input: Any | None = None,
    capacity_snapshot: dict[str, Any] | None = None,
    safe_input_budget_snapshot: dict[str, Any] | None = None,
    enable_planning: bool = False,
    redis_client: Any | None = None,
    sandbox_config: Any | None = None,
    minio_client: Any | None = None,
)
```

Pydantic exposes `AgentRunInfo(**data)` because it allows arbitrary types. Required runtime fields are `query`, `model_config_list`, `observer`, `agent_config`, and `stop_event`.

`context_input` has priority over `history` for production context assembly: when present, authorized context items come from the immutable run snapshot and historical conversation objects are not separately appended to the agent memory.

## Agent factory and loop APIs

### `CoreAgent`

```python
CoreAgent.__init__(
    self,
    observer: MessageObserver,
    prompt_templates: dict[str, Any] | None = None,
    verification_config: AgentVerificationConfig | None = None,
    *args,
    **kwargs,
)
```

`CoreAgent` extends SmolAgents `CodeAgent`. Common keyword arguments passed through `kwargs` include `tools`, `model`, `name`, `description`, `max_steps`, `managed_agents`, `instructions`, `context_runtime`, `enable_planning`, `redis_client`, `conversation_id`, `user_id`, and `executor`.

Important methods/helpers:

```python
CoreAgent.run(self, task: str, stream: bool = False, reset: bool = True, images: list | None = None, additional_args: dict | None = None, max_steps: int | None = None, return_full_result: bool | None = None)
parse_code_blobs(text: str) -> str
convert_code_format(text) -> str
```

Execution format:

- Executable model actions are extracted from `<code>...</code>` blocks.
- Legacy ```<RUN>...</RUN>``` blocks still work.
- Plain ```python/```py blocks are intentionally ignored for execution so knowledge-base examples are not accidentally run.
- Display blocks can use `<DISPLAY:language>...</DISPLAY>` and are converted to Markdown for final answers.

### `NexentAgent`

```python
NexentAgent.__init__(
    self, observer: MessageObserver, model_config_list: list[ModelConfig],
    stop_event: threading.Event, mcp_tool_collection=None, redis_client=None,
    sandbox_config=None, minio_client=None,
    conversation_id=None, user_id=None,
)

NexentAgent.create_single_agent(self, agent_config: AgentConfig, _managed_context: bool = False, *, context_items_override: Sequence[ContextItemInput] | None = None) -> CoreAgent
```

Factory behavior:

- `create_model(model_cite_name)` finds a `ModelConfig` by `cite_name`, constructs `OpenAIModel`, and attaches `stop_event`.
- `create_tool(tool_config)` dispatches by `ToolConfig.source` and wraps local/builtin/MCP tools for host execution when remote sandboxing is active.
- `create_single_agent` recursively builds managed agents, wraps A2A agents, builds a `ContextManager`/`ManagedContextRuntime`, optionally builds a sandbox executor, creates `CoreAgent`, wires plan tools when planning is enabled, and returns the agent.
- `agent_run_with_observer(query, reset=True)` streams a `CoreAgent.run(..., stream=True)` loop into the observer and adds final-answer/error/token-count events.

### `agent_run`

```python
async def agent_run(agent_run_info: AgentRunInfo):
    ...  # async generator yielding JSON strings from MessageObserver
```

Runtime flow:

1. `agent_run` starts `agent_run_thread` in a background thread.
2. The thread sets monitoring capacity/budget snapshots, emits an uncertainty-reserve warning when present, normalizes MCP hosts when supplied, constructs `NexentAgent`, creates a `CoreAgent`, adds authorized history/context, and calls `agent_run_with_observer`.
3. The async generator repeatedly drains `observer.get_cached_message()` and yields each JSON string until the thread finishes.
4. A final drain yields any remaining messages.

## Model APIs

### `OpenAIModel`

```python
OpenAIModel.__init__(
    self, observer: MessageObserver = MessageObserver,
    temperature=0.2, top_p=0.95, ssl_verify=True,
    model_factory: str | None = None, display_name: str | None = None,
    extra_body: dict[str, Any] | None = None,
    max_output_tokens: int | None = None, max_tokens: int | None = None,
    safe_input_budget_snapshot: SafeInputBudgetSnapshot | dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
    *args,
    **kwargs,
)
```

`model_id`, `api_key`, and `api_base` are inherited OpenAI-compatible keyword arguments. The adapter:

- Streams completions and forwards tokens/reasoning to `MessageObserver`.
- Converts dict messages to SmolAgents `ChatMessage` objects.
- Applies `extra_body` only when explicitly supplied.
- Uses `max_output_tokens` unless a trusted W2 safe-input-budget snapshot supplies the request output limit.
- Rejects stale/mismatched W1/W2 budget snapshots at dispatch.
- Records prompt-cache status, token usage, finish reason, and OpenInference attributes.
- Raises on `stop_event` interruption or malformed provider error strings/dicts.

## Observer and stream event contract

```python
MessageObserver.__init__(self, lang='zh', enable_nl2a_wrapper=False)
MessageObserver.add_message(self, agent_name, process_type, content, **kwargs)
MessageObserver.get_cached_message(self) -> list[str]
MessageObserver.get_final_answer(self) -> str | None
```

Common `ProcessType` values emitted by SDK runtime:

| Event | Meaning |
| --- | --- |
| `AGENT_NEW_RUN` | New run/task marker; MCP path emits `<MCP_START>` before connecting tools. |
| `STEP_COUNT` | Agent step number. |
| `MODEL_OUTPUT_THINKING`, `MODEL_OUTPUT_DEEP_THINKING`, `MODEL_OUTPUT_CODE` | Streaming model text classified by observer token parsing. |
| `PARSE` | Parsed executable code action. |
| `TOOL` | Visible tool-call event with optional `tool_name`, `tool_arguments`, `tool_call_id`. |
| `EXECUTION_LOGS` | Code/tool execution logs and last output snippets. |
| `TOKEN_COUNT` | Per-step token/context/cache metrics. |
| `HISTORY_SUMMARY` | Context compression/history summary event. |
| `SUBAGENT_START`, `SUBAGENT_END`, `AGENT_FINISH` | Nested managed-agent/A2A boundaries and completion. |
| `VERIFICATION` | Verification and guardrail results. |
| `PLAN`, `PLAN_STEP_UPDATE`, `AUTOMATION_PROPOSAL` | Planning and scheduled-task proposal events. |
| `FINAL_ANSWER`, `ERROR`, `MAX_STEPS_REACHED` | Terminal answer/error/control events. |

## MCP transport helpers

```python
_normalize_mcp_config(mcp_host_item: str | dict[str, Any]) -> dict[str, Any]
```

Rules:

- String URL ending exactly in `/sse` -> `{"url": url, "transport": "sse"}`.
- String URL ending exactly in `/mcp` -> `{"url": url, "transport": "streamable-http"}`.
- Other string URL -> `streamable-http`.
- Dict must include `url`; explicit `transport` must be `sse` or `streamable-http` and overrides auto-detection.
- `authorization` becomes `headers.Authorization`; if both `headers` and `authorization` are supplied, authorization is merged into a copy of headers.

## A2A APIs

```python
ExternalA2AAgentConfig(
    *, agent_id: str, name: str, description: str = '', url: str,
    api_key: str | None = None, transport_type: str = 'http-streaming',
    protocol_version: str = '1.0', protocol_type: str = 'JSONRPC',
    timeout: float = 300.0, raw_card: dict[str, Any] | None = None,
    custom_headers: dict[str, str] | None = None,
) -> None

A2AAgentInfo(agent_id: str, name: str, url: str, api_key: str | None = None, transport_type: str = 'http-streaming', protocol_version: str = '1.0', protocol_type: str = 'JSONRPC', timeout: float = 300.0, raw_card: dict[str, Any] | None = None, custom_headers: dict[str, str] | None = None)
ExternalA2AAgentProxy.call(self, query: str, history: list[dict[str, str]] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]
ExternalA2AAgentProxy.sync_call(self, query: str, history: list[dict[str, str]] | None = None, context: dict[str, Any] | None = None) -> str
ExternalA2AAgentWrapper.run(self, task: str = None, **kwargs) -> str
A2AAgentProxyTool.forward(self, input_str: str) -> str
```

Protocol constants are `JSONRPC`, `HTTP+JSON`, and `GRPC`. `raw_card.skills` can enrich agent descriptions with capabilities and examples. Custom headers override the default bearer authorization header when supplied.

## Sandbox APIs

```python
SandboxConfig(
    level: SandboxLevel = SandboxLevel.LOCAL,
    scope: SandboxScope = SandboxScope.SESSION,
    docker_image: str = 'nexent/nexent-sandbox:latest',
    memory_limit_mb: int = 512, cpu_quota: float = 1.0,
    network_disabled: bool = True, timeout_seconds: int = 30,
    shell_policy: ShellPolicy = ShellPolicy.DISABLED,
    output_dir: str = '/home/sandbox/workdir/output',
    auto_sync_outputs: bool = True,
    extra_kwargs: dict[str, Any] = {},
) -> None

build_python_executor(config: SandboxConfig, logger_: logging.Logger, managed_agents_exist: bool = False, host_tools_exist: bool = False) -> Any
release_python_executor(executor: Any, logger_: logging.Logger) -> None
```

`SandboxLevel`: `local`, `docker`, `wasm`. `SandboxScope`: `session`, `system`. `ShellPolicy`: `disabled`, `restricted`, `boxed`.

The SDK sandbox module does not read environment variables. Remote executors are wrapped with a shell-call guard and missing-package diagnostics. Docker/WASM executor construction falls back to a local executor when optional dependencies or runtime backends are unavailable. Non-local sandboxing with managed agents falls back to local because managed agents share the parent's Python executor.

## Monitoring APIs

```python
AgentRunMetadata(
    tenant_id: str | None = None, user_id: str | None = None,
    agent_id: int | None = None, conversation_id: int | None = None,
    agent_name: str | None = None, query: str | None = None,
    is_debug: bool | None = None, language: str | None = None,
    model_name: str | None = None, memory_enabled: bool | None = None,
    history_count: int | None = None, minio_files_count: int | None = None,
    extra_metadata: dict[str, Any] = {},
)

MonitoringConfig(enable_telemetry: bool = False, service_name: str = 'nexent-backend', provider: str = 'otlp', otlp_endpoint: str = 'http://localhost:4318', ...)
MonitoringManager.configure(self, config: MonitoringConfig) -> None
MonitoringManager.start_agent_run(self, metadata: AgentRunMetadata | dict[str, Any] | None = None, operation_name: str = 'agent.run')
MonitoringManager.trace_tool_call(self, tool_name: str, agent_name: str, tool_input: dict | None = None, **attributes)
MonitoringManager.trace_retriever_call(self, retriever_name: str, agent_name: str | None = None, retrieval_input: dict | None = None, **attributes)
```

`NexentAgent` wraps tools with monitoring. `KnowledgeBaseSearchTool` and `SearchMemoryTool` are classified as retriever spans. Trace payload mode should remain bounded (`summary`/`metrics`/`full` with configured limits) to avoid leaking or overloading trace backends.

## Scheduler APIs

```python
ScheduleSpec(
    mode: ScheduleMode, rule_type: ScheduleRuleType, timezone: str,
    start_at: datetime, end_at: datetime | None = None,
    cron_expr: str | None = None, interval_seconds: int | None = None,
    max_fire_count: int | None = None,
) -> None

compute_next_fire_at(spec: ScheduleSpec, after: datetime, fire_count: int) -> datetime | None
is_valid_cron_expression(expression: str) -> bool

SchedulerConfig(poll_interval_seconds: float = 5.0, lease_seconds: float = 120.0, max_concurrency: int = 2, shutdown_grace_seconds: float = 30.0, error_backoff_seconds: float = 1.0, max_error_backoff_seconds: float = 30.0)
LeaseScheduler(store, executor, config: SchedulerConfig, owner_id: str | None = None)
```

`ScheduleMode`: `ONCE`, `RECURRING`. `ScheduleRuleType`: `AT`, `INTERVAL`, `CRON`. Cron validation expects five fields. Returned fire times are UTC-aware datetimes.

## Skill manager APIs

```python
SkillManager.__init__(self, base_skills_dir: str | None = None)
SkillManager.list_skills(self, *, tenant_id: str | None) -> list[dict[str, str]]
SkillManager.load_skill(self, name: str, *, tenant_id: str | None) -> dict[str, Any] | None
SkillManager.save_skill(self, skill_data: dict[str, Any], *, tenant_id: str | None) -> dict[str, Any]
SkillManager.run_skill_script(self, skill_name: str, script_path: str, params: str | None = None, *, tenant_id: str | None) -> Any
SkillLoader.load(path: str) -> dict[str, Any]
SkillLoader.parse(content: str, source_path: str = '') -> dict[str, Any]
```

The manager is tenant-isolated and treats the base skills directory as immutable after first construction. Script execution should be tested with temporary skill roots and without real credentials or service startup.
