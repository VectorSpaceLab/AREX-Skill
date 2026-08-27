# Backend Testing Reference

Use this reference when selecting tests, designing mocks, or planning difficult verification cases for backend FastAPI app/service/database changes.

## Test scope and commands

Nexent backend tests are pytest-based and normally live under these areas:

| Test area | Covers | When to run |
| --- | --- | --- |
| `test/backend/app/` | FastAPI route functions, `TestClient`, HTTP status/envelope mapping, auth helper usage, service delegation. | After app endpoint changes or exception mapping changes. |
| `test/backend/services/` | Service orchestration, database helper calls, SDK/external client mocking, permission decisions, prompt/model/skill logic. | After service logic changes. |
| `test/backend/agents/` | Backend NL2Agent/NL2Skill helpers and agent-side orchestration. | When backend agent prompt/config construction changes. |
| `test/backend/consts/` | Version/constants behavior. | After constant/version/error-code changes. |
| `test/backend/utils/` | Auth/config/prompt/file/etc. utility behavior. | After utility changes. |

Representative setup and run commands from a checkout:

```bash
cd backend
uv sync --extra data-process --extra test
uv pip install -e ../sdk
cd ..
pytest test/backend/app/test_agent_app.py -q
pytest test/backend/services/test_agent_service.py -q
```

Use focused pytest files first. The full backend suite can require more dependencies and more extensive mocking.

## Core testing rules

- Use pytest assertions, fixtures, `pytest.mark.asyncio` for async tests, and `pytest-mock` where available.
- Patch where the dependency is looked up, not where it is originally defined.
- Apply import-time patches before importing app modules that create clients or load global singletons.
- Mock external I/O by default: Supabase, Postgres, MinIO, Redis, Elasticsearch, model providers, external SaaS, HTTP clients, SDK agent execution, Docker/Kubernetes, and data-process workers.
- Do not run FastAPI service entrypoints just to test route functions. Use `FastAPI()` plus `include_router(...)` or direct async function calls.
- Keep new comments and docstrings in English.
- Preserve existing legacy response envelopes unless a coordinated frontend/API contract change is part of the task.

## Mocking patterns

### App endpoint tests

App tests should create a small FastAPI app around the router under test and patch the imported service/auth names in the app module.

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.agent_app import agent_runtime_router

app = FastAPI()
app.include_router(agent_runtime_router)
client = TestClient(app)

@pytest.mark.asyncio
async def test_agent_run_delegates_to_service(mocker):
    run_agent_stream = mocker.patch("apps.agent_app.run_agent_stream")
    # Arrange run_agent_stream to return a StreamingResponse or raise a domain exception.
```

Patch examples:

| App module | Patch examples |
| --- | --- |
| `apps.agent_app` | `run_agent_stream`, `create_nl2agent_stream`, `get_current_user_id`, `get_current_user_info`, `get_agent_info_impl`, `update_agent_info_impl`, `publish_version_impl` |
| `apps.skill_app` | `SkillService`, `get_current_user_id`, `get_current_user_info`, `create_nl2skill_stream`, `install_skills_from_zip_for_tenant`, `update_skill_list` |
| `apps.model_managment_app` | `create_model_for_tenant`, `check_model_connectivity`, `verify_model_config_connectivity`, `suggest_capacity`, `get_current_user_id` |
| `apps.prompt_template_app` | `list_prompt_templates_impl`, `get_prompt_template_detail_impl`, `create_prompt_template_impl`, `update_prompt_template_impl`, `delete_prompt_template_impl`, `get_current_user_id` |
| `apps.remote_mcp_app` | `get_remote_mcp_server_list`, `check_mcp_health_and_update_db`, `MCPContainerManager`, `get_current_user_info` |
| `apps.tenant_app` / `apps.user_app` | service functions plus `get_current_user_id` or `get_current_user_context` |

If importing an app module triggers global storage/database/client construction, stub those dependencies in `sys.modules` or patch factory functions before the import. Existing app tests use this pattern for storage, MinIO, Elasticsearch, database sessions, monitoring, and SDK modules.

### Service tests

Service tests should import only the service under test and patch collaborators at the service module lookup site.

```python
@pytest.mark.asyncio
async def test_update_agent_uses_db_and_permissions(mocker):
    query_agent = mocker.patch("services.agent_service.search_agent_info_by_agent_id")
    update_agent = mocker.patch("services.agent_service.update_agent")
    # Arrange DB records and assert service returns a plain dict or raises a domain exception.
