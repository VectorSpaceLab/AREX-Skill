# Backend Troubleshooting Reference

Use this reference to diagnose backend route/service/database failures without starting live services unnecessarily.

## Fast symptom map

| Symptom | Likely layer | First checks | Usual fix |
| --- | --- | --- | --- |
| Route not found or wrong endpoint handles a path | App/router | Run `scripts/list_fastapi_routes.py`; inspect router prefix and route order. | Add route to the correct router/app process, preserve concrete-before-parameterized ordering, and avoid breaking legacy prefixes. |
| 401 Unauthorized | App/auth utility | Check `authorization` header use, `get_current_user_id/info/context`, speed-mode behavior, JWT secret/config, token DB mock. | Patch auth helper in tests; in code, pass auth through app layer and keep service permission checks explicit. |
| 403 Forbidden or hidden prompt fields | Permission/service visibility | Check role, tenant, ASSET_OWNER status, group IDs, in-group permission, knowledge-base read/edit adapters. | Use `asset_owner_visibility`, skill permission helpers, repository access helpers, or permission adapters consistently. |
| 409 duplicate or conflict | App/service exception mapping | Check duplicate skill/model/prompt/repository validation and exception class. | Raise the existing domain exception in service; map to 409 or existing envelope at app boundary. |
| App returns plain dict or inconsistent envelope | App route | Compare neighboring endpoints in same app. | Return `JSONResponse`/typed response/streaming response matching the route family. |
| Service returns `HTTPException` or `JSONResponse` | Service layer | Inspect service function return/raise statements. | Move HTTP mapping to app; make service return plain objects and raise domain exceptions. |
| Import-only test tries to contact Redis/Postgres/MinIO/Elasticsearch/Supabase | Import-time globals | Check global client construction and imports in app/service/database modules. | Patch client factories/modules before importing the target; prefer static AST scripts for route discovery. |
| Direct env access appears outside constants | Const/env rule | Static search for `os.getenv`, `os.environ.get`, or `getenv(` outside the constants source of truth. | Move read/default/coercion to `backend/consts/const.py`; import the constant elsewhere. |
| Prompt template sync fails on startup | Prompt service/config app | Check default YAML schema, placeholders, zh/en variants, and prompt-template DB mocks. | Restore required keys/placeholders; update normalization and prompt-template tests. |
| `/agent/run` streams stop unexpectedly | Runtime service/SDK boundary | Check `run_agent_stream`, runtime state cancel signal, streaming channel, stop event, conversation persistence, SDK runner mocks. | Isolate backend route/service behavior first; use SDK runtime guidance for event semantics and model/tool config. |
| AIDP startup fails | Config app startup | Check `ENABLE_AIDP_KNOWLEDGE` plus required AIDP URL/key constants. | Provide required config for live startup or disable the feature in test/import contexts. |

## Environment-variable violations

Project policy: backend env vars are centralized in `backend/consts/const.py`; SDK code should receive configuration through parameters.

Troubleshooting steps:

```bash
rg -n "os\.getenv|os\.environ\.get|getenv\(" backend sdk/nexent --glob '*.py'
```

1. Separate legacy findings from new changes.
2. For a new or changed variable, add it in `backend/consts/const.py` with the same default/coercion style used by nearby constants.
3. Replace app/service/util env reads with imports from `consts.const`.
4. If SDK code needs the value, pass it from backend services into SDK config objects/functions.
5. Add a focused test or static assertion that prevents the violation from returning.
6. If the variable affects deployment env files or SQL/init behavior, route those updates to `deployment-operations`.

Avoid changing process environment inside tests after modules are imported; constants are evaluated at import time.

## Auth and tenant failures

### Standard bearer-token routes

Most endpoints accept `authorization: Optional[str] = Header(None)` and call a helper from `utils.auth_utils`.

- In speed mode, `get_current_user_id` returns default user/tenant identities.
- Outside speed mode, missing or invalid authorization raises `UnauthorizedError`.
- JWT verification requires the configured JWT secret and user-tenant lookup.
- `get_current_user_info` adds locale from request cookies.
- `get_current_user_context` also resolves role for admin/tenant decisions.

Test guidance:

- Patch the helper where imported in the app module, such as `apps.skill_app.get_current_user_id`.
- For service-level permission tests, patch DB helper lookups such as user tenant or group ID functions at the service module lookup site.
- Do not build real Supabase clients or decode real production tokens in unit tests.

### Permission and visibility failures

- ASSET_OWNER-scoped agent prompts may be masked for ordinary tenants through `apply_agent_detail_prompt_visibility`.
- Skill visibility/edit permission depends on creator, role, groups, and `ingroup_permission`.
- Repository access may reject ordinary users before listing/creating/importing marketplace entries.
- Knowledge-base app permission adapters map missing KB to 404 and denied access to 403.

If a caller sees a resource in a list but receives a denial on detail/update, compare list post-processing with detail/edit permission checks; they may intentionally use different permission levels.

## Exception envelope diagnosis

Nexent uses mixed exception handling. Do not normalize response envelopes blindly; match the app process and route family.

