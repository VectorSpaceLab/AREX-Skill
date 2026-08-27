# Tools, Skills, MCP, subagents, and sandbox boundaries

This reference is the agent-facing catalog for Yuxi extension surfaces. It explains when tools appear, which objects own storage and permission checks, and what should be verified before changing runtime behavior.

## Tool registry and assembly

Yuxi tools are registered with a `@tool` decorator that records category, display metadata, and a LangChain tool instance. Importing the toolkit package registers built-in/debug tools; knowledge-base tools are registered but only surfaced through the built-in knowledge-base Skill dependency path.

Runtime assembly has three phases:

1. `prepare_agent_runtime_context()` filters the current user's visible tools, knowledge bases, MCP servers, Skills, and subagents.
2. `resolve_configured_runtime_tools(context)` loads configured built-in tools and enabled MCP tools.
3. `SkillsMiddleware` adds Skill-gated tools and MCP dependencies only after the Agent activates a readable Skill by reading its `SKILL.md`.

Do not bypass this order by hard-coding tools into routes, front-end components, or knowledge-base code. If a tool should be available to all configured agents, make it a built-in tool and let context normalization expose it. If it is domain-specific, declare it through a Skill dependency.

## Built-in tools

| Tool | Surface | Runtime rules | Gates/tests |
| --- | --- | --- | --- |
| `present_artifacts` | Show generated output files in the frontend after a run. | Accepts files only under `/home/gem/user-data/outputs`; rejects non-files and internal tool output directories such as large tool results or conversation history. Disabled for subagents. | Sandbox/backend unit tests cover output path rules; E2E artifact behavior requires services. |
| `ocr_parse_file` | Convert a sandbox file to Markdown and save the result. | Input must be under `/home/gem/user-data/workspace`, `/uploads`, or `/outputs`; output is written under `/home/gem/user-data/outputs/ocr/`; result returns source path, parsed path, engine, char count, preview, and truncation flag. | OCR engine/service optional; path validation is CPU-testable, OCR quality is not. |
| `ask_user_question` | Interrupt a run to ask the user structured questions. | Requires at least one valid question; returns an answer object. Do not use for routine process control. Disabled for subagents. | Chat interrupt and stream tests cover interruption payloads. |
| `install_skill` | Install a user-private Skill from sandbox content or allowed Git source and activate it in the current main Agent config. | Installs to the current user's personal workspace only; rejects subagent runtime; validates source and skill names; updates only user-owned current Agent config. | `test/unit/toolkits/test_install_skill.py`. |
| `web_search` / Tavily-backed search | Optional web search built-in. | Registered only when a supported search provider key/config is available. Treat network calls as external-credential gated. | Unit tests can verify provider registration; do not call the network without approval. |

SubAgentBackend filters `present_artifacts`, `ask_user_question`, and `install_skill` even when selected. In default approval mode it also hides sensitive backend tools so a child run cannot bypass main-thread approvals.

## Knowledge-base tools as an Agent surface

Knowledge-base internals are not owned here, but the Agent-facing tool surface is:

- `list_kbs`
- `query_kb`
- `find_kb_document`
- `open_kb_document`
- `get_mindmap`
- `search_file`
- `download_kb_file`

Key rules:

- Knowledge-base access is exposed through the built-in `knowledge-base` Skill. The Agent first sees the Skill prompt, reads its `SKILL.md`, and only then gets the KB tool dependencies.
- `_visible_knowledge_bases` is derived from user permissions and Agent config during runtime context preparation. Tool execution must stay inside that visible set.
- `context.knowledges` is a resource scope, not a direct file mount and not a replacement for the `knowledge-base` Skill.
- Knowledge bases are not mounted into `/home/gem/skills` or `/home/gem/user-data`; Agents should use `query_kb`, `find_kb_document`, `open_kb_document`, and related tools rather than traversing a filesystem path.
- `download_kb_file` writes downloads to the Agent output scope and remains subject to sandbox/file visibility rules.

## Skills storage, installation, activation, and dependencies

Yuxi has two Skill storage layers:

| Layer | Storage and index | Runtime path | Dependency support | Who can manage |
| --- | --- | --- | --- | --- |
| Shared/built-in Skills | Platform Skill directory plus database index with source type, share config, enabled flag, and dependencies. | Read-only projection under `/home/gem/skills/<slug>/...`. | `tool_dependencies`, `mcp_dependencies`, and `skill_dependencies` are honored. | Admins manage shared Skills; built-ins are protected but can be enabled/disabled. |
| Personal Skills | Current user's workspace under `agents/skills/<slug>` with Redis metadata cache. | Directly under `/home/gem/user-data/workspace/agents/skills/<slug>/...`. | Dependencies are not parsed for personal Skills. | Owning user can preview/delete/refresh; install tool writes here. |

