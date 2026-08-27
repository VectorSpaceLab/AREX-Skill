# Argilla server deployment guide

This reference distills Argilla 2.8.0dev0 server deployment behavior into self-contained operating guidance. Use it to choose and adapt a deployment path without relying on the source repository checkout.

## Deployment decision matrix

| Path | Use when | What it creates/needs | Safety gate |
| --- | --- | --- | --- |
| Hugging Face Spaces UI/template | Fast hosted Argilla for testing or teams that already use HF accounts/OAuth. | A Docker Space, HF OAuth sign-in, a default `argilla` workspace, optional paid persistent storage. | Requires HF account/settings changes and may lose data without persistent storage. |
| Python SDK `Argilla.deploy_on_spaces` | A Python workflow should create or resume a HF Space and return an authenticated SDK client. | Duplicates the Argilla Space template, creates/uses a Space repo, sets `API_KEY` and `WORKSPACE` secrets, waits for build, and returns `rg.Argilla(...)`. | Network/API action; require an HF token and explicit user approval. |
| Docker Compose | Local/server deployment with controlled PostgreSQL, Elasticsearch, Redis, server, worker, and volumes. | Five long-running services plus persistent volumes. | Validate configuration first; replace sample credentials; start only when user intentionally requests it. |
| Direct Python package/server | Advanced development or managed host where services are provisioned separately. | `argilla-server`, search engine, Redis, DB, migrations, user creation, Uvicorn. | Requires explicit service prerequisites and migration/user creation plan. |
| Kubernetes/Helm pattern | Cluster deployment with ingress, persistence, worker, Redis, and Elasticsearch/operator or external services. | Deployments, service, ingress, PVC, worker, search, Redis. | Cluster mutation; use Secrets for credentials and review storage/search/ingress values first. |

## Hugging Face Spaces

### Quick hosted path

A Space deployment is the fastest route when the user accepts a hosted Docker app and HF account/OAuth semantics. For non-test usage, request persistent storage. Without persistent storage, Space restarts caused by maintenance, inactivity, or settings changes can reset datasets, users, workspaces, and local configuration.

Operational notes:

- A default workspace named `argilla` is created for the Space workflow.
- Default HF OAuth lets users who can access the Space sign in and, by default, join as annotators for allowed workspaces.
- For organization Spaces, use private visibility when access must be limited to organization members.
- `USERNAME` and `PASSWORD` secrets are mainly useful if OAuth is disabled or if organization ownership needs an explicit username. For personal Spaces with HF OAuth, the creator can normally sign in with Hugging Face.
- Set `ARGILLA_SHOW_HUGGINGFACE_SPACE_PERSISTENT_STORAGE_WARNING=false` only if the user intentionally accepts the storage risk.
- Set `HF_HUB_DISABLE_TELEMETRY=1` or `HF_HUB_OFFLINE=1` before server launch when telemetry must be disabled.

### Python SDK deployment

Use this only when the user has authorized a Hugging Face API operation:

```python
import argilla as rg

client = rg.Argilla.deploy_on_spaces(
    api_key="replace-with-8-or-more-characters",
    repo_name="argilla",
    org_name=None,              # set to an HF organization when needed
    hf_token=None,              # or pass an explicit HF token
    space_storage="small",      # recommended beyond throwaway tests
    space_hardware="cpu-basic",
    private=False,
)
```

Verified 2.8.0dev0 behavior:

- `api_key` must be at least 8 characters.
- The method obtains or prompts for an HF token, creates/uses `<org_or_user>/<repo_name>`, duplicates the Argilla Space template if missing, creates a Docker Space repo, waits while the Space is building, then returns an authenticated `rg.Argilla` client.
- If the Space already exists and is stopped, it restarts the Space and warns that the supplied API key may differ from the server's stored API key.
- When `private=True`, the returned SDK client includes `headers={"Authorization": "Bearer <hf_token>"}`. That HF token header is separate from the Argilla API key.

For an already-created private Space, connect with both credentials:

```python
import argilla as rg

client = rg.Argilla(
    api_url="https://your-user-or-org-your-space.hf.space/",
    api_key="argilla-api-key-from-the-space",
    headers={"Authorization": "Bearer <hf-token-with-space-access>"},
)
```

## Local Docker Compose

Use the bundled [Compose template](../scripts/docker-compose.argilla.local.yaml) as a local-only starting point. It includes profiles so simply opening the file does not start anything. Suggested workflow:

```bash
# Config validation only; no containers should be started by this command.
docker compose -f scripts/docker-compose.argilla.local.yaml config

# Intentional local start after replacing sample credentials and reviewing volumes.
docker compose --profile local-argilla -f scripts/docker-compose.argilla.local.yaml up -d

# Inspect logs if startup is slow or fails.
docker compose --profile local-argilla -f scripts/docker-compose.argilla.local.yaml logs -f argilla worker elasticsearch postgres redis
```

