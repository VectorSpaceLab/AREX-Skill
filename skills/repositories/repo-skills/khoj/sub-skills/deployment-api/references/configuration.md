# Configuration and Deployment Variants

This reference covers Khoj server installation choices, environment variables, database configuration, domain/auth setup, model providers, and production process settings.

## Choose an Install Path

### Pip Local Server

Use this for a single-machine self-hosted server where the operator controls the Python environment.

Recommended shape:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install 'khoj[local]'
USE_EMBEDDED_DB=true khoj --anonymous-mode
```

Notes:

- The `local` extra provides embedded PostgreSQL support through `pgserver`.
- `--anonymous-mode` is appropriate only for personal local use or trusted private networks.
- First run may prompt for admin credentials and model setup unless `--non-interactive` and relevant env vars are supplied.
- Restart after first run or major model/provider changes so server state and defaults reload cleanly.

### Pip Production-Like Server

Use this when you want external PostgreSQL, authentication, or gunicorn/cloud integrations.

Typical shape:

```bash
python -m pip install 'khoj[prod]'
POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432 khoj --host 0.0.0.0 --port 42110 --non-interactive
```

Set secure admin, domain, database, and auth env vars before starting. Do not use anonymous mode for public or team deployments.

### Docker Compose Server

The compose deployment uses services for PostgreSQL with pgvector, optional Terrarium sandbox, optional SearxNG search, optional computer/operator service, and the Khoj server. The server binds host port `42110` to container port `42110`, mounts persistent config and model-cache volumes, and runs the server command with `--host 0.0.0.0 --port 42110 -vv --anonymous-mode --non-interactive` by default.

Core compose env vars include:

```bash
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=database
POSTGRES_PORT=5432
KHOJ_DJANGO_SECRET_KEY=change-me
KHOJ_DEBUG=False
KHOJ_ADMIN_EMAIL=username@example.com
KHOJ_ADMIN_PASSWORD=change-me
```

For a public or multi-user Docker deployment, remove `--anonymous-mode`, use strong secrets, configure auth, set domain variables, and use HTTPS or a secure reverse proxy.

### Image and Process Notes

- The standard Docker image installs the package, builds the web UI, collects static files, and uses the server module entrypoint directly.
- The production Dockerfile installs the `prod` extra and uses `gunicorn -c gunicorn-config.py src.khoj.main:app`.
- Gunicorn defaults bind to `0.0.0.0:42110`, `GUNICORN_WORKERS=6`, `GUNICORN_TIMEOUT=180`, `GUNICORN_GRACEFUL_TIMEOUT=90`, `GUNICORN_KEEP_ALIVE=60`, worker class `uvicorn.workers.UvicornWorker`, and stdout/stderr logging.

## CLI Flags

Use these in server commands, systemd units, compose `command`, or manual starts:

```bash
khoj --host 127.0.0.1 --port 42110 --anonymous-mode
khoj --host 0.0.0.0 --port 42110 --non-interactive
khoj --socket /tmp/uvicorn.sock --non-interactive
khoj --host 0.0.0.0 --port 42110 --sslcert /path/cert.pem --sslkey /path/key.pem
```

Important behavior:

- `--host` and `--port` control uvicorn only when not using `--socket`.
- `--socket` is intended for reverse-proxy deployments.
- `--sslcert` and `--sslkey` must both be present to enable SSL config and HTTPS redirect middleware.
- `--non-interactive` requires admin env vars on first run; otherwise admin creation cannot complete.
- `--version` is safe only through direct parser inspection; the console script can still import server code first.

## Database Configuration

Khoj uses Django PostgreSQL settings. Defaults are PostgreSQL on localhost with user/password `postgres/postgres` and database `khoj`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_DB` | `khoj` | Database name. |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host. In compose, this is `database`. |
| `POSTGRES_PORT` | `5432` | PostgreSQL port. Empty when embedded pgserver uses a Unix socket. |
| `POSTGRES_USER` | `postgres` | Database user. |
| `POSTGRES_PASSWORD` | `postgres` | Database password. |
| `USE_EMBEDDED_DB` | false | If true, starts pgserver and uses an embedded PostgreSQL instance. |
| `PGSERVER_DATA_DIR` | package-relative `pgserver_data` | Embedded PostgreSQL data directory. |

