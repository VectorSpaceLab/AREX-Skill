---
name: docs-gpt
description: "Use DocsGPT for repository-specific backend/API,
  agent/tool/workflow, source/retrieval, deployment/auth/operations,
  frontend/extensions, and E2E work."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DocsGPT repo operating skill

Use this skill when working inside the DocsGPT repository: backend/API changes, agents/tools/workflows, source ingestion and retrieval, deployment/auth/ops, frontend/extensions, or verification planning. It is an operating guide for the current repo layout; it is not a general RAG or Flask guide.

## First moves

1. Confirm you are at the DocsGPT repo root. Expected anchors: `application/app.py`, `application/asgi.py`, `application/core/settings.py`, `frontend/package.json`, `docs/content/quickstart.mdx`, `tests/`, and `CONTRIBUTING.md`.
2. For any non-trivial code change, read `CONTRIBUTING.md` and follow repo-local instructions.
3. Reuse existing services and environments before creating anything:
   - Check for `.venv/` or `venv/`.
   - Check Postgres via `POSTGRES_URI`; Postgres is the canonical user-data store.
   - Check Redis for Celery, caches, SSE journals, OIDC handoff/session state, and remote-device queues.
4. Do not default to `setup.sh` or `setup.ps1` during normal feature work. Prefer the documented development-environment path and explicit commands.
5. Keep secrets out of logs, tests, generated docs, and skill output. Redact `API_KEY`, provider keys, `INTERNAL_KEY`, OIDC secrets, SCIM tokens, S3 credentials, and database passwords.

## Repository map

- `application/` — Flask backend, ASGI wrapper, API blueprints, agents, tools, retrieval, parser/ingestion, vector stores, settings, storage, Celery, auth, admin, OIDC/SCIM, sandbox/artifacts, devices, schedules.
- `tests/` — backend/unit/integration tests and Playwright e2e harness under `tests/e2e/`.
- `frontend/` — Vite + React + TypeScript UI.
- `docs/` — Next/Nextra documentation site and runbooks.
- `scripts/` — local/e2e helper scripts, DB init/migration/backfill tools, admin bootstrap, mock LLM/IdP utilities.
- `deployment/` — Docker Compose and Kubernetes/deployment manifests.
- `extensions/` — Chatwoot bridge and React widget.

For a fuller map and ownership cues, load `references/repo-map.md`.

For checkout identity and machine-readable skill entry points, read `references/repo-provenance.md` and `references/repo-routing-metadata.json`.

## Development commands that matter

Backend setup and run:

```bash
source .venv/bin/activate  # if present
uv pip install -r application/requirements.txt  # or pip install -r application/requirements.txt
uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload
```

Use `flask --app application/app.py run --host=0.0.0.0 --port=7091` only for a quick WSGI-only loop. It omits ASGI-mounted routes: `/mcp` and native async reconnect reader `GET /api/messages/<id>/events`. Chat `POST /stream` still exists as a Flask route, but disconnect auto-resume cannot be validated under `flask run`.

Worker:

```bash
celery -A application.app.celery worker -l INFO
# macOS local loop:
python -m celery -A application.app.celery worker -l INFO --pool=solo
```

Validation:

```bash
ruff check .
python -m pytest
cd frontend && npm run lint && npm run build
cd docs && npm run build
```

E2E harness:

```bash
cd tests/e2e
npm run e2e:install
npm run e2e:up
npm run e2e
npm run e2e:down
```

Load `references/dev-environment.md` for detailed service, env, and validation notes.

## Route to the focused subskill

| Task | Load |
| --- | --- |
| Native chat endpoints, `/stream`, `/api/answer`, `/api/search`, OpenAI-compatible `/v1/chat/completions`, conversations, attachments, SSE reconnects | `chat-api/SKILL.md` |
| Agent CRUD, agent types, public links/import/export, API keys, built-in/custom tools, MCP, workflows, schedules, artifacts/code execution, webhooks | `agents-tools-workflows/SKILL.md` |
| Uploads, remote/wiki sources, parser/Celery ingestion, source config, chunking, vector stores, retrievers, hybrid search, GraphRAG | `sources-retrieval/SKILL.md` |
| ASGI vs WSGI startup, settings, Postgres/Redis/Celery, Docker/Compose, OIDC, SCIM, RBAC, teams, admin, observability, model/provider config | `deployment-auth-ops/SKILL.md` |
| React/Vite frontend, icons/components, docs site, Chatwoot, React widget, Playwright tiers, screenshots/videos for PRs | `frontend-extensions-e2e/SKILL.md` |

## High-signal facts to preserve

- Backend version is exposed through `application/version.py`; current evidence showed `0.18.0`.
- ASGI production and full local dev entrypoint is `application.asgi:asgi_app`; production uses gunicorn with Uvicorn workers against the same target.
- `/api/answer` is non-streaming JSON; `/stream` is SSE streaming; `/api/search` returns fast retrieval results; `/v1/chat/completions` is OpenAI-compatible and uses `Authorization: Bearer <agent_api_key>`.
- Conversations are always persisted server-side; `visibility="listed"` controls sidebar listing. The old `save_conversation` field is deprecated/ignored.
- Postgres stores users, agents, prompts, sources, attachments, workflows, logs, conversations, and token usage. MongoDB is only for `VECTOR_STORE=mongodb` or one-shot legacy backfill.
- `VECTOR_STORE=pgvector` is required for GraphRAG; `GRAPHRAG_ENABLED=true` gates the feature.
- Redis backs Celery, event streams, OIDC handoffs/refresh state, session revocations, and remote-device queues.
- New frontend icons should prefer `lucide-react`; use SVG React imports for brand/domain illustrations; avoid new `<img src={Asset}>` icon patterns.

## Included helper scripts

These scripts are safe to run from the repo root and do not expose secrets.

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /v1
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --json
python skills/disco/docs-gpt/scripts/check_local_config.py --repo .
python skills/disco/docs-gpt/scripts/check_local_config.py --repo . --check-services --json
```

Use `inspect_api_routes.py` when route facts are stale or you need an API inventory without starting the app. Use `check_local_config.py` before diagnosing runtime startup, worker/API communication, OIDC/SCIM, vector-store, or model-provider problems.

## Verification posture

Prefer red/green TDD:

- For backend behavior, add/update focused tests under `tests/` and run the smallest relevant pytest path first, then broader `python -m pytest` if scope warrants.
- For parser/retrieval changes, include ingest/search examples or tests that prove source metadata, chunking, and vector-store behavior.
- For ASGI/SSE/MCP changes, validate under `uvicorn application.asgi:asgi_app`, not only `flask run`.
- For frontend changes, run `cd frontend && npm run lint` and `npm run build`; add/update Vitest or Playwright when behavior changes.
- For docs-only changes, run `cd docs && npm run build`; run Vale if prose linting is available.
- For PR readiness, summarize user-visible behavior and config/dependency/deployment implications, and ask the user to attach a screenshot or video for UI changes.

Load `references/verification-matrix.md` before choosing final tests.

## Do not do these by default

- Do not stop/recreate Postgres, Redis, Docker, or a Python environment unless the task is explicitly setup/troubleshooting and evidence shows reuse is unsafe.
- Do not run setup scripts for ordinary feature work.
- Do not run destructive DB backfills/migrations against user data without explicit approval and a backup/rollback plan.
- Do not claim `/mcp` or `/api/messages/<id>/events` works when you tested only with `flask run`.
- Do not treat optional CUDA/local model/STT/sandbox/Chatwoot/OIDC/SCIM/Playwright coverage as verified unless that backend/service/browser stack was actually run.