Service stack:

| Service | Role | Key settings |
| --- | --- | --- |
| `argilla` | Server/UI/API on port 6900. | `ARGILLA_HOME_PATH`, `ARGILLA_DATABASE_URL`, `ARGILLA_ELASTICSEARCH`, `ARGILLA_REDIS_URL`, owner credentials, telemetry flags, optional `REINDEX_DATASETS`, `UVICORN_APP`. |
| `worker` | RQ background workers for jobs. | Same DB/search/Redis/home env as server; command `python -m argilla_server worker --num-workers ...`. |
| `postgres` | Persistent relational DB for server state. | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, volume. |
| `elasticsearch` | Search/vector index backend. | Elasticsearch 8.x single-node, security disabled for local sample, persistent data volume. |
| `redis` | Background job queue backend. | `ARGILLA_REDIS_URL` must match server/worker. |

For quick local tests, sample credentials are fine only on a private development machine. For anything shared, replace `USERNAME`, `PASSWORD`, `API_KEY`, and `ARGILLA_AUTH_SECRET_KEY`, and avoid exposing port 6900 without TLS/proxy controls.

## Direct Python server package

Use this when the host has services managed outside Docker. The server package exposes the module command `python -m argilla_server`.

Minimum service prerequisites:

1. Python environment with `argilla-server` installed. If using PostgreSQL from a pip install, ensure the async PostgreSQL driver support is installed.
2. Search engine reachable at `ARGILLA_ELASTICSEARCH` with `ARGILLA_SEARCH_ENGINE=elasticsearch` or `opensearch`.
3. Redis reachable at `ARGILLA_REDIS_URL`.
4. Database URL set through `ARGILLA_DATABASE_URL`; SQLite is default but PostgreSQL is recommended for shared service deployments.
5. Stable `ARGILLA_AUTH_SECRET_KEY` for any multi-worker/multi-instance deployment.

Typical explicit sequence:

```bash
export ARGILLA_HOME_PATH=/srv/argilla
export ARGILLA_DATABASE_URL='postgresql+asyncpg://argilla:replace-me@db.example.internal:5432/argilla'
export ARGILLA_SEARCH_ENGINE=elasticsearch
export ARGILLA_ELASTICSEARCH='http://search.example.internal:9200'
export ARGILLA_REDIS_URL='redis://redis.example.internal:6379/0'
export ARGILLA_AUTH_SECRET_KEY='replace-with-a-stable-secret'

python -m argilla_server database migrate
python -m argilla_server database users create \
  --first-name Admin --username admin --role owner \
  --password 'replace-with-strong-password' --api-key 'replace-with-strong-api-key' \
  --workspace default
python -m argilla_server start --host 0.0.0.0 --port 6900
```

Run workers separately when import/export/webhook/background jobs are needed:

```bash
python -m argilla_server worker --num-workers 2
```

## Kubernetes/Helm-style deployment notes

The selected Kubernetes pattern uses the same server image and environment variables as Docker Compose, plus a worker deployment.

Important values to model in a chart or manifest:

- Server image: `argilla/argilla-server:<tag>`.
- `ARGILLA_AUTH_SECRET_KEY`: store in a Kubernetes Secret, not a plain values file.
- `USERNAME`, `PASSWORD`, `API_KEY`: owner bootstrap values; store as Secrets and rotate for production.
- Persistence: mount `ARGILLA_HOME_PATH` (for example `/data`) to a PVC when using SQLite, Space/server IDs, or other local state. Prefer external PostgreSQL for shared/HA use.
- Search: either deploy Elasticsearch 8.x/OpenSearch 2.x in-cluster or configure an external endpoint with `ARGILLA_ELASTICSEARCH`, `ARGILLA_SEARCH_ENGINE`, TLS/CA settings, and resource requests.
- Redis: deploy standalone Redis or point `ARGILLA_REDIS_URL` and `ARGILLA_REDIS_USE_CLUSTER` to an external Redis/cluster.
- Worker: use `python -m argilla_server worker --num-workers ${BACKGROUND_NUM_WORKERS}` with the same DB/search/Redis/home environment as the server.
- Ingress/proxy: align public path, `ARGILLA_BASE_URL`, TLS, OAuth redirect URI, and `X-Forwarded-*` headers.

## Reverse proxy and base path

If Argilla is exposed under a prefix such as `https://example.org/argilla`, set:

```bash
export ARGILLA_BASE_URL=/argilla
```

Proxy requirements:

- Forward traffic from the external prefix to the Argilla backend on port 6900.
- Preserve `Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` headers where possible.
- Keep `ARGILLA_BASE_URL` and the proxy strip/preserve-prefix behavior aligned; mismatch causes broken static assets, API paths, OAuth callbacks, or SDK `api_url` failures.
- Configure OAuth redirect URIs using the externally visible URL plus `/oauth/<provider-name>/callback`.
