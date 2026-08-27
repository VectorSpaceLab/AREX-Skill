# DocsGPT repository map

Use this when deciding where to inspect or modify code.

## Backend (`application/`)

- `app.py` — Flask app factory/instance, blueprint registration, Celery object wiring, DB bootstrap hooks. Full app import can touch configuration and service setup, so prefer source inspection or focused module imports before starting the app.
- `asgi.py` — production-compatible ASGI shell that mounts the Flask WSGI app plus ASGI-native routes such as `/mcp` and `GET /api/messages/<id>/events`.
- `api/answer/` — native answer/search/stream routes:
  - `/api/answer` non-streaming answer.
  - `/stream` SSE chat stream.
  - `/api/search` fast retrieval endpoint.
- `api/v1/routes.py` — OpenAI-compatible `/v1/chat/completions` and `/v1/models`.
- `api/user/` — user-facing REST namespaces for agents, tools, workflows, sources, prompts, conversations, models, teams, sharing, analytics, attachments, artifacts, and schedules.
- `api/admin/routes.py` — admin dashboard endpoints under `/api/admin`.
- `api/oidc/`, `api/scim/` — OIDC sign-in/session lifecycle and SCIM provisioning.
- `api/events/` and async reconnect code — user notification SSE and per-message replay/reconnect.
- `agents/` — agent implementations and workflow engine. Key docs: `docs/content/Agents/basics.mdx`, `nodes.mdx`, `api.mdx`, `openai-compatible.mdx`.
- `agents/tools/` — built-in tools, base `Tool`, tool manager/discovery, API tool, MCP/remote-device integration points.
- `parser/` — document reader and parsers used by upload/ingestion workflows.
- `retriever/`, `vectorstore/`, `graphrag/` — retrieval strategy, vector store adapters, GraphRAG graph extraction/retrieval.
- `core/settings.py` — Pydantic settings and environment variable defaults; check this before adding config.
- `core/models/` — model/provider registry and YAML model catalogs.
- `seed/` — YAML-driven premade agent seeding.
- `storage/`, `database/`, `models/` — persistence abstractions and SQLAlchemy data models.
- `celery_init.py`, `celeryconfig.py` — worker app and queue settings.

## Tests (`tests/`)

- `tests/api/` — endpoint behavior, admin/RBAC/teams/devices/SSE.
- `tests/integration/` — broader app flows including chat/v1 API/SCIM.
- `tests/agents/` — agent runtime, default tools, workflow engine.
- `tests/parser/`, `tests/retriever/`, `tests/vectorstore/`, `tests/graphrag/` — ingestion/retrieval behavior.
- `tests/e2e/` — Playwright UI/API stack. Use `tests/e2e/README.md` and `tests/e2e/package.json` for commands.
- `tests/QA_TESTS.md` — manual/QA coverage notes.

## Frontend (`frontend/`)

- Vite + React + TypeScript app.
- Main source under `frontend/src/` with components, conversation logic, hooks, locale files, settings, upload, and Redux store wiring.
- Commands: `npm run dev`, `npm run lint`, `npm run build`, `npm run test`.
- New icons: prefer `lucide-react`; use SVG React imports for brand/domain assets that must theme via `currentColor`; avoid new `<img src={Asset}>` icon uses.

## Docs site (`docs/`)

- Next/Nextra documentation.
- Commands: `npm install`, `npm run build`, `npm run dev`, `npm run start`.
- High-value references:
  - `docs/content/Deploying/Development-Environment.mdx`
  - `docs/content/Deploying/DocsGPT-Settings.mdx`
  - `docs/content/Deploying/Postgres-Migration.mdx`
  - `docs/content/Deploying/OIDC-SSO.mdx`
  - `docs/content/Deploying/Access-Control.mdx`
  - `docs/runbooks/sse-notifications.md`

## Scripts (`scripts/`)

- `scripts/db/init_postgres.py` — explicit schema/migration step for production or hardened deploys.
- `scripts/db/backfill.py` — one-shot offline Mongo-to-Postgres migration; optional `pymongo` extra required.
- `scripts/grant_admin.py` — bootstrap/list/revoke global admin grants.
- `scripts/mock_llm.py` — OpenAI-compatible mock model server for benchmarking and API tests.
- `scripts/e2e/` — Docker/e2e stack helpers and mock OIDC IdP. Some scripts start long-running services; do not run `--help` blindly.
- `scripts/qa/durability_e2e.py` — durability QA helper.
- `scripts/build_daytona_snapshot.py` — sandbox snapshot helper for Daytona.

## Deployment and extensions

- `deployment/docker-compose*.yaml` — full, hub, local, and dev variants. The dev compose is useful for e2e stack setup; do not substitute it for targeted local debugging unless needed.
- `extensions/chatwoot/` — webhook bridge service. Has its own `.env_sample` and `app.py`.
- `extensions/react-widget/` — embeddable React widget package published as `docsgpt`; consult its README before changing integration guidance.
