# Deployment and Integrations

This reference covers service entry points, container profiles, the web console, MCP deployment, cloud sync, distributed workers, and the face-aware playground.

## FastAPI service

Primary backend entry points:

```bash
uvicorn m_flow.api.client:app --host 0.0.0.0 --port 8000
python -m m_flow.api.client
```

Useful HTTP probes:

- `GET /` → root service status
- `GET /health` → liveness/readiness
- `GET /health/detailed` → component diagnostics

The API app builds CORS origins from `CORS_ALLOWED_ORIGINS`, or falls back to `UI_APP_URL` and `http://localhost:3001`.
The generated OpenAPI schema advertises both bearer-token and cookie auth.

## Docker Compose stack

| Service | Profile | Ports | Purpose | Notes |
| --- | --- | --- | --- | --- |
| `mflow-api` | default | `8000`, `9230` | FastAPI backend | mounts `.env` and exposes `/health` |
| `mflow-mcp` | `mcp` | `8001:8000`, `9231:9230` | MCP server | defaults to SSE in Docker |
| `frontend` | `ui` | `3000` | Next.js console | depends on `mflow-api` |
| `neo4j` | `neo4j` | `7474`, `7687` | Graph database | APOC + GDS plugins enabled |
| `postgres` | `postgres` | `5432` | PGVector-capable Postgres | default DB for relational/vector setups |
| `chromadb` | `chromadb` | `3002` | ChromaDB service | token auth configured from `VECTOR_DB_KEY` |
| `redis` | `redis` | `6379` | Redis cache | includes `redisinsight` on `5540` |
| `fanjing-face` | `playground` | `5001` | Face-recognition companion | requires sibling repo and `FACE_API_KEY` |

Compose launch patterns:

```bash
docker compose up
docker compose --profile ui up
docker compose --profile mcp up
docker compose --profile ui --profile playground up --build -d
```

## Web UI

CLI launch:

```bash
mflow -ui
```

Programmatic launch:

```python
from m_flow.api.v1.ui import start_ui
```

`start_ui()` can start the backend API, MCP server, and frontend together. The default CLI path opens a browser and auto-downloads frontend assets when needed.

Frontend package scripts:

| Script | Purpose |
| --- | --- |
| `pnpm dev` | Next.js development server on port 3000 |
| `pnpm build` | production build |
| `pnpm start` | production server |
| `pnpm lint` | lint frontend code |
| `pnpm test` / `pnpm test:run` | Vitest |
| `pnpm test:coverage` | Vitest coverage |
| `pnpm test:e2e` / `pnpm test:e2e:ui` | Playwright |

Frontend runtime config:

- `NEXT_PUBLIC_API_URL` → backend base URL, default `http://localhost:8000`
- `NEXT_PUBLIC_WS_URL` → WebSocket base URL, derived from the API URL when unset
- `NEXT_PUBLIC_AUTO_LOGIN` → enable or disable auto-login
- `NEXT_PUBLIC_DEFAULT_USER_EMAIL` / `NEXT_PUBLIC_DEFAULT_USER_PASSWORD` → default demo credentials
- token storage key: `mflow_token`

## MCP and IDE integration

- `stdio` is the local IDE/default mode.
- `sse` is the Docker/web-client mode.
- `http` is streamable HTTP for clients that want a pure HTTP transport.

Default Docker MCP mapping:

- host port `8001` → container port `8000`
- debug port `9231` → container debug port `9230`

## Cloud sync and distributed workers

Cloud sync uses:

- `MFLOW_CLOUD_API_URL`
- `MFLOW_CLOUD_AUTH_TOKEN`

The distributed helper package uses Modal and queue-backed worker fan-out:

- `mflow_workers/app.py` defines the Modal app
- `mflow_workers/queues.py` defines the work queues
- `mflow_workers/entrypoint.py` starts graph and memory workers
- `MFLOW_DISTRIBUTED=true` switches code paths that support distributed execution

## Face-aware playground

Playground integration depends on a companion `fanjing-face-recognition` service and a shared `FACE_API_KEY`.

Recommended modes:

- Linux: M-flow + face service in Docker is supported
- macOS/Windows: keep the face service on the host so it can access the camera

The backend translates `localhost` to `host.docker.internal` when needed inside Docker.

Playground setup is reference-only because it clones an external service, downloads model files, and needs camera/credential access. Use the prerequisites and sequence above instead of running automated installers by default.
