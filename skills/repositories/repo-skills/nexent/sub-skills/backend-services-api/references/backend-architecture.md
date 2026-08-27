# Backend Architecture Reference

This reference distills Nexent backend source and docs into an operating contract for future backend changes. It is intentionally self-contained; use source files only as the checkout being edited, not as required reading for this sub-skill.

## Backend shape

Nexent's backend is a Python 3.11 FastAPI service layer for agent configuration, runtime streaming, repository/market flows, model configuration, tools/MCP, prompts, tenants/users/groups, knowledge/memory APIs, northbound partner APIs, and background entrypoints.

Important backend source areas:

| Area | Responsibility | Change guidance |
| --- | --- | --- |
| `backend/apps/` | FastAPI HTTP boundary: routers, request parsing, auth extraction, response envelopes, exception-to-HTTP mapping, app composition. | Add/modify endpoints here, but keep business rules in services. Preserve existing path and response compatibility. |
| `backend/services/` | Business orchestration: SDK calls, database helpers, external clients, permission decisions, stream assembly, prompt-generation workflows. | Raise domain exceptions; do not return FastAPI responses or raise `HTTPException` from service code. |
| `backend/database/` | SQLAlchemy models and database CRUD helpers; MinIO/Postgres client wrappers. | Use `get_db_session()` and soft deletes; keep transaction management centralized. |
| `backend/agents/` | Backend-side agent runtime managers, NL2Agent/NL2Skill orchestration helpers, pre-processing managers. | Use this sub-skill for service wiring; use the SDK runtime sub-skill for direct SDK object semantics. |
| `backend/consts/` | Environment constants, Pydantic request/response models, business error codes/messages, domain exceptions, feature flags. | This is the single source of truth for env vars, exceptions, and shared models. |
| `backend/prompts/` | YAML prompt templates for manager/managed agents, NL2Agent/NL2Skill, guardrails, utility prompts, memory and evaluation prompts. | Preserve placeholders and language variants. Prompt-template DB sync depends on these files. |
| `backend/tool_collection/` | Backend-maintained local MCP/LangChain tool surfaces and NL2Agent MCP helpers. | Keep tool registration and schema generation aligned with tool config APIs. |
| `backend/utils/` | Auth, config, prompt-template, file, Redis, logging, model-name, monitoring, and thread utilities. | Reuse utilities rather than duplicating token, tenant, storage, or prompt logic in apps. |

## Service entrypoints and app composition

Treat service entrypoint files as reference-only evidence when editing backend code. Do not copy them into tests or run them just to inspect routes.

| Entrypoint | Role | Key composition notes |
| --- | --- | --- |
| `backend/config_service.py` | Config/admin API process, default port 5010. | Loads env, configures logging, starts evaluation maintenance, serves `apps.config_app.app`, logs `APP_VERSION`. |
| `backend/runtime_service.py` | Runtime/chat API process, default port 5014. | Serves `apps.runtime_app.app`; runtime app adds `ExceptionHandlerMiddleware` and includes `/agent/run`, conversation, share, file, voice, and NL2Skill runtime routes. |
| `backend/northbound_service.py` | Partner/northbound API process, default port 5013. | Serves `apps.northbound_base_app.northbound_app`, which includes `/nb/v1`, `/nb/v1/knowledge`, and `/nb/a2a` routers. |
| `backend/data_process_service.py` | Data-process service manager. | Coordinates Redis/Ray/Celery/Flower and data-process workers; route deep data-processing issues to `knowledge-data-memory`. |
| `backend/mcp_service.py` | FastMCP server plus management API. | Mounts local, remote, and OpenAPI-derived MCP tools; route direct MCP transport/tool runtime details to `sdk-agent-runtime` or `deployment-operations` as appropriate. |

Common app construction uses `create_app(...)` with default `root_path="/api"`, CORS, monitoring setup, and shared exception handlers. `config_app` includes most configuration/admin routers. `runtime_app` includes only runtime user flows plus global middleware. `northbound_base_app` disables monitoring by default and combines northbound REST/chat/knowledge APIs with A2A endpoints.

