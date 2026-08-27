# API, OpenAPI, and Auth Operations

## FastAPI App Shape

InvokeAI builds a FastAPI app titled `Invoke - Community Edition` with custom Swagger/ReDoc handlers at `/docs` and `/redoc`. The OpenAPI function is customized by the application and the UI/static files are mounted after API router registration.

Middleware and app-level behavior relevant to operators:

- Auth router is included first under `/api` so authentication routes exist before protected routes.
- `SlidingWindowTokenMiddleware` refreshes a valid Bearer token on successful mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) via the `X-Refreshed-Token` response header.
- CORS is configured from `allow_origins`, `allow_credentials`, `allow_methods`, and `allow_headers`; `X-Refreshed-Token` is exposed.
- GZip is enabled for responses above 1000 bytes.
- `/` mounts the bundled web UI when available; `/static` mounts static docs assets.
- If `unsafe_disable_picklescan` is enabled, startup logs a warning because model install/load scanning is disabled.

Use `scripts/inspect_openapi_routes.py` to summarize route families. It imports the live app only when dependencies are present; otherwise use `--fallback` for bundled route-family knowledge.

## Router Families

All listed router prefixes are included under the app-level `/api` prefix unless noted.

| Router | Prefix | Operational role | Route elsewhere for |
| --- | --- | --- | --- |
| Authentication | `/api/v1/auth` | login, logout, setup status, setup admin, current user, admin user CRUD | auth DB/user mistakes stay here |
| App info/config | `/api/v1/app` | version, dependency report, patchmatch, runtime config, external provider config, log level, invocation cache | backend install details to root troubleshooting; model provider model records to `../model-management/SKILL.md` |
| Models | `/api/v2/models` | model records, model scan/install/delete, HF login, starter models | model-management |
| Download queue | `/api/v1/download_queue` | model/download jobs | model-management |
| Queue | `/api/v1/queue` | session queue enqueue/control/status/history | `../workflows-queues/SKILL.md` |
| Workflows | `/api/v1/workflows` | workflow records, tags, thumbnails, categories | `../workflows-queues/SKILL.md` |
| Custom nodes | `/api/v2/custom_nodes` | installed custom node packs and reload | `../workflow-nodes/SKILL.md` |
| Images | `/api/v1/images` | upload, metadata, thumbnails, star/delete, intermediates | operations only for auth/access/CORS symptoms |
| Boards | `/api/v1/boards`, `/api/v1/board_images`, `/api/v1/virtual_boards` | board and image organization | operations only for auth/access symptoms |
| Style presets | `/api/v1/style_presets` | style preset CRUD/import/export | workflow/UI feature usage outside this sub-skill |
| Utilities | `/api/v1/utilities` | dynamic prompts, prompt expansion, image-to-prompt | node/workflow/model specifics elsewhere |
| Client state | `/api/v1/client_state` | client state persistence per queue | workflows-queues for queue context |
| Recall | `/api/v1/recall` | recall parameters by queue | workflows-queues for workflow/session context |
| Model relationships | `/api/v1/model_relationships` | related model relationships | model-management |

## OpenAPI Discovery

Preferred safe route discovery options:

- Running server: request `/openapi.json`, `/docs`, or `/redoc` from the configured host/port.
- Installed full app environment: run `python scripts/inspect_openapi_routes.py --json` to import `invokeai.app.api_app`, call `app.openapi()`, and summarize route paths/tags.
- Partial inspection environment: run `python scripts/inspect_openapi_routes.py --fallback` to print bundled route-family knowledge without importing FastAPI/Torch/server dependencies.

If importing the app fails, the likely causes are missing runtime dependencies, incompatible Python version, missing Torch/backend packages, or app imports that expect full service initialization. Use the fallback output for routing and ask the user to run discovery in the real installed environment when exact route schemas are required.

## Multiuser Mode Basics

`multiuser` defaults to `false`. In single-user mode:

- Auth setup/login endpoints report that authentication is not required or disabled.
- Dependencies that allow default access return a synthetic system admin user (`system@system.invokeai`) for operations designed to work in both modes.

When `multiuser` is `true`:

- `/api/v1/auth/status` reports `setup_required`, `multiuser_enabled`, `strict_password_checking`, and, during first setup only, the first admin email when no admin exists.
- `/api/v1/auth/setup` creates the first admin only when no active admin exists.
- `/api/v1/auth/login` returns a JWT token, user DTO, and `expires_in` seconds. Normal login is 1 day; `remember_me` is 7 days.
- `/api/v1/auth/logout` is currently a stateless-token no-op that returns success after token validation.
- `/api/v1/auth/me` returns the current user for a valid token.
- Admin endpoints under `/api/v1/auth/users` list/create/get/update/delete users.
- A user can update their own profile at `/api/v1/auth/me`; password changes require the current password.

JWT signing uses HS256. The JWT secret is initialized during app startup from the database. If token creation/verification reports that the secret is not initialized, the auth service was used before application startup completed or outside the normal dependency initialization path.

## User Service Behavior

The default user service stores users in the configured SQLite database. Important operational properties:

- User IDs are UUID strings.
- Passwords are bcrypt hashes; bcrypt input is truncated to 72 bytes.
- Strict password validation requires at least 8 characters plus uppercase, lowercase, and a digit.
- Non-strict mode accepts any non-empty password, but password strength can still be classified as weak/moderate/strong.
- Email validation uses normal email-validator behavior but allows special-use/local domains with basic syntax checks.
- Active admins are counted to prevent deleting the last administrator through the admin API.
- User listing excludes the internal `system` user from admin API output.

## User-Management CLIs

Console scripts mutate the configured users database. Never run them against a production root for inspection only. Use `scripts/inspect_cli_help.py --command users` for help text and option discovery.

- `invoke-useradd --root ROOT --email EMAIL --password PASSWORD [--name NAME] [--admin]`: creates a user; without email/password it prompts interactively.
- `invoke-userdel --root ROOT --email EMAIL [--force]`: deletes a user; without `--force` it prompts for confirmation.
- `invoke-userlist --root ROOT [--json]`: lists users as table or JSON.
- `invoke-usermod --root ROOT --email EMAIL [--name NAME] [--password PASSWORD] [--admin|--no-admin]`: updates display name/password/admin status; without `--email` it prompts interactively.

All four CLIs accept `--root`/`-r`. They set `INVOKEAI_ROOT` before loading config. They do not accept `--config`, so non-default config-file testing should be done with controlled env/root layout or app APIs, not by assuming user-management CLIs read arbitrary config paths.

## Auth Troubleshooting Signals

- `403 Multiuser mode is disabled`: expected when calling login/setup in single-user mode.
- `401 Incorrect email or password`: no matching active credentials or password mismatch.
- `403 User account is disabled`: credentials match an inactive user.
- `401 Missing authentication credentials`: protected endpoint was called without `Authorization: Bearer ...`.
- `401 Invalid or expired authentication token`: invalid signature, expired token, or token payload validation failure.
- `403 Admin privileges required`: token is valid but non-admin for admin-only endpoint.
- `400 Administrator account already configured`: `/setup` called after an active admin exists.
- `400 Cannot delete the last administrator`: admin delete would leave no active admins.

## Access-Control Helpers

Image and board routes use cross-router authorization helpers. For non-admin users, image mutation/read access depends on direct image ownership, board ownership, and board visibility. Shared/public boards can permit read or mutation paths depending on the helper. When diagnosing image/board 403s, inspect user ID, board ownership, and board visibility before assuming token failure.