```

Patch examples:

| Service module | Patch examples |
| --- | --- |
| `services.agent_service` | imported `database.*` helpers, `agent_run`, `agent_run_manager`, `preprocess_manager`, `streaming_channel_manager`, conversation service imports, `tenant_config_manager`, `build_memory_context` |
| `services.skill_service` | `skill_db`, `query_group_ids_by_user`, `get_user_tenant_by_user_id`, `SkillManager`, `SkillLoader`, YAML/ZIP/file helpers |
| `services.model_management_service` | model DB helpers, provider/service lookups, tenant config helpers, capacity suggestion helpers |
| `services.prompt_template_service` | `prompt_template_db` helpers, `get_prompt_generate_prompt_template`, normalization helpers |
| `services.agent_repository_service` / `services.skill_repository_service` | repository DB helpers, permission lookups, import/precheck helpers, duplicate-detection helpers |
| `services.northbound_service` | token/auth helpers, streaming chat start/stop, conversation/file/vector helpers, rate-limit helpers |

Services should raise domain exceptions or return plain values. If a service test observes `HTTPException` or `JSONResponse` from service code, treat it as a layer-boundary smell unless the existing module explicitly documents that legacy behavior.

## Test selection by change type

| Change type | Suggested focused tests |
| --- | --- |
| `/agent` app route or service wiring | `test/backend/app/test_agent_app.py`, `test/backend/services/test_agent_service.py`, plus version tests if touching agent versions. |
| Agent versioning or repository | `test/backend/services/test_agent_version_service.py`, `test/backend/app/test_agent_repository_app.py`, `test/backend/services/test_agent_repository_service.py`. |
| `/skills` CRUD/upload/import or repository | `test/backend/app/test_skill_app.py`, `test/backend/services/test_skill_service.py`, `test/backend/app/test_skill_repository_app.py`, `test/backend/services/test_skill_repository_service.py`, `test/backend/services/test_repository_import_precheck.py`. |
| NL2Agent/NL2Skill backend orchestration | `test/backend/services/test_nl2agent_service.py`, `test/backend/services/test_nl2skill_service.py`, `test/backend/agents/test_nl2agent_agent.py`, `test/backend/agents/test_nl2skill_agent.py`. |
| Model/provider/capacity | `test/backend/app/test_model_managment_app.py`, `test/backend/services/test_model_management_service.py`, `test/backend/services/test_model_health_service.py`, `test/backend/services/test_model_capacity_suggestion_service.py`, `test/backend/services/test_model_provider_service.py`. |
| Prompt generation/templates | `test/backend/app/test_prompt_app.py`, `test/backend/services/test_prompt_service.py`, `test/backend/app/test_prompt_template_app.py`, `test/backend/services/test_prompt_template_service.py`. |
| Conversation/runtime streaming | `test/backend/app/test_conversation_management_app.py`, `test/backend/services/test_conversation_management_service.py`, `test/backend/services/test_streaming_channel.py`, plus agent runtime tests when route changes touch `/agent/run`. |
| Auth/user/tenant/group/invitation | `test/backend/app/test_user_management_app.py`, `test/backend/services/test_user_management_service.py`, `test/backend/app/test_tenant_app.py`, `test/backend/services/test_tenant_service.py`, `test/backend/app/test_group_app.py`, `test/backend/services/test_group_service.py`, invitation tests. |
| MCP/tool config | `test/backend/app/test_remote_mcp_app.py`, `test/backend/services/test_remote_mcp_service.py`, `test/backend/services/test_mcp_management_service.py`, `test/backend/services/test_mcp_container_service.py`, `test/backend/app/test_tool_config_app.py`. |
| Memory/knowledge/data-process API boundary | App/service tests for memory, vector database, file management, data-process; use `knowledge-data-memory` for deep behavior and optional service constraints. |
| Version constant | `test/backend/consts/test_app_version.py`, plus route test for `/tenant_config/deployment_version` if response shape changes. |

## Static route verification

Run the bundled route scanner before and after route changes:

```bash
python skills/disco/nexent/sub-skills/backend-services-api/scripts/list_fastapi_routes.py --repo-root . --json > nexent-routes.json
```

Check for:

- A new route appears under the expected prefix and app module.
- No accidental duplicate method/path pair.
- Concrete routes still precede parameterized route families in the source module.
- Service/db/exception imports line up with the expected owner.

The scanner is not a substitute for runtime tests; it only detects static FastAPI decorators and import relationships.

## Difficult synthetic usability cases for verification

### Case 1: Add a new backend env var without violating the source-of-truth rule

Task shape:

1. Add a backend feature flag or timeout used by one service.
2. Define and coerce it in `backend/consts/const.py`.
3. Import the constant in the service or app that needs it.
4. Add or update env examples/deployment docs if the variable affects real deployments; route those file changes to deployment ownership.
5. Add tests proving the service uses the imported constant and that direct env reads did not spread.

Assertions:

- Static search finds no new `os.getenv()` or `os.environ.get()` outside the constants source of truth.
- Service tests patch the service module's imported constant or exercise the default value without mutating global env after import.
- No SDK module reads the env var; SDK config is passed as parameters.

### Case 2: Trace a failing `/agent` or `/skills` API and select mocks

Task shape:

1. Given a failing route, use the static scanner and API map to identify app module, endpoint function, service owner, DB helpers, and exception class.
2. Write or update one app test that patches the service at the app module lookup site and asserts HTTP status/envelope.
3. Write or update one service test that patches DB/external/SDK collaborators at the service module lookup site and asserts domain return/exception behavior.

Assertions:

- App test does not call real DB/storage/model/Redis/Elasticsearch/Supabase.
- Service test does not raise `HTTPException` from service code.
- The selected domain exception maps to the documented HTTP status or structured envelope.

## Common import-time test setup hazards

Some backend modules create global clients or import optional SDK/external modules during import. If a test imports such modules too early, it can try to configure storage, database, monitoring, Elasticsearch, Supabase, or SDK dependencies before mocks are installed. Prefer this order:

1. Insert backend source path if the test environment needs it.
2. Patch/stub external modules and client factories.
3. Patch database sessions or global clients.
4. Import the app/service under test.
5. Create a small `FastAPI()` test app only for the router under test.

Avoid `from module import *` in tests; explicit imports make patch targets and ownership clearer.