## Layer contracts

### App layer (`backend/apps/`)

App endpoints must:

1. Define or include an `APIRouter` with a stable prefix.
2. Parse input with Pydantic models from `consts.model`, FastAPI `Body`, `Query`, `Path`, `Header`, and file/upload types.
3. Retrieve bearer tokens with `authorization: Optional[str] = Header(None)` when auth is needed.
4. Resolve identity through `utils.auth_utils` helpers such as `get_current_user_id`, `get_current_user_info`, `get_current_user_context`, or northbound bearer helpers.
5. Delegate business work to `services.*` functions/classes.
6. Convert domain/service exceptions to `HTTPException` or an existing response envelope at the HTTP boundary.
7. Return `JSONResponse(status_code=HTTPStatus.OK, content=...)` or an existing typed/streaming response shape.

Do not put long business workflows, SDK orchestration, DB transaction logic, or token parsing inside app functions. Keep route ordering stable: concrete routes must come before parameterized catch-all routes where the same prefix is used (for example `/skills/official` before `/skills/{skill_name}`).

### Service layer (`backend/services/`)

Services must:

- Implement business logic and orchestration.
- Call database helpers, SDK functions, external clients, prompt utilities, and background managers.
- Raise domain exceptions from `consts.exceptions` or `AppException` with an `ErrorCode` when a business error needs structured handling.
- Return plain Python objects, async generators, or domain data structures, not FastAPI `Response` objects.
- Read backend configuration via imports from `consts.const`; do not call env APIs directly in service code.

When a service must proceed after a non-critical DB/external failure, catch the most specific domain exception or low-level exception, log the context, and either return a documented fallback or wrap it in a domain exception for the app layer.

### Database layer (`backend/database/`)

Database helpers must:

- Define ordinary models in `db_models.py` using `TableBase` unless a special no-audit table is intentional.
- Let `TableBase` provide `create_time`, `update_time`, `created_by`, `updated_by`, and `delete_flag`.
- Use `with get_db_session() as session:` for transaction boundaries.
- Avoid direct `commit()`, `rollback()`, and `close()` in helper functions; the context manager centralizes them.
- Soft-delete rows with `delete_flag='Y'` and default reads to `delete_flag='N'`.
- Let DB exceptions propagate to services/app handlers unless a service explicitly owns a fallback.

Use SQLAlchemy Core-style `insert`, `update`, and `select` plus `session.execute()`/`session.scalars()` where the surrounding module follows that style. `session.add()` is acceptable only where already idiomatic.

### Consts, models, and errors

`backend/consts/const.py` is the only backend file that should read environment variables. Shared request/response models belong in `backend/consts/model.py`. Domain exceptions belong in `backend/consts/exceptions.py`. New business error codes belong in `backend/consts/error_code.py` and their messages/status mappings must stay synchronized with the existing error-message/status modules.

Nexent currently uses both structured and legacy exception styles:

| Style | Use when | Handling |
| --- | --- | --- |
| `AppException(ErrorCode, message, details)` | The client needs a stable business code and structured details. | `app_factory` and runtime middleware map it through its `http_status` and `error_code`. |
| Legacy simple exceptions such as `UnauthorizedError`, `ForbiddenError`, `ValidationError`, `NotFoundException`, `SkillException`, `SkillDuplicateError`, `QuotaExceededError` | Existing service/app families already use them or a simple HTTP mapping is sufficient. | App endpoints map them to HTTP status codes; runtime middleware handles selected shared exceptions. |

## Environment-variable source of truth

When adding a backend feature flag or service config variable:

1. Add the variable and default/coercion in `backend/consts/const.py`.
2. Import the resolved constant from `consts.const` in apps/services/utils.
3. Pass resolved configuration into SDK objects as constructor/function parameters. Do not add SDK `from_env()` helpers for this project.
4. Update deployment env examples and operational documentation when the variable is required for real services; route deployment-file updates to `deployment-operations` if the task includes Docker/Kubernetes env files.
5. Add tests that prove no app/service/SDK code reads the env var directly.
6. Run a static search for direct env reads outside `backend/consts/const.py`; move or justify any existing legacy exception before expanding it.

