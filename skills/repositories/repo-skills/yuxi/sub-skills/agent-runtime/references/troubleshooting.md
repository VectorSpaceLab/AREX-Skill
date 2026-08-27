# Agent runtime troubleshooting

Use this reference to narrow symptoms before changing code. Run non-mutating probes first, avoid leaking secrets, and distinguish CPU-testable logic from service/credential gated behavior.

## Safe probes

Run from repository root:

```bash
# Service inventory and logs
docker compose ps
docker logs api-dev --tail 100
docker logs worker-dev --tail 100
docker logs sandbox-provisioner --tail 100

# Health probes; do not include credentials in the command line output
curl -s http://localhost:5050/api/system/health
curl -s http://localhost:8002/health

# Targeted unit suites for agent-runtime behavior
docker compose exec api uv run --group test pytest test/unit/services/test_agent_request_queue_service.py
docker compose exec api uv run --group test pytest test/unit/middlewares/test_steer_middleware.py
docker compose exec api uv run --group test pytest test/unit/backends/test_sandbox_backends.py
docker compose exec api uv run --group test pytest test/unit/middlewares/test_subagent_task_middleware.py test/unit/services/test_subagent_run_service.py
docker compose exec api uv run --group test pytest test/unit/routers/test_skill_router.py test/unit/services/test_skill_service.py test/unit/toolkits/test_install_skill.py
docker compose exec api uv run --group test pytest test/unit/routers/test_mcp_router.py test/unit/services/test_mcp_service.py
```

Only run E2E stream/runtime tests when API, worker, Postgres, Redis, MinIO/thread storage, sandbox-provisioner, and test/admin credentials are intentionally available:

```bash
docker compose exec api uv run --group test pytest -m e2e test/e2e/test_subagent_stream_e2e.py
docker compose exec api uv run --group test pytest -m e2e test/e2e/test_personal_skill_agent_e2e.py
```

## Symptom guide

| Symptom | Likely layer | First checks | Targeted proof |
| --- | --- | --- | --- |
| `POST /api/agent/runs` returns 404 for agent/thread | Route/submission scope | Verify `agent_slug` is an Agent slug; verify thread exists for web chat; external invocation can create conversations only through its command path. | Agent router and invocation router unit tests if present; queue service tests for scope conflicts. |
| Same external request creates duplicate or conflict | Run submission idempotency | Check `meta.request_id` / invocation `request_id`; conflicts are expected when reused across user/agent/thread. | `test_agent_request_queue_service.py` idempotency cases. |
| Busy thread rejects a synchronous call | Queue policy | Confirm route used `queue_policy=reject`; rejection is expected for sync agent-call when a thread is active or paused. | Queue service reject tests. |
| Queued messages appear in conversation too early | Queue/message delivery status | Queued user messages should remain in request/queued delivery status until dispatch. Inspect request snapshot rather than conversation body only. | Queue service message delivery tests. |
| Steer does not interrupt a running tool | Steer middleware safety boundary | Steer only hands off before next model call or after tool-free model turn; it does not cancel a started model call/tool batch. | `test_steer_middleware.py`; E2E steer test if services run. |
| Queue remains paused after failure/cancel | Queue recovery | Use thread request snapshot; after failed/cancelled run with backlog, user must continue paused FIFO head. If queue was empty when failure occurred, new requests can dispatch. | Queue paused/continue tests. |
| Resume creates an unexpected queued request | Resume route | Resume with `payload.resume` bypasses request queue and creates a new run from checkpoint; `queue_policy` must be `enqueue`. | Chat stream interrupt/resume tests. |
| Run stuck in pending/running with no stream | Worker/ARQ/Redis/Postgres | Check `worker-dev` logs, Redis connectivity, pending run recovery, and API/worker shared config. Confirm DB commit happened before enqueue. | Agent run service/queue tests; E2E only if services available. |
| SSE disconnect loses events | Run stream cursor | Use `Last-Event-ID` or `after_seq`; clients must ignore heartbeat comments and consume `event/data/id`. | Chat stream service tests and `test_agent_async_e2e.py` when live. |
| `verbose=false` misses expected debug fields | Stream compaction | Compact mode intentionally removes debug-heavy metadata and empty agent state. Use verbose mode for diagnostics. | Chat stream compact event tests. |
| `/result` appears stale | Run finalization | `/result` is read-only and reads terminal persisted message/status; it will not restart a run. Check run terminal state and output message id. | Agent run result tests. |
| API-key request 401/403 | Auth/API-key boundary | Ensure `Authorization: Bearer yxkey_...`; production must use HTTPS. Do not log the key. The key has only bound-user permissions. | `test_api_key_security.py` plus route-specific tests. |
| External agent-call cannot override context | Invocation safety | This is intentional; `agent_call_meta.context` must not override runtime context. Use explicit `model_spec` for model override. | Agent invocation adapter/router tests. |

