---
name: backend-api-services
description: "Modify and debug Transformer Lab FastAPI backend routers,
  services, schemas, auth/team context, DB migrations, and backend Python
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---
# backend-api-services

Use this sub-skill for backend work in `api/`: FastAPI app setup, routers, services, Pydantic schemas, auth/team context, SQLAlchemy/Alembic, filesystem-backed storage, and Python backend tests/lint.

## Load order

1. Read [references/api-architecture.md](references/api-architecture.md) before changing code.
2. Use [references/backend-testing.md](references/backend-testing.md) for test/lint commands and test patterns.
3. Use [references/troubleshooting.md](references/troubleshooting.md) when debugging startup, auth, DB, task YAML, cache, or org-context issues.

## Route to another sub-skill

- Task/job/provider launch lifecycle, compute-provider dispatch, local/remote queue semantics: `../task-execution-compute/SKILL.md`.
- CLI behavior, `lab` command UX, SDK package APIs, or remote SDK package behavior: `../cli-sdk-workflows/SKILL.md`.
- Frontend fetch clients, React browser UI, browser auth retries, or visual verification: `../frontend-web-app/SKILL.md`.

## Backend operating rules

- Keep routers thin: request parsing, FastAPI dependencies, HTTP status mapping, and simple response shaping only.
- Put business logic in `api/transformerlab/services/`; use Pydantic request/response schemas in `api/transformerlab/schemas/`.
- Protected routes need `get_user_and_team` or an app-level router dependency; owner-only routes use `require_team_owner`.
- JWT requests require `X-Team-Id` or the team cookie; API-key requests may be team-scoped or fall back through `X-Team-Id`/personal team.
- Use `lab.storage` and workspace helpers for team-scoped filesystem state unless a DB table is clearly required.
- Keep SQLAlchemy code SQLite and PostgreSQL compatible. Do not add DB or Alembic foreign keys.
- For SQLAlchemy `DateTime` values, use `utc_now_naive()` from `transformerlab.utils.datetime_utils`.
- If `lab-sdk/` changes affect backend imports, reinstall the local SDK package and restart the API; the API imports installed `lab` code.
- Remember the API source-run caveat: backend code runs from the `api/` source tree, while `api/pyproject.toml` is mainly dependency packaging.
