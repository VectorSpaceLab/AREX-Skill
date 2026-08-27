---
name: deployment-maintenance
description: "Operate BiSheng deployment, local setup, Docker Compose, uv/npm
  commands, backend operational scripts, migrations versus backfills, arch
  guard, and SDD maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deployment-maintenance

Use this sub-skill when a task asks how to install, run, deploy, configure, migrate, operate, or maintain the BiSheng repository rather than changing one runtime subsystem's business logic.

## Start here

Run bundled helper commands from this sub-skill directory, or adjust the script path to this directory after import.


1. Inspect the deployment and script layout without starting services:
   ```bash
   python scripts/check_deployment_layout.py --repo-root <bisheng-checkout>
   ```
2. Read [references/workflows.md](references/workflows.md) for local dev, Docker Compose, worker, config, migrations, backend scripts, SDD, and arch-guard workflows.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for startup, config, storage, script, migration, and deployment symptoms.

## Owned responsibilities

- Docker Compose deployment under `docker/`, Nginx/entrypoint behavior, optional FT/OnlyOffice/Unstructured services, and production runtime topology.
- Local backend setup via uv, Platform/Client npm setup, worker commands, and Linsight process startup.
- `config.yaml` layering, `BS_*` env overrides, Redis config cache, encrypted password pitfalls, and storage service prerequisites.
- Backend operational scripts under `src/backend/scripts/`, root `scripts/`, and `tools/`.
- Alembic DDL versus manual data backfills, migration sequencing, and script dry-run/apply conventions.
- `AGENTS.md`, `docs/constitution.md`, `docs/SDD-Guide.md`, `scripts/arch-guard.sh`, and feature SDD maintenance process.

## Route sibling areas instead of duplicating them

- Use `backend-core` for API/service/model implementation details.
- Use `knowledge-rag` for knowledge worker/parser/vector behavior after the services are running.
- Use `workflow-engine` for workflow execution internals after the worker queue is healthy.
- Use `linsight-mcp` for Linsight task runtime internals after process startup is healthy.
- Use `identity-permissions-tenancy` for permission, tenant, SSO, gateway, and approval semantics.
- Use `frontend-apps` for React app code, Vite details beyond setup/proxy, and UI tests.

## Non-negotiables

- Run backend commands from `src/backend/` and frontend commands from the owning app directory.
- Prefer `uv sync --frozen` for backend dependencies; do not silently mutate user environments.
- Manual data migrations/backfills default to dry-run and require explicit apply.
- Alembic migrations contain DDL only; data backfill/cleanup belongs in operational scripts.
- Do not write plaintext passwords into config YAML. BiSheng encrypts sensitive config values.
- If `scripts/arch-guard.sh` reports a violation, fix the violation rather than bypassing the hook.
