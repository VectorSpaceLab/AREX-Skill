# Deployment and API Troubleshooting

Use this guide to diagnose common Khoj server deployment failures without accidentally importing `khoj.main`, starting the server, mutating a database, or depending on source-checkout files.

## `khoj --help` Fails Before Showing Help

Symptom examples:

- `khoj --help` raises a PostgreSQL `OperationalError`.
- Help/version commands run migrations or collect static files.
- The failure happens before argparse output appears.

Root cause:

- The console script points to `khoj.main:run`.
- Loading that entrypoint imports `khoj.main`.
- `khoj.main` initializes Django, runs `migrate --noinput`, and runs `collectstatic --noinput` at import time before `run()` calls `khoj.utils.cli.cli`.
- If PostgreSQL or settings are unavailable, a parser-looking command can fail as a server startup command.

Safe response:

```bash
python skills/khoj/sub-skills/deployment-api/scripts/inspect_cli.py --args -- --help
python skills/khoj/sub-skills/deployment-api/scripts/inspect_cli.py --args -- --host 0.0.0.0 --port 42110 -vv --anonymous-mode --non-interactive
```

If working outside this generated skill tree, reproduce the safe behavior by importing only `khoj.utils.cli.cli`, not `khoj` and not `khoj.main`.

## PostgreSQL Connection Refused

Symptoms:

- Startup fails during import or migrations with `connection refused`.
- Host is `localhost` but no local PostgreSQL server is running.
- Docker server cannot connect to `localhost:5432` even though the compose database exists.

Checks:

1. Identify whether the deployment expects external PostgreSQL or embedded pgserver.
2. For external PostgreSQL, verify `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.
3. In Docker Compose, `POSTGRES_HOST` should be the database service name, usually `database`, not `localhost`.
4. Confirm PostgreSQL has pgvector available; the compose image uses a pgvector-enabled PostgreSQL image.
5. Confirm the server waits for database health in compose or equivalent system orchestration.

Fix patterns:

```bash
# Local embedded DB path, requires khoj[local]
USE_EMBEDDED_DB=true khoj --anonymous-mode

# Docker compose-style external DB
POSTGRES_HOST=database POSTGRES_PORT=5432 POSTGRES_DB=postgres POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres khoj --host 0.0.0.0 --port 42110
```

If `USE_EMBEDDED_DB=true` logs that embedded initialization failed, check that the package was installed with the local extra and that the embedded data directory is writable.

## Non-Interactive First Run Cannot Create Admin

Symptoms:

- Startup with `--non-interactive` reports admin user cannot be created.
- Docker starts but admin login credentials are missing or unknown.

Root cause:

- First-run initialization needs an admin email and password.
- In non-interactive mode, Khoj cannot prompt, so `KHOJ_ADMIN_EMAIL` and `KHOJ_ADMIN_PASSWORD` must be set.

Fix:

```bash
export KHOJ_ADMIN_EMAIL=admin@example.com
export KHOJ_ADMIN_PASSWORD='replace-with-strong-password'
export KHOJ_DJANGO_SECRET_KEY='replace-with-long-random-secret'
khoj --non-interactive
```

For Docker, set these in the server service environment. Restart after first-run setup so all settings are loaded consistently.

## CSRF, Disallowed Host, Cookie, or Admin Login Failures

Symptoms:

- `CSRF verification failed` in the admin panel.
- `Bad Request (400)` or `DisallowedHost` when using an IP/custom domain.
- Login appears to succeed but cookies are not set or are not sent.
- Works at `localhost` but fails at `127.0.0.1`, custom domain, reverse proxy, or Tailscale address.

Configuration model:

- `KHOJ_DOMAIN` is the externally visible domain or IP without `http://` or `https://`.
- `KHOJ_ALLOWED_DOMAIN` is the internal host accepted by Django, useful behind a reverse proxy or load balancer; it defaults to `KHOJ_DOMAIN`.
- `KHOJ_NO_HTTPS=true` disables secure cookies and switches CORS custom origins to `http`, suitable only for local/private HTTP access.
- Without `KHOJ_DOMAIN`, cookie domains default to `localhost`.

Fix patterns:

```bash
# Private LAN over HTTP
KHOJ_DOMAIN=192.168.0.104 KHOJ_NO_HTTPS=true khoj --host 0.0.0.0 --port 42110

# Reverse proxy reaches service by internal DNS name
KHOJ_DOMAIN=khoj.example.com KHOJ_ALLOWED_DOMAIN=server khoj --host 0.0.0.0 --port 42110
```

Diagnostic steps:

1. Remove URL schemes from `KHOJ_DOMAIN` and `KHOJ_ALLOWED_DOMAIN`; use `khoj.example.com`, not `https://khoj.example.com`.
2. Match the browser host to `KHOJ_DOMAIN`.
3. If using HTTP, set `KHOJ_NO_HTTPS=true` and understand the security tradeoff.
4. If behind a reverse proxy, set `KHOJ_ALLOWED_DOMAIN` to the host header or internal service name that reaches Khoj.
5. Prefer `localhost` for local admin access when cookie domain defaults are in use.

## Model Provider Setup Mismatches

### OpenAI

Symptoms:

- Chat model exists but requests fail with auth errors.
- Vision options are enabled for a model/provider that does not support them.

Fix:

- Set `OPENAI_API_KEY` or create an admin `AI Model API` with a valid OpenAI key.
- Use model type `OpenAI` and a valid OpenAI model name.
- Enable vision only for supported OpenAI vision-capable models.

### Anthropic

Symptoms:

- Claude model fails even though an API key is present.
- A base URL was copied from an OpenAI-compatible setup.

