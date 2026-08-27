# API and Service Ownership Map

Use this map to choose the owning app module, service module, database helper, and mock target before changing a Nexent backend API. For a live checkout, run the bundled static scanner to get the exact route list:

```bash
python skills/disco/nexent/sub-skills/backend-services-api/scripts/list_fastapi_routes.py --repo-root .
python skills/disco/nexent/sub-skills/backend-services-api/scripts/list_fastapi_routes.py --repo-root . --json
```

The scanner parses Python AST only; it does not import backend modules, connect to databases, or start FastAPI.

## App processes and router sets

| App/process | Main app object | Included router families | Notes |
| --- | --- | --- | --- |
| Config/admin API | `apps.config_app.app` | `/model`, `/config`, `/agent` config routes, `/repository/agent`, `/repository/skill`, `/indices`, `/datamate`, `/dify`, `/idata`, `/ragflow`, `/file` config routes, `/tool`, `/prompt`, `/prompt_templates`, `/skills`, `/tenant_config`, `/mcp-tools`, `/mcp`, `/user`, `/user/oauth`, `/user/cas`, `/summary`, `/tenants`, `/groups`, `/users`, `/invitations`, `/notifications`, `/a2a/*`, `/haotian`, `/evaluation-*`, `/evaluators`, `/memory`, `/platform/quota`. | Startup syncs system default prompt templates and starts memory dreaming scheduler. Speed mode selects mock user-management router. |
| Runtime API | `apps.runtime_app.app` | `/agent/run`, `/agent/nl2agent/run`, `/agent/stop/*`, `/agent/automations`, `/conversation`, `/share`, runtime `/file`, runtime `/voice`, `/skills/nl2skill/run`. | Adds runtime exception middleware with trace IDs and structured error envelopes. |
| Northbound API | `apps.northbound_base_app.northbound_app` | `/nb/v1`, `/nb/v1/knowledge`, `/nb/a2a`. | Partner-facing chat, knowledge, and A2A endpoints. Monitoring is disabled by default for this app. |
| Data-process service | `data_process_service.py` | Service manager rather than app-router owner for this sub-skill. | Deep file conversion/Ray/Celery behavior belongs to `knowledge-data-memory`. |
| MCP service | `mcp_service.py` | FastMCP server plus management endpoints. | Backend config routes manage MCP records; transport/tool runtime details are not owned by this sub-skill. |

All app objects are created through the shared app factory unless they are service-specific helpers. The default public API root is `/api`, so frontend/deployment callers may see `/api` prepended to these prefixes.

## Route family ownership

### Agent runtime, configuration, versions, and automation

| Route family | App owner | Service owner(s) | Common DB/helper collaborators | Primary exceptions and envelopes | Notes |
| --- | --- | --- | --- | --- | --- |
| `POST /agent/run`, `POST /agent/nl2agent/run`, `GET /agent/stop/{conversation_id}` | `agent_app` runtime router | `agent_service.run_agent_stream`, `nl2agent_service.create_nl2agent_stream`, `agent_service.stop_agent_tasks` | conversation services, runtime state service, streaming channel, agent run manager, memory config service, SDK `agent_run` via service | `ForbiddenError` -> 403; `UnauthorizedError` -> 401 for NL2Agent; generic -> 500; runtime middleware may add trace IDs. | Streaming responses are SSE. Use SDK sub-skill for direct SDK event/model semantics. |
| Agent config CRUD/search/import/export/version routes under `/agent` | `agent_app` config router | `agent_service`, `agent_version_service`, `prompt_service`, `asset_owner_visibility` | `agent_db`, `agent_version_db`, `tool_db`, `skill_db`, `model_management_db`, `group_db`, `user_tenant_db` | `SkillDuplicateError` -> 409 on import; asset-owner prompt visibility can mask fields; other errors currently often map to 500. | Preserve legacy action-style routes such as `/agent/update` and `/agent/search_info`. |
| `/agent/automations` and conversation-bound automation route | `agent_automation_app` | `agent_automation.facade`, schedule engine, automation models/errors | automation DB helpers through facade/services | `UnauthorizedError`, automation-specific errors | Scheduled automation overlaps agent runtime and conversation state. |
| Agent repository `/repository/agent` | `agent_repository_app` | `agent_repository_service` | agent repository DB, agent/version import/export helpers | `UnauthorizedError`, `SkillDuplicateError` | Handles published agent listing/import and precheck logic. |
| A2A client/server management `/a2a/*` and `/a2a/client/*` | `a2a_client_app`, `a2a_server_app` | `a2a_client_service`, `a2a_server_service` | `a2a_agent_db` | service-specific discovery/endpoint errors | Direct external A2A protocol behavior crosses into SDK/runtime concerns. |

