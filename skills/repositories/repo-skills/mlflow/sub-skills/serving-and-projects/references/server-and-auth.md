# Server And Auth Operations

## Choosing A Tracking Server Shape

Start by deciding whether the task is local development, team self-hosting, artifact proxying, or auth/RBAC administration.

- Local trial: `mlflow server` uses a local SQLite-backed default unless an existing file store is detected. Keep host defaulted to localhost.
- Shared team server: use a SQLAlchemy backend store, explicit artifact root or proxied artifact destination, and `--host 0.0.0.0` only with explicit allowed hosts and CORS origins.
- Artifact proxy only: `--artifacts-only` serves artifact endpoints and disables tracking operations; pair with `--artifacts-destination` and a real tracking server elsewhere.
- Development server: `--dev` enables reload/debug for the tracking server only. The full repo frontend/backend dev workflow is separate and described in `projects-and-deployments.md`.

Common baseline patterns:

```bash
# Local-only process, persistent local DB in the working directory
mlflow server --host 127.0.0.1 --port 5000

# Shared SQL backend with server-proxied artifacts
mlflow server \
  --backend-store-uri postgresql://USER:PASSWORD@HOST:5432/DB \
  --artifacts-destination s3://BUCKET/PREFIX \
  --host 0.0.0.0 \
  --allowed-hosts mlflow.example.com \
  --cors-allowed-origins https://notebook.example.com
```

Do not put real credentials in reusable snippets. Ask the user for secret handling and prefer environment variables or secret managers.

## Backend Store, Registry Store, And Artifact Root

- `--backend-store-uri` stores experiments, runs, metrics, params, tags, and related tracking metadata. Prefer SQLAlchemy URIs such as SQLite/PostgreSQL/MySQL for MLflow 3; filesystem URIs are legacy maintenance-mode behavior.
- `--registry-store-uri` stores registered models; if omitted, it follows the backend store URI.
- `--read-replica-backend-store-uri` routes read operations to a replica and writes to the primary. MLflow does not provide automatic failover to the primary if the read replica is unavailable.
- `--default-artifact-root` applies to new experiments only; it does not rewrite existing experiment artifact locations.
- `--serve-artifacts` proxies artifacts through the tracking server. With a SQL backend and no explicit artifact root, MLflow defaults to a proxied `mlflow-artifacts:/` style destination when artifact serving is enabled.
- `--artifacts-destination` is the object store or filesystem destination behind the artifact proxy.

When diagnosing artifact issues, compare all three locations: tracking URI, experiment artifact location, and server artifact destination. A model or run created before an artifact-root change may still point to the old URI.

## Security Middleware

MLflow tracking server security middleware is enabled by default. It protects against host-header/DNS rebinding, CORS abuse, and clickjacking.

Important defaults and options:

- Default allowed hosts include localhost and private IP ranges for development convenience.
- Default allowed origins include localhost origins.
- Use `--allowed-hosts` for public DNS names, private hostnames, reverse proxy host headers, Docker service names, or load balancer hostnames.
- Use `--cors-allowed-origins` for browser clients such as notebooks or custom UIs.
- Use `--x-frame-options DENY` or `SAMEORIGIN` unless iframe embedding is intentionally required.
- Avoid `--allowed-hosts "*"`, `--cors-allowed-origins "*"`, and `--disable-security-middleware` outside isolated local testing.

If a server is reachable by IP/hostname but API/UI requests fail, check host header and origin configuration before assuming the backend store is broken.

## Basic Auth App

MLflow basic HTTP auth requires installing auth extras and running the tracking server with `--app-name basic-auth`.

Operational checklist:

1. Install the auth extra in the runtime environment: `pip install 'mlflow[auth]'`.
2. Set a stable `MLFLOW_FLASK_SERVER_SECRET_KEY` before server startup; all replicas must share the same value.
3. Use a SQL backend suitable for auth persistence.
4. Start the server with `mlflow server --app-name basic-auth ...`.
5. Manage users, roles, and permissions through the documented auth Python/REST APIs or admin UI.

Basic auth is for remote tracking-server access where clients communicate through REST APIs. Restarting without `--app-name basic-auth` disables enforcement but does not erase persisted users/permissions.

## RBAC And Resource Coverage

Current auth docs describe role-based permissions including `READ`, `USE`, `EDIT`, `MANAGE`, and `NO_PERMISSIONS`. Covered resource classes include experiments, registered models, prompts, scorers, and AI Gateway resources such as secrets, endpoints, and model definitions. Prompt permissions are distinct from registered-model permissions even when prompt and model names share the registry wire surface.

For detailed experiment/run/model semantics, route to `tracking-and-registry`; use this sub-skill only to stand up or diagnose auth-enabled server operation.

## Database Migrations

Migrations are not safe probes. Before running any DB migration command:

- Confirm whether the URI targets tracking metadata, registry metadata, auth metadata, or a file-store migration.
- Require a backup or snapshot for shared databases.
- Confirm MLflow version compatibility and planned rollback.
- Run against a staging copy first when possible.
- Record the exact revision target, usually `head`.

Auth DB upgrade shape:

```bash
mlflow server --app-name basic-auth ...
# Auth DB migrations may be exposed through the auth DB command group in MLflow internals.
# Only run the auth DB upgrade command with the intended auth database URI and revision.
```

Tracking DB migrations and file-store-to-DB migrations can alter persistent metadata. Do not infer a database URI from logs or shell history; ask the user for the target.

## Databricks Proxy Development Caveats

When the local MLflow dev server proxies to Databricks, environment variables must be set consistently before starting the dev process:

```bash
export DATABRICKS_HOST="https://your-workspace.example"
export DATABRICKS_TOKEN="..."
export MLFLOW_TRACKING_URI="databricks"
export MLFLOW_REGISTRY_URI="databricks-uc"
```

Keep token values out of skill content, logs, and bug reports. If the registry URI is omitted, model registry requests may not route to Unity Catalog as expected. If variables are exported after server startup, restart the process.