Fix:

- Set `ANTHROPIC_API_KEY` or create an admin `AI Model API` with the Anthropic key.
- Use model type `Anthropic`.
- Do not configure an API base URL for normal Anthropic API use.

### Gemini / Google

Symptoms:

- Gemini model fails with auth or unknown model errors.
- Model type is incorrectly set to OpenAI.

Fix:

- Set `GEMINI_API_KEY` or create a Google AI Model API.
- Use model type `Google`.
- Use a current Gemini model name and a realistic prompt limit.

### Ollama or Other OpenAI-Compatible Local Providers

Symptoms:

- Docker cannot reach `localhost:11434`.
- Khoj starts before the local provider is running.
- Model name exists in provider but not in Khoj admin settings.

Fix:

```bash
# Native host start
OPENAI_BASE_URL=http://localhost:11434/v1/ OPENAI_API_KEY=placeholder KHOJ_DEFAULT_CHAT_MODEL=qwen3 khoj --anonymous-mode

# Docker server reaching provider on host
OPENAI_BASE_URL=http://host.docker.internal:11434/v1/ OPENAI_API_KEY=placeholder KHOJ_DEFAULT_CHAT_MODEL=qwen3
```

If first-run discovery did not add the model, add an admin `AI Model API` with the base URL and placeholder key, then add a `Chat Model` with model type `Openai`, the exact provider model name, the AI Model API, and a max prompt size.

### LiteLLM

Symptoms:

- Proxy returns errors about unsupported parameters.
- A non-OpenAI provider is exposed through LiteLLM but Khoj model type is not OpenAI.

Fix:

- Start LiteLLM as an OpenAI-compatible proxy and drop unsupported parameters where needed.
- In Khoj admin, use model type `Openai`, attach an AI Model API pointing to the LiteLLM proxy URL, and set a compatible model name.

### LM Studio

Symptoms:

- JSON mode or structured-output errors.
- The provider previously worked but now fails after LM Studio API changes.

Fix:

- Treat LM Studio as currently unsupported/fragile for Khoj because Khoj uses JSON mode extensively.
- Prefer Ollama, vLLM, llama.cpp server, LiteLLM, or another OpenAI-compatible provider that supports the structured-output behavior Khoj needs.

### GCP Vertex AI

Symptoms:

- Permission denied, region errors, model not found, or authentication failures.

Fix:

- Ensure the service account has Vertex AI permissions and the Vertex AI API is enabled.
- Base64-encode the service account JSON as the AI Model API key.
- Set the AI Model API base URL to `https://{region}-aiplatform.googleapis.com/v1/projects/{project}`.
- Use model type `Anthropic` or `Google` according to the hosted model family.
- Match model region and max prompt size to the selected Vertex model.

## Static Files or Web UI Problems

Symptoms:

- Web app loads without styles/assets.
- `/_next` assets 404.
- Startup fails during static collection.

Relevant behavior:

- `khoj.main` runs `collectstatic --noinput` during import.
- The app mounts `/static` from the package static directory.
- Middleware rewrites `/_next...` paths to `/static/_next...`.
- Docker images build the web app and copy built files into the package before collecting static files.

Checks:

1. Confirm the installed package/image includes built web assets.
2. Confirm the process user can create/write the static directory during startup if missing.
3. In custom images, build the web UI before server runtime collection.
4. Behind a proxy, do not strip or rewrite `/static` and `/_next` in a way that bypasses the app middleware.

## Docker Container Exits with `Killed`

Likely cause:

- Docker ran out of memory while building/installing dependencies, loading models, or running the server.

Fixes:

- Increase memory allocated to Docker.
- Use the published image instead of building locally if appropriate.
- Avoid loading large local models on memory-constrained hosts.
- Prefer CPU wheels and avoid unnecessary GPU/CUDA packages when building images for CPU-only deployment.

## Pip Dependency Conflicts

Symptoms:

- Installing Khoj into an existing Python environment creates incompatible dependency versions.
- `pip check` reports conflicts after install.

Fixes:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'khoj[local]'
python -m pip check
```

Use a dedicated virtual environment or pipx-style isolated environment instead of a shared system Python.

## Tokenizers or Rust Build Failures

Symptoms:

- Installation fails while building `tokenizers` or another Rust-backed dependency.
- Errors mention missing Rust compiler, cargo, or build backend.

Fixes:

- Upgrade pip first so prebuilt wheels are used when available.
- Install Rust tooling when a wheel is unavailable for the platform.
- Use a supported Python version (`>=3.10,<3.13`).
- On platforms with local model/GPU extras, set the provider-specific build flags only when needed.

## Native API Smoke-Test Expectations

The repository tests establish useful expectations for deployment checks:

- `/api/search` without auth returns forbidden when not in anonymous mode.
- Invalid bearer tokens return forbidden.
- Invalid content type parameters return validation errors.
- In anonymous mode, configured route tests can access authenticated routes through the default user.
- `/api/content/types` returns `['all']` when no content config exists in anonymous mode.

Keep these as behavioral orientation, not as a requirement to run the test suite during deployment troubleshooting.

## Escalation Checklist

Before suggesting invasive changes, collect:

- Install method: pip, Docker Compose, production image, custom image, or gunicorn.
- Full command flags, with secrets redacted.
- Relevant env vars, with secrets redacted.
- Whether the failure happens during parser inspection, import, migrations, collectstatic, initialization prompts, route setup, provider call, or first API request.
- Whether the server is anonymous, magic-link/OAuth authenticated, behind a reverse proxy, or exposed directly.
- Database mode: external PostgreSQL vs `USE_EMBEDDED_DB=true`.
