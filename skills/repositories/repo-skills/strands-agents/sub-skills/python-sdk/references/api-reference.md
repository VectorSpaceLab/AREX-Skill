# Python SDK API reference

This reference captures the verified public surface and the highest-value source-backed contracts for the Python SDK.

## Public exports

| Package | Public surface |
| --- | --- |
| `strands` | `Agent`, `AgentBase`, `AgentSkills`, `InterventionHandler`, `agent`, `models`, `ModelRetryStrategy`, `MultiAgentPlugin`, `Plugin`, `PosixShellSandbox`, `Sandbox`, `SandboxPathNotFoundError`, `SandboxTimeoutError`, `Skill`, `Snapshot`, `storage`, `tool`, `ToolContext`, `types`, `telemetry` |
| `strands.models` | `bedrock`, `model`, `BaseModelConfig`, `BedrockModel`, `CacheConfig`, `CacheToolsConfig`, `Model` |
| `strands.tools` | `tool`, `PythonAgentTool`, `InvalidToolUseNameException`, `normalize_schema`, `normalize_tool_spec`, `convert_pydantic_to_tool_spec`, `ToolProvider` |
| `strands.plugins` | `MultiAgentPlugin`, `Plugin`, `hook` |
| `strands.multiagent` | `EdgeCondition`, `EdgeConditionWithContext`, `GraphBuilder`, `GraphResult`, `MultiAgentBase`, `MultiAgentResult`, `Status`, `Swarm`, `SwarmResult` |
| `strands.session` | `FileSessionManager`, `RepositorySessionManager`, `S3SessionManager`, `SaveLatestStrategy`, `SessionManager`, `SessionRepository`, `SnapshotSessionManager`, `SnapshotTrigger` |
| `strands.memory` | `AddMessagesContext`, `AggregateMemoryError`, `ExtractionConfig`, `ExtractionResult`, `ExtractionTrigger`, `ExtractionTriggerContext`, `Extractor`, `ExtractorContext`, `InjectionConfig`, `InjectionContext`, `InjectionFormatContext`, `InjectionQueryContext`, `InjectionTrigger`, `IntervalTrigger`, `InvocationTrigger`, `MemoryAddOptions`, `MemoryAddToolConfig`, `MemoryContentBlockType`, `MemoryEntry`, `MemoryInjectionConfig`, `MemoryManager`, `MemoryManagerConfig`, `MemoryMessageFilter`, `MemorySearchOptions`, `MemoryStore`, `MemoryStoreConfig`, `MemoryToolConfig`, `ModelExtractor`, `SearchOptions` |
| `strands.sandbox` | `ExecutionResult`, `FileInfo`, `LANGUAGE_PATTERN`, `OutputFile`, `PosixShellSandbox`, `Sandbox`, `StreamChunk`, `StreamType` |
| `strands.telemetry` | `EventLoopMetrics`, `Trace`, `metrics_to_string`, `MetricsClient`, `Tracer`, `get_tracer`, `StrandsTelemetry` |

## Verified signature facts

