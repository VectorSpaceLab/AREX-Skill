# Deployment and Maintenance Workflows

## Local development workflow

Backend from `src/backend/`:

```bash
uv sync --frozen
export config=config.yaml
uv run uvicorn bisheng.main:app --host 0.0.0.0 --port 7860 --workers 1 --no-access-log
uv run pytest test/<module>/test_file.py -q
uv run ruff check --fix <changed-files>
uv run ruff format <changed-files>
```

Platform app from `src/frontend/platform/`:

```bash
npm install
npm start -- --host 0.0.0.0
npm run build
npm test
```

Client app from `src/frontend/client/`:

```bash
npm install
npm run dev
npm run build
npm run check-imports
npm run test:ci
```

## Worker startup workflow

From `src/backend/` with the same `config` environment as the API:

```bash
uv run celery -A bisheng.worker.main worker -l info -c 20 -P threads -Q knowledge_celery -n knowledge@%h
uv run celery -A bisheng.worker.main worker -l info -c 100 -P threads -Q workflow_celery -n workflow@%h
uv run celery -A bisheng.worker.main beat -l info
uv run python bisheng/linsight/worker.py --worker_num 4 --max_concurrency 5
```

Route runtime failures after startup:

- knowledge worker internals: `knowledge-rag`.
- workflow worker internals: `workflow-engine`.
- Linsight worker internals: `linsight-mcp`.
- tenant/permission worker context: `identity-permissions-tenancy`.

## Docker Compose workflow

The primary Compose file is `docker/docker-compose.yml`. It starts MySQL, Redis, backend API, backend worker, frontend, Milvus dependencies, Milvus standalone, Elasticsearch, and MinIO-like object storage. Optional compose files cover fine-tuning, OnlyOffice, and unstructured parsing services.

Common quick start:

```bash
cd docker
docker compose -f docker-compose.yml -p bisheng up -d
```

For mixed local development, start infrastructure in Docker, then stop containers that conflict with source-run API/worker/frontend processes.

## Config workflow

Runtime settings merge layers:

```text
YAML config -> BS_* environment -> database config -> Redis cache (~100s TTL)
```

Important config rules:

- API, workers, and scripts must use the same `config` env value.
- Passwords in config YAML are Fernet-encrypted; never write plaintext to debug.
- MinIO `sharepoint` must match frontend proxy target host exactly for signed URLs.
- Gateway mode changes frontend proxy target from FastAPI to the Java gateway.

## Migration versus script workflow

Schema changes:

- Whole-table creation can be represented by SQLModel table definitions if create-all handles it.
- Existing table changes require Alembic revisions under `bisheng/core/database/alembic/versions/`.
- Alembic revisions should not perform data backfills, dedupes, reads-then-writes, or cleanups.

Data operations:

- Use `src/backend/scripts/` with dry-run by default and `--apply` or equivalent for writes.
- Shell wrappers set `PYTHONPATH=./` and are run from `src/backend/`.
- Scripts touching OpenFGA/Redis/Milvus/ES/MinIO initialize app context and close it.
- Cross-tenant maintenance uses tenant bypass helpers intentionally.

## SDD and architecture guard workflow

For non-trivial features:

1. Read `docs/constitution.md` and the relevant `AGENTS.md` files.
2. Follow `docs/SDD-Guide.md`: spec, design, tasks, branch, implementation waves, task review, e2e, code review.
3. Keep feature artifacts under `features/v{X.Y.Z}/{NNN}-{name}/`.
4. Let `scripts/arch-guard.sh` enforce architecture rules and fix violations immediately.

## Source script inventory

Useful repo-owned script categories:

- Root `scripts/arch-guard.sh` and RBAC/ReBAC leak checks: copy/reference as architecture checks; do not run as generic formatting.
- `src/backend/scripts/*.py/*.sh`: operational backfills, migrations, diagnostics, exports; often safe in dry-run but may require live DB/app context.
- `tools/*errcode*`: error-code i18n extraction/scanning helpers.
- Docker scripts: deployment operations, not unit-test helpers.

## Test selection

Use focused commands from the owning sub-skill first. Use broader commands when shared maintenance changed:

```bash
cd src/backend
uv run pytest test/common/ test/core/ test/permission/ test/tenant/ -q
bash ../../scripts/arch-guard.sh
```

Run frontend test suites from their app directories only.
