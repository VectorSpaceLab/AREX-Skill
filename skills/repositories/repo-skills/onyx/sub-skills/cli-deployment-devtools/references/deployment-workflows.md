# Deployment and Local Development Workflows

This reference distills common Onyx deployment and local-dev operations. It intentionally provides concrete commands instead of sending future agents to source README files. Confirm before destructive deploy, host, or DB operations.

## Choose the right surface

| Need | Preferred surface |
| --- | --- |
| Query an Onyx server or manage guided self-hosted install | `onyx-cli`; see [onyx-cli.md](onyx-cli.md). |
| Start repo development dependencies and generated artifacts | `ods`; see [ods-devtools.md](ods-devtools.md). |
| Manually run published Docker Compose app stack | Docker Compose commands in this reference. |
| Helm/Kubernetes install, render, or chart validation | Helm/Kubernetes section below. |
| Backend implementation, migrations authoring, or Celery internals | Route to `backend-platform`. |
| Frontend implementation or Bun package details | Route to `web-frontend`. |

## Local development setup

Prerequisites for a source checkout:

```bash
uv venv .venv --python 3.13
uv sync
uv run playwright install

cd web
bun install
cd -
```

Run the common development stack with `ods`:

```bash
# Start infra only: Postgres, cache/search/file-store/model dependencies.
ods compose dev --infra

# Apply migrations after first DB startup or schema changes.
ods db upgrade

# Start backend and model server with hot reload in separate terminals.
ods backend model_server
ods backend api

# Start the web dev server.
ods web dev
```

Notes:

- `ods compose dev` exposes development ports; use `--infra` when you want only backing services and will run API/web locally.
- `ods backend` loads developer environment values, creates the developer `.env` from the template if missing, and lets shell env values win.
- If background jobs or Celery behavior matter, route to `backend-platform` before choosing a worker startup path.
- The web app normally runs on `http://localhost:3000`; backend API on `8080`; model server on `9000`, unless ports are changed.

Manual Docker-only app startup from the Docker Compose deployment directory:

```bash
docker compose up -d
```

After containers are healthy, use the web app at `http://localhost:3000`. To build local images instead of pulling published images:

```bash
docker compose up -d --build
```

Building web/model images may require Docker Hardened Images access; see [troubleshooting.md](troubleshooting.md) before assuming a public pull/build will work.

## Docker Compose deployment modes

### Standard stack

Standard Compose starts the full Onyx application and dependencies: API server, background worker, web server, model servers, Postgres, OpenSearch, Redis, MinIO, and related services. The API server runs migrations before starting.

Common operations:

```bash
# Guided install/upgrade path.
onyx-cli deploy install
onyx-cli deploy status
onyx-cli deploy logs api_server --tail 200
onyx-cli deploy upgrade --tag v4.4.6

# Manual Compose path when already in the deployment directory.
docker compose pull
docker compose up -d --wait
```

Use `onyx-cli deploy stop` to stop without deleting data. Do not run uninstall or volume-removal commands without explicit approval.

### Lite stack

Lite mode removes vector database/search, Redis, model servers, MinIO, and background workers from the default start set. It keeps core chat, LLM conversations, tools, user file uploads, Projects, Agent knowledge, and code interpreter support with Postgres-backed cache/auth/file storage.

Commands:

```bash
onyx-cli deploy install --lite

# Manual overlay form.
docker compose -f docker-compose.yml -f docker-compose.onyx-lite.yml up -d
```

Use Lite when resources are constrained or RAG/search/connectors are not needed. Do not choose Lite if the task requires indexing, connector sync, vector retrieval, or Redis-backed/background-worker behavior.

### Dev overlay

The dev overlay exposes service ports and builds the backend dev image target when building locally:

```bash
onyx-cli deploy install --dev

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait
```

Use it for local testing and debugging, not as a production hardening recipe.

### Craft overlay

Docker Compose Craft runs sandboxes through the host Docker socket. That socket is root-equivalent on the host. Only enable Craft on hosts the user fully controls:

```bash
onyx-cli deploy install --include-craft

docker compose -f docker-compose.yml -f docker-compose.craft.yml up -d --wait
```

Craft has separate Kubernetes behavior under Helm: Kubernetes sandboxes require Kubernetes 1.33 or newer, and setting a Docker sandbox backend is not a bypass for Helm Craft deployments.

## Environment templates and secrets

Compose deployment files read `.env` in the deployment directory. The guided installer creates it from the bundled template; manual deployments should copy the template values into a local `.env` and then edit only the local file.

Common environment points:

- `IMAGE_TAG` controls Onyx image versions. Leaving it as `latest` tracks published updates; pin a `vX.Y.Z` tag when reproducibility matters.
- `IMAGE_TAG=<tag>-dev` selects dev-tag image variants. Today the backend dev image is the important difference because it includes debugging tools such as shell editors, curl, process tools, and psql.
- `USER_AUTH_SECRET` must be non-empty for secure auth. The guided installer generates one; manual deployments should generate a strong random value.
- Auth is enabled by default. Email/password works out of the box; SSO provider settings are configured through the admin UI for current versions.
- Never write API keys, SMTP passwords, DB passwords, or OAuth secrets into committed files.
- Guided `onyx-cli deploy upgrade` preserves `.env` edits and backs up hand-edited managed files before overwriting with consent or `--force`.

