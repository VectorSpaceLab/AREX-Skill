---
name: transformerlab-app
description: "Operate on the Transformer Lab application monorepo: React web UI,
  FastAPI backend, task/job compute providers, Typer CLI, and Python SDK
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Transformer Lab App Repo Skill

Use this skill for work on the Transformer Lab application repository: the React web UI, FastAPI API, task/job execution system, compute providers, `lab` CLI, and `transformerlab` Python SDK. The skill is self-contained; read the bundled references instead of reopening the source docs that were used to create it.

## First Checks

1. Read [Repository provenance](references/repo-provenance.md) if the current checkout may differ from the snapshot used to build this skill.
2. Use [Development commands](references/development-commands.md) to choose setup, lint, test, app-run, and API curl checks.
3. Use [Troubleshooting](references/troubleshooting.md) for cross-cutting environment, install, auth, service, and backend issues.
4. If you are only checking local readiness, run the bundled helper:

```bash
python <this-skill>/scripts/check_transformerlab_dev_readiness.py --repo-root <checkout>
```

The helper is read-only by default. It checks expected repo files, Node/Python/tool versions, known ports, and optional server reachability without starting the app or mutating environments.

## Route by Task

| User request or code area | Read next |
| --- | --- |
| React/TypeScript UI, Joy UI components, routes, authenticated fetches, SWR, task/job screens, visual checks, Playwright selectors | [frontend-web-app](sub-skills/frontend-web-app/SKILL.md) |
| FastAPI routers, service layer, Pydantic schemas, auth/team context, DB/Alembic, backend tests/lint, API curl auth | [backend-api-services](sub-skills/backend-api-services/SKILL.md) |
| `task.yaml`, task import, job launch, local/remote queues, compute providers, sweeps, interactive sessions, logs, quotas, storage probes, multi-node behavior | [task-execution-compute](sub-skills/task-execution-compute/SKILL.md) |
| `lab` CLI commands, profiles/config/auth, JSON/pretty output, Textual monitor, task/job CLI flows, Python SDK APIs, `tfl-remote-trap` | [cli-sdk-workflows](sub-skills/cli-sdk-workflows/SKILL.md) |

## Repo Operating Rules

- Do not commit directly to `main`; create a branch for code work.
- Frontend work uses React 18 + TypeScript in `src/renderer/`. The app is a browser web app; do not add Electron, IPC, or main-process patterns.
- Frontend UI uses MUI Joy (`@mui/joy`) and `lucide-react`, not MUI Material or MUI icons.
- Backend business logic belongs in `api/transformerlab/services/`; routers should validate HTTP input/output and call services.
- Use Pydantic models in `api/transformerlab/schemas/` for distinct API validation/serialization contracts.
- Prefer filesystem storage for tasks/jobs/artifacts when repo patterns already do so; keep SQLAlchemy code SQLite and PostgreSQL compatible.
- Do not add foreign keys to DB tables or Alembic migrations.
- For SQLAlchemy `DateTime` values, use `utc_now_naive()` from `transformerlab.utils.datetime_utils`.
- CLI command output must preserve pretty and JSON modes; root global options such as `--format`, `--profile`, and `--no-interactive` come immediately after `lab`.
- SDK task scripts should call `lab.init()` before logging/progress/save helpers and pass `Lab.finish(score=...)` a dictionary, not a scalar.

## Fast Validation Map

- Frontend changed: run `npm run format` on changed frontend files or `npm run format:check` for dry-run; use browser visual verification for UI layout changes.
- Backend changed: run focused `cd api && pytest ...`; run `cd api && ruff check` and format changed Python files with Ruff.
- CLI changed under `cli/src/`: run `cd cli && python -m pytest tests/ -v` or focused command tests.
- SDK changed under `lab-sdk/`: reinstall the local SDK into the runtime env used by the API or tests, then restart the API if backend behavior imports the SDK.
- Task/provider behavior changed: select both backend/service/provider unit tests and at least one task/job lifecycle verification path from [task-execution-compute](sub-skills/task-execution-compute/SKILL.md).

## Version Signals From Distillation

- App package version from `package.json`: `0.40.1`.
- API dependency package version from `api/pyproject.toml`: `transformerlab-api` `0.27.0`.
- CLI package version: `transformerlab-cli` `0.0.68`; entry point is `lab`.
- SDK package version: `transformerlab` `0.1.46`; import root is `lab`.
- Supported frontend runtime in repo guidance: Node v22. Avoid Node v23+ unless maintainers update support.

## When To Stop And Ask

Ask the user before installing or repairing broad API/GPU environments, changing cloud credentials, starting long-running services, running Playwright/docker stacks, launching real remote providers, deleting data, or applying DB migrations against user data. Use the bundled references to identify the smallest safe check first.