| Surface | Verified contract |
| --- | --- |
| `Agent.__init__` | Accepts `model`, `messages`, `tools`, `system_prompt`, `structured_output_model`, `callback_handler`, `conversation_manager`, `record_direct_tool_call`, `load_tools_from_directory`, `trace_attributes`, then keyword-only `agent_id`, `name`, `description`, `state`, `context_manager`, `plugins`, `hooks`, `interventions`, `session_manager`, `memory_manager`, `structured_output_prompt`, `tool_executor`, `retry_strategy`, `concurrent_invocation_mode`, `checkpointing`, `sandbox`. |
| `Agent.__call__` / `invoke_async` / `stream_async` | Accept `prompt` plus keyword-only `invocation_state`, `structured_output_model`, `structured_output_prompt`, `idempotency_token`, and `limits`. |
| `Agent.structured_output(output_model, prompt=None)` | Returns the requested Pydantic model type. The method is deprecated in favor of `structured_output_model` on the main invocation path. |
| `Agent.as_tool(*, name=None, description=None, preserve_context=False)` | Returns an `AgentTool` wrapper. |
| `Agent.add_hook(callback, event_type=None, *, order=HookOrder.DEFAULT)` | Registers a callback by explicit event type or by inferring the event type from annotations. |
| `Agent.take_snapshot(...)` / `load_snapshot(snapshot)` | Expose the snapshot API used by checkpointing and time-travel workflows. |
| `tool(func=None, description=None, inputSchema=None, name=None, context=False)` | Supports both decorator and factory forms. `context=True` injects `ToolContext` into the named parameter. |
| `MCPClient.__init__` | Accepts `transport_callable`, then keyword-only `startup_timeout=30`, `tool_filters`, `prefix`, `application_name`, `application_version`, `continue_on_error`, `elicitation_callback`, `progress_callback`, and `tasks_config`. |
| `MCPClient.load_servers(config)` | Accepts either a config mapping or a file path and returns enabled clients. |
| `SlidingWindowConversationManager` | Defaults verified: `window_size=40`, `should_truncate_results=True`, `per_turn=False`, `pin_first=None`, `proactive_compression=None`. |
| `SummarizingConversationManager` | Defaults verified: `summary_ratio=0.3`, `preserve_recent_messages=10`, `summarization_agent=None`, `summarization_system_prompt=None`, `pin_first=None`, `proactive_compression=None`. |
| `FileSessionManager` / `S3SessionManager` | `FileSessionManager(session_id, storage_dir=None, **kwargs)` and `S3SessionManager(session_id, bucket, prefix='', boto_session=None, boto_client_config=None, region_name=None, endpoint_url=None, **kwargs)`. |
| `GraphBuilder` | Zero-arg constructor; mutators include `add_node`, `add_edge`, `set_entry_point`, `set_max_node_executions`, `set_execution_timeout`, `set_node_timeout`, `set_graph_id`, `set_session_manager`, `set_hook_providers`, `set_plugins`, `build`. |
| `Swarm` | `Swarm(nodes, *, entry_point=None, max_handoffs=20, max_iterations=20, execution_timeout=900.0, node_timeout=300.0, repetitive_handoff_detection_window=0, repetitive_handoff_min_unique_agents=0, session_manager=None, hooks=None, id=_DEFAULT_SWARM_ID, trace_attributes=None, plugins=None)`. |

## Package metadata and extras

