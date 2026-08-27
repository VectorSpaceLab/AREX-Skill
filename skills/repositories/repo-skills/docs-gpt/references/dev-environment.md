# DocsGPT development environment reference

## Prerequisite checks

Before installing or starting services, inspect what already works:

```bash
ls -d .venv venv 2>/dev/null || true
python --version || true
command -v uv || true
command -v psql || true
command -v redis-cli || true
printf '%s\n' "${POSTGRES_URI:-POSTGRES_URI not set}"
```

If `POSTGRES_URI` is set, test reachability without printing passwords:

```bash
python - <<'PY'
import os
from urllib.parse import urlparse
uri = os.environ.get('POSTGRES_URI')
print('POSTGRES_URI set:', bool(uri))
if uri:
    p = urlparse(uri)
    print('postgres host:', p.hostname, 'port:', p.port or 5432, 'db:', p.path.lstrip('/'))
PY
```

If Redis is local/default:

```bash
redis-cli -n 0 PING
redis-cli -n 2 PING
```

Redis DB 0 is the default Celery broker/result path; Redis DB 2 is used by `CACHE_REDIS_URL` defaults for app cache, SSE, OIDC state, revocations, and remote-device coordination.

## Python backend install

Normal path once an environment is chosen:

```bash
source .venv/bin/activate
uv pip install -r application/requirements.txt
# or: pip install -r application/requirements.txt
```

Test dependencies are separate:

```bash
pip install -r tests/requirements.txt
```

The repo is an application checkout rather than a packaged Python distribution. Run Python commands from the repo root (or with the repo root on `PYTHONPATH`) so `application` imports resolve.

## Run modes

### Full local development / production parity

```bash
uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload
```

Use this for anything involving:

- `/mcp`
- `GET /api/messages/<id>/events`
- async SSE reconnect behavior
- production-parity routing

### Fast Flask-only loop

```bash
flask --app application/app.py run --host=0.0.0.0 --port=7091
```

Use only when you do not need ASGI-mounted routes. It serves the WSGI Flask app and still has `POST /stream`, but the reconnect route and MCP mount are absent.

### Celery worker

```bash
celery -A application.app.celery worker -l INFO
# macOS:
python -m celery -A application.app.celery worker -l INFO --pool=solo
```

A bare worker consumes all configured queues. Use `-Q docsgpt` and `-Q parsing` only when explicitly splitting general app tasks from heavy document parsing/OCR workers.

## Data stores and vector stores

- Postgres is mandatory for user data in real deployments.
- MongoDB is not required for default installs. It is only used when `VECTOR_STORE=mongodb` or for the offline legacy backfill script.
- Vector stores are independent of user data: supported names include `faiss`, `pgvector`, `qdrant`, `milvus`, `elasticsearch`, `lancedb`, and `mongodb`.
- GraphRAG requires `VECTOR_STORE=pgvector` and `GRAPHRAG_ENABLED=true`.

## Useful local probes

```bash
python skills/disco/docs-gpt/scripts/check_local_config.py --repo .
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/sources
python - <<'PY'
from application.version import get_version
print(get_version())
PY
```

For model registry edits:

```bash
python - <<'PY'
from application.core.model_registry import ModelRegistry
print(ModelRegistry)
PY
```

## Validation command selection

- Backend API/parser/retrieval/security/storage changes: `ruff check .` and focused `python -m pytest <path>`; broaden to `python -m pytest` before PR.
- ASGI/SSE/MCP changes: run under Uvicorn and include an SSE/MCP-focused test path.
- Celery/ingestion changes: run focused tests plus a worker-backed local smoke when services exist.
- Frontend changes: `cd frontend && npm run lint && npm run build`.
- Docs changes: `cd docs && npm run build`; run `vale .` if Vale is installed and prose changed.
- E2E/UI flows: use the `tests/e2e` npm scripts and attach screenshots/videos for PR review.
