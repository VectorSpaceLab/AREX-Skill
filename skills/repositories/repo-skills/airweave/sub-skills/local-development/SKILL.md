---
name: local-development
description: "Operate the Airweave local Docker stack safely: start, reuse,
  restart, recreate, destroy, seed environment, check ports, and recover health
  failures."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Airweave Local Development

Use this sub-skill when a future Airweave task needs the local Docker stack running or diagnosed. It owns stack bootstrap, restart/recreate/destroy decisions, `.env` seeding, service profiles, port checks, and health recovery.

Do not use this sub-skill for backend endpoint details, connector implementation, frontend page logic, MCP transport behavior, or Monke connector orchestration. After the stack is healthy, route search, collection, source-connection, connect-session, and webhook workflows to `../backend-api/SKILL.md`.

## Safe operating rules

1. Work from an explicit repository root. The bundled helper accepts `--repo-root /path/to/airweave` and works from any current directory.
2. Prefer `status` before mutation:
   ```bash
   bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
     --repo-root "$AIRWEAVE_REPO" status
   ```
3. A plain `start` is state-preserving: it seeds `.env` only when needed, starts missing/stopped services, and reuses running containers instead of deleting data.
4. Use `restart` for already-created containers when you want to preserve Postgres/Redis/Vespa volumes.
5. Use `recreate` only when container state is stale or service definitions changed; it removes compose containers and volumes, then starts fresh from the current `.env`.
6. Use `destroy` only with explicit user intent. It removes compose containers and Docker volumes; it does not intentionally edit `.env` or purge manually managed host files.

## Common commands

```bash
# Fresh or reuse-safe start, including backend, frontend, connect widget, Vespa, Temporal, Redis, Postgres, Svix.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
  --repo-root "$AIRWEAVE_REPO" start

# Backend/service stack without frontend UI.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
  --repo-root "$AIRWEAVE_REPO" start --skip-frontend

# Preserve data; restart existing containers and rerun health checks.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
  --repo-root "$AIRWEAVE_REPO" restart

# Recreate containers and compose volumes from current repo config.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
  --repo-root "$AIRWEAVE_REPO" recreate

# Destructive cleanup; add --yes for noninteractive confirmation.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh \
  --repo-root "$AIRWEAVE_REPO" destroy
```

Equivalent environment toggles are supported for automation: `NONINTERACTIVE=1`, `SKIP_FRONTEND=1`, `SKIP_CONNECT=1`, `SKIP_LOCAL_EMBEDDINGS=1`, `ENABLE_DOCLING=1`, `VERBOSE=1`, and `QUIET=1`.

## Startup decisions

- Fresh checkout with no `.env`: the helper copies `.env.example`, generates missing `ENCRYPTION_KEY`, `STATE_SECRET`, `SVIX_JWT_SECRET`, `FIRST_SUPERUSER_PASSWORD`, and `POSTGRES_PASSWORD`, fills safe local defaults such as `FIRST_SUPERUSER=admin@example.com`, `POSTGRES_USER=airweave`, `SKIP_AZURE_STORAGE=true`, `STORAGE_BACKEND=filesystem`, and `SPARSE_EMBEDDER=fastembed_bm25`.
- Embeddings: OpenAI keys prefer `openai_text_embedding_3_small` with 1536 dimensions and skip the local embeddings container. Mistral keys prefer `mistral_embed` with 1024 dimensions. No API key on a freshly seeded env uses `local_minilm` with 384 dimensions and starts the local embeddings container. An existing `.env` is not overwritten except for missing required values.
- Reusing containers: if Airweave containers already run, `start` reports status instead of recreating them. If containers exist but are stopped, `start` brings them back up and runs health checks.
- Optional profiles: `--skip-frontend`, `--skip-connect`, `--skip-local-embeddings`, and `--enable-docling` map to the compose profiles for frontend, connect widget, local embeddings, and Docling OCR.

## Expected local service surface

See `references/local-stack.md` for the service graph, ports, startup modes, and health commands. The primary expected endpoints are:

- Backend API: `http://localhost:8001`, health at `/health` and readiness at `/health/ready`
- Frontend UI: `http://localhost:8080` unless skipped
- Connect widget: `http://localhost:8082` unless skipped
- Vespa document/query API: `http://localhost:8081`, config server on `19071`
- Temporal gRPC/UI: `7233`, `8233`, and `http://localhost:8088`
- PostgreSQL: `localhost:5432`; Redis: `localhost:6379`; Svix: `http://localhost:8071`
- Local embeddings: host `9878` when `DENSE_EMBEDDER=local_minilm`; Docling: `5001` only when enabled

## Verification hooks

For command-level checks before a real stack run:

```bash
bash -n skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --help
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" status
```

For a backend-native smoke after the stack is healthy and a Python 3.13 backend environment with `pytest`/`pytest-asyncio` is active:

```bash
cd "$AIRWEAVE_REPO/backend"
TEST_ENV=local python -m pytest tests/e2e/smoke/test_storage_backend.py -q
```

This storage smoke verifies the backend health endpoint, stub-source sync, ARF files, manifests, and entity files. If it fails because `stub` is unavailable, check whether internal sources are enabled for the local test environment before treating storage as broken.

## Troubleshooting entry points

- Docker or Compose missing, daemon down, or port conflicts: `references/troubleshooting.md#docker-compose-and-port-failures`
- Missing or invalid env values, including `STATE_SECRET` and `SVIX_JWT_SECRET` length validation: `references/troubleshooting.md#environment-and-settings-failures`
- Vespa init or schema dimension mismatch: `references/troubleshooting.md#vespa-failures`
- Backend, Temporal worker, Svix, or storage smoke failures: `references/troubleshooting.md#backend-worker-svix-and-storage-failures`