### Skills, repositories, tools, prompts, and MCP management

| Route family | App owner | Service owner(s) | Common DB/helper collaborators | Primary exceptions | Notes |
| --- | --- | --- | --- | --- | --- |
| `/skills` CRUD/list/install/upload/file-tree/instance routes | `skill_app` | `SkillService`, `get_official_skills_with_status`, `install_skills_from_zip_for_tenant`, `update_skill_list` | `skill_db`, `group_db`, `user_tenant_db`, SDK `SkillManager` and `SkillLoader` through service | `UnauthorizedError` -> 401, `ForbiddenError` -> 403, `SkillException` -> 400/409/500 | Order concrete routes before `/{skill_name}` and `/{skill_id:int}` routes. Skill package parsing lives in service code. |
| `POST /skills/nl2skill/run` | `skill_app` runtime router | `nl2skill_service.create_nl2skill_stream` | prompt utilities, model config, streaming helpers | auth and streaming exceptions | Direct agent/tool config semantics route to `sdk-agent-runtime`. |
| `/repository/skill` | `skill_repository_app` | `skill_repository_service` | skill repository DB, skill DB, repository precheck/import helpers | `ForbiddenError`, `UnauthorizedError`, `SkillDuplicateError` | `ensure_skill_repository_access` blocks ordinary USER role access. |
| `/tool` | `tool_config_app` | `tool_configuration_service` | `tool_db`, `user_tenant_db`, remote MCP/openAPI helpers | `MCPConnectionError`, `NotFoundException` | OpenAPI-service import touches MCP refresh paths. |
| `/mcp` | `remote_mcp_app` | `remote_mcp_service`, `tool_configuration_service`, `mcp_container_service` | remote MCP DB, container/runtime helpers | MCP validation/name/container/port errors, `UnauthorizedError` | Container lifecycle and real Docker behavior route to deployment/runtime owners. |
| `/mcp-tools` | `mcp_management_app` | `mcp_management_service` | market/community MCP DB | MCP validation/conflict/not-found errors | Community/registry market operations. |
| `/prompt` | `prompt_app` | `prompt_service`, `PromptOptimizationService` | prompt utilities, model service dependencies | generic prompt-generation errors | Streaming or LLM calls should be mocked in tests. |
| `/prompt_templates` | `prompt_template_app` | `prompt_template_service` | `prompt_template_db`, prompt-template utilities | `DuplicateError`, `NotFoundException`, `ValidationError` | System default template is immutable and synced on startup. |

### Models, providers, voice, tenants, users, groups, and auth