## Agent context/config failures

### New setting does not appear in the UI

Likely cause: the setting was added outside the context schema or hidden by metadata/role filtering.

Checks:

1. Add runtime settings to the appropriate context dataclass field.
2. Ensure field metadata has `configurable` not set to false unless hidden by design.
3. For admin-only fields, verify current user role.
4. Confirm Agent detail serialization includes configurable items for the backend.

Target tests: context/auth tests, agent repository tests, or focused router tests around configurable items.

### Runtime uses the wrong model/tools/Skills/MCP

Likely cause: confusion between persisted `config_json.context`, runtime override, and prepared context.

Checks:

1. Inspect persisted Agent config and per-run override (`model_spec`, `tool_approval_mode`).
2. Confirm `prepare_agent_runtime_context()` normalized resources for the current user.
3. Remember that omitted resource lists default to all visible resources; explicit lists restrict.
4. Confirm hidden role-filtered fields are not silently accepted from unauthorized users.

Target tests: context auth/resource normalization, tool/MCP service tests, and Skills middleware tests.

## Middleware and file/runtime failures

### Attachment visible in UI but Agent cannot read it

Likely layer: attachment materialization or file-thread scope.

Checks:

1. Confirm attachment file id belongs to the target thread and was bound in the intake transaction.
2. Check AttachmentMiddleware added readable upload paths to state/prompt.
3. For subagents, remember uploads/outputs use parent file thread id.
4. Do not expect file contents to be inlined; the Agent must call file tools.

Target tests: attachment state/materialize tests, sandbox split-scope tests, E2E attachment test if live.

### Image input fails for one provider

Likely layer: provider image compatibility.

Checks:

1. Some OpenAI-compatible providers reject image blocks even if `read_file` returned them.
2. The middleware should fall back by telling the Agent to use `ocr_parse_file` when image rejection is detected.
3. OCR requires a configured engine/service; failure to parse via OCR is not proof that image bridge is broken.

Target tests: model input middleware tests and sandbox image/binary tests. Service OCR checks require configured engine.

### Large tool result disappears from context

Likely layer: filesystem middleware or summary L1 cleanup.

Checks:

1. Large non-`read_file` tool results may be written to `outputs/large_tool_results` with a preview kept in context.
2. Summary L1 cleanup can offload historical tool results once the threshold is crossed.
3. The output file path in the replacement message is the source of full content.

Target tests: sandbox backend large result/offload tests and summary middleware tests.

### Summary triggers too early or too late

Likely layer: summary config and approximate token counts.

Checks:

1. Summary trigger uses approximate context token count, not provider billing `usage_metadata`.
2. `summary_threshold` is K tokens; runtime multiplies by 1024.
3. L2 summary only runs after L1 if remaining context exceeds `summary_threshold * summary_l2_trigger_ratio`.
4. Provider-reported usage blacklists should not affect summary trigger.

Target tests: summary middleware and token usage middleware tests.

### Tool approval or ask-user interrupt does not resume correctly

Likely layer: interrupt payload/resume path.

Checks:

1. Approval and ask-user-question are checkpoint interruptions, not ordinary queue messages.
2. Resume must pass the expected payload and should not render resume input as a normal user message.
3. Running interrupted threads reject new ordinary requests until resume completes.

Target tests: chat stream interrupt tests and queue interrupted-request tests.

## Tools and artifact failures

### `present_artifacts` returns path errors

Rules:

- Input file must exist and be a regular file.
- It must resolve under `/home/gem/user-data/outputs`.
- It must not be inside internal directories such as `large_tool_results` or conversation history.
- Subagents cannot call this tool directly.

Target tests: sandbox backend output/artifact tests and SubAgentBackend tool filter tests.

