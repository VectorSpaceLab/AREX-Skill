# Runtime Topology

Yuxi is operated through Docker Compose. Treat Compose files as the canonical
runtime topology for development and production; local bare-metal Python/Node
runs are not the default operating path.

## Development stack

Default command after configuration is ready:

```bash
docker compose up --build -d
```

Convenience Makefile entries:

| Command | Effect | Safety |
| --- | --- | --- |
| `make up` | Requires `.env`; runs `docker compose up -d`. | Starts or updates containers. Ask before running. |
| `make up-lite` | Requires `.env`; starts the lightweight service set with `LITE_MODE=true` and `VITE_USE_RUNS_API=false`. | Starts containers; intended to save resources. |
| `make down` | Runs `docker compose down`. | Stops containers. Ask before running. |
| `make logs` | Prints bounded API logs plus branch/commit/system info. | Read-only but may expose local context. |
| `make reset` | Stops the stack, deletes Docker volumes, starts again, then seeds users. | Destructive; never run without explicit approval. |
| `make seed` | Executes the database seeding helper inside the API container. | Mutates database and prints demo credentials; disposable dev only. |

Development services:

| Service | Container | Host exposure | Purpose |
| --- | --- | --- | --- |
| `web` | `web-dev` | `localhost:5173` | Vue/Vite web UI with hot reload. |
| `api` | `api-dev` | `localhost:5050` | FastAPI server mounted at `/api`; hot reloads backend code. |
| `worker` | `worker-dev` | none | ARQ worker for AgentRun execution and recovery scans. |
| `sandbox-provisioner` | `sandbox-provisioner` | `127.0.0.1:8002` | Creates and proxies per-thread sandboxes for tools. |
| `postgres` | `postgres` | `127.0.0.1:5432` | Business data, queues, users, LangGraph checkpoint state. |
| `redis` | `redis` | `127.0.0.1:6379` | ARQ, run events, cancellation, short-lived config/model caches. |
| `minio` | `minio` | `127.0.0.1:9000`, `127.0.0.1:9001` | Object storage for attachments, files, and public assets. |
| `milvus` | `milvus` | `127.0.0.1:19530`, `127.0.0.1:9091` | Vector search backend for knowledge bases. |
| `etcd` | `milvus-etcd-dev` | none | Milvus metadata coordination. |
| `graph` | `graph` | `127.0.0.1:7474`, `127.0.0.1:7687` | Neo4j knowledge graph service. |
| `mineru-api` | `mineru-api` | `127.0.0.1:30001` | Optional GPU OCR/PDF parsing service under the `all` profile. |
| `paddlex` | `paddlex-ocr` | `127.0.0.1:8080` | Optional PaddleX/PP-Structure OCR service under the `all` profile. |

Development API and worker share the same startup environment: database URLs,
Redis, Milvus, Neo4j, MinIO, OCR service URLs, sandbox provider URL/token,
timeouts, CORS, model/search/OCR credentials, and `LITE_MODE`.

## Lite mode

Lite mode is for fast startup when knowledge-base and graph-heavy capabilities
are not needed:

```bash
make up-lite
```

Expected behavior:

- `LITE_MODE=true` is passed to the backend.
- Heavy knowledge/graph routes are not registered, and the UI hides related
  entries.
- The official Makefile command requests the core web/API/storage services and
  relies on Compose dependency resolution for required API dependencies.
- If a task needs async AgentRun execution under Lite mode, verify whether a
  worker container is running before debugging agent behavior.

Do not diagnose missing knowledge-base, evaluation, external-KB, or graph routes
as a bug until Lite mode is ruled out.

## Production stack

Production uses `docker-compose.prod.yml` and `.env.prod`:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Optional OCR/GPU services are added with:

```bash
docker compose -f docker-compose.prod.yml --profile all up -d --build
```

Production topology differences:

- `web` runs Nginx as `web-prod` and publishes port `80`.
- Browser traffic reaches the API through same-origin `/api/...`; direct API
  container ports are not published.
- PostgreSQL, Redis, MinIO, Milvus, Neo4j, and OCR service ports are not exposed
  to the host by default. Prefer `docker compose exec` for local maintenance.
- Public avatar/agent images are served through read-only same-origin
  `/minio/public/...`; do not expose MinIO object API or console to the public
  internet.
- `api-prod` and `worker-prod` require strong persisted secrets and production
  environment variables before Compose will create them.

Production health checks:

| Endpoint | Meaning |
| --- | --- |
| `http://localhost/api/system/health` | Nginx can reach the API and the public health route returns version/status. |
| `http://localhost/` | Nginx serves the built web app. |
| container health checks | Compose can see API, sandbox-provisioner, Postgres, Redis, MinIO, Milvus, Neo4j, and optional OCR health where configured. |

Add TLS at the external reverse proxy/load balancer for real production use,
especially when API keys, JWTs, or provider callbacks cross the network.

## Optional OCR profile

`mineru-api` and `paddlex` are in the `all` profile. They are not part of the
core CPU/any deployment requirement.

| Service | Typical need | Default backend connection |
| --- | --- | --- |
| `mineru-api` | GPU PDF/layout parsing with local MinerU models. | API/worker use `MINERU_API_URI`, defaulting to `http://mineru-api:30001`. |
| `paddlex` | GPU PP-Structure/PaddleX OCR. | API/worker use `PADDLEX_URI`, defaulting to `http://paddlex:8080`. |

Cloud OCR alternatives do not require these containers but do require their own
provider tokens. See `configuration-and-secrets.md`.

## Read-only checks

For an already running stack, prefer:

```bash
scripts/check-runtime-health.sh --project-dir . --dev
scripts/check-runtime-health.sh --project-dir . --prod
```

The script checks Compose service state and public health endpoints. Add `--logs`
only when the user accepts that container logs may include sensitive local data.

## Source helpers classified as reference-only

The original init, image-pull, and seed helpers are not bundled as runnable
skill scripts because they mutate local state, pull network images, or write
persistent database rows. Distilled operating facts:

- The init helper creates `.env`, prompts for required model/search credentials,
  generates JWT/sandbox/instance secrets when blank, and pulls core images.
- The image-pull helper uses a registry mirror, retags images to their original
  names, and removes mirror tags. Use only when image pulls fail and the user
  accepts network/image side effects.
- The seed helper initializes demo departments/users only when the database has
  no users. It is not a production onboarding path and should never be run on an
  initialized or real deployment without explicit approval.
