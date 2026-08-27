# Local stack troubleshooting

Start with the bundled status command. It is non-mutating and works from any current directory when `--repo-root` is supplied.

```bash
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" status
```

## Docker, Compose, and port failures

### Docker or Compose is missing

Expected signals:

- `Docker Compose not found`
- `Docker daemon not running`
- `Cannot connect to the Docker daemon`
- status shows no container runtime

Recovery:

```bash
docker --version
docker info
docker compose version || docker-compose --version
```

Install/start Docker Desktop, Docker Engine, or a compatible Podman setup, then retry the helper. Do not edit Airweave service code until the container runtime is healthy.

### Port already in use

Common local ports are `5432`, `6379`, `7233`, `8001`, `8071`, `8080`, `8081`, `8082`, `8088`, `9090`, `9878`, `19071`, and optionally `5001`. The current local vector/search service is Vespa, so treat older Qdrant-oriented references to `6333` as stale unless the compose file was changed.

Find conflicting listeners:

```bash
# Linux/macOS examples
lsof -nP -iTCP:8001 -sTCP:LISTEN
lsof -nP -iTCP:8080 -sTCP:LISTEN
lsof -nP -iTCP:5432 -sTCP:LISTEN
```

Safe recoveries:

1. Stop the conflicting local process if it is unrelated.
2. If the conflict is an old Airweave container, run `status`, then `restart` or `recreate` as appropriate.
3. If only frontend or connect ports conflict, start without them: `start --skip-frontend --skip-connect`.
4. If `9878` conflicts and `.env` uses an API-backed dense embedder, use `--skip-local-embeddings`.

### Stale containers or profile mismatch

Symptoms: containers exist but frontend/connect/docling are missing, or status shows old images after compose changes.

Recovery ladder:

```bash
# Preserve data and restart existing containers.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" restart

# If service definitions/profiles changed and restart is not enough.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" recreate
```

Use `destroy` only when the user accepts losing compose volumes.

## Environment and settings failures

Backend settings load eagerly. Even import-only checks and container startup can fail if required env values are absent or too short.

High-value checks:

```bash
cd "$AIRWEAVE_REPO"
grep -E '^(FIRST_SUPERUSER|FIRST_SUPERUSER_PASSWORD|ENCRYPTION_KEY|STATE_SECRET|POSTGRES_HOST|POSTGRES_USER|POSTGRES_PASSWORD|SVIX_JWT_SECRET|DENSE_EMBEDDER|EMBEDDING_DIMENSIONS|SPARSE_EMBEDDER|STORAGE_BACKEND)=' .env
```

Required local expectations:

- `STATE_SECRET` must satisfy the backend minimum-length validation.
- `SVIX_JWT_SECRET` must be at least 32 bytes for HMAC-SHA256.
- `DENSE_EMBEDDER`, `EMBEDDING_DIMENSIONS`, and `SPARSE_EMBEDDER` must be set together.
- If `DENSE_EMBEDDER` is OpenAI- or Mistral-backed, the matching API key must be present before embedding-dependent flows work.
- If `DENSE_EMBEDDER=local_minilm`, do not skip the local embeddings container.
- For local storage smoke tests, prefer `STORAGE_BACKEND=filesystem` and `STORAGE_PATH=./local_storage` unless testing cloud storage explicitly.

Safe recovery:

```bash
# Fill only missing required local values without destroying containers.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" start --skip-frontend

# Then restart backend/worker with the corrected env.
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" restart
```

If a freshly copied `.env.example` leaves an API-backed dense embedder but no API key, either add a valid API key or switch to local embeddings:

```bash
cd "$AIRWEAVE_REPO"
python - <<'PY'
from pathlib import Path
p = Path('.env')
text = p.read_text()
for key, value in {
    'DENSE_EMBEDDER': 'local_minilm',
    'EMBEDDING_DIMENSIONS': '384',
    'SPARSE_EMBEDDER': 'fastembed_bm25',
}.items():
    lines = [line for line in text.splitlines() if not line.startswith(key + '=')]
    lines.append(f'{key}={value}')
    text = '\n'.join(lines) + '\n'
p.write_text(text)
PY
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root "$AIRWEAVE_REPO" restart
```

## Vespa failures

Vespa startup has two phases: the `airweave-vespa` config/document service becomes healthy, then `airweave-vespa-init` templates and deploys the application package using `EMBEDDING_DIMENSIONS`.

Expected healthy signals:

```bash
curl -sf http://localhost:8081/state/v1/health | grep 'up'
docker inspect airweave-vespa-init --format '{{.State.Status}} {{.State.ExitCode}}'
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8081/document/v1/
```

Common failures and recoveries:

- `airweave-vespa-init` exited nonzero: inspect `docker logs airweave-vespa-init`, confirm `.env` has a numeric `EMBEDDING_DIMENSIONS`, then `recreate` if the schema package was deployed with the wrong dimension.
- Config server never reaches `up`: inspect `docker logs airweave-vespa`, ensure ports `8081` and `19071` are free, and check Docker memory availability.
- Backend search errors after changing embedder dimensions: Vespa schema dimensions and backend embeddings must match. Recreate Vespa volumes after intentional dimension changes.

## Backend, worker, Svix, and storage failures

### Backend health is down

Check logs and core dependencies before changing code:

```bash
docker logs airweave-backend --tail 200
docker logs airweave-db --tail 100
docker logs airweave-redis --tail 100
docker logs airweave-svix --tail 100
curl -sf http://localhost:8001/health/ready
```

Likely causes: missing env values, database migration failure, Redis/Svix not healthy, incompatible embedder configuration, or port conflict.

### Temporal worker is not processing syncs

```bash
docker logs airweave-temporal-worker --tail 200
docker logs airweave-temporal --tail 100
docker logs airweave-temporal-init --tail 100
```

The worker uses the same backend image and environment as the API container. Fix backend settings first, then restart.

### Svix blocks backend startup

Svix depends on Postgres and Redis and uses `SVIX_JWT_SECRET`. If the backend waits on or fails against Svix:

```bash
docker inspect airweave-svix --format '{{.State.Health.Status}}'
docker logs airweave-svix --tail 100
grep '^SVIX_JWT_SECRET=' "$AIRWEAVE_REPO/.env"
```

Regenerate a long secret if needed, then `restart`.

### Storage smoke fails

The native safe smoke is `backend/tests/e2e/smoke/test_storage_backend.py`. It expects a healthy backend, local environment, a stub source, and readable filesystem storage in the backend/worker container or host `local_storage` path.

Run after stack health is green:

```bash
cd "$AIRWEAVE_REPO/backend"
TEST_ENV=local python -m pytest tests/e2e/smoke/test_storage_backend.py -q
```

If it fails:

1. Confirm backend health: `curl -sf http://localhost:8001/health`.
2. Confirm local storage mapping exists: `docker exec airweave-temporal-worker test -d /app/local_storage`.
3. Confirm `.env` uses filesystem storage unless intentionally testing cloud storage.
4. Confirm internal/stub sources are available in the local test environment.
5. Inspect worker logs for sync errors before assuming storage code is broken.

## Optional frontend, connect, and Docling toggles

- `--skip-frontend` is appropriate for backend API tests and connector development that does not need the dashboard UI.
- `--skip-connect` is appropriate unless a task specifically needs the embeddable widget.
- `--enable-docling` starts the Docling OCR container and wires `DOCLING_BASE_URL` into backend containers. If Docling is not needed, leave it disabled to reduce startup time and port usage.

If optional services fail but backend health is green, keep the stack running and route UI/widget issues to the appropriate sub-skill instead of destroying the backend stack.