### `ocr_parse_file` rejects a path

Rules:

- Input must be a sandbox virtual path under `/home/gem/user-data`.
- Only `workspace`, `uploads`, and `outputs` namespaces are allowed.
- Actual host path must exist as a regular file after virtual resolution.
- Output Markdown is written to `/home/gem/user-data/outputs/ocr/`.
- OCR engine selection depends on system config and available processors.

Target tests: sandbox path/OCR routing tests for validation; OCR engine integration only with services/providers.

### `ask_user_question` fails validation

Rules:

- Provide at least one valid question.
- Options must be structured and meaningful; strings may be parsed as JSON but invalid strings fail.
- Do not use this for routine “continue?” prompts.
- Subagents cannot call it.

Target tests: chat interrupt and stream mapping tests.

### `install_skill` fails or does not activate the Skill

Checks:

1. Subagent runtime is not allowed to install Skills.
2. Sandbox path install must download through sandbox file API, not host path assumptions.
3. Git/source installs need explicit skill names when required by source type.
4. Only current user's personal workspace is modified.
5. Current Agent config is updated only when it belongs to the user.

Target tests: `test/unit/toolkits/test_install_skill.py` and personal Skill E2E when services are available.

## Skills runtime failures

### Skill prompt appears but tools are not available

Likely cause: Skill not activated yet.

Checks:

1. At run start the Agent sees Skill metadata and `SKILL.md` path.
2. Tool/MCP dependencies are added only after the Agent reads the Skill's `SKILL.md`.
3. Personal Skills do not parse shared dependency fields.
4. Personal Skill with the same slug shadows the shared Skill and removes shared dependencies.

Target tests: skill service shadow/dependency tests and skills middleware tests.

### Shared Skill changes are not visible in run

Checks:

1. Shared/built-in Skills project into a thread-specific read-only skills scope at graph build time.
2. Existing run state may not reflect modifications made after graph creation.
3. Built-in sync preserves enabled state but updates code-defined fields at startup.
4. Personal Skill metadata can be cached for about five minutes unless refreshed.

Target tests: skill service sync/cache tests and sandbox split-scope tests.

### Skill upload or remote install rejected

Checks:

1. Frontmatter must parse and slug/name rules must be valid.
2. ZIP paths cannot traverse, include unsafe symlinks, or exceed expected structure.
3. Normal users cannot confirm shared installs.
4. Remote host must be allowed by system policy.
5. Remote install is network/side-effect gated; do not run it casually during verification.

Target tests: skill router/service upload/import/remote tests.

## MCP failures

### MCP server visible in management but tools missing in runtime

Checks:

1. Server must be enabled/“added”. Disabled records are management-visible but not runtime-visible.
2. Agent context must include the MCP slug or default to all visible MCPs.
3. Tool-level disabled list may hide specific tools.
4. Runtime cache is keyed by config; update should change the hash/cache key.
5. Remote server connectivity may fail independently of config validation.

Target tests: MCP service enabled config/cache tests; live connectivity only with approved remote endpoint.

### API rejects stdio MCP configuration

This is intentional. User/API-managed MCP servers can be Streamable HTTP or SSE only. Stdio launches a local process inside API/worker and is allowed only for code-defined built-ins with fixed command/args and code review.

Target tests: MCP router/service stdio rejection tests.

### Built-in MCP update ignores connection edits

This is intentional. Built-in MCP connection/display fields are code-owned and overwritten at startup. Management state keeps enabled flag and disabled tool list only.

Target tests: MCP router/service built-in update tests.

## Subagent failures

### Main Agent cannot see a subagent

Checks:

1. Child Agent row must use backend `SubAgentBackend` and `is_subagent=true`.
2. It must be visible to the current user by share config.
3. If main Agent `subagents` list is explicit, the slug must be listed.
4. If list is blank/omitted, current visible subagents should be loaded.
5. Normal Agents cannot be called as subagents.

Target tests: subagent task middleware visible/reject tests and agent repository subagent tests.

### `task` hangs or returns running/timeout message

Checks:

1. `task` blocks waiting for child run terminal state, but timeout returns a running result and child thread ID.
2. The parent should then use `subagent_status` or `subagent_await`; do not treat timeout as task completion.
3. Worker/ARQ/SSE issues can still affect child run execution.

