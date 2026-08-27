# SDK Runtime Troubleshooting

Use this guide for SDK-agent-runtime failures before escalating to sibling sub-skills. Keep diagnostics deterministic: prefer construction checks, static inspection, mocked tests, and the bundled inspection script over live model/service calls.

## Quick diagnostic checklist

1. Run `python sub-skills/sdk-agent-runtime/scripts/inspect_sdk_runtime.py --repo-root . --json` and confirm target modules, signatures, tool exports, and MCP normalization examples.
2. Confirm `AgentConfig.model_name` exactly equals one `ModelConfig.cite_name`.
3. Confirm tests do not iterate real `agent_run` unless model/MCP/tool/network calls are mocked.
4. Confirm MCP URLs end exactly in `/sse` or `/mcp`, or provide explicit `transport`.
5. Confirm SDK code receives config objects; backend env-var reads and service wiring belong to `backend-services-api`.

## Import and dependency mismatches

Symptoms:

- `ModuleNotFoundError` while importing optional SDK modules.
- `pip check` conflicts when trying to install all backend/data-process and SDK distribution dependencies into one environment.
- `nexent.data_process.core` import fails in an SDK-only install.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Optional data-processing dependencies are not installed in the SDK-only environment. | Treat deep data-processing workflows as optional or route them to `knowledge-data-memory`; install only the needed extras in a controlled inspection/runtime environment. |
| Backend/data-process dependency variants conflict with SDK distribution pins. | Use separate minimal environments for SDK distribution inspection and backend/data-process inspection when necessary; do not encode private environment paths in runtime guidance. |
| External tool/provider package missing (`exa_py`, `tavily`, `linkup`, OpenAI-compatible client extras). | For unit tests, mock the external package or tool class. For live use, install the specific dependency and provide credentials explicitly. |
| Source path not importable. | Run from a checkout and pass `--repo-root` to the bundled script, or install the SDK package in editable mode. |

Do not fix import failures by adding SDK-level `os.getenv()` reads; configuration stays outside the SDK and is passed in as model/tool/sandbox objects.

## External model calls accidentally happen in tests

Symptoms:

- Unit tests hang, hit network, fail with provider auth errors, or consume tokens.
- `OpenAIModel.__call__` is reached while only object construction was intended.

Fixes:

- Do not iterate the real `agent_run` async generator in construction tests.
- Inject a fake async runner that yields JSON observer chunks.
- Monkeypatch `NexentAgent` when testing `agent_run_thread` routing.
- Monkeypatch `OpenAIModel`, provider clients, or the agent's model callable when testing `CoreAgent` behavior.
- Set `AgentVerificationConfig(llm_verification_enabled=False)` for deterministic verification tests.

A safe test can construct `AgentRunInfo` with `api_key=""` and `url="http://example.invalid/v1"` as long as it does not call the real provider path.

## `Model ... not found`

`NexentAgent.create_model` searches `model_config_list` by `ModelConfig.cite_name`. The `AgentConfig.model_name` field must be the alias, not the provider model id.

Correct:

```python
ModelConfig(cite_name="default_llm", model_name="Qwen/Qwen2.5-32B-Instruct", url="...", api_key="...")
AgentConfig(name="agent", description="...", tools=[], model_name="default_llm")
```

Incorrect:

```python
AgentConfig(..., model_name="Qwen/Qwen2.5-32B-Instruct")  # unless cite_name is also that exact string
```

## `AgentRunInfo` validation errors

Common missing/invalid fields:

- `query` is required.
- `model_config_list` must be a list of `ModelConfig` objects.
- `observer` must be a `MessageObserver` for real execution.
- `agent_config` must be an `AgentConfig`.
- `stop_event` must be a `threading.Event`-like object with `is_set()` and `set()` for real control.
- `tools` in `AgentConfig` is required even when empty.

Because `AgentRunInfo` allows arbitrary types, validation may succeed while runtime still fails if an injected object lacks the expected methods. Prefer lightweight fakes with the same method names over raw dicts for `observer`, `stop_event`, Redis, MinIO, or tool clients.

## MCP transport chooses the wrong type

Nexent detection is suffix-based:

- URL string ending exactly `/sse` -> `sse`.
- URL string ending exactly `/mcp` -> `streamable-http`.
- Anything else -> `streamable-http`.
- Dict `transport` wins over auto-detection.

Failure patterns:

| Symptom | Check | Fix |
| --- | --- | --- |
| `/sse` server is treated as `streamable-http`. | URL has trailing slash, query string, or path suffix after `/sse`. | Use `{"url": ".../sse", "transport": "sse"}` or normalize the URL. |
| `/mcp` server is treated as `sse`. | Explicit dict transport says `sse`. | Remove/replace explicit transport. |
| `ValueError: MCP host dict must contain 'url' key`. | Dict key is missing or misspelled. | Provide `url`. |
| `ValueError: Invalid transport type`. | Transport is not exactly `sse` or `streamable-http`. | Use one of those exact strings. |
| Authorization header missing. | Token was not passed as `authorization` or `headers.Authorization`. | Pass `authorization="Bearer ..."` or explicit `headers`. |

If the URL is assembled by backend NL2Agent/NL2Skill code, route the service-string construction bug to `backend-services-api`; keep this SDK transport contract unchanged unless tests prove the SDK helper is wrong.

## MCP connection timeout or server failure

Symptoms:

- Final observer message says `Couldn't connect to the MCP server.`
- The run emits `<MCP_START>` and then fails before tool creation.

Fixes:

- Confirm MCP host list normalization first without connecting.
- In unit tests, monkeypatch `ToolCollection.from_mcp` to a context manager and assert normalized arguments.
- For live debugging, confirm the server is reachable outside the SDK and that auth headers match the server's transport.
- Do not set `trust_remote_code=True` against untrusted MCP servers unless the deployment policy allows it; the SDK currently passes that flag when creating the collection.

## Tool creation failures

Symptoms:

- `Error in creating tool: ... not found in local`.
- `Unknown builtin tool`.
- Tool constructor complains about unexpected params.
- Tool calls appear twice or not at all in stream/monitoring.

Fixes:

| Problem | Fix |
| --- | --- |
| `class_name` typo or unexported local tool. | Compare against SDK tool exports with `inspect_sdk_runtime.py`. Add/export the tool only if it is a true SDK-local tool. |
| Wrong `source`. | Use `local`, `mcp`, `langchain`, or `builtin` according to the factory branch. |
| Runtime-only objects passed in `params`. | Move observer, vector DB clients, embedding/rerank models, document whitelists, memory service/context, or storage clients into `metadata` as the factory expects. |
| `inputs` is a JSON string but malformed. | Store a JSON object string or pass `None`; the factory only assigns parsed dicts. |
| Search/email/multimodal tools require credentials or services. | Mock the tool in tests; provide credentials and network only for approved live checks. |
| Retriever span classification missing. | `KnowledgeBaseSearchTool` and `SearchMemoryTool` are the SDK-recognized retriever classes. Custom retrievers need explicit monitoring calls. |

Deep knowledge-base, vector database, storage, or memory behavior belongs in `knowledge-data-memory`.

## Code-block parsing failures

Symptoms:

- `ValueError: no valid executable code block pattern`.
- Model returns historical tool records, JSON action traces, or plain Python Markdown blocks and the agent treats them as final answer or invalid action.

Fixes:

- In prompts/templates, require executable actions inside `<code>...</code>`.
- Do not rely on plain ```python blocks for execution; they are intentionally ignored.
- Use `<DISPLAY:python>...</DISPLAY>` for code that should appear in the final answer, not run.
- If model output includes historical action records, prompt it not to copy prior tool logs and to emit one fresh executable action or a final answer.

## Stop events and interruptions

Symptoms:

- Stream appears to continue after cancellation.
- Final output includes `Agent execution interrupted by external stop signal`.
- Provider call raises `Model is interrupted by stop event`.

Behavior:

- `agent_run` runs the agent loop in a background thread and yields queued observer messages until the thread exits.
- `stop_event.set()` is cooperative; the current model/tool step may finish or raise before the run stops.
- `OpenAIModel` checks `stop_event` while streaming chunks and raises when set.
- `CoreAgent._run_stream` stops its loop when `stop_event.is_set()`.

Test fixes:

- Always set `stop_event` in `finally` when wrapping a fake stream.
- Avoid assuming instant cancellation; assert the event was set and that the wrapper drained or closed predictably.

## Verification or guardrail surprises

Symptoms:

- Tool action blocked before execution.
- Tool output is masked instead of blocked.
- Final answer is replaced by controlled failure text.
- `ProcessType.VERIFICATION` chunks appear unexpectedly.

Checks:

- `AgentVerificationConfig.enabled` must be true before verification emits observer events.
- `step_verification_enabled` and `critical_events` control tool precheck/result/retrieval/handoff/code-execution checks.
- New input can terminate on `block`; tool input can block; history/tool output block is downgraded to mask.
- `fail_policy="warn"` keeps a candidate answer with a warning; `repair_then_controlled_summary` can return a controlled inability summary.
- Disable LLM verification in deterministic tests unless the verifier model is mocked.

## Sandbox backend problems

Symptoms:

- Docker/WASM sandbox silently falls back to local.
- Shell calls are blocked with a `SecurityError` message.
- Missing package diagnostics appear inside sandbox output.
- Managed agents run without non-local sandbox isolation.

Checks and fixes:

| Symptom | Explanation | Fix |
| --- | --- | --- |
| Docker/WASM fallback to local | Optional executor dependency or runtime backend unavailable. | Install the optional executor dependency and provide a working Docker/WASM runtime, or accept local fallback for tests. |
| Non-local sandbox with managed agents falls back local | Managed agents share the parent's executor in SmolAgents. | Test sandbox and managed-agent behavior separately; document limitation for live use. |
| Shell blocked | `ShellPolicy.DISABLED` scans for `subprocess` and `os` shell calls before execution. | Use SDK tools or pure Python; enable a stricter approved policy only at application/deployment level. |
| Host tool cannot be reached from remote sandbox | Host-tool bridge/network path failed. | Prefer unit tests with local executor or mocked bridge; live Docker networking belongs to deployment operations. |
| Output sync fails | `auto_sync_outputs=True` but no working MinIO client/bucket. | Provide `minio_client` only in live integration or disable auto sync for tests. |

## Monitoring has no spans or missing attributes

Symptoms:

- No OTLP traces/metrics.
- Tool/retriever spans lack input/output.
- Prompt-cache/context metrics are absent.

Checks:

- `MonitoringConfig.enable_telemetry` must be true and OpenTelemetry dependencies must be installed.
- Configure provider/endpoint/headers before running the agent.
- Bind `AgentRunMetadata` at the request boundary; `NexentAgent` then enriches spans with agent name/query when available.
- Use bounded `trace_content_mode` and size limits to avoid payload leaks.
- Tool outputs are recorded only when wrapped tool calls actually execute.
- Prompt-cache metrics require provider usage data or selected capability profiles; otherwise status may be `unsupported` or `unavailable`.

Monitoring deployment, collector, and dashboard setup belong to `deployment-operations`; SDK span semantics belong here.

## Scheduler trigger issues

Symptoms:

- Cron expression rejected.
- Next fire time is `None`.
- Timezone results seem shifted.
- Durable scheduler runs repeatedly or not at all.

Checks:

- Cron expressions are five-field cron strings.
- `interval_seconds` must be positive for interval schedules.
- `max_fire_count` stops recurring schedules when `fire_count >= max_fire_count`.
- `end_at` suppresses fires after the end time.
- Naive datetimes are interpreted in `ScheduleSpec.timezone`; return values are UTC-aware.
- `LeaseScheduler` requires a store implementing claim/renew/release semantics and an async executor; use fake bounded stores in tests.

## Skill manager issues

Symptoms:

- Skill not found under tenant.
- Script not found or unsafe params fail.
- Skill root unexpectedly changes between manager instances.

Checks:

- Pass the same `tenant_id` used to save/list/load.
- Use `SkillLoader.parse` for static `SKILL.md` checks when script execution is unnecessary.
- Use a temporary base directory in tests; do not use live user skill roots.
- `SkillManager` treats the base skills directory as immutable after first construction, so build a new test process/fixture if the base path must change.

## Backend NL2Agent/NL2Skill SDK handoff failures

Symptoms:

- Backend-created `AgentRunInfo` has wrong MCP URL/auth, capacity snapshots, context config, history/context input, or stop behavior.
- Stream wrapper fails to set `stop_event` on cancellation/error.

Split responsibilities:

- SDK contract: `AgentRunInfo`, `AgentConfig`, `MessageObserver`, `agent_run`, MCP normalization, and stop-event semantics are documented here.
- Backend service construction, tenant model lookup, authorization propagation, prompt assembly, route responses, and exceptions belong to `backend-services-api`.

For tests, emulate native patterns: build the run-info object, monkeypatch `agent_run`, yield fake JSON chunks, and assert `stop_event.set()` is called in cleanup/error/cancel paths.