| Route family | App owner | Service owner(s) | Common DB/helper collaborators | Primary exceptions | Notes |
| --- | --- | --- | --- | --- | --- |
| `/model` | `model_managment_app` | `model_management_service`, `model_health_service`, `model_capacity_suggestion_service`, provider services | model management DB and tenant config helpers | `ValueError` often maps to 409/400; other errors to 500 | Capacity suggestions are non-mutating; model connectivity should be mocked unless a provider is explicitly provisioned. |
| `/voice` | `voice_app` | `voice_service` | tenant config/model helpers | `VoiceServiceException`, `STTConnectionException`, `TTSConnectionException`, `VoiceConfigException` | Voice service config belongs in backend constants and tenant config. |
| `/tenant_config/deployment_version` | `tenant_config_app` | direct constant response | `APP_VERSION` from constants | none | Version management updates `APP_VERSION`; frontend displays it through this endpoint. |
| `/tenants`, `/platform/quota`, `/tenants/{tenant_id}/quota` | `tenant_app`, `quota_app` | `tenant_service`, `quota_service` | tenant/user DB, quota DB/helpers | `ForbiddenError`, `NotFoundException`, `ValidationError`, `UnauthorizedError`, `PlatformQuotaConflictError` | Role-aware admin flows use `get_current_user_context` or tenant DB checks. |
| `/groups`, `/users`, `/invitations`, `/notifications` | `group_app`, `user_app`, `invitation_app`, `notification_app` | corresponding services | group/user/invitation/notification DB helpers | `NotFoundException`, `ValidationError`, `UnauthorizedError`, `DuplicateError`, `ForbiddenError` | Group IDs and in-group permissions affect asset visibility. |
| `/user` | `user_management_app` or `mock_user_management_app` | `user_management_service`, `user_service`, CAS service where relevant | token/session/user DB helpers, Supabase clients | invite/auth/user registration exceptions, `UnauthorizedError`, `ValidationError` | Config app selects mock router in speed mode. |
| `/user/oauth`, `/user/cas` | `oauth_app`, `cas_app` | OAuth/CAS services | OAuth account/session/user tenant DB | OAuth/CAS/tenant-resource exceptions | OAuth provider env values must still flow through constants or provider definitions. |

### Conversation, northbound, knowledge/memory/data, evaluation, and external integrations

| Route family | App owner | Service owner(s) | Common DB/helper collaborators | Route note |
| --- | --- | --- | --- | --- |
| `/conversation`, `/share` | `conversation_management_app`, `conversation_share_app` | conversation management/share service, file management service | conversation/message/attachment DB and file helpers | Runtime/frontend streaming contract often also needs `frontend-integration`. |
| `/nb/v1`, `/nb/v1/knowledge`, `/nb/a2a` | `northbound_app`, `northbound_knowledge_app`, `northbound_base_app` | `northbound_service`, vector/file/Redis services, A2A server service | token DB, knowledge DB, a2a DB | Partner-facing errors include rate limit, auth, conversation not found, and A2A JSON-RPC errors. |
| `/indices`, `/summary`, `/file`, `/tasks`, `/memory*` | vector, summary, file, data-process, memory apps | vector DB service, file management service, data-process service, memory services | knowledge, storage, memory, Redis, model DB helpers | Generic app/service boundary belongs here; deep vector/storage/memory/data-process behavior routes to `knowledge-data-memory`. |
| `/evaluation-*`, `/evaluators` | evaluation apps | evaluation services and report service | evaluation set/annotation/agent evaluation DB helpers | Evaluation prompt/model calls should be mocked unless explicitly provisioned. |
| `/datamate`, `/dify`, `/idata`, `/ragflow`, `/haotian`, `/image` | integration apps | integration-specific services | external config and knowledge/file helpers | External service calls require mocks or explicit credentials. |
| `/monitoring` | `monitoring_app` | direct monitoring DB session helpers | monitoring DB session | Use monitoring tests/static checks unless a monitoring DB is provisioned. |

## Failure trace playbooks

### Trace `/agent` route failures

1. Identify the router: runtime routes are on `agent_runtime_router`; config/edit routes are on `agent_config_router`.
2. Confirm the app process: `/agent/run`, `/agent/nl2agent/run`, and `/agent/stop/*` are included by runtime app; many `/agent/*` config routes are included by config app.
3. Inspect app-level auth and exception mapping:
   - `agent_run_api` delegates to `run_agent_stream` and maps `ForbiddenError` to 403, generic errors to 500. In debug mode it may expose the underlying error string.
   - `nl2agent_run_api` calls `get_current_user_info`, delegates to `create_nl2agent_stream`, returns SSE, maps `UnauthorizedError` to 401, and logs generic failures as 500.
   - Config endpoints commonly call `get_current_user_id/info`, derive effective tenant, and delegate to `agent_service` or `agent_version_service`.