Target tests: subagent task wait-timeout tests and subagent stream E2E if services are running.

### `subagent_start` returns busy

This is expected when the same child thread already has an active run. Use the returned busy payload, wait/cancel/query the active run, or start a new child thread if semantically appropriate.

Target tests: subagent run service busy translation tests.

### Async subagent tools reject a run id

Checks:

1. `subagent_status`, `subagent_cancel`, and `subagent_await` require `run_id` created by the current parent run.
2. Cross-parent or cross-user run ids are rejected.
3. A continuation `thread_id` must belong to the relation for the parent/subagent, not an ordinary conversation thread.

Target tests: subagent service cross-parent/relation rejection tests.

### Subagent output file is not visible to parent

Checks:

1. Subagents share parent file thread for uploads/outputs.
2. They use a separate checkpoint thread and separate skills thread.
3. File written outside `/home/gem/user-data/outputs` may not be shown as an artifact.
4. `present_artifacts` is disabled for subagents; parent may present final files after child completion if needed.

Target tests: sandbox split-scope tests and subagent stream E2E.

## Sandbox/file failures

### Permission denied for a sandbox path

Rules:

- Reads/lists are restricted to approved virtual roots.
- Writes are allowed in workspace/outputs where the backend permits; uploads and Skills projection are read-only.
- Path traversal and paths outside the virtual prefix are rejected.
- `/home/gem/skills` is read-only; personal Skills live under user workspace.

Target tests: sandbox backend path traversal, upload write rejection, and outputs write allowance.

### Sandbox-provisioner health is wrong

Checks:

1. Default development backend should report Docker when using Compose defaults.
2. API/worker use `SANDBOX_PROVISIONER_URL` and token; provisioner itself uses backend variables such as Docker/Kubernetes settings.
3. Never inject `SANDBOX_PROVISIONER_TOKEN` into the sandbox container environment.
4. Dynamic sandbox containers are created on demand, not necessarily at startup.

Target tests: sandbox provisioner config/unit tests; live health requires services.

### Binary/document read behavior surprises the Agent

Rules:

- Small image reads may return multimodal blocks.
- PDF/Office documents route to OCR parsing guidance.
- Known audio/video or unknown binary types are rejected unless handled by a dedicated tool.
- Large binary files may be rejected before read.

Target tests: sandbox backend binary/image/document tests.

## Langfuse, provider, and external-service failures

### No Langfuse trace appears

Checks:

1. Langfuse is optional; missing keys disable tracing without breaking chat.
2. Required config is public key, secret key, and base URL.
3. Confirm keys are passed into the API container; do not print them.
4. Generate one real Agent run, then inspect Langfuse by recent trace/user/session.
5. Feedback score sync needs an assistant message linked to a trace.

Target tests: Langfuse service and chat stream Langfuse tests. Live console verification requires credentials/network.

### Model provider call fails

Checks:

1. Confirm default model resolution and per-run `model_spec` override.
2. Provider credentials/network are external gates; do not run real calls without approval.
3. Some providers may report usage metadata differently; token usage blacklists do not necessarily mean chat is broken.
4. Image support differs by provider; OCR fallback is expected for image rejection.

Target tests: model input, token usage, and model provider unit tests; live connectivity only with explicit opt-in.

### Web search tool absent

Likely cause: no supported search provider key/config at import time. Treat Tavily/web search as optional. Do not fail core agent-runtime verification because it is absent.

### API-key integration works locally but is unsafe in production

Rules:

- API keys must be sent as bearer tokens and treated as secrets.
- Use HTTPS in production; local HTTP is only for local development.
- Create separate keys per external system and rotate/disable on suspected leak.
- The key inherits bound-user permissions; permission failures may be correct.

## When to stop and ask

Ask the user before:

- Running live model, OCR, Tavily, remote MCP, Langfuse, or remote Skill workflows that require credentials/network or create external records.
- Modifying production-like `.env`, MCP server configs, API keys, Skill sharing, or system model/provider settings.
- Running E2E tests that create/deletes agents, threads, files, Skills, or external evaluation datasets.
- Changing queue semantics, subagent security checks, or sandbox path boundaries in a way that could allow concurrent context mutation or path escape.

Do not ask for routine CPU unit tests, static inspection, or non-mutating Docker/log/health probes when working in the local development checkout.