## Generated Compose/template rules

The standard generated compose outputs are rendered from one shared template. Treat generated Compose files as build artifacts:

```bash
# Check for drift.
ods generate-compose

# Rewrite generated outputs after template changes.
ods generate-compose --write
```

Rules:

- Edit the shared template when changing the default/prod/no-letsencrypt generated variants; do not hand-edit generated outputs.
- The generator also refreshes deployment copies embedded into `onyx-cli` for guided installs.
- The compose-sync pre-commit hook enforces generation; if generated files drift, regenerate and include the refreshed copies in the same change.
- User-facing install documentation ships with guided self-hosted installs; keep contributor-only notes in contributor-facing docs or bundled skill references, not in install output.

## Migrations and run commands

Compose API containers run Alembic upgrade before starting the API server. For source development, apply migrations explicitly:

```bash
ods db current
ods db upgrade
ods db upgrade --schema private
```

Manual backend development equivalents when not using `ods`:

```bash
cd backend
alembic upgrade head
uvicorn model_server.main:app --reload --port 9000
AUTH_TYPE=basic uvicorn onyx.main:app --reload --port 8080
```

Prefer `ods backend` and `ods db` when possible because they resolve ports, load developer env, and auto-detect containerized Postgres details. Route migration authoring and backend test strategy to `backend-platform`.

Destructive migration/DB commands require approval:

```bash
ods db downgrade -1
ods db restore snapshot.dump --clean
ods db drop
```

Before destructive DB operations, capture the target database/schema, backup state, running app impact, and whether shared services/users are present.

## Safe logs and database access

Read deployment logs without opening broad unbounded streams:

```bash
onyx-cli deploy logs api_server --tail 200
onyx-cli deploy logs background --since 10m --tail 200
ods logs --follow=false --tail 100 api_server
```

Read-only SQL access from a host checkout or devcontainer:

```bash
PGPASSWORD="${POSTGRES_PASSWORD:-password}" \
  psql -h "${POSTGRES_HOST:-localhost}" -U postgres -c "SELECT 1;"
```

If no local `psql` client is available, use Docker without TTY flags:

```bash
docker exec onyx-relational_db-1 psql -U postgres -c "SELECT 1;"
```

Safety rules:

- Use read-only SQL first. Require explicit approval before `UPDATE`, `DELETE`, `TRUNCATE`, `DROP`, `ALTER`, restore, downgrade, or volume removal.
- Do not use `docker exec -it` in non-TTY agent shells.
- Prefer `--tail`, `--since`, and service filters for logs to reduce secret/document exposure.
- If the Compose project name is not `onyx`, identify the actual container names with read-only Docker listing commands or pass the correct `ods --project`/`onyx-cli deploy --project` value.

## Helm and Kubernetes high-level workflow

The Helm chart deploys Onyx to Kubernetes with bundled Redis operator support, CloudNativePG Postgres by default, optional external Redis/Postgres/secrets, web/API/model/celery components, autoscaling choices, and optional Craft Kubernetes sandboxes.

Render before installing:

```bash
helm dependency update deployment/helm/charts/onyx
helm template test-output deployment/helm/charts/onyx \
  --set auth.opensearch.values.opensearch_admin_password='StrongPassword123!'
```

Basic test install pattern for an ephemeral namespace:

```bash
helm install onyx deployment/helm/charts/onyx -n onyx --create-namespace \
  --set postgresql.primary.persistence.enabled=false \
  --set auth.opensearch.values.opensearch_admin_password='StrongPassword123!'

kubectl -n onyx port-forward service/onyx-nginx 8080:80
```

Confirm before uninstalling or deleting PVCs:

```bash
helm uninstall onyx -n onyx
kubectl -n onyx get pvc
```

Important Helm/Kubernetes facts:

- For chart upgrades from older 0.4.x releases, treat legacy Vespa removal/migration as a special case; do not run a blind `helm upgrade` if legacy Vespa resources remain.
- With bundled Redis enabled, the chart installs the Redis operator/subchart; no separate Redis CRD pre-step is needed for that path.
- The chart can provision Postgres through CloudNativePG. Set Postgres off and point config to an external DB when using managed Postgres.
- External Secrets Operator is not installed by the chart. Install ESO and define the SecretStore/ClusterSecretStore before enabling external secret rendering.
- Do not copy Docker Compose hostnames into Helm config. Names such as `api_server`, `inference_model_server`, and `cache` contain underscores and are invalid Kubernetes DNS labels. Let chart-computed service names stand.
- Set `DOMAIN` and `WEB_DOMAIN` deliberately for real Helm deployments; do not leave production values pointing at localhost.
- Craft Helm deployments require Kubernetes 1.33+ for restartable init sidecars and sandbox pod behavior.
- HPA is the default autoscaling engine; use KEDA only when the KEDA operator is installed and managed separately.

For chart validation when Helm/Python deps are installed, optional checks include chart rendering, chart-testing install against a local kind cluster, and targeted `helm template` guards for Craft Kubernetes version compatibility.
