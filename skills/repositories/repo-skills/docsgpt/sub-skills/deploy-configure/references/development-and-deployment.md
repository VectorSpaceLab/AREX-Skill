# Development and Deployment

## Local prerequisites

- Python 3.12 for the backend source workflow.
- Postgres reachable through `POSTGRES_URI`; it is the canonical user-data store.
- Redis for Celery, cache, schedules, event replay, and device coordination.
- Node/npm for the Vite frontend and separately for the docs site.
- A configured LLM provider and either local or remote embeddings.

Do not recreate a healthy environment or service merely because a setup helper exists. MongoDB is not part of the default install.

## Process topology

### Web

Preferred development target:

```bash
uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload
```

Production uses the same ASGI object through an ASGI-capable Gunicorn worker. The ASGI shell mounts:

- `/mcp` for FastMCP;
- `GET /api/messages/<message_id>/events` for async reconnect reading;
- the WSGI Flask application for all other routes.

`flask --app application.app run` omits the first two mounts.

### Workers

A bare Celery worker consumes all configured queues. Use this for a single worker:

```bash
celery -A application.app.celery worker -l INFO
```

To separate heavy document parsing, run the main worker with `-Q docsgpt` and a parser worker with `-Q parsing`. Keep `DOCUMENT_PARSE_QUEUE` aligned. Worker visibility timeout must exceed legitimate long tasks; prefetch `1` limits loss after hard termination.

### Frontend

```bash
cd frontend
npm install --include=dev
npm run dev
```

Set the frontend API target according to the deployment. Validate CORS, proxy, cookie, and public URL behavior from a browser-facing origin, not only from inside a container network.

## Database lifecycle

Development defaults can create the target database and apply Alembic migrations at application start. In production:

1. back up Postgres;
2. set `AUTO_CREATE_DB=false` and `AUTO_MIGRATE=false`;
3. run migrations as a controlled job against the exact release image;
4. verify schema head and application health;
5. roll out web then workers with rollback available.

Do not run legacy backfills as generic upgrades. Inspect source/target versions, row counts, idempotency, locks, and rollback first.

## Container/Kubernetes checklist

- Pin one DocsGPT release across web and workers.
- Configure readiness on `/api/health`; use a separate liveness policy that does not restart a slow but healthy migration.
- Pass the same Postgres, Redis, encryption, auth, model, storage, and queue settings to every process that needs them.
- Use persistent storage for local files or select S3-compatible object storage.
- Disable proxy buffering for SSE and use timeouts longer than expected agent runs.
- Give workers enough memory for parsing/OCR/model loads; recycle worker children using the configured memory/task limits.
- Run one scheduler authority (RedBeat-backed) rather than duplicate schedulers.
- Mount `MODELS_CONFIG_DIR` read-only and keep API keys in secrets.
- For sandboxed code, isolate the runner network and resources; never run untrusted code in the web process.

## Validation ladder

1. TCP/service preflight for Postgres and Redis.
2. backend import and version.
3. `/api/health` and `/api/config`.
4. `/v1/models` or `/api/models` with appropriate auth.
5. one non-streaming answer using a test agent/provider.
6. one streaming answer through the real proxy.
7. one tiny ingestion task and worker completion.
8. feature-specific smoke: OIDC, S3, connector, vector store, MCP, or sandbox.

Never promote a deployment from unit/import checks alone when the selected workflow depends on live services.