Activation lifecycle:

1. At run start, configured shared/built-in Skills and their Skill dependency closure become `_prompt_skills` and `_readable_skills`.
2. SkillsMiddleware injects a concise prompt listing readable Skill names/descriptions and their `SKILL.md` paths.
3. When the Agent reads a readable `SKILL.md`, the Skill slug is added to `activated_skills`.
4. On later model calls, dependencies of activated Skills add their tools and MCP tools to the available tool set.

Important rules:

- Shared/built-in Skill projection is read-only. Scripts can execute from it, but writes must go to workspace or outputs.
- Personal Skills with the same slug shadow shared Skills completely, including shared dependencies. Deleting the personal version lets the shared version return on future runs.
- Shared install/update validates frontmatter, slug safety, path traversal, symlinks, file trees, dependency visibility, and permission scopes.
- Personal metadata is cached for about five minutes; install/delete/manual refresh updates it immediately.
- Normal users can install uploads/remotes only as personal Skills; shared installs need admin permissions.
- Built-in Skill files are not editable through normal Skill management APIs.

Native proof focus:

- `test/unit/services/test_skill_service.py` covers slug parsing, upload/import, dependency validation, personal/shared shadowing, caches, builtin updates, and path safety.
- `test/unit/routers/test_skill_router.py` covers route permissions and install draft boundaries.
- `test/unit/toolkits/test_install_skill.py` covers the Agent tool install boundary.
- `test/e2e/test_personal_skill_agent_e2e.py` proves runtime reading of a personal Skill when live services are available.

## Remote Skill installation safety

Remote Skill discovery/install can invoke an external source fetch in a one-time sandbox. Keep these gates explicit:

- Allowed remote hosts are system-configured and exact-host matched; default intent is GitHub/ModelScope style sources, not arbitrary URLs.
- Remote source policy lives in database system options, not environment variables alone.
- Remote install should not inherit global or user agent environment variables; it must not expose credentials to untrusted repos.
- Kubernetes sandbox use disables ServiceAccount token automount for these one-time operations.
- Only extract validated relative paths; reject traversal, over-large trees, or invalid Skill metadata.
- Do not run remote installation in verification unless the user approves network and side effects.

## MCP integration

Supported runtime transports:

| Transport | Who may configure | Use case |
| --- | --- | --- |
| Streamable HTTP | Admin/API-managed remote server | Preferred remote MCP integration. |
| SSE | Admin/API-managed remote server | Standard HTTP long-running MCP connection. |
| Stdio | Code-defined built-in servers only | Local process inside API/worker container; requires code review and fixed command/args. |

MCP service behavior:

- Built-in MCP server definitions are synced at startup from code into the database. Connection/display fields are overwritten from code; enabled state and tool disabled lists persist.
- API-created/updated MCP servers may not configure arbitrary `stdio` commands. Legacy user-created stdio entries are disabled and require migration to remote HTTP/SSE.
- Runtime tool loading reads enabled server configs from database, filters disabled tools, and caches tools by config hash. Updating config should invalidate by changing the hash/cache key rather than requiring service restart.
- Tool-level enable/disable is per MCP server.

Stdio safety boundary:

- Stdio is equivalent to launching a local process in the API/worker container. Never construct `command`, `args`, or `env` from HTTP payloads, user database rows, or untrusted environment values.
- Pin package versions for built-in stdio MCP packages. Do not commit secrets into code or database configs.
- Prefer remote SSE/Streamable HTTP when possible.

Native proof focus:

- `test/unit/routers/test_mcp_router.py` covers API validation, normal-user stripping, rejecting stdio command changes, and built-in update restrictions.
- `test/unit/services/test_mcp_service.py` covers built-in sync, legacy stdio disablement, enabled config loading, cache rebuilds, and tool error handling.
- `test/e2e/test_mcp_stdio_security.py` is service/security oriented and should only be used when E2E services are intentionally running.

## Subagents

Yuxi subagents are Agent-backed, not a separate legacy table. A subagent is a normal `agents` row with `is_subagent=true` and backend `SubAgentBackend`.

Management/API rules:

- `GET /api/agent` lists chat-usable main Agents by default.
- `GET /api/agent?include_subagents=true` includes subagents for management views.
- Creating or updating a `SubAgentBackend` must carry or infer `is_subagent=true`.
- A normal Agent cannot masquerade as a subagent, and a `SubAgentBackend` cannot be saved as a normal main Agent.
- Subagents cannot be the default chat Agent and do not appear in the chat quick switch list.

Main Agent configuration:

- `ChatBotContext.subagents` is the allowed child-agent list.
- Blank/omitted/empty list means all currently visible subagents for the user, including built-ins such as `general-purpose` when available.
- Explicit selection restricts to selected visible subagent slugs.
- Each child run uses the child Agent's own `config_json.context`; if the child model is blank, the subagent task middleware can inherit the parent's current model for that call.

Synchronous tool:

| Tool | Behavior |
| --- | --- |
| `task(description, subagent_slug, thread_id=None)` | Starts or continues a child subagent run, blocks for final result, and returns the child thread ID plus final assistant text. Use for short tasks whose result is immediately needed. |

Asynchronous lifecycle tools:

| Tool | Behavior |
| --- | --- |
| `subagent_start(description, subagent_slug, thread_id=None)` | Starts or continues a child run and immediately returns `run_id`, `thread_id`, status, URLs, and state payload. |
| `subagent_status(run_id)` | Returns latest status, last progress messages, result if terminal, and child run state. |
| `subagent_cancel(run_id)` | Cancels a child run after verifying it belongs to the current parent run. |
| `subagent_await(run_id)` | Waits for terminal result; timeout returns current snapshot with `wait_timed_out`. |

Subagent scope/security rules:

- Child checkpoint thread is distinct from the parent thread.
- Child `file_thread_id` points to the parent file thread, so uploads/outputs are shared with the parent conversation.
- Child `skills_thread_id` points to the subagent's own skills scope, so its Skills do not pollute the main Agent.
- Subagents do not mount another subagent-task middleware; no nested subagent chain.
- All async lifecycle tools verify `run_id` belongs to the current parent run and user.
- If a child thread already has an active run, start returns a busy structure rather than hiding queueing.
- The parent should not call subagents by shell, curl, or HTTP routes; use the middleware tools.

Native proof focus:

- `test/unit/middlewares/test_subagent_task_middleware.py` covers visible child selection, unconfigured child rejection, child scope, inherited model, wait timeout, continuation thread checks, async lifecycle tools, and parent-run authorization.
- `test/unit/services/test_subagent_run_service.py` covers relation creation, continuation, busy translation, context persistence, non-subagent rejection, parent mismatch rejection, and cross-parent access rejection.
- `test/e2e/test_subagent_stream_e2e.py` proves live streaming, child run state, and shared output files when services/admin user are present.

## Sandbox and file boundaries used by tools/subagents

Agent-visible virtual roots:

| Virtual path | Meaning | Mutability |
| --- | --- | --- |
| `/home/gem/user-data/workspace` | User-level shared workspace. | Writable by tools; shared across the user's threads. |
| `/home/gem/user-data/uploads` | Current file-thread uploads. | Read-only from the Agent's perspective for uploaded inputs. |
| `/home/gem/user-data/outputs` | Current file-thread outputs/artifacts. | Writable; final outputs should go here. |
| `/home/gem/skills` | Current skills-thread projection of shared/built-in Skills. | Read-only. |

Runtime split scope:

| Scope | Main Agent | SubAgentBackend |
| --- | --- | --- |
| Checkpoint thread | Current `thread_id` | Child thread id. |
| File thread/uploads/outputs | Current `thread_id` | Parent file thread id. |
| Skills projection | Current Agent's skills thread | Child/subagent skills thread. |
| Workspace | Same user uid | Same user uid. |

Path rules:

- Sandbox virtual path prefix is `/home/gem/user-data`; do not mix it with host checkout paths.
- Viewer/download APIs resolve only approved virtual roots; they do not expose the entire sandbox or host filesystem.
- Upload writes are rejected; output writes are allowed.
- Documents/images may route through OCR or multimodal read behavior; audio/video and unknown binary formats are rejected unless a specific tool supports them.
- Large non-`read_file` tool results may be evicted/offloaded to outputs to avoid context loops.
- Knowledge bases are not filesystem mounts; use KB tools.

Native proof focus:

- `test/unit/backends/test_sandbox_backends.py` covers split file/skills scopes, personal Skill projection, output-only artifact exposure, virtual path traversal rejection, binary/image/document read behavior, OCR routing, timeout handling, and download errors.

## Change checklist for extension surfaces

Before editing tool/Skill/MCP/subagent behavior, answer these checks:

1. Which layer owns the feature: context normalization, tool registry, Skill dependency, MCP service, subagent middleware, sandbox backend, or API router?
2. Does the feature require credentials, network, external service, Docker sandbox, or a model provider? If yes, add a gate and a no-credential fallback.
3. Is the capability visible to normal users, admins only, main Agents only, or subagents too?
4. Does the change preserve personal/shared Skill shadowing and dependency behavior?
5. Does it preserve the split file-thread and skills-thread scope for subagents?
6. Are run events/state updates sufficient for the frontend to show progress after refresh or SSE reconnect?
7. Which native unit test proves the boundary, and which optional E2E proves the live behavior?