| Field | Value |
| --- | --- |
| `requires-python` | `>=3.10` |
| Build backend | `hatchling` + `hatch-vcs` |
| Base runtime deps | `boto3`, `botocore`, `docstring_parser`, `httpx`, `jsonschema`, `mcp`, `pydantic`, `typing-extensions`, `pyyaml`, `watchdog`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-threading` |
| Optional extras | `anthropic`, `gemini`, `litellm`, `llamaapi`, `mistral`, `ollama`, `openai`, `writer`, `sagemaker`, `otel`, `docs`, `a2a`, `bidi`, `bidi-io`, `bidi-gemini`, `bidi-openai`, `cedar` |
| Meta extras | `all`, `bidi-all` |
| Dev extra | `dev` |

## Model and provider contract

`strands.models.__getattr__` lazily exposes heavier providers so importing `strands.models` does not force every optional dependency.

| Module | Class | Extra | Notes |
| --- | --- | --- | --- |
| `strands.models.bedrock` | `BedrockModel` | base | Default model when `Agent(model=None)` |
| `strands.models.anthropic` | `AnthropicModel` | `anthropic` | Anthropic-style streaming and structured output |
| `strands.models.gemini` | `GeminiModel` | `gemini` | Gemini streaming and token counting |
| `strands.models.litellm` | `LiteLLMModel` | `litellm` + `openai` | OpenAI-compatible wrapper with LiteLLM proxy support |
| `strands.models.llamaapi` | `LlamaAPIModel` | `llamaapi` | LlamaAPI transport |
| `strands.models.llamacpp` | `LlamaCppModel` | base | Local llama.cpp server integration |
| `strands.models.mistral` | `MistralModel` | `mistral` | Mistral provider |
| `strands.models.ollama` | `OllamaModel` | `ollama` | Local Ollama provider |
| `strands.models.openai` | `OpenAIModel` | `openai` | OpenAI and OpenAI Responses API contract |
| `strands.models.sagemaker` | `SageMakerAIModel` | `sagemaker` | OpenAI-compatible SageMaker wrapper |
| `strands.models.writer` | `WriterModel` | `writer` | Writer SDK integration |
| `strands.experimental.bidi` | `Bidi*` classes | `bidi`, `bidi-io`, `bidi-gemini`, `bidi-openai` | Experimental bidirectional streaming path |

### Model base contract

`Model` defines the common provider surface:

- `update_config(**model_config)`
- `get_config()`
- `structured_output(output_model, prompt, system_prompt=None, **kwargs)`
- `stream(messages, tool_specs=None, system_prompt=None, *, tool_choice=None, system_prompt_content=None, invocation_state=None, **kwargs)`
- `count_tokens(messages, tool_specs=None, system_prompt=None, system_prompt_content=None)`
- `stateful`
- `context_window_limit`
- `estimate_utilization(input_tokens)`

Provider implementations should translate throttling and context-window errors into typed SDK exceptions such as `ModelThrottledException` and `ContextWindowOverflowException` and chain the original exception with `from`.

## Tool contract

- `FunctionToolMetadata` extracts name, description, input schema, and validation model from a Python function.
- `DecoratedFunctionTool.stream(...)` returns `ToolStreamEvent`, `ToolInterruptEvent`, or `ToolResultEvent` values.
- Sync tool bodies are run in a worker thread; async generators stream their yielded events.
- The `tool_spec` setter validates the tool name and required fields; it cannot rename the tool at runtime.
- `ToolContext` injection requires `@tool(context=True)` or a custom context parameter name.

## MCP client contract

- `MCPClient` runs a background thread with its own asyncio loop.
- `load_servers(config)` accepts either a mapping or a config file and supports `command` / `url`, `disabled`, `continue_on_error`, env interpolation, and transport selection.
- `call_tool_sync` and `call_tool_async` support per-call cancellation.
- Task-augmented execution is opt-in through `TasksConfig` and server/task capability detection.
- `CLIENT_SESSION_NOT_RUNNING_ERROR_MESSAGE` is the canonical session-state failure message when the client is used outside its context manager.

## Memory, sessions, and checkpoints

- `MemoryManager` is a plugin that registers search/add tools and can also inject or extract memory context.
- `MemoryStore` is a protocol with `search` plus optional `add`, `add_messages`, `initialize`, and `get_tools`.
- `SessionManager` persists agent, multi-agent, and bidi state through hooks; unsupported multi-agent/bidi methods raise `NotImplementedError` by default.
- `SnapshotSessionManager` persists snapshots to a `Storage` backend and supports restore/save latest workflows.
- `Checkpoint` lives in the experimental checkpoint module and marks pause points at `after_model` or `after_tools` boundaries.

## Hooks, interventions, plugins, sandbox, telemetry, and multi-agent

- Hook event names are shared and use `Before{Action}Event` / `After{Action}Event` pairs.
- `InterventionHandler` handles `before_invocation`, `before_tool_call`, `after_tool_call`, `before_model_call`, and `after_model_call`.
- `Plugin` and `MultiAgentPlugin` provide composable extension points for agents and orchestrators.
- `Sandbox` provides async command, code, and file operations; `PosixShellSandbox` is the shell-backed base for Docker and SSH variants.
- `Tracer`, `StrandsTelemetry`, `EventLoopMetrics`, and `MetricsClient` cover tracing and metrics.
- `GraphBuilder` / `Graph` and `Swarm` are the main multi-agent orchestration surfaces; `A2A` helpers live under `strands.multiagent.a2a`.
