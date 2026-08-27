# Server Startup and API Surface

This reference summarizes how the Khoj Python server starts, how to validate CLI parsing safely, and how the main REST route families are mounted. It is self-contained for deployment/API tasks and does not require reading repository files.

## Runtime Shape

Khoj is a Python package exposing the console script `khoj = khoj.main:run`. The server combines FastAPI for API routes and web routing with Django for settings, database models, admin UI, sessions, auth, migrations, and static files.

Key runtime facts:

- Package metadata requires Python `>=3.10,<3.13`.
- Core runtime dependencies include FastAPI, uvicorn, Django, pgvector/psycopg2, sentence-transformers, torch, transformers, OpenAI/Anthropic/Gemini clients, APScheduler, and content parsers.
- Optional `local` install support adds embedded PostgreSQL through `pgserver`.
- Optional `prod` install support adds gunicorn plus cloud/production integrations.
- The console script imports `khoj.main` before calling `run()`, so importing the console entrypoint is not parser-only.

## Startup Lifecycle

When `khoj.main` is imported, module-level initialization happens before `run()` parses CLI flags:

1. Sets `DJANGO_SETTINGS_MODULE` to `khoj.app.settings` if it is unset.
2. Calls `django.setup()`.
3. Runs Django migrations with `migrate --noinput`.
4. Runs `collectstatic --noinput`.
5. Creates the FastAPI app, configures CORS origins from `KHOJ_DOMAIN` and `KHOJ_NO_HTTPS`, and prepares the Django ASGI app.

When `run()` executes:

1. Sets `TOKENIZERS_PARALLELISM=false`.
2. Parses command-line flags with `khoj.utils.cli.cli`.
3. Stores log path, verbosity, host, port, SSL files, anonymous mode, and version in shared state.
4. Runs first-time initialization; interactive mode can prompt for admin and model setup, while `--non-interactive` requires admin env vars.
5. Creates the log directory and attaches a file logger.
6. Starts recurring scheduler coordination backed by database process locks.
7. Calls route and middleware configuration.
8. Mounts Django at `/server` and static files at `/static`.
9. Initializes model/search server state.
10. Starts uvicorn unless the process is being loaded by gunicorn.

Gunicorn imports `src.khoj.main:app`; when `gunicorn` is present in `sys.modules`, `khoj.main` runs server initialization with `should_start_server=False` and registers scheduler shutdown through `atexit`.

## CLI Parser Facts

`khoj.utils.cli.cli(args=None)` is the safe parser entrypoint. It imports only the parser module and does not initialize Django or start migrations. It uses `parse_known_args`, logs unknown trailing arguments, attaches the installed distribution version as `version_no`, prints the version and exits if `--version` is supplied, and returns an argparse namespace for normal flags.

