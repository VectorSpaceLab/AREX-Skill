# Deployment Workflows

## Docker Compose Self-Hosting

Use Docker Compose for normal self-hosting. RAGFlow expects at least 4 CPU cores, 16 GB RAM, 50 GB disk, Docker 24+, and Docker Compose v2.26.1+. Python 3.13 is only required for source launches. gVisor is only needed if the sandbox/code-executor feature is enabled.

Typical CPU launch from the Docker configuration directory:

```bash
cd docker
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml logs -f ragflow-cpu
```

Typical GPU launch:

```bash
cd docker
# Set DEVICE=gpu in .env, keeping COMPOSE_PROFILES aligned with DOC_ENGINE and DEVICE.
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml logs -f ragflow-gpu
```

The Compose file includes the base service definitions and starts the `ragflow-cpu` or `ragflow-gpu` service according to `DEVICE`. Browser access normally uses `SVR_WEB_HTTP_PORT` mapped to container port `80`; the backend API uses `SVR_HTTP_PORT` mapped to `9380`.

After changing `.env`, `service_conf.yaml.template`, or Compose settings, restart the containers:

```bash
cd docker
docker compose -f docker-compose.yml up -d
```

Use `down` only when the user accepts stopping containers. Use `down -v` only when the user accepts deleting Docker volumes and losing existing stored data.

## Docker Document-Engine Switching

RAGFlow stores text and vectors in the selected document engine. Docker supports these `DOC_ENGINE` values:

| Engine | Compose profile | Main service config section | Typical use |
| --- | --- | --- | --- |
| `elasticsearch` | `elasticsearch` | `es` | Default Docker path and broad compatibility. |
| `infinity` | `infinity` | `infinity` | Infinity-backed retrieval; not officially supported on Linux arm64 in the documented switch flow. |
| `opensearch` | `opensearch` | `os` | OpenSearch-backed retrieval with OpenSearch credentials. |
| `oceanbase` | `oceanbase` | `oceanbase` | OceanBase-backed document database; requires host limit preparation. |
| `seekdb` | `seekdb` | `seekdb` | SeekDB/OceanBase-lite deployment path. |

Safe switch checklist:

1. Confirm the user understands whether existing engine data must be preserved or can be discarded.
2. Stop containers. If the engine storage must be reset, use the volume-deleting stop only after explicit confirmation.
3. Set `DOC_ENGINE` in `.env`.
4. Ensure `COMPOSE_PROFILES` expands to include the selected `DOC_ENGINE` and the active `DEVICE`.
5. Ensure `service_conf.yaml.template` has the matching engine section and host/credential values.
6. Start the stack and check RAGFlow plus the selected engine logs.

Example switch to Infinity when data loss is acceptable:

```bash
cd docker
docker compose -f docker-compose.yml down -v
# Set DOC_ENGINE=infinity in .env.
docker compose -f docker-compose.yml up -d
```

## Source Development Launch

Use source launch when the user is developing or debugging RAGFlow code. Source launch still relies on Dockerized base services for MySQL, MinIO, Redis, and the selected document engine.

Prerequisites:

- Python 3.13 only; the project declares support for Python `>=3.13,<3.14`.
- `uv` for dependency management.
- Docker and Docker Compose for dependent services.
- Optional `pre-commit` for contributor workflows.
- Optional jemalloc for task-executor performance; missing jemalloc can break manual `LD_PRELOAD` workflows.

Typical setup:

```bash
uv sync --python 3.13 --frozen
uv run python3 ragflow_deps/download_deps.py
docker compose -f docker/docker-compose-base.yml up -d
```

For source mode, make sure service hostnames in the service config resolve locally or replace them with loopback addresses and exposed ports. The documented base stack exposes MySQL, document engine, MinIO, and Redis ports for host-side backend processes.

Backend process model:

- The API server is one Python process type.
- Task executors are separate Python processes and process document work from Redis-backed queues.
- The backend launcher starts API and task-executor processes by default; `WS` controls how many task-executor worker instances are started.
- If starting processes manually, run at least one API server and one task executor or uploads/parsing can appear to hang even when the UI is reachable.

Common backend launch from a source checkout after activating the project's Python environment and setting the import path to the checkout root:

```bash
bash docker/launch_backend_service.sh
```

Frontend launch:

```bash
cd web
npm install
npm run dev
```

If the frontend dev server cannot reach the API, check the Vite proxy target and distinguish the frontend dev port from `SVR_HTTP_PORT`.

## Queue And Worker Notes

- In the default Python deployment mode, task executors depend on Redis connectivity.
- `WS` controls worker count for task executors launched by the backend launcher; set it to at least `1`.
- NATS configuration exists for Go/hybrid deployment paths; the Compose NATS service is attached to the `ragflow-go` profile.
- If ingestion jobs are accepted but never complete, check Redis credentials, Redis host/port from the backend process context, document-engine health, and whether task executors are actually running.

## HTTPS And nginx Overview

RAGFlow serves the browser-facing UI through nginx in the Docker image. For HTTPS:

1. Obtain a certificate and private key for the public hostname.
2. Mount the certificate and key read-only into the RAGFlow container.
3. Mount or select the HTTPS nginx configuration.
4. Replace the placeholder domain in the HTTPS nginx config with the real hostname.
5. Ensure host ports `80` and `443` are available, then restart the stack.

When changing upload size, keep `MAX_CONTENT_LENGTH` and nginx `client_max_body_size` aligned. A mismatch can make large uploads fail before they reach the backend.

## Helm/Kubernetes Overview

Use Helm when the target runtime is Kubernetes. The chart deploys RAGFlow and optional in-cluster dependencies, or connects to external MySQL, MinIO/S3-compatible storage, and Redis.

Core commands:

```bash
helm upgrade --install ragflow ./helm --namespace ragflow --create-namespace
helm lint ./helm
helm template ragflow ./helm > rendered.yaml
```

Helm document-engine choices are `infinity`, `elasticsearch`, and `opensearch` through `env.DOC_ENGINE`. Helm defaults to `infinity`, while Docker defaults to `elasticsearch`; do not assume the same default across deployment modes.

For external services in Helm:

- Set `mysql.enabled=false`, then provide `env.MYSQL_HOST`, `env.MYSQL_PORT`, `env.MYSQL_DBNAME`, `env.MYSQL_USER`, and `env.MYSQL_PASSWORD`.
- Set `minio.enabled=false`, then provide `env.MINIO_HOST`, `env.MINIO_PORT`, `env.MINIO_ROOT_USER`, and `env.MINIO_PASSWORD` or equivalent S3 settings.
- Set `redis.enabled=false`, then provide `env.REDIS_HOST`, `env.REDIS_PORT`, and `env.REDIS_PASSWORD` if Redis auth is enabled.
- Use `ingress.enabled=true` plus ingress host settings when exposing the UI through Kubernetes ingress.