4. Trace service collaborators:
   - `agent_service` uses `agent_run_manager`, `preprocess_manager`, `runtime_state_service`, `streaming_channel_manager`, conversation persistence services, memory context, prompt-template services, model DB, tool DB, skill DB, attachment/file helpers, and SDK `agent_run`.
   - Version routes use `agent_version_service`; guardrail generation uses `prompt_service`; list/detail visibility uses `asset_owner_visibility`.
5. Select mocks at lookup sites:
   - App tests patch names imported into `apps.agent_app`, such as `apps.agent_app.run_agent_stream`, `apps.agent_app.create_nl2agent_stream`, `apps.agent_app.get_current_user_info`, or `apps.agent_app.get_agent_info_impl`.
   - Service tests patch names imported into `services.agent_service`, such as `services.agent_service.search_agent_info_by_agent_id`, `services.agent_service.update_agent`, `services.agent_service.agent_run`, `services.agent_service.streaming_channel_manager`, or specific conversation helper imports.
6. If the failure is a streaming event shape or SDK config issue, use `sdk-agent-runtime` for the SDK-level event/config contract after the backend route/service path is identified.

### Trace `/skills` route failures

1. Identify whether the route is CRUD/package management (`router`) or NL2Skill streaming (`skill_creator_router`).
2. Check route order: list/static routes (`/official`, `/install`, `/upload`, `/instance`, `/scan_skill`) must remain before parameterized `/{skill_name}` or `/{skill_id:int}` routes.
3. Inspect app mapping:
   - `create_skill` builds `skill_data` from `SkillCreateRequest`, gets `(user_id, tenant_id)`, calls `SkillService.create_skill`, maps `UnauthorizedError` to 401, duplicate `SkillException` to 409, other `SkillException` to 400, and generic errors to 500.
   - `create_skill_from_file` accepts `SKILL.md` or ZIP bytes and delegates parsing/storage to `SkillService.create_skill_from_file`.
   - File tree/content endpoints must hide ASSET_OWNER-scoped skills from ordinary tenants.
4. Trace service collaborators:
   - `SkillService` handles YAML/ZIP parsing, parameter config extraction, permission defaults, access validation, SDK `SkillManager`/`SkillLoader`, and `skill_db` persistence.
   - Group and role checks use `group_db`, `user_tenant_db`, constants such as `PERMISSION_EDIT`, `PERMISSION_READ`, `PERMISSION_PRIVATE`, and role constants.
5. Select mocks at lookup sites:
   - App tests patch `apps.skill_app.SkillService`, `apps.skill_app.get_current_user_id`, `apps.skill_app.get_current_user_info`, `apps.skill_app.create_nl2skill_stream`, or `apps.skill_app.install_skills_from_zip_for_tenant`.
   - Service tests patch `services.skill_service.skill_db`, `services.skill_service.query_group_ids_by_user`, `services.skill_service.get_user_tenant_by_user_id`, `services.skill_service.SkillManager`, or file/YAML helpers.

## Adding a new app/service/domain capability

Use this checklist to keep route and service ownership clear:

1. Find the closest existing route family and response envelope using this map and the static route scanner.
2. If adding a new route family, decide whether it belongs in config app, runtime app, northbound app, or a service-specific app. Avoid adding runtime-only routes to config app or admin/config routes to runtime app.
3. Add Pydantic request/response models in shared constants only when the shape is reused or complex; otherwise keep simple `Body`, `Query`, and `Path` parameters in the app.
4. Implement service logic in a service module with plain return objects and domain exceptions.
5. Add database helpers only for persistence and keep tenant/user permission checks in services unless the app has a thin permission adapter.
6. Map domain exceptions at the app boundary and verify the JSON envelope expected by frontend/northbound callers.
7. Add focused app and service tests with explicit mocks; do not depend on live model providers, external SaaS, DB, Redis, Elasticsearch, MinIO, Docker, or K8s unless the selected case provisions them.
