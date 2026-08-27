# Airweave local stack reference

This reference summarizes the local Docker stack controlled by the bundled helper `scripts/local-stack.sh`. Always pass an explicit repo root or set `AIRWEAVE_REPO` before invoking it from a future task.

## Helper surface

```bash
# Non-mutating inventory and health report.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" status

# Safe default: seed only missing env, reuse running containers, start stopped/missing services.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" start

# Preserve volumes and data.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" restart

# Remove compose containers and named volumes, then start again from current files.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" recreate

# Destructive cleanup; requires confirmation unless --yes or --noninteractive is supplied.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" destroy
```

Options may be supplied as flags or environment variables:

| Flag | Environment variable | Effect |
| --- | --- | --- |
| `--noninteractive` | `NONINTERACTIVE=1` | Do not prompt for API keys or confirmations. |
| `--yes` | none | Confirm destructive `destroy` in automation. |
| `--skip-frontend` | `SKIP_FRONTEND=1` | Do not start the frontend profile. |
| `--skip-connect` | `SKIP_CONNECT=1` | Do not start the connect-widget profile. |
| `--skip-local-embeddings` | `SKIP_LOCAL_EMBEDDINGS=1` | Do not start local embeddings; requires a compatible API-backed dense embedder. |
| `--enable-docling` | `ENABLE_DOCLING=1` | Start `docling-serve` and wire `DOCLING_BASE_URL` inside backend containers. |
| `--verbose` | `VERBOSE=1` | Print debug commands and shell tracing. |
| `--quiet` | `QUIET=1` | Reduce banner/status noise. |

## Fresh start versus reuse

A fresh start means no Airweave compose containers exist or `recreate` removed them. The helper then:

1. verifies Docker/Podman and Compose availability;
2. copies `.env.example` to `.env` if `.env` is absent;
3. generates missing secret values with Python `secrets` or `openssl`;
4. fills safe local defaults that the backend settings expect;
5. chooses embedding mode from `.env` and available API keys;
6. starts compose services with the selected profiles;
7. waits for Vespa deployment and backend health before reporting final status.

A reuse start means containers already exist. The helper does **not** reseed or rewrite an existing `.env` except for missing required values during a normal `start`. If containers are already running, it reports status and avoids destructive cleanup. If containers are stopped, it starts them again with the selected profiles and reruns health checks. Use `restart` when containers exist and you want an explicit compose restart while preserving volumes.

## Environment seeding

Fresh `.env` creation is based on `.env.example`, with these local defaults filled when absent:

| Variable | Local behavior |
| --- | --- |
| `ENCRYPTION_KEY` | Generated secret for encrypted local credentials. |
| `STATE_SECRET` | Generated URL-safe secret; must satisfy backend minimum length validation. |
| `SVIX_JWT_SECRET` | Generated URL-safe secret; must be at least 32 bytes for Svix HMAC validation. |
| `FIRST_SUPERUSER` | Defaults to `admin@example.com` if empty. |
| `FIRST_SUPERUSER_PASSWORD` | Generated local password if empty. |
| `POSTGRES_USER` | Defaults to `airweave` if absent. |
| `POSTGRES_PASSWORD` | Generated local database password if empty. |
| `SKIP_AZURE_STORAGE` | Defaults to `true` for faster local startup. |
| `STORAGE_BACKEND` | Defaults to `filesystem` if absent. |
| `STORAGE_PATH` | Defaults to `./local_storage` if absent. |
| `SPARSE_EMBEDDER` | Defaults to `fastembed_bm25` if absent. |

Embedding choice is intentionally conservative:

- Real `OPENAI_API_KEY` => `DENSE_EMBEDDER=openai_text_embedding_3_small`, `EMBEDDING_DIMENSIONS=1536`, no local embeddings container unless `.env` explicitly says `DENSE_EMBEDDER=local_minilm`.
- Real `MISTRAL_API_KEY` and no OpenAI key => `DENSE_EMBEDDER=mistral_embed`, `EMBEDDING_DIMENSIONS=1024`.
- No API key on a freshly seeded env => `DENSE_EMBEDDER=local_minilm`, `EMBEDDING_DIMENSIONS=384`, local embeddings container on host port `9878`.
- Existing `.env` values are respected. If an existing API-backed dense embedder lacks its API key, fix `.env` or choose local embeddings before debugging service code.

## Service graph and ports

| Service/container | Purpose | Host surface | Notes |
| --- | --- | --- | --- |
| `airweave-db` | PostgreSQL metadata database | `localhost:5432` | Uses named volume `postgres_data`; health via `pg_isready`. |
| `airweave-redis` | Redis cache/pubsub/queues | `localhost:6379` | Uses named volume `redis_data`; health via `redis-cli ping`. |
| `airweave-svix` | Local webhook delivery service | `http://localhost:8071` | Uses Postgres and Redis; required by backend/worker. |
| `airweave-temporal` | Temporal service | `localhost:7233`, `localhost:8233` | Uses Postgres; `temporal-init` registers `SyncId` search attribute. |
| `airweave-temporal-ui` | Temporal web UI | `http://localhost:8088` | Useful for sync workflow inspection. |
| `airweave-vespa` | Vespa vector/search engine | `http://localhost:8081`, config `19071` | Data in `vespa_data`; app package mounted from `vespa/app`. |
| `airweave-vespa-init` | One-shot Vespa app deploy | no public port | Templates schema with `EMBEDDING_DIMENSIONS`; exit code must be `0`. |
| `airweave-backend` | FastAPI backend | `http://localhost:8001`, metrics `9090` | Runs migrations on startup when configured; health at `/health` and `/health/ready`. |
| `airweave-temporal-worker` | Sync worker | no public port | Uses same backend image and env; writes ARF files to local storage. |
| `airweave-frontend` | React dashboard | `http://localhost:8080` | Profile-controlled; skipped by `--skip-frontend`. |
| `airweave-connect` | Connect widget | `http://localhost:8082` | Profile-controlled; skipped by `--skip-connect`. |
| `airweave-embeddings` | Local MiniLM embeddings | `http://localhost:9878` | Profile-controlled; required when `DENSE_EMBEDDER=local_minilm`. |
| `airweave-docling` | Optional OCR fallback | `http://localhost:5001` | Profile-controlled; enabled by `--enable-docling`. |

If older notes mention Qdrant port `6333`, confirm the current compose file first: this skill evidence uses Vespa as the local vector/search service.

## Health and status commands

Use the helper first:

```bash
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" status
```

Manual checks when you need a narrower signal:

```bash
# Container inventory and compose state.
docker ps --filter 'name=airweave-' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
cd "$AIRWEAVE_REPO" && docker compose --env-file .env -f docker/docker-compose.yml ps

# Backend readiness from host and from inside the container.
curl -sf http://localhost:8001/health
curl -sf http://localhost:8001/health/ready
docker exec airweave-backend curl -sf http://localhost:8001/health

# Vespa config and document API readiness.
curl -sf http://localhost:8081/state/v1/health
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8081/document/v1/
docker inspect airweave-vespa-init --format '{{.State.Status}} {{.State.ExitCode}}'

# Optional UIs.
curl -sf http://localhost:8080      # frontend, when enabled
curl -sf http://localhost:8082      # connect widget, when enabled
curl -sf http://localhost:5001/health  # docling, when enabled
```

Backend/API tasks that depend on a running stack should continue in `../backend-api/SKILL.md` after these checks pass.
