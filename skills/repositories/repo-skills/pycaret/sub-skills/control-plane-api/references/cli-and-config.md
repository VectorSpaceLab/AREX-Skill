# CLI and configuration

The backend is published as `pycaret-server` and exposes one console script:

```bash
pycaret-server <command> [options]
```

## CLI commands

| Command | Purpose | Important options and behavior |
|---|---|---|
| `pycaret-server init` | Zero-touch local bootstrap. | `--data-dir ./data`, `--force`. Writes a `.env` under the data dir, creates a SQLite URL, artifact dir, random JWT secret, random Fernet `PYCARET_SECRETS_KEY`, `PYCARET_ENVIRONMENT=dev`, `PYCARET_RUNS_BACKEND=inprocess`, and `PYCARET_STORAGE_BACKEND=local`; then applies migrations. Idempotent unless `--force`. |
| `pycaret-server serve` | Start the FastAPI app with uvicorn. | `--host` default `127.0.0.1`; `--port` default `8020`; `--reload` uses factory mode and excludes `.venv`, `node_modules`, artifacts, `__pycache__`, DB files, journals, and logs from reload watching. |
| `pycaret-server migrate` | Run Alembic upgrade. | `--url` overrides `PYCARET_DATABASE_URL`; `--revision` default `head`; `--reset-dev` deletes the SQLite DB file first and refuses non-SQLite URLs. |
| `pycaret-server worker` | Run the Redis-backed worker loop. | `--queues default,gpu`, `--worker-id`, `--redis-url`. The worker refuses startup when Redis is unreachable and claims Jobs atomically through DB `locked_by`/`locked_at`. |
| `pycaret-server doctor` | Health probe for scripts and operators. | Checks DB with `SELECT 1`, checks Redis only when `PYCARET_RUNS_BACKEND=redis`, and verifies the artifact directory is writable. Exit code `0` if healthy. |
| `pycaret-server version` | Print the backend package version. | Verified target version: `0.1.0a0`. |

Direct local startup:

```bash
pip install pycaret-server
pycaret-server init --data-dir ./data
pycaret-server serve --host 127.0.0.1 --port 8020
```

From a uv workspace checkout:

```bash
uv run --package pycaret-server pycaret-server serve --reload
uv run --package pycaret-server pycaret-server migrate --revision head
```

Optional dependency groups exposed by the package include database/storage/LLM
and test support: `postgres`, `mysql`, `s3`, `notebook`, `llm-anthropic`,
`llm-openai`, `llm`, `dev`, and `test`. If a Redis worker environment lacks the
Redis Python client, install the queue dependency explicitly in that worker
environment.

## Settings model

Configuration is loaded by a cached Pydantic Settings object. Environment
variables use the `PYCARET_` prefix, and a `.env` file in the process working
directory is also read.

### Core settings

| Setting field | Env var | Default | Notes |
|---|---|---|---|
| `app_name` | `PYCARET_APP_NAME` | `PyCaret Server` | FastAPI title and root metadata. |
| `environment` | `PYCARET_ENVIRONMENT` | `dev` | Informational: `dev`, `staging`, `prod`. |
| `debug` | `PYCARET_DEBUG` | `false` | Enables SQLAlchemy echo and more verbose behavior. |
| `database_url` | `PYCARET_DATABASE_URL` | `sqlite:///./pycaret.db` | SQLite for dev, Postgres/MySQL for production-shaped installs. |
| `artifact_dir` | `PYCARET_ARTIFACT_DIR` | `./artifacts` | Local object-store root and CSV upload location. |
| `cors_origins` | `PYCARET_CORS_ORIGINS` | localhost/127.0.0.1 on port `3020` | Configure for browser UI origins. |
| `enable_deployments` | `PYCARET_ENABLE_DEPLOYMENTS` | `true` | Feature flag for in-house serving. |
| `enable_websocket` | `PYCARET_ENABLE_WEBSOCKET` | `true` | Event-stream fan-out flag. |

### Auth and secrets

| Setting field | Env var | Default | Notes |
|---|---|---|---|
| `jwt_secret` | `PYCARET_JWT_SECRET` | weak dev fallback | Must be strong and persistent outside dev. |
| `jwt_algorithm` | `PYCARET_JWT_ALGORITHM` | `HS256` | Token signing algorithm. |
| `access_token_ttl_minutes` | `PYCARET_ACCESS_TOKEN_TTL_MINUTES` | `60` | Access token lifetime. |
| `refresh_token_ttl_days` | `PYCARET_REFRESH_TOKEN_TTL_DAYS` | `30` | Refresh token lifetime. |
| `secrets_key` | `PYCARET_SECRETS_KEY` | `None` | Fernet key for LLM keys, connection secrets, webhooks, and PATs. If unset, an ephemeral per-process key is generated; secrets written with it are unreadable after restart. |

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Queue and worker settings

| Setting field | Env var | Default | Notes |
|---|---|---|---|
| `runs_backend` | `PYCARET_RUNS_BACKEND` | `inprocess` | `inprocess` uses the API process ThreadPoolExecutor; `redis` enqueues Jobs for workers. |
| `redis_url` | `PYCARET_REDIS_URL` | `redis://localhost:6379/0` | Used by queue adapter and worker. |
| `worker_id` | `PYCARET_WORKER_ID` | `None` | Stable id for worker locks; worker generates one if absent. |
| `worker_queues` | `PYCARET_WORKER_QUEUES` | `default` | Comma-separated queues for worker/admin display. |