Recognized flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--log-file` | `~/.khoj/khoj.log` | Server log file path. |
| `--verbose`, `-v` | count, default `0` | Increase logging verbosity; `-vvv` yields `3`. |
| `--host` | `127.0.0.1` | Host passed to uvicorn when not using a socket. |
| `--port`, `-p` | `42110` | Port passed to uvicorn. |
| `--socket` | unset | Unix socket path for reverse-proxy deployments. |
| `--sslcert` | unset | SSL certificate path. |
| `--sslkey` | unset | SSL key path. |
| `--version`, `-V` | false | Print installed Khoj version and exit. |
| `--anonymous-mode` | false | Use the default authenticated user with no login requirement. |
| `--non-interactive` | false | Skip prompts; requires env-based first-run setup values. |

Safe parser validation examples:

```bash
python skills/khoj/sub-skills/deployment-api/scripts/inspect_cli.py
python skills/khoj/sub-skills/deployment-api/scripts/inspect_cli.py --args -- --host 0.0.0.0 --port 42110 -vv --anonymous-mode --non-interactive
python skills/khoj/sub-skills/deployment-api/scripts/inspect_cli.py --args -- --help
```

If a user asks why `khoj --help` fails with a database error, explain that `khoj` imports `khoj.main` before parsing. Use the bundled helper or a direct `from khoj.utils.cli import cli` parser inspection instead.

## Service Mounts and Middleware

`configure_routes(app)` mounts these route groups:

| Prefix | Router role |
| --- | --- |
| `/api` | General API: account, search, update, transcription, settings, health, user info. |
| `/api/chat` | Chat and conversation APIs; route detailed payload work to `chat-agents`. |
| `/api/agents` | Agent APIs; route detailed behavior to `chat-agents`. |
| `/api/automation` | Automation APIs; route details to `automations-memory`. |
| `/api/model` | Model option and user model-selection APIs. |
| `/api/memories` | Memory APIs; route details to `automations-memory`. |
| `/api/content` | Content upload/sync/type APIs; route details to `content-indexing`. |
| `/api/notion` | Notion integration endpoints; route content behavior to `content-indexing`. |
| Web client routes | Browser UI and static/web application routes. |
| `/auth` | Included only when not in anonymous mode. |
| `/api/subscription` | Included only when billing env vars enable billing. |
| `/api/phone` | Included only when Twilio env vars enable phone integration. |

Middleware configured after route setup:

- Optional HTTPS redirect if SSL config was supplied through both `--sslcert` and `--sslkey`.
- Client-disconnect suppression returning status `499` for aborted clients.
- Database connection cleanup around FastAPI/Django mixed sync/async requests.
- Authentication middleware using session, bearer token, first-party client secrets, phone clients, or anonymous default user.
- Server-error middleware that redirects non-API web 5xx errors to `/server/error`.
- Next.js static path remapping from `/_next` to `/static/_next`.
- Session middleware using `KHOJ_DJANGO_SECRET_KEY`, or the insecure development fallback if unset.

## Top-Level REST Route Map

General `/api` routes:

| Method and path | Auth | Purpose |
| --- | --- | --- |
| `DELETE /api/self` | authenticated | Delete the current user account. |
| `GET /api/search` | authenticated | Search indexed content. Parameters include `q`, `n`, `t`, `r`, `max_distance`, and `dedupe`; route ranking/filter details to `search-retrieval`. |
| `GET /api/update` | authenticated | Trigger content re-indexing. Parameters include `t` and `force`; route ingestion details to `content-indexing`. |
| `POST /api/transcribe` | authenticated | Upload audio for speech-to-text, limited to 10 MiB. |
| `GET /api/settings` | authenticated | Return user configuration; `detailed=true` expands details. |
| `PATCH /api/user/name` | authenticated | Set first/last name from a one- or two-part name. |
| `PATCH /api/user/memory` | authenticated | Enable or disable memory for the user; route behavior details to `automations-memory`. |
| `GET /api/health` | authenticated | Returns JSON containing the authenticated user's email. In anonymous mode the default user can satisfy auth. |
| `GET /api/v1/user` | authenticated | Returns user profile, subscription activity, document presence, and Khoj version. |

Model `/api/model` routes:

| Method and path | Auth | Purpose |
| --- | --- | --- |
| `GET /api/model/chat/options` | public in code | List configured chat model options with IDs, names, strengths, and descriptions. |
| `GET /api/model/chat` | authenticated | Return the user's selected or default chat model. |
| `POST /api/model/chat` | authenticated | Switch the user's chat model by `id`, subject to subscription tier restrictions. |
| `POST /api/model/voice` | authenticated | Switch the user's voice model by `id`, subject to subscription tier restrictions. |
| `POST /api/model/paint` | authenticated | Switch the user's image generation model by `id`, subject to subscription tier restrictions. |

## Operational Checks

Use checks in increasing order of side effects:

1. Parser-only: run `inspect_cli.py` with representative flags.
2. Package import: import `khoj.utils.cli` or other non-server modules only.
3. Configuration review: inspect env vars and command flags without importing `khoj.main`.
4. Database check: verify PostgreSQL host/port/user/password or embedded DB settings before starting Khoj.
5. Startup check: run the server only after database and first-run admin/model settings are ready.
6. API health check: call `/api/health` with authentication, or in anonymous mode after startup.

Avoid treating the API health route as anonymous by default; it requires an authenticated request unless the server is started with anonymous mode.
