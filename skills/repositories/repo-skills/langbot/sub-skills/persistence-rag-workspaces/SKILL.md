---
name: persistence-rag-workspaces
description: "Maintain LangBot persistence, Alembic migrations, Workspace
  tenancy, cloud directory state, RAG knowledge bases, vector backends, storage,
  monitoring, and telemetry workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Persistence, RAG, Workspaces, and Monitoring

Use this sub-skill for database models, migrations, tenant scoping, Workspace
collaboration, cloud directory/launch behavior, RAG/knowledge-base operations,
vector backends, file storage, monitoring exports, and telemetry.

## Read First

- [references/persistence-and-migrations.md](references/persistence-and-migrations.md)
  for SQLAlchemy/SQLModel, SQLite/PostgreSQL, Alembic, and release migrations.
- [references/workspaces-and-tenancy.md](references/workspaces-and-tenancy.md)
  for `RequestContext`, `ExecutionContext`, membership, tenant scopes, and
  resource isolation.
- [references/rag-vector-storage.md](references/rag-vector-storage.md) for
  knowledge bases, parsers, vector stores, and local/S3 storage.
- [references/monitoring-and-telemetry.md](references/monitoring-and-telemetry.md)
  for monitoring APIs, retention, resource stats, and telemetry boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) for migration,
  vector, storage, and tenant-context failures.

## Hard Rules

- New schema changes use Alembic under the current Alembic versions directory;
  do not add new legacy `dbmXXX` migrations.
- Tenant services must accept a `RequestContext` or trusted execution context
  and fail closed when context is missing.
- API keys are bound to one Workspace; do not let request headers switch an API
  key's tenant.
- Vector/database service-backed tests are optional unless the task changes that
  backend; SQLite and unit tests cover the general path.

## Focused Checks

```bash
python scripts/select_langbot_checks.py persistence-rag
uv run pytest tests/integration/persistence/test_migrations.py -q --tb=short
uv run pytest tests/unit_tests/vector/test_mgr.py tests/unit_tests/vector/test_vdb_filter_conversion.py -q --tb=short
uv run pytest tests/unit_tests/storage/test_storage_manager.py tests/unit_tests/rag/test_runtime_service.py -q --tb=short
```