| Where | Behavior |
| --- | --- |
| Shared app factory | `HTTPException` becomes `{"message": detail}`; `AppException` becomes `{"code", "message", "details"}`; `QuotaExceededError` becomes a 413 quota payload; generic exceptions become a generic 500. |
| Runtime app middleware | Adds `trace_id`; maps `AppException`, `QuotaExceededError`, `HTTPException`, and generic exceptions into structured runtime envelopes. |
| Individual app endpoints | Many endpoints catch legacy exceptions and raise `HTTPException` directly; some return legacy `{message, data}` or typed response models for compatibility. |
| Service layer | Should raise domain exceptions or return plain objects. HTTP mapping belongs in app code. |

When adding a new domain error:

1. Prefer an existing exception if the route family already uses it.
2. Use `AppException` plus `ErrorCode` when clients need stable business codes.
3. Add or update error-message and status mappings when a new `ErrorCode` is introduced.
4. Add app tests for status/envelope and service tests for exception raising.

## Database and transaction pitfalls

Common failures:

- Helper calls `commit()`, `rollback()`, or `close()` manually.
- Delete code physically deletes where the table expects soft delete.
- Read code forgets `delete_flag='N'`.
- New model redefines audit fields already provided by `TableBase`.
- Service catches broad DB exceptions and hides a real data-integrity problem.

Fix checklist:

1. Put table fields in `db_models.py` and ordinary tables on `TableBase`.
2. In helper functions, use `with get_db_session() as session:`.
3. Use `insert`/`update`/`select` and return plain dicts or IDs using existing helper patterns.
4. Set `created_by`/`updated_by` in create/update paths.
5. Soft-delete with `delete_flag='Y'` and keep reads filtered to active records.
6. Test helper usage by patching the helper at the service import site unless a DB integration test is explicitly selected.

If the task changes schema, do not stop at Python model changes. Coordinate SQL migration/init/version updates with the deployment operations owner.

## Route and app-composition pitfalls

- A route can exist in a module but not be served by the expected app process if the router is included only by config, runtime, or northbound app.
- Duplicate prefixes can be intentional. For example, `/agent` has separate runtime/config routers; `/skills` has CRUD and NL2Skill routers; `/voice` and `/file` have config/runtime variants.
- Parameterized routes can shadow static routes if source order is wrong.
- Some route families keep legacy action paths such as `/agent/update`, `/config/save_config`, or `/model/batch_update`; do not rename them without a coordinated API migration.

Use the static route scanner to confirm method, path, router variable, source module, endpoint function, and import relationships. If the scanner output differs from runtime behavior, check conditional `include_router` logic and app process selection.

## Prompt-template failures

Symptoms and fixes:

| Symptom | Check | Fix |
| --- | --- | --- |
| Startup sync fails | Config app startup calls prompt-template sync. | Validate YAML parses and required sections/placeholders remain. |
| User prompt template create/update rejected | `template_name`, `template_type`, zh/en content normalization. | Use `agent_generate`, non-empty normalized zh content, and unique names per tenant/user/type. |
| System template update/delete fails | `template_id = 0`. | This is intentional; update YAML/system sync flow instead of user-template CRUD. |
| Generated prompt misses tools/agents/task | YAML placeholders removed or renamed. | Restore placeholders or update rendering utilities and tests together. |

For YAML prompt authoring quality beyond backend wiring, use the prompt-writing skill if available in the active project.

## Startup and live dependency failures

Do not start full backend services while debugging static route or unit-test failures. The entrypoints can require real env, Redis, Ray/Celery, Postgres, MinIO, Elasticsearch, Supabase, model providers, or external service URLs.

- Use app-router unit tests for HTTP behavior.
- Use service tests with mocks for business behavior.
- Use the static route scanner for route inventory.
- Use integration/live startup only when the user explicitly asks for service operation verification or has provisioned dependencies.

If imports fail in an inspection/test environment because backend and SDK dependency variants conflict, use isolated Python environments or a project-prepared environment rather than loosening package pins blindly. Keep environment paths and host-specific details out of code, tests, and runtime documentation.

## `/agent` debugging checklist

1. Scan routes and identify runtime vs config app ownership.
2. Patch app imports first: auth helper, `run_agent_stream`, NL2Agent stream, agent/version service functions.
3. If app-level mapping is correct, move to `services.agent_service` and patch imported DB helpers, streaming manager, runtime state service, memory context, prompt/template utilities, and SDK `agent_run`.
4. For SSE failures, assert `StreamingResponse` media type and chunk format at app level, but mock the async generator.
5. For permission failures, check ASSET_OWNER visibility and user/tenant/group helper return values.
6. For SDK object/config failures, route SDK-level investigation to `sdk-agent-runtime`.

## `/skills` debugging checklist

1. Scan `/skills` route order and confirm whether the route is CRUD/package management or NL2Skill streaming.
2. Patch app imports: `SkillService`, `get_current_user_id/info`, official-skill install/list helpers, or `create_nl2skill_stream`.
3. For upload/package failures, inspect service-level ZIP/YAML parsing and path normalization with in-memory bytes or temp files.
4. For permission failures, patch group/user tenant lookups and assert `PERMISSION_EDIT`, `PERMISSION_READ`, or `PERMISSION_PRIVATE` behavior.
5. For repository import conflicts, expect `SkillDuplicateError` with duplicate names and a 409 app response.
6. For SDK skill loading internals, separate backend package handling from SDK skill-manager behavior and route direct SDK semantics to `sdk-agent-runtime`.
