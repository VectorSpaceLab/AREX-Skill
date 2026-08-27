# Agent runtime map

This reference maps Yuxi's agent runtime behavior into layers a future Researcher can modify or verify. Paths are repository-relative entry points, not external links. Use the sibling troubleshooting reference for failure-first diagnosis.

## Scope and boundaries

Yuxi is a Docker Compose managed FastAPI + LangGraph + Vue platform. Agent runtime work is usually CPU/any at the code level, but live run verification depends on API/worker/Postgres/Redis and sometimes MinIO, sandbox-provisioner, model providers, Langfuse, Tavily, MCP servers, or OCR services.

Own in this sub-skill:

- Agent backend definitions, context/config schema, and Graph construction.
- Web chat, external invocation, queue/steer, AgentRun creation, worker handoff, and SSE streaming.
- Runtime middleware: filesystem/sandbox, attachments, Skills, subagents, summary/offload, image/OCR compatibility, token usage, model retry, and approval.
- Built-in tools as runtime surfaces, Skills activation, MCP tool loading, subagent calls, API-key boundaries, and Langfuse trace association.

Do not own in depth:

- Knowledge-base ingestion/indexing/graph internals except as exposed through agent tools.
- OCR engine implementation except the agent-facing `ocr_parse_file` and image fallback boundaries.
- Deployment/environment authoring except service assumptions needed to test agent runtime.
- CLI workflow details except external API semantics shared with agent invocation.

## Layered execution flow

### 1. Agent definition and configuration

Primary objects:

- `BaseAgent`: common LangGraph backend abstraction, including `get_graph()`, `context_schema`, capabilities, checkpoint use, and run invocation configuration.
- `BaseContext`: dataclass schema that drives both backend runtime values and front-end runtime configuration fields.
- `ChatBotContext`: extends the base context with `subagents` for main-agent delegation.
- `SubAgentContext`: hides runtime-only child fields and prevents nested subagent configuration.
- Database `Agent` rows: store user-facing name/slug/backend, `is_subagent`, share config, and `config_json.context`.

Important runtime fields in `BaseContext`:

| Field | Runtime meaning |
| --- | --- |
| `system_prompt` | Base prompt saved in Agent config, later extended by user workspace files and middleware prompt sections. |
| `model` | Main model spec; blank resolves to the system default during runtime context preparation. |
| `tools` | Enabled built-in tool names; blank/omitted means current user's visible tools after normalization. |
| `knowledges` | Knowledge-base resource scope, not the knowledge-base Skill itself. |
| `mcps` | Enabled MCP server slugs available to the run. |
| `skills` | Selected Skills; dependencies expand into readable/prompt Skill closures. |
| `summary_*` | Summary threshold, keep window, prompt, tool-result preview/offload, and L2 trigger ratio. |
| `max_execution_steps` | LangGraph recursion limit for a run. |
| `model_retry_times` | Model retry count for Chatbot graph. |
| `tool_approval_mode` | Sensitive tool approval mode; default asks before write/edit/command-sensitive backend tools. |
| `thread_id`, `uid`, `run_id`, `request_id` | Runtime identifiers, not ordinary user-configurable fields. |

Context lifecycle:

1. Frontend and API persist selected values under `config_json.context`.
2. Run creation merges persisted context with runtime ids and optional per-run overrides.
3. `prepare_agent_runtime_context()` normalizes model/tools/knowledges/MCP/Skills/subagents against the current user's visibility.
4. It derives `_visible_knowledge_bases`, `_prompt_skills`, `_readable_skills`, `_runtime_skill_metadata`, `_runtime_skill_dependency_map`, and `_runtime_skill_sources`.
5. The Graph is then built from the prepared context; middleware should not reimplement resource-visibility filtering.

Do not add a front-end-only Agent behavior setting when it affects runtime. Add or extend a context schema field and let configurable item generation expose it.

### 2. Graph construction and middleware order

Main Chatbot graph construction:

