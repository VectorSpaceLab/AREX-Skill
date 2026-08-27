# Persistence and Migrations

## Persistence Manager

LangBot uses SQLAlchemy/SQLModel with async sessions. SQLite is the default
community database; PostgreSQL is supported for production/cloud paths. The
persistence manager exposes tenant scopes, tenant unit-of-work helpers,
discovery scopes, table creation, resource stats, and shutdown.

## Migration Model

Fresh schemas are created from metadata, then frozen legacy migrations run up to
the 3.x baseline, then Alembic migrations run to head. New schema changes should
be Alembic revisions, not new legacy `dbmXXX` migrations.

Schema-change checklist:

1. Update persistence entity/model definitions.
2. Add an Alembic revision under the active versions path.
3. Include downgrade/rollback behavior where the repo expects it.
4. Update services, serializers, DTOs, API/MCP/web callers if the field is
   user-visible.
5. Add SQLite migration tests; add PostgreSQL tests when backend-specific.
6. Confirm tenant resource isolation if the field is Workspace-scoped.

## Test Selection

- SQLite migrations: safe local integration candidate.
- PostgreSQL migration tests: require `TEST_POSTGRES_URL` and service setup.
- Release/cloud migrations: run only for cloud/operator migration changes.

## Common Pitfall

A migration that works on SQLite can still fail on PostgreSQL due to type,
constraint, index, or transaction semantics. Run Postgres-specific tests when
changing Postgres-only paths, pgvector, release migrations, or cloud tenancy.
