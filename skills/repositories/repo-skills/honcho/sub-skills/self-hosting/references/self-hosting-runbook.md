# Honcho Self-hosting Runbook

This runbook assumes commands are run from the Honcho repository root. Keep secrets in environment variables or `.env`; use `config.toml` for non-secret base configuration when desired.

## Operating model

Honcho self-hosting has two cooperating processes over shared infrastructure:

| Component | Required? | Purpose | Typical start command |
|---|---:|---|---|
| API server | Yes | FastAPI HTTP API, `/v3/*` routers, synchronous Dialectic chat, `/health`, `/metrics` when enabled | `uv run fastapi dev src/main.py` |
| Deriver worker | Yes for memory | Queue consumer for representation work, summaries, peer cards, dreams, and reconciliation work | `uv run python -m src.deriver` |
| PostgreSQL + pgvector | Yes | Application database plus pgvector-backed default vector storage | external Postgres or compose `database` service |
| Redis | Optional outside compose | Cache when `CACHE_ENABLED=true`; Honcho falls back to in-memory caching if Redis is unreachable | compose `redis` service or `redis://...` |
| External vector store | Optional | Turbopuffer or LanceDB instead of default pgvector storage | configured with `VECTOR_STORE_TYPE` |

The API startup lifespan initializes telemetry, registers metrics collectors, validates the embedding schema, initializes cache, and only then serves requests. The same embedding dimension invariant is enforced for the deriver before queue processing.

## Docker Compose path

Docker Compose is the recommended local self-hosting path. The compose file builds the image from source; there is no pre-built Docker Hub image documented in the self-hosting guide.

```bash
cp .env.template .env
# Edit .env: set provider keys and any model/vector/auth overrides.
cp docker-compose.yml.example docker-compose.yml
docker compose up -d --build
```

What compose starts by default:

- `api` bound to `127.0.0.1:8000`.
- `deriver` started after the API and infrastructure health checks.
- `database` using `pgvector/pgvector:pg15`, bound to `127.0.0.1:5432`, with `database/init.sql` mounted for first-boot extension setup.
- `redis` bound to `127.0.0.1:6379`.
- `CACHE_ENABLED=true` and `CACHE_URL=redis://redis:6379/0?suppress=true` inside API and deriver containers.
- A shared `lancedb-data` volume for LanceDB if `VECTOR_STORE_TYPE=lancedb`.

Optional compose modes:

```bash
# Build with the LanceDB optional dependency.
INSTALL_LANCEDB=true docker compose up -d --build

# Basic checks.
docker compose ps
curl http://localhost:8000/health
docker compose logs api --tail 50
docker compose logs deriver --tail 50
```

The compose file binds PostgreSQL and Redis to localhost only. Do not widen those bindings in production unless you have a separate network and credential hardening plan.

## Manual path

```bash
uv sync
cp .env.template .env
# Edit .env.
```

Prepare PostgreSQL with pgvector. A quick local database can be launched with:

```bash
docker run --name honcho-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d pgvector/pgvector:pg15
```

Enable the extension once in the Honcho database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then set at least:

```bash
DB_CONNECTION_URI=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
AUTH_USE_AUTH=false
LOG_LEVEL=DEBUG
LLM_OPENAI_API_KEY=sk-...
```

Run migrations and start both processes:

```bash
uv run alembic upgrade head
uv run fastapi dev src/main.py
# Separate terminal:
uv run python -m src.deriver
```

## Verification sequence

Use layered checks because `/health` is intentionally lightweight and does not check the database, migrations, or LLM providers.

```bash
# Process is up.
curl http://localhost:8000/health

# Database + migrations + API route are working.
curl -s -X POST http://localhost:8000/v3/workspaces \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'

# Migration status when debugging schema errors.
uv run alembic current

# Docker log checks.
docker compose logs api --tail 50
docker compose logs deriver --tail 50
```

For SDK smoke tests, point the client at the self-hosted URL, for example `base_url="http://localhost:8000"` in Python or `baseUrl: "http://localhost:8000"` in TypeScript.

## Embedding dimension bootstrap

Default pgvector columns are created as `vector(1536)`. If the deployment uses a different embedding dimension, bootstrap before serving traffic:

```bash
uv run alembic upgrade head
export EMBEDDING_VECTOR_DIMENSIONS=768
uv run python scripts/configure_embeddings.py --dry-run
uv run python scripts/configure_embeddings.py --yes
uv run fastapi dev src/main.py
uv run python -m src.deriver
```

Important constraints:

- `EMBEDDING_VECTOR_DIMENSIONS` is the single source of truth.
- `VECTOR_STORE_DIMENSIONS` is deprecated; if set, Honcho warns and then overwrites vector-store dimensions from embedding settings.
- The configure script locks `documents` and `message_embeddings`, refuses any non-null embeddings, drops and recreates HNSW indexes, and alters both embedding columns in one transaction.
- The startup validator fails closed when required vector columns are missing, unbounded, or have a dimension that differs from `EMBEDDING_VECTOR_DIMENSIONS`.
- For Turbopuffer/LanceDB, namespaces are lazy-created. Startup samples existing namespaces; use `scripts/configure_embeddings.py --report` for a fuller external-store inventory.

## Auth operations

Local examples often use `AUTH_USE_AUTH=false`. For production, enable auth and set a secret:

```bash
uv run python scripts/generate_jwt_secret.py
# Set AUTH_JWT_SECRET=<generated_secret>
AUTH_USE_AUTH=true
```

Generate tokens with `scripts/generate_jwt.py`:

```bash
uv run python scripts/generate_jwt.py --admin --expires 24h
uv run python scripts/generate_jwt.py --workspace my-workspace --expires 30d
uv run python scripts/generate_jwt.py --workspace my-workspace --peer my-peer --expires 1y
uv run python scripts/generate_jwt.py --workspace my-workspace --session my-session --expires 8h
TOKEN=$(uv run python scripts/generate_jwt.py --admin --print-only)
```

The script enforces these rules: `--admin` cannot be combined with scoped flags, and `--peer` or `--session` requires `--workspace`.

## Production hardening checklist

- Put HTTPS in front of the API via a reverse proxy.
- Enable `AUTH_USE_AUTH=true` and keep `AUTH_JWT_SECRET` out of source control.
- Use strong database credentials and restrict database/Redis network access.
- Run `uv run alembic upgrade head` after updating Honcho and before starting the API/deriver.
- Scale background throughput with `DERIVER_WORKERS` or additional deriver processes; workers coordinate through the database queue.
- Enable `METRICS_ENABLED=true` when Prometheus scraping is desired. The API exposes `/metrics` on port 8000; the deriver exposes metrics on port 9090 in its process/container.
- Enable `SENTRY_ENABLED=true` with `SENTRY_DSN` for error tracking if desired.
- Back up PostgreSQL regularly, e.g. `docker compose exec database pg_dump -U postgres postgres > backup.sql` and restore with `docker compose exec -T database psql -U postgres postgres < backup.sql`.

## Update routine

```bash
# Before starting the new version.
uv run alembic upgrade head

# Confirm current revision when diagnosing.
uv run alembic current

# Then restart both API and deriver.
```

If an update also changes embedding dimensions or embedding model dimensions, do not mutate a populated deployment in place; bring up a fresh deployment at the new dimension and migrate data out of band.