1. Prepare runtime context and sync shared/built-in Skill projections for the current skills thread.
2. Resolve model spec and configured built-in/MCP tools.
3. Create the LangGraph agent with the Chatbot state schema, prompt, tools, middleware, and checkpointer.

Main Chatbot middleware order:

| Middleware | Runtime responsibility |
| --- | --- |
| Steer middleware | Ends the current run at safe model-call boundaries when a queued Steer request is ready. |
| Filesystem middleware | Builds composite sandbox/user-data/Skills filesystem and offloads large non-read-file tool results to outputs. |
| Attachment middleware | Adds uploaded file paths to the prompt/state; content is read by tools, not inlined wholesale. |
| Skills middleware | Injects Skill prompts and adds Skill-gated tools/MCP dependencies only after Skill activation. |
| Subagent middleware | Adds `task` and async subagent lifecycle tools when the main Agent has visible subagents. |
| Summary middleware | L1 tool-result cleanup/offload and optional L2 summary when context exceeds configured threshold. |
| TodoList middleware | Maintains runtime todo state for the frontend state panel. |
| PatchToolCalls middleware | Normalizes tool-call chunk/message shapes for provider compatibility. |
| ModelRetry middleware | Retries model calls according to context. |
| ImageInputCompatibility middleware | Bridges OpenAI-compatible image blocks and falls back to OCR when image input is rejected. |
| TokenUsage middleware | Records approximate context and provider-reported usage aggregates in state/run records. |
| Tool approval middleware | Adds sensitive tool approval interruption behavior unless the mode trusts tools. |

SubAgentBackend graph uses the same filesystem, attachment, Skills, summary, todo, patch, retry, image, and token middleware, but it does not mount the subagent-task middleware. It also filters tools that should not be directly available to child agents: `present_artifacts`, `ask_user_question`, and `install_skill`; in default approval mode it also hides sensitive backend tools.

### 3. Run submission, request queue, and steer

Primary HTTP routes under `/api/agent`:

| Route | Purpose |
| --- | --- |
| `POST /api/agent/runs` | Create a chat run or resume an interrupted run. |
| `GET /api/agent/requests/{request_id}` | Read queued/request status for the current user. |
| `GET /api/agent/thread/{thread_id}/requests?agent_slug=...` | Read thread queue snapshot. |
| `POST /api/agent/thread/{thread_id}/requests/continue?agent_slug=...` | Continue a paused queue after failure/cancel. |
| `POST /api/agent/requests/{request_id}/cancel` | Cancel a queued request before dispatch. |
| `POST /api/agent/requests/{request_id}/steer` | Promote/mark a queued request as Steer. |
| `GET /api/agent/requests/{request_id}/events` | Request-stage SSE until dispatch/cancel/reject. |
| `GET /api/agent/runs/{run_id}` | Read AgentRun view. |
| `GET /api/agent/runs/{run_id}/result` | Read final result after terminal state. |
| `POST /api/agent/runs/{run_id}/cancel` | Request cancellation for a running AgentRun. |
| `GET /api/agent/runs/{run_id}/events` | Run-stage SSE, with `Last-Event-ID` or `after_seq` replay cursor and `verbose=false` compact mode. |
| `GET /api/agent/thread/{thread_id}/active_run` | Read active run for a thread. |

Submission rules:

- Ordinary web chat uses `RunSubmissionCommand` and the request queue service. Resume bypasses request queueing and creates a new run from checkpoint input.
- `request_id` is the idempotency key. Reusing it across user/agent/thread scope is a conflict.
- Conversation existence is required for ordinary web chat; external invocation may create a thread by command.
- Only after the database transaction commits should a run be enqueued to ARQ/worker.

Queue policies:

| Policy | Behavior |
| --- | --- |
| `enqueue` | Dispatch immediately if idle; otherwise persist FIFO request and request-stage SSE. |
| `reject` | Dispatch only if immediately possible; otherwise persist a rejected request for idempotency and return rejection. |
| `steer` | Persist as queued but mark as priority handoff after the current safe model/tool boundary. |

