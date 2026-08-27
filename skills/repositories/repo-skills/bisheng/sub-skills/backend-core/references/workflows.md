# Backend Core Workflows

## When to read

Read this for BiSheng FastAPI backend core tasks: routes, DDD modules, schemas, settings, SQLModel DAO surfaces, error codes, and focused tests that are not specifically workflow, RAG, Linsight, permission, or deployment work.

## Quick surface inspection

Run the bundled inspector from a BiSheng checkout root:

```bash
python scripts/inspect_backend_surface.py --repo-root <bisheng-checkout>
```

The helper uses filesystem and AST inspection only; it does not import app modules or require MySQL/Redis/OpenFGA.

## App startup and router workflow

Key runtime facts:

- `bisheng.main:create_app()` builds the FastAPI app, installs exception handlers, registers middleware, and includes both v1 and v2 router groups.
- Lifespan calls `initialize_app_context(config=settings)`, `init_default_data()`, startup backfills, then closes app context and thread pool on shutdown.
- `bisheng/api/router.py` owns the global `/api/v1` and `/api/v2` route groups.
- `/api/v1` is frontend-facing. `/api/v2` is external/RPC-style and includes knowledge, filelib, chat, assistant, workflow, LLM, flow, and citation routes.

Checklist for adding a backend API:

1. Route to the owning domain module. If it is a new bounded context, use `bisheng/<module>/api/router.py` and `bisheng/<module>/domain/...`.
2. Keep endpoint functions thin: parse/validate request, depend on `UserPayload`, and call a service.
3. Register the module router in `bisheng/api/router.py` exactly once.
4. Return via `resp_200`, domain error codes, or `BaseErrorCode` exceptions. Do not launder internal exceptions through `resp_500(message=str(e))`.
5. Add focused tests under `src/backend/test/<module>/`.

## DDD module workflow

BiSheng's backend convention is:

```text
api/router.py or api/endpoints/...  ->  domain/services/...  ->  domain/repositories/... or DAO  ->  database/models/...
```

Allowed variations:

- Simple legacy modules may use a service that calls an existing DAO directly.
- Workflow and MCP modules use specialized layouts rather than a full `api/domain/repositories` tree.
- `common/`, `core/`, and `database/models/` are shared infrastructure and must not import business domain services.

Review points:

- New endpoints do not import ORM models directly.
- New service code does not add raw queries when a DAO/repository boundary is expected.
- Cross-module API imports are avoided.
- Error code module numbers follow `common/errcode/` conventions.

## Response and pagination workflow

Core response classes live in `common/schemas/api.py`:

- `UnifiedResponseModel[T]` is the normal envelope.
- `resp_200(data, message="SUCCESS")` returns success.
- `resp_500(code, data, message)` exists for business-compatible response formatting, not for swallowing unexpected internal exceptions.
- `PageData[T]` uses `data` and `total` for classic pagination.
- `PageInfiniteCursorData[T]` uses `data`, `page_size`, `has_more`, and `next_cursor` for cursor pagination.
- `SSEResponse` is used for event-stream payloads.

When implementing cursor pagination, also read `identity-permissions-tenancy`; the fetch-until-enough loop and DM8 keyset behavior are permission-sensitive.

## Settings and application context workflow

- Settings are Pydantic models in `core/config/settings.py` plus config submodules.
- Config loading is layered: YAML, environment variables, database config, then Redis cache.
- Infrastructure clients are managed through `core/context/` managers and initialized by lifespan.
- One-off scripts that need Redis, MinIO, Milvus, Elasticsearch, OpenFGA, or HTTP clients must initialize and close app context; database-only scripts may use DB sessions directly.

Avoid:

- Re-parsing YAML in new runtime code.
- Creating independent Redis/MinIO/ES clients instead of using managers.
- Writing plaintext secrets to config files.

## Data model and DAO workflow

- Legacy ORM/DAO files live in `database/models/`.
- Domain-specific models may live under `bisheng/<module>/domain/models/`.
- DAOs conventionally expose sync `get_*`/`create_*` and async `aget_*`/`a*` methods.
- Use dialect helpers for DM8-compatible JSON, large text, and timestamp defaults.
- Tenant-aware ORM SELECT filtering is automatic, but raw SQL and bulk statements are not.

## Focused test workflow

Run from `src/backend/`:

```bash
uv sync --frozen
uv run pytest test/<module>/test_file.py::test_case -q
uv run pytest test/common/ test/core/ test/database/ -q
uv run ruff check --fix <changed-files>
uv run ruff format <changed-files>
```

Use the smallest test target first. Escalate to broader module suites only when shared schemas, settings, app context, router registration, or middleware changed.

## Review checklist

- Endpoint, service, DAO, and schema boundaries are preserved.
- Exceptions are logged or propagated intentionally.
- Loguru calls use `{}` placeholders or f-strings; no `exc_info=` with loguru.
- New tests are under `test/<module>/`.
- DM8 compatibility is considered for DDL, JSON, text, keyset, and raw SQL.
- Tenant and permission concerns are routed to the dedicated identity sub-skill when they determine correctness.