Queue names recognized by the dispatcher and docs: `default`, `cpu-heavy`,
`gpu`, and `inference`. A Run with `use_gpu=True` in setup or plan params routes
Trial-Jobs to `gpu` with `requested_resources={"gpu": 1}`.

### Storage settings

| Setting field | Env var | Default | Notes |
|---|---|---|---|
| `storage_backend` | `PYCARET_STORAGE_BACKEND` | `local` | `local`, `s3`, or `minio`. |
| `storage_bucket` | `PYCARET_STORAGE_BUCKET` | `None` | Required for S3/MinIO. |
| `storage_endpoint_url` | `PYCARET_STORAGE_ENDPOINT_URL` | `None` | MinIO endpoint or compatible S3 endpoint. |
| `storage_region` | `PYCARET_STORAGE_REGION` | `us-east-1` | S3 region. |
| `storage_access_key` | `PYCARET_STORAGE_ACCESS_KEY` | `None` | S3/MinIO access key. |
| `storage_secret_key` | `PYCARET_STORAGE_SECRET_KEY` | `None` | S3/MinIO secret key. |

Object store selection is cached on first use. Tests and scripts should clear it
with `pycaret_server.storage.reset_for_tests()` after changing env vars.

### Notebook and alert settings

| Setting field | Env var | Default | Notes |
|---|---|---|---|
| `notebook_backend` | `PYCARET_NOTEBOOK_BACKEND` | `local` | `local` placeholder or `docker` container sessions. |
| `notebook_image` | `PYCARET_NOTEBOOK_IMAGE` | `None` | Docker image override. |
| `notebook_data_dir` | `PYCARET_NOTEBOOK_DATA_DIR` | `None` | Mounted data dir for notebook runtime. |
| `notebook_network` | `PYCARET_NOTEBOOK_NETWORK` | `None` | Docker network override. |
| `notebook_idle_timeout_seconds` | `PYCARET_NOTEBOOK_IDLE_TIMEOUT_SECONDS` | `1800` | Idle reaper threshold. |
| `smtp_host` | `PYCARET_SMTP_HOST` | `None` | Email alerts fail cleanly when absent. |
| `smtp_port` | `PYCARET_SMTP_PORT` | `587` | SMTP port. |
| `smtp_use_tls` | `PYCARET_SMTP_USE_TLS` | `true` | TLS toggle. |
| `smtp_username` | `PYCARET_SMTP_USERNAME` | `None` | SMTP auth. |
| `smtp_password` | `PYCARET_SMTP_PASSWORD` | `None` | SMTP auth. |
| `smtp_from` | `PYCARET_SMTP_FROM` | `None` | Sender address. |

## Isolated TestClient fixture pattern

Use this pattern for backend API tests or smoke scripts. It prevents writes to
the caller's default DB/artifact directory and resets singletons that cache
settings-derived state.

```python
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Set env before importing app/db modules.
monkeypatch.setenv("PYCARET_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
monkeypatch.setenv("PYCARET_JWT_SECRET", "test-secret-only-please")
monkeypatch.setenv("PYCARET_ARTIFACT_DIR", str(tmp_path / "artifacts"))
monkeypatch.setenv("PYCARET_SECRETS_KEY", Fernet.generate_key().decode())

# 2. Clear settings and rebind SQLAlchemy globals if the process may have
#    imported pycaret_server before the env change.
from pycaret_server.config import get_settings
get_settings.cache_clear()

from pycaret_server.db import session as sess_mod
sess_mod.engine = create_engine(
    f"sqlite:///{tmp_path / 'test.db'}",
    connect_args={"check_same_thread": False},
    future=True,
)
sess_mod.session_factory = sessionmaker(
    bind=sess_mod.engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Optional but robust when package-level exports already exist.
import pycaret_server.db as db_pkg
db_pkg.engine = sess_mod.engine
db_pkg.session_factory = sess_mod.session_factory

# 3. Reset cached singletons.
from pycaret_server.crypto import reset_for_tests as reset_crypto
from pycaret_server.storage import reset_for_tests as reset_storage
from pycaret_server.llm.router import reset_router
from pycaret_server.runs.broker import event_broker
from pycaret_server.runs.orchestrator import reset_orchestrator
from pycaret_server.scheduler import shutdown_scheduler
from pycaret_server.serving import reset_registry
from pycaret_server.runtime import reset_for_tests as reset_gpu

for fn in (reset_crypto, reset_storage, reset_router, reset_orchestrator,
           shutdown_scheduler, reset_registry, reset_gpu):
    fn()
event_broker.clear()

# 4. Create schema and run the app.
from pycaret_server.db import Base
Base.metadata.create_all(sess_mod.engine)

from pycaret_server.app import create_app
with TestClient(create_app()) as client:
    assert client.get("/healthz").json() == {"ok": True}
```

If you do not manually `create_all`, the app lifespan auto-applies Alembic on a
blank SQLite DB. Production-like non-SQLite databases require explicit
`pycaret-server migrate` before serve.

## Minimal API flow with curl

```bash
TOKEN=$(curl -sX POST http://localhost:8020/api/v1/setup/bootstrap \
  -H 'content-type: application/json' \
  -d '{"email":"admin@example.com","password":"supersecret","workspace_name":"Default"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

curl -sH "authorization: bearer $TOKEN" http://localhost:8020/api/v1/workspaces
curl -sH "authorization: bearer $TOKEN" http://localhost:8020/api/v1/auth/me
curl -s http://localhost:8020/openapi.json > pycaret-openapi.json
```

For a full train/deploy smoke, use the bundled
`scripts/run_lifecycle_smoke.py` rather than hand-assembling every request.