Steer boundaries:

- Steer does not cancel an in-progress model call or a tool batch already started.
- `abefore_model` checks for waiting steer before the next model call.
- `aafter_model` covers a tool-free model turn where steer arrived after the previous check.
- The current run completes normally, then worker dispatches the steer request as the next run for the same thread.
- Only one pending steer is accepted for a thread.

### 4. Worker execution, persistence, and streaming

AgentRun and request intake are facts in PostgreSQL. Redis/ARQ deliver work and Redis Streams carry run events, but final run status must be written back to PostgreSQL.

Runtime path:

1. Run request is accepted and, if dispatchable, creates a pending AgentRun.
2. Worker loads the run, Agent config, context, model override, tool approval mode, and checkpoint context.
3. Worker executes the agent graph using the prepared context and middleware stack.
4. Chat service maps raw LangGraph stream chunks to Yuxi semantic events, saves partial/final messages, extracts agent state, handles tool approval/ask-user interruptions, and persists token usage/trace info.
5. SSE endpoints stream request events until dispatch and run events until terminal `end`.

SSE boundaries:

- `GET /api/agent/runs/{run_id}/events` returns `text/event-stream` with event/data/id fields.
- Heartbeat comment lines may appear and clients must ignore them.
- `Last-Event-ID` or `after_seq` replays from a Redis Stream cursor.
- `verbose=false` strips debug-heavy fields while preserving data needed for UI/external clients.
- `/result` is read-only and should not trigger another run.

### 5. External invocation and API-key boundary

Authentication accepts JWT bearer tokens and API keys with the `yxkey_` prefix. API keys are hashed at rest, displayed only once at creation, and act with the bound user's permissions.

External system run routes:

| Route | Purpose |
| --- | --- |
| `POST /api/agent-invocation/agent-call/runs` | Agent call style invocation; can be async or blocking to terminal result. |
| `POST /api/agent-invocation/agent-call/runs/result` | Read an OpenAI-compatible result shape for an agent-call run. |
| `POST /api/agent-invocation/eval/runs` | Run one evaluation sample and optionally include trajectory summary. |
| `POST /api/agent-invocation/channel/messages` | Channel message integration using the same queue/run lifecycle. |

Security gates:

- Production API-key traffic must use HTTPS. Never paste or log full keys in diagnostics.
- `agent_id` and `agent_slug` values are Agent slugs, not numeric database ids.
- External `agent_call_meta.context` must not override runtime context. Model override uses the explicit `model_spec` field.
- OpenAI-style content arrays with text/image blocks are adapted by the invocation boundary; image support still depends on downstream model/OCR capabilities.

### 6. Attachments, image fallback, and summary/offload

Attachments:

- Uploaded files are stored under the thread's uploads scope and recorded in LangGraph state.
- Attachment middleware injects readable paths into prompts; it does not inline entire files.
- Agents should use file tools to inspect `/home/gem/user-data/uploads/...` paths.
- Child subagents share the parent file thread for uploads/outputs so they can read parent attachments and return artifacts to the parent thread.

Image/OCR fallback:

- `read_file` can return multimodal image blocks for small image binaries.
- The image compatibility middleware bridges OpenAI-compatible chat completion image inputs.
- If a model rejects image input, the middleware returns an OCR fallback response that directs use of `ocr_parse_file`.
- `ocr_parse_file` is optional/service-dependent because actual OCR engines may be local, service-based, or external.

Summary/offload:

- Summary trigger uses approximate token counts, not provider-reported billing totals.
- L1 cleanup truncates large historical tool arguments and offloads large tool results to `outputs/large_tool_results` while preserving a preview/path.
- L2 summary runs only if L1 still exceeds `summary_threshold * summary_l2_trigger_ratio`.
- Compression status is emitted as `context_compression` stream events.

### 7. Langfuse and evaluation boundary