When `USE_EMBEDDED_DB=true`, Khoj tries to import `pgserver`, create/start the embedded database, ensure pgvector extension, create the configured database if missing, and point Django at the pgserver Unix socket. If this fails, the settings code logs an error and falls back toward standard PostgreSQL settings.

## Admin and First Run

Admin credentials are required for the Django admin panel at `/server/admin/` and for non-interactive first-run setup.

| Variable | Purpose |
| --- | --- |
| `KHOJ_ADMIN_EMAIL` | Admin email used during initial admin creation. |
| `KHOJ_ADMIN_PASSWORD` | Admin password used during initial admin creation. |
| `KHOJ_DJANGO_SECRET_KEY` | Django and session secret; must be unique and strong outside throwaway local use. |
| `KHOJ_DEBUG` | Enables debug behavior when true. Keep false in production. |

If `--non-interactive` is used and either admin email or password is absent on first run, initialization reports that admin user creation cannot complete. For interactive local starts, Khoj can prompt for missing values.

## Domains, CSRF, Cookies, CORS, and HTTPS

Relevant env vars:

| Variable | Behavior |
| --- | --- |
| `KHOJ_DOMAIN` | External domain or IP without scheme. Used for CSRF trusted origins, cookie domain, and CORS custom origins. |
| `KHOJ_ALLOWED_DOMAIN` | Internal service host accepted by Django `ALLOWED_HOSTS`; defaults to `KHOJ_DOMAIN`. Set this for reverse proxies/load balancers that reach Khoj by an internal name. |
| `KHOJ_NO_HTTPS` | If true, disables secure cookies and uses `http` origins; useful only for local/private HTTP deployments. |

Settings behavior:

- Without `KHOJ_DOMAIN`, session and CSRF cookie domains default to `localhost`.
- With `KHOJ_DOMAIN`, cookie domains are set to that value, and secure cookies are enabled unless `KHOJ_NO_HTTPS=true`.
- CSRF trusted origins include `https://*.KHOJ_DOMAIN`, `https://KHOJ_DOMAIN`, `http://*.KHOJ_DOMAIN`, and `http://KHOJ_DOMAIN`.
- Allowed hosts include subdomains of `KHOJ_ALLOWED_DOMAIN`, `localhost`, `127.0.0.1`, IPv6 localhost, and the exact allowed domain.
- FastAPI CORS includes localhost/app origins plus `http(s)://KHOJ_DOMAIN` and wildcard port variants.

Common local-private remote pattern:

```bash
KHOJ_DOMAIN=192.168.0.104 KHOJ_NO_HTTPS=true khoj --host 0.0.0.0 --port 42110
```

Common reverse-proxy pattern:

```bash
KHOJ_DOMAIN=khoj.example.com KHOJ_ALLOWED_DOMAIN=server khoj --host 0.0.0.0 --port 42110 --non-interactive
```

## Authentication Modes

### Anonymous Mode

`--anonymous-mode` lets requests authenticate as the default user without login. Use only for single-user, local, or trusted private deployments. It should be removed for multi-user or public deployments.

### Magic Link Authentication

For email magic links, set:

```bash
RESEND_API_KEY=...
RESEND_EMAIL=login@example.com
```

Without Resend, magic links can be generated manually from the admin panel for user records, but the operator must deliver links out of band.

### Google OAuth

For Google OAuth, use the production-capable package/image path and set:

```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Also configure authorized origins and redirect URIs in the Google Cloud project for the deployed domain.

## Model Provider Configuration

First-run initialization can create default model settings from env vars, and the admin panel can add or edit model settings later.

### Commercial Providers

| Provider | Env var | Admin model type | Notes |
| --- | --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | `OpenAI` | Use OpenAI model names such as `gpt-4o`; set vision only for supported OpenAI vision models. |
| Anthropic | `ANTHROPIC_API_KEY` | `Anthropic` | Do not set an API base URL for normal Anthropic API use. |
| Gemini | `GEMINI_API_KEY` | `Google` | Use Google/Gemini model names and match prompt limits. |

`KHOJ_DEFAULT_CHAT_MODEL` can select a default model name during initialization when it matches available model setup.

### OpenAI-Compatible Local or Proxy Providers

Set an AI Model API with an API base URL and a placeholder API key if the provider does not require one. Then create a Chat Model with model type `Openai`, attach that AI Model API, set the provider's model name, and set a realistic max prompt size.

Examples:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1/
OPENAI_API_KEY=placeholder
KHOJ_DEFAULT_CHAT_MODEL=qwen3
```

