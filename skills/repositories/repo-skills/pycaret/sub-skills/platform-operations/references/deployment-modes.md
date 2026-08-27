# Deployment modes

PyCaret 4.0 ships the engine plus a FastAPI Control Plane and a React UI. The
verified platform version for this skill is `pycaret` 4.0.0a8 and
`pycaret-server` 0.1.0a0 on the source commit recorded by the root skill.

## Mode 1: single-process development install

Use this when the operator wants the smallest local API process and can run the
UI separately.

```bash
pip install pycaret-server
pycaret-server init --data-dir ./data
pycaret-server migrate
pycaret-server serve --host 0.0.0.0 --port 8020
pycaret-server doctor
```

Expected defaults:

| Surface | Default |
|---|---|
| API | `http://localhost:8020` |
| Health | `GET /healthz` |
| API docs | `GET /docs` |
| Database | SQLite under the chosen data directory |
| Artifacts | local filesystem under the chosen data directory |
| Run backend | `inprocess`; jobs execute in the API process |
| Scheduler | APScheduler inside the API process |
| UI | separate web dev server or web container, normally port `3020` |

`pycaret-server init` writes a `.env` file in the data directory with a random
JWT secret, a Fernet `PYCARET_SECRETS_KEY`, a SQLite URL, local artifact path,
`PYCARET_RUNS_BACKEND=inprocess`, and `PYCARET_STORAGE_BACKEND=local`. Re-run
with `--force` only when intentionally replacing that generated config.

## Mode 2: compact Docker Compose

The compact Compose shape is the one-command self-host path for a laptop or
small single-host install.

```bash
docker compose up --build
# open http://localhost:3020
```

Services and ports:

| Service | Host port | Container port | Role |
|---|---:|---:|---|
| `api` | `${PYCARET_API_PORT:-8020}` | `8020` | FastAPI, SQLite DB, local artifacts, in-process scheduler and run executor |
| `web` | `${PYCARET_WEB_PORT:-3020}` | `8080` | nginx-served React bundle; proxies `/api` and run WebSocket paths to `api:8020` |
| named volume | n/a | mounted at `/data` in `api` | SQLite DB, artifacts, and persisted Fernet key |

Operational commands:

```bash
docker compose logs -f api
docker compose logs -f web
docker compose restart api
docker compose down
# destructive: removes containers and the named data volume
docker compose down --volumes
```

The API container entrypoint persists a generated Fernet key at a key file under
its data volume when `PYCARET_SECRETS_KEY` is not supplied. This is what keeps
encrypted secrets readable across container restarts. Use
`scripts/check_container_secret_key.sh` to validate the expected key file in a
mounted or copied data directory without printing the key.

## Mode 3: production-shaped Docker Compose

The production-shaped Compose file separates platform dependencies on one host:

| Service | Role |
|---|---|
| `postgres` | Postgres metadata DB |
| `redis` | Redis queue and pub/sub bus |
| `minio` | S3-compatible object storage |
| `minio-bootstrap` | one-shot bucket creation |
| `api` | FastAPI Control Plane |
| `worker` | `pycaret-server worker --queues default` using the same API image |
| `web` | nginx-served React UI |

Start it from a source distribution that contains the Docker files:

```bash
docker compose -f infra/docker/docker-compose.prod.yml up --build
```

Default exposed ports:

| Surface | Port |
|---|---:|
| UI | `3020` |
| API | `8020` |
| MinIO S3 API | `9000` |
| MinIO admin UI | `9001` |

Set real secrets before using this beyond a local smoke test:

```bash
export PYCARET_PG_PASSWORD='replace-me'
export PYCARET_JWT_SECRET='replace-me-with-48-plus-random-bytes'
export PYCARET_SECRETS_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
export PYCARET_S3_ACCESS_KEY='replace-me'
export PYCARET_S3_SECRET_KEY='replace-me'
docker compose -f infra/docker/docker-compose.prod.yml up --build
```

Important behavior:

- The API and worker both need the same DB, Redis, storage, and Fernet settings.
- The included worker listens only on `default`; add separate worker processes
  for `cpu-heavy`, `gpu`, or `inference` queues.
- Volumes named for Postgres, Redis, and MinIO persist across `docker compose
  down`. `docker compose down --volumes` wipes them.

## Mode 4: Kubernetes/Helm status

Treat Helm as an operator target, not as a proven production-complete path in
this verified snapshot. Evidence shows chart metadata and values for API,
worker, web, Postgres, Redis, MinIO, ingress, and observability knobs, but the
in-repo Helm README and full-platform test plan identify the chart as a stub or
not smoke-tested against a real cluster.

Use Helm guidance only after confirming that the actual distribution contains
renderable templates and a successful cluster smoke test. Minimum checks before
calling it deployable:

```bash
helm lint ./infra/helm/pycaret
helm template pycaret ./infra/helm/pycaret --namespace pycaret > rendered/pycaret-rendered.yaml
kubectl -n pycaret get pods
kubectl -n pycaret exec deploy/<api-deployment-name> -- pycaret-server doctor
```

Target Helm concepts reflected by the values file:

- API and worker share the API image.
- `worker.queues` is a comma-separated queue list, defaulting to
  `default,cpu-heavy` in values.
- Secrets should come from Kubernetes Secret refs for JWT, Fernet encryption,
  Postgres password, and object-store credentials.
- Bring-your-own Postgres, Redis, and S3 are intended via external URLs and
  disabled bundled services.
- GPU workers are intended as a separate worker pool with `queues=gpu` and a
  GPU resource limit, but verify templates and hardware scheduling first.

## Mode 5: Terraform/cloud status

Treat Terraform directories as V2 stubs in this snapshot. They document intended
cloud shapes, not runnable modules:

| Cloud | Intended compute | Intended DB | Intended object store | Intended cache | Intended secret store |
|---|---|---|---|---|---|
| AWS | ECS/Fargate or EKS | RDS Postgres | S3 | ElastiCache | Secrets Manager |
| GCP | Cloud Run or GKE | Cloud SQL | GCS | Memorystore | Secret Manager |
| Azure | Container Apps or AKS | Azure Database for PostgreSQL | Blob Storage | Azure Cache | Key Vault |

Before using Terraform in a real deployment, require actual `main.tf`,
`variables.tf`, `outputs.tf`, IAM/networking resources, image references,
secret wiring, migration execution, and a successful `terraform plan` plus
platform smoke test.