Langfuse is optional observability, not a required runtime dependency. It is enabled only when public key, secret key, and base URL are configured. Missing or invalid Langfuse configuration should not break normal chat.

Mapping:

- Yuxi user -> Langfuse `user_id`.
- Conversation thread -> Langfuse `session_id`.
- Each AgentRun -> one trace.
- User feedback on an assistant message can be synchronized as a `user-feedback` score when the message is linked to a trace.

Verification requires a real conversation and Langfuse credentials. Do not run Langfuse dataset uploads/evals unless the user explicitly allows side effects.

## Backend and credential gates

| Capability | Gate | Safe fallback |
| --- | --- | --- |
| Unit tests for context/queue/Skills/MCP/subagents/sandbox | CPU + backend test deps | Run without live model providers. |
| Run/SSE E2E | Docker Compose API, worker, Postgres, Redis | Use unit tests if services are unavailable. |
| Personal Skill runtime E2E | API, sandbox-provisioner, MinIO/thread storage, admin/test user | Verify service/unit storage rules only. |
| OCR parsing/image fallback | OCR engine or configured OCR service/provider | Verify path/fallback logic; do not claim OCR quality. |
| Live model calls | Provider credentials/network | Use mocked/unit tests. |
| Tavily/web search | `TAVILY_API_KEY`/network | Tool may be absent; do not treat as core failure. |
| Remote MCP | Remote server URL/auth/network | Verify config validation and cache behavior. |
| Built-in stdio MCP | Code-reviewed fixed server only | Do not create stdio server from API/user input. |
| Langfuse | Langfuse keys/base URL/network | Normal chat should run without tracing. |
| API-key examples | Generated `yxkey_...` secret | Never log or store the secret in test fixtures/docs. |

## Native test map

Run from repository root. Prefer targeted tests before broad suites.

| Candidate | Command | Requirement | Proves |
| --- | --- | --- | --- |
| Skill router | `docker compose exec api uv run --group test pytest test/unit/routers/test_skill_router.py` | CPU/unit | Skill management routes and authorization shapes. |
| Skill service | `docker compose exec api uv run --group test pytest test/unit/services/test_skill_service.py` | CPU/unit | Skill parsing, install/import, dependency, personal/shared shadowing, and cache rules. |
| Sandbox backend | `docker compose exec api uv run --group test pytest test/unit/backends/test_sandbox_backends.py` | CPU/unit | File scope, split file/skills threads, path permission, OCR routing, binary read, and tool result offload rules. |
| Request queue | `docker compose exec api uv run --group test pytest test/unit/services/test_agent_request_queue_service.py test/unit/middlewares/test_steer_middleware.py` | CPU/unit | Enqueue/reject/steer lifecycle, idempotency, paused queues, and safe steer handoff. |
| Subagent runtime | `docker compose exec api uv run --group test pytest test/unit/middlewares/test_subagent_task_middleware.py test/unit/services/test_subagent_run_service.py` | CPU/unit | Allowed subagents, child scopes, sync/async tools, busy/relation/security checks. |
| MCP runtime | `docker compose exec api uv run --group test pytest test/unit/routers/test_mcp_router.py test/unit/services/test_mcp_service.py` | CPU/unit | Remote-only API config, built-in stdio protection, enabled/tool cache behavior. |
| Install Skill tool | `docker compose exec api uv run --group test pytest test/unit/toolkits/test_install_skill.py` | CPU/unit | Agent tool installs personal Skills only for current user and rejects subagent runtime. |
| Subagent stream E2E | `docker compose exec api uv run --group test pytest -m e2e test/e2e/test_subagent_stream_e2e.py` | Docker services + admin/test user | Real run stream records child run state and shared output files. |
| Personal Skill agent E2E | `docker compose exec api uv run --group test pytest -m e2e test/e2e/test_personal_skill_agent_e2e.py` | Docker services + sandbox/thread storage | Main Agent reads personal Skill from workspace at runtime. |
