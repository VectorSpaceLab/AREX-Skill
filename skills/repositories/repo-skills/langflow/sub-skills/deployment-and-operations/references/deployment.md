# Deployment Patterns

This reference covers Docker, Docker Compose, PostgreSQL, volumes, custom images, multi-worker operations, reverse proxies, and observability/storage settings for Langflow.

## Docker Quickstart

Start a disposable local container:

```bash
docker run --rm -p 7860:7860 langflowai/langflow:latest
```

For a configured container, pass environment variables explicitly or through an `.env` file:

```bash
docker run --rm \
  -p 7860:7860 \
  --env-file .env \
  -v langflow-data:/app/langflow \
  langflowai/langflow:latest
```

Inside a container, bind Langflow to `0.0.0.0` so Docker port publishing can reach it:

```text
LANGFLOW_HOST=0.0.0.0
LANGFLOW_PORT=7860
LANGFLOW_CONFIG_DIR=/app/langflow
```

## Compose with PostgreSQL and Volumes

A durable Compose deployment should include:

- A `langflow` service using `langflowai/langflow:<version>`.
- A `postgres` service with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.
- `LANGFLOW_DATABASE_URL=postgresql://user:password@postgres:5432/dbname` in the Langflow service.
- `LANGFLOW_CONFIG_DIR=/app/langflow` in the Langflow service.
- A volume mounted at `/app/langflow` for Langflow runtime data.
- A volume mounted at PostgreSQL's data directory for database persistence.

Minimal pattern:

```yaml
services:
  langflow:
    image: langflowai/langflow:latest
    ports:
      - "7860:7860"
    depends_on:
      - postgres
    environment:
      - LANGFLOW_HOST=0.0.0.0
      - LANGFLOW_DATABASE_URL=postgresql://langflow:change-me@postgres:5432/langflow
      - LANGFLOW_CONFIG_DIR=/app/langflow
      - LANGFLOW_AUTO_LOGIN=False
      - LANGFLOW_SUPERUSER=admin
      - LANGFLOW_SUPERUSER_PASSWORD=change-me
      - LANGFLOW_SECRET_KEY=replace-with-long-random-secret
    volumes:
      - langflow-data:/app/langflow

  postgres:
    image: postgres:16-trixie
    environment:
      POSTGRES_USER: langflow
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: langflow
    volumes:
      - langflow-postgres:/var/lib/postgresql/data

volumes:
  langflow-data:
  langflow-postgres:
```

Use a pinned version tag instead of `latest` when reproducibility matters. The `postgres:16-trixie` base avoids surprise OS-base changes on existing PostgreSQL volumes.

## Compose Environment Files

For local Compose files, move secrets to `.env` and reference them:

```text
POSTGRES_USER=langflow
POSTGRES_PASSWORD=replace-me
POSTGRES_DB=langflow
LANGFLOW_DATABASE_URL=postgresql://langflow:replace-me@postgres:5432/langflow
LANGFLOW_CONFIG_DIR=/app/langflow
LANGFLOW_SECRET_KEY=replace-with-long-random-secret
```

Compose service pattern:

```yaml
services:
  langflow:
    env_file:
      - .env
    environment:
      - LANGFLOW_DATABASE_URL=${LANGFLOW_DATABASE_URL}
      - LANGFLOW_CONFIG_DIR=${LANGFLOW_CONFIG_DIR}
  postgres:
    env_file:
      - .env
```

Before `docker compose up`, validate the file:

```bash
python scripts/check_env_vars.py --env-file .env --context docker-compose
```

## Upgrade Docker Without Losing Flows

1. Use persistent volumes for both Langflow data and the database.
2. Back up the volumes or database before changing image tags.
3. Pin the current image tag in Compose, then update the tag deliberately.
4. Pull the new image:

```bash
docker compose pull
```

5. Restart with the same volumes:

```bash
docker compose up -d
```

6. Check logs and health:

```bash
docker compose logs -f langflow
curl -fsS http://localhost:7860/health
```

If a migration is required, preview it first and apply only after backup.

## Package Flow Files into an Image

Use this when a deployment should start with bundled flow JSON files.

Project layout:

```text
custom-langflow/
  Dockerfile
  flows/
    my-flow.json
```

Dockerfile:

```dockerfile
FROM langflowai/langflow:latest
RUN mkdir -p /app/flows
COPY flows/*.json /app/flows/
ENV LANGFLOW_LOAD_FLOWS_PATH=/app/flows
ENV LANGFLOW_AUTO_LOGIN=True
```

Build and run:

```bash
docker build -t example/langflow-flows:1.0.0 .
docker run --rm -p 7860:7860 --env-file .env example/langflow-flows:1.0.0
```

Notes:

- `LANGFLOW_LOAD_FLOWS_PATH` loads flow JSON files at startup.
- `LANGFLOW_AUTO_LOGIN=True` is commonly used for automatic flow loading in controlled images; do not expose such an image publicly without access controls.
- `LANGFLOW_LOAD_FLOWS_OVERWRITE_ON_NAME_MATCH=True` makes packaged flows authoritative when names match existing flows; keep it `False` when preserving UI edits is more important.
- Validate the flow JSON before building the image with the flow-authoring helper if that sub-skill is available.

## Custom Langflow Image with Components or Code

Use a custom image when the deployment needs additional Python packages, custom components, or modified Langflow files.

Safer pattern for custom components:

```dockerfile
FROM langflowai/langflow:latest
WORKDIR /app
COPY components/ /app/components/
ENV LANGFLOW_COMPONENTS_PATH=/app/components
ENV LANGFLOW_HOST=0.0.0.0
EXPOSE 7860
CMD ["python", "-m", "langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
```

If replacing installed package files, keep the change narrow, record the exact Langflow base tag, clear only relevant Python caches, and test startup in a disposable container before publishing. Prefer extension/custom-component mechanisms over overwriting site-packages when possible.

## Multi-worker and Queues

A single worker can use the default in-process async job queue. Multiple workers need shared coordination:

```text
LANGFLOW_WORKERS=4
LANGFLOW_JOB_QUEUE_TYPE=redis
LANGFLOW_REDIS_QUEUE_URL=redis://redis:6379/1
```

Rules:

- Set `LANGFLOW_JOB_QUEUE_TYPE=redis` on every worker; mixed worker modes are unsupported.
- Use `LANGFLOW_REDIS_QUEUE_URL` when Redis requires authentication or TLS, for example `rediss://user:password@host:6380/1`.
- Keep the Redis queue DB separate from the Redis cache DB to avoid key collisions.
- If clients use polling, tune watchdog values only after observing abandoned or incorrectly canceled builds.

## Reverse Proxy and Public Exposure

For public deployments, run Langflow behind a reverse proxy such as Caddy, Nginx, Traefik, or a cloud ingress. The proxy should handle:

- HTTPS/TLS certificates and redirects.
- Hostname routing to Langflow's internal port `7860`.
- Request size limits that match `LANGFLOW_MAX_FILE_SIZE_UPLOAD`.
- WebSocket/SSE-friendly buffering settings for streaming builds and logs.
- Authentication or network restrictions when Langflow itself is in auto-login mode.

Use direct `LANGFLOW_SSL_CERT_FILE` and `LANGFLOW_SSL_KEY_FILE` only when the process itself should terminate TLS. Reverse-proxy TLS is usually easier to operate.

## Observability and Logs

Useful logging settings:

```text
LANGFLOW_LOG_LEVEL=info
LANGFLOW_LOG_ENV=container
LANGFLOW_LOG_FILE=/var/log/langflow/langflow.log
LANGFLOW_LOG_DIR=/var/log/langflow
```

Operational guidance:

- Use `LANGFLOW_LOG_LEVEL=debug` only during short investigations; debug logs can be noisy and may include sensitive context from failing flows.
- `LANGFLOW_LOG_ENV=container` emits container-friendly structured logs to stdout.
- If a log collector scrapes files, ensure `LANGFLOW_LOG_FILE` is inside the directory the collector watches and that the directory is mounted or writable.
- For Prometheus metrics, enable the Prometheus settings and expose only the intended metrics port/path through the proxy.
- For Grafana/Loki/Promtail, align log format, file path, volume mounts, and scraper config.

The heavier production-style Compose pattern may include Traefik, a split backend/frontend, PostgreSQL, RabbitMQ, Redis result backend, Celery worker, Flower, Prometheus, and Grafana. Treat those services as an operations stack: validate every required environment variable, secret, network, label, volume, and health check before rollout.

## File Storage and Sandbox Boundaries

Langflow stores runtime files relative to configured storage and config settings. For operations:

- Persist `LANGFLOW_CONFIG_DIR` for logs, file storage, monitor data, generated secrets, and related runtime state.
- Set file upload limits with `LANGFLOW_MAX_FILE_SIZE_UPLOAD` and ensure the reverse proxy allows at least the same size.
- Keep file-system tool access constrained with `LANGFLOW_FS_TOOL_BASE_DIR`; do not mount broad host directories into that sandbox.
- Use managed/object storage settings only after confirming credentials, bucket permissions, network access, and backup/retention policies.

## Pre-deployment Validation Checklist

- `check_env_vars.py` passes or all warnings are intentionally accepted.
- Database URL uses the correct hostname for the runtime context.
- Langflow config directory and database data directory are persistent and backed up.
- `LANGFLOW_SECRET_KEY` is stable, strong, and not committed.
- `LANGFLOW_AUTO_LOGIN` is suitable for the exposure level.
- Superuser credentials are set when authentication is enabled.
- API/provider credentials are injected through secrets, not baked into images or flow JSON.
- Health endpoint responds after startup.
- Logs are visible through `docker logs`, `docker compose logs`, system logs, or the configured collector.
- Migration preview has been reviewed before applying destructive fixes.
