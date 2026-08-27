# Install and Run Langflow

This reference covers local installation, source checkout startup, CLI command behavior, environment-variable precedence, and operational identity/secret setup for Langflow.

## Local Package Installation

Recommended local path:

```bash
uv pip install -U langflow
uv run langflow run
```

Langflow requires a supported Python version from the current project range, and `uv` is the recommended package manager for reproducible package installation and command execution. The default server listens on `http://127.0.0.1:7860` or `http://localhost:7860`, depending on the chosen host binding.

If `langflow` is deliberately installed globally or in the active environment's `PATH`, direct invocation is also valid:

```bash
langflow run
```

Prefer `uv run langflow ...` when the task is inside a project-specific environment, CI job, or temporary shell where direct `PATH` resolution might point to the wrong installation.

## Run from a Source Checkout

For a Langflow checkout used for development or validation:

```bash
make init
make run_cli
```

`make init` installs backend/frontend dependencies and pre-commit hooks. `make run_cli` builds and starts Langflow from source. For hot-reload development, run the backend and frontend separately:

```bash
make backend
make frontend
```

The backend runs on port `7860`; the Vite frontend development server runs on port `3000`. Use `LFX_DEV=1 make backend` to dynamically load all components while developing custom or built-in components. Use `LFX_DEV=openai,mistral make backend` to load only selected component modules for faster iteration.

## CLI Invocation and Precedence

The Langflow CLI is installed with the Python package. Key commands verified for this package family include:

- `langflow run`: start the server.
- `langflow superuser`: create a superuser with explicit `--username` and `--password`.
- `langflow api-key`: create an API key as a superuser.
- `langflow migration`: preview or apply database schema fixes.
- `langflow copy-db`: copy legacy/cache database files into the installation area when needed.
- `langflow lfx`: bridge to LFX commands when available.

Configuration precedence is:

1. CLI flags passed to `langflow run`.
2. Variables loaded from the `.env` file selected with `--env-file`.
3. System environment variables visible to the process.
4. Langflow defaults.

Example:

```bash
uv run langflow run --env-file .env --port 9000
```

If `.env` contains `LANGFLOW_PORT=7860`, the server still uses port `9000` because the CLI flag wins.

Boolean CLI flags have positive and negative forms:

```bash
uv run langflow run --remove-api-keys
uv run langflow run --no-remove-api-keys
uv run langflow run --backend-only
uv run langflow run --no-backend-only
```

## Common `langflow run` Options

Use CLI options for one-off startup behavior and `.env` for durable deployment configuration.

| CLI option | Environment equivalent | Use |
| --- | --- | --- |
| `--host` | `LANGFLOW_HOST` | Bind address. Use `127.0.0.1` for local-only; use `0.0.0.0` inside containers. |
| `--port` | `LANGFLOW_PORT` | HTTP port, default `7860`. |
| `--env-file` | n/a | Load a specific `.env` file. |
| `--backend-only` / `--no-backend-only` | `LANGFLOW_BACKEND_ONLY` | Start without the visual frontend for API-only use. |
| `--log-level` | `LANGFLOW_LOG_LEVEL` | `debug`, `info`, `warning`, `error`, or `critical`. |
| `--log-file` | `LANGFLOW_LOG_FILE` | File path for logs when file logging is desired. |
| `--workers` | `LANGFLOW_WORKERS` | Worker process count. Requires shared queue planning when greater than one. |
| `--worker-timeout` | `LANGFLOW_WORKER_TIMEOUT` | Worker timeout in seconds. |
| `--components-path` | `LANGFLOW_COMPONENTS_PATH` | Local custom component directory. |
| `--frontend-path` | `LANGFLOW_FRONTEND_PATH` | Custom built frontend assets for source/custom images. |
| `--max-file-size-upload` | `LANGFLOW_MAX_FILE_SIZE_UPLOAD` | Upload size limit in MB. |
| `--ssl-cert-file-path` | `LANGFLOW_SSL_CERT_FILE` | TLS certificate file for direct HTTPS. |
| `--ssl-key-file-path` | `LANGFLOW_SSL_KEY_FILE` | TLS private key file for direct HTTPS. |