For Docker connecting to a host-local provider, use a host-gateway URL such as `http://host.docker.internal:11434/v1/` when supported by the Docker environment.

Provider notes:

- Ollama exposes an OpenAI-compatible API and works well with `OPENAI_BASE_URL` on first run or an admin-created AI Model API later.
- LiteLLM can proxy many providers through an OpenAI-compatible API; its proxy should be started with parameters that avoid forwarding unsupported model parameters when needed.
- LM Studio support is currently fragile/unsupported because Khoj uses JSON mode extensively and LM Studio compatibility has changed; prefer Ollama, vLLM, llama.cpp server, LiteLLM, or another OpenAI-compatible server that supports Khoj's structured-output needs.
- Vertex AI configuration uses an AI Model API whose key is a base64-encoded service account JSON and whose base URL is `https://{region}-aiplatform.googleapis.com/v1/projects/{project}`; Chat Model type should match the hosted model family, such as `Anthropic` or `Google`.

## Optional Service Integrations

Only configure these if the user asks for the feature:

| Variable | Enables |
| --- | --- |
| `KHOJ_TERRARIUM_URL` | Self-hosted code execution sandbox URL. |
| `E2B_API_KEY` | Remote E2B code sandbox. |
| `KHOJ_SEARXNG_URL` | Self-hosted SearxNG web search. |
| `SERPER_DEV_API_KEY` | Serper web search. |
| `OLOSTEP_API_KEY` | Olostep webpage reading. |
| `FIRECRAWL_API_KEY` | Firecrawl web search/read. |
| `EXA_API_KEY` | Exa search. |
| `KHOJ_OPERATOR_ENABLED` | Computer/operator feature when the corresponding service/runtime is available. |
| `KHOJ_TELEMETRY_DISABLE` | Disable telemetry when true. |

Route detailed feature behavior to the sibling sub-skills responsible for chat, tools, automations, and content.

## Minimal Configuration Recipes

### Local Anonymous Embedded DB with OpenAI-Compatible Local Provider

Use this for a personal machine with a local provider such as Ollama:

```bash
export USE_EMBEDDED_DB=true
export KHOJ_DJANGO_SECRET_KEY='replace-with-a-long-random-secret'
export KHOJ_ADMIN_EMAIL='admin@example.com'
export KHOJ_ADMIN_PASSWORD='replace-with-a-strong-password'
export OPENAI_BASE_URL='http://localhost:11434/v1/'
export OPENAI_API_KEY='placeholder'
export KHOJ_DEFAULT_CHAT_MODEL='qwen3'
khoj --anonymous-mode --non-interactive
```

Explain to the user that anonymous mode removes login protection, so it is suitable only for local/private access.

### Docker Compose with Host Ollama

Set the server environment to include:

```bash
OPENAI_BASE_URL=http://host.docker.internal:11434/v1/
OPENAI_API_KEY=placeholder
KHOJ_DEFAULT_CHAT_MODEL=qwen3
```

Keep `extra_hosts: host.docker.internal:host-gateway` when the Docker runtime needs it. Restart the server after changing these values.

### Authenticated Remote Server Behind Reverse Proxy

```bash
KHOJ_DOMAIN=khoj.example.com
KHOJ_ALLOWED_DOMAIN=server
KHOJ_DJANGO_SECRET_KEY=replace-with-long-random-secret
KHOJ_ADMIN_EMAIL=admin@example.com
KHOJ_ADMIN_PASSWORD=replace-with-strong-password
RESEND_API_KEY=...
RESEND_EMAIL=login@example.com
```

Remove `--anonymous-mode`, keep HTTPS at the proxy, and set `KHOJ_NO_HTTPS=true` only when the Khoj process itself receives HTTP from a trusted internal proxy and cookie behavior requires it.