Common constant groups include search/vector/database/storage service URLs, Supabase/JWT/CAS/OAuth auth config, data-process/Ray/Celery/Redis settings, runtime streaming TTL/cancel settings, MCP Docker/image settings, model/provider capacity flags, AIDP integration, tenant/asset-owner permissions, and `APP_VERSION`.

## Auth, tenant, and permission flow

Most app endpoints derive identity using one of these helpers:

| Helper | Returns | Typical use |
| --- | --- | --- |
| `get_current_user_id(authorization)` | `(user_id, tenant_id)` | Standard app endpoints. In speed mode it returns default identities; otherwise it requires a valid JWT and user-tenant mapping. |
| `get_current_user_info(authorization, request)` | `(user_id, tenant_id, language)` | Endpoints that need locale/cookie language, NL2Agent/NL2Skill, prompt generation, or asset visibility. |
| `get_current_user_context(authorization)` | `(user_id, tenant_id, role)` | Tenant/user/admin routes that must evaluate role. |
| `validate_bearer_token` / `get_user_and_tenant_by_access_key` | token validation data | Northbound/API-key flows. |

Permission patterns:

- ASSET_OWNER-scoped agents can hide prompt fields from ordinary tenants; use `asset_owner_visibility` post-processing for list/detail responses.
- Skill visibility and edit rights combine creator, role, group IDs, and in-group permission (`EDIT`, `READ_ONLY`, `PRIVATE`).
- Knowledge-base read/edit permission adapters convert service `ValueError` to 404 and `PermissionError` to 403 at the FastAPI boundary.
- Repository flows validate creator/publisher/reviewer rights in service helpers and map `UnauthorizedError`, `ForbiddenError`, and duplicate-skill cases in the app layer.

## Prompt-template ownership

Prompt templates are YAML files under backend prompt directories plus database rows for user/system prompt-generation templates. YAML templates can contain `system_prompt`, `planning`, `managed_agent`, `final_answer`, `tools_requirement`, and `few_shots` sections. Common placeholders include `tools`, `managed_agents`, `task`, `remaining_steps`, `authorized_imports`, `facts_update`, and `answer_facts`.

Prompt-template service rules:

- The system default prompt template has `template_id = 0`, name `system_default`, and type `agent_generate`.
- Config app startup syncs the YAML-backed system default into the database.
- User prompt templates must normalize content keys, reject empty names/content, reject unsupported template types, detect duplicate names per tenant/user/type, and prevent updates/deletes of the system default.
- Keep English comments/docstrings in code, but string literals/YAML content may be localized where the product expects zh/en variants.

## Safe backend change workflows

### Add or change an endpoint

1. Use `scripts/list_fastapi_routes.py` to confirm the current prefix, function name, and collision risks.
2. Add or update request/response models in `consts.model` if the payload is shared or complex.
3. Add an app endpoint that parses input, obtains auth, and delegates to a service.
4. Put business logic in a service and data persistence in database helpers.
5. Add or reuse domain exceptions and map them at the app boundary.
6. Add app tests that patch services at the app module lookup site and service tests that patch database/external collaborators at the service lookup site.
7. If the response shape is consumed by the frontend, route the TypeScript/client update to `frontend-integration`.

### Add a database-backed feature

1. Add or update `db_models.py` model fields and database helper functions.
2. Use `get_db_session()` and audit/soft-delete conventions.
3. Add service methods that validate permissions and call helpers.
4. Add app endpoints and tests.
5. If the schema changes through SQL migrations or fresh-deploy init files, route migration/init/version updates to `deployment-operations`.

### Add a backend prompt or NL2Agent/NL2Skill behavior

1. Update the nearest YAML template(s) and keep zh/en variants aligned where both exist.
2. Preserve placeholders expected by prompt rendering utilities.
3. Update prompt utilities or prompt-template services if the schema changes.
4. Add tests around normalized content, prompt generation/optimization service calls, and app streaming/error envelopes.
5. Route direct SDK agent config or event semantics to `sdk-agent-runtime`.