## `.env` Template

Start with a minimal `.env` and add only variables the deployment needs:

```text
LANGFLOW_HOST=0.0.0.0
LANGFLOW_PORT=7860
LANGFLOW_CONFIG_DIR=/app/langflow
LANGFLOW_DATABASE_URL=postgresql://langflow:change-me@postgres:5432/langflow
LANGFLOW_AUTO_LOGIN=False
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=replace-with-a-strong-password
LANGFLOW_SECRET_KEY=replace-with-a-long-random-secret
LANGFLOW_LOG_LEVEL=info
LANGFLOW_REMOVE_API_KEYS=False
```

Use the bundled helper before starting:

```bash
python scripts/check_env_vars.py --env-file .env --context docker-compose
```

The helper catches unsupported names, malformed booleans/integers, common database URL mistakes, missing production secrets, and container host mismatches without importing Langflow.

## Authentication, API Keys, and Secrets

For shared, production, or internet-accessible deployments:

1. Set `LANGFLOW_AUTO_LOGIN=False`.
2. Set `LANGFLOW_SUPERUSER` and `LANGFLOW_SUPERUSER_PASSWORD` to non-default values.
3. Set `LANGFLOW_SECRET_KEY` to a long random value and keep it stable across restarts.
4. Start Langflow with the `.env` file.
5. Create API keys with a superuser account or with `langflow api-key` when the CLI is enabled and authenticated as expected.
6. Keep provider keys and API tokens out of flow JSON, images, logs, and committed `.env` files.

Useful command to generate a secret value locally:

```bash
python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
```

Do not rotate `LANGFLOW_SECRET_KEY` casually: changing it can invalidate encrypted credentials, sessions, and tokens. Plan rotation like any other production secret migration.

## Databases and Data Location

Without an explicit `LANGFLOW_DATABASE_URL`, local Langflow uses its default database location derived from the configuration/cache behavior. For durable operations, set both:

- `LANGFLOW_CONFIG_DIR`: durable directory for logs, storage, monitor data, generated secrets, and related runtime files.
- `LANGFLOW_DATABASE_URL`: database connection string, usually PostgreSQL for Compose/production.

SQLite is acceptable for local experimentation and single-user development. When using SQLite explicitly, prefer an absolute path:

```text
LANGFLOW_DATABASE_URL=sqlite:////var/lib/langflow/langflow.db
```

For PostgreSQL:

```text
LANGFLOW_DATABASE_URL=postgresql://user:password@postgres:5432/langflow
```

In Docker Compose, `postgres` should be the service name. `localhost` from inside the Langflow container points back to the Langflow container, not to the PostgreSQL service.

## Safe Migration and Upgrade Flow

Before upgrading Langflow or changing database backends:

1. Stop writes to the running service.
2. Back up the database and `LANGFLOW_CONFIG_DIR` volume/directory.
3. Record the current Langflow image/package version.
4. Run migration preview:

```bash
uv run langflow migration
```

5. Only after reviewing the preview and confirming the backup, apply fixes:

```bash
uv run langflow migration --fix
```

For Docker, run the migration command in a one-off container or through the running service image with the same environment and volumes attached.

## Moving from SQLite to PostgreSQL Without Losing Data

Use this as an operational plan rather than a single blind command:

1. Export critical flows from the UI/API or use a verified database backup.
2. Stop Langflow.
3. Back up the SQLite database file and the full `LANGFLOW_CONFIG_DIR`.
4. Start PostgreSQL with a persistent volume and create the target database/user.
5. Set `LANGFLOW_DATABASE_URL=postgresql://...` and keep `LANGFLOW_CONFIG_DIR` persistent.
6. Start Langflow and run migration preview/fix if required.
7. Re-import flows or run a controlled database migration strategy if preserving internal users/API keys is required.
8. Verify login, flow list, API key creation, and a simple flow execution before deleting the SQLite backup.

If API keys, users, and encrypted credentials must be preserved exactly, do not rely only on flow export/import. Preserve the database and secret key, and test the migration in a staging copy first.
