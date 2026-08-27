# Migrations and Data Sync

## Purpose

Use this reference when changing Nexent database schema, versioned migration scripts, fresh-deploy init SQL, or one-off data synchronization scripts.

## Migration rule

When adding or changing tables, columns, indexes, constraints, seed data, or permissions through a migration script, keep fresh-deploy SQL in sync. The required update set is:

- Versioned migration under deployment SQL migrations.
- Docker fresh-deploy init SQL.
- Kubernetes/Helm fresh-deploy init SQL when that chart contains its own init copy.
- Backend ORM/model/schema code and tests.
- App version or release notes when project policy requires it.

## How to make a schema change safely

1. Identify the current app version and latest migration naming convention.
2. Add an idempotent migration or extend the appropriate merged migration file only when that is the repo's current convention.
3. Update fresh-deploy init SQL so new installations get the same schema without replaying migrations.
4. Update backend database models/helpers and any Pydantic/API models.
5. Update tests for both migration/static SQL presence and backend behavior.
6. If the change affects frontend data shape, update TypeScript types and service mappers.

## Data sync scripts

Data synchronization scripts can mutate users, skills, Supabase/PostgreSQL rows, or skill directories. Treat them as upgrade-only operations:

- Read the script and migration notes before running.
- Confirm backup and target environment.
- Do not run sync scripts in ordinary verification; test with mocks or static checks unless the user approves a live target.

## Static checker

Use `scripts/check_sql_migration_sync.py --repo-root <checkout>` to list migration/init/version files and catch common omissions. This helper does not execute SQL or connect to a database.
