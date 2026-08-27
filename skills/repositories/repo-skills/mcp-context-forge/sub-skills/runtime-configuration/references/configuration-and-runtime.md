# Configuration and runtime

This reference is the operator-facing map for ContextForge startup settings.
It focuses on the values that change how the gateway starts, what it binds to,
and which management surfaces are available.

## Required secrets

These must be present in every environment:

| Variable | Purpose | Notes |
| --- | --- | --- |
| `JWT_SECRET_KEY` | Signs gateway JWTs | Generate with `init-secrets`. Never keep the placeholder. |
| `AUTH_ENCRYPTION_SECRET` | Encrypts stored credentials | Generate with `init-secrets`. Never keep the placeholder. |

Use `init-secrets` for manual review or `init-secrets --patch-env .env` to patch an
existing env file in place.

## Common runtime variables

| Variable | Typical meaning | Safe reminder |
| --- | --- | --- |
| `HOST` | Bind address | `.env.example` usually uses `0.0.0.0`; code defaults are more restrictive. |
| `PORT` | Listen port | `make dev` commonly uses `8000`; production-style startup commonly uses `4444`. |
| `DATABASE_URL` | SQLAlchemy backend | SQLite is convenient for local work; PostgreSQL is the production default. |
| `REDIS_URL` | Redis backend | Optional for simple local runs, important for shared cache or coordination. |
| `AUTH_REQUIRED` | Authentication gate | Keep it intentional; do not assume a dev-friendly example matches production. |
| `MCPGATEWAY_UI_ENABLED` | Admin UI visibility | `.env.example` may enable it for local convenience. |
| `MCPGATEWAY_ADMIN_API_ENABLED` | Admin API visibility | `.env.example` may enable it for local convenience. |
| `PLUGINS_ENABLED` | Plugin framework | Off by default unless the deployment needs it. |
| `OBSERVABILITY_ENABLED` | Internal observability | Off by default unless traces/metrics are being collected. |
| `API_ALLOW_BASIC_AUTH` | API basic auth | Off by default; JWT is the preferred path. |
| `DOCS_ALLOW_BASIC_AUTH` | Docs basic auth | Off by default; only enable if you truly need it. |

## Code defaults vs `.env.example`

The repository intentionally uses different values in `.env.example` for a smoother
local setup than the underlying code defaults.

Typical examples:

- `HOST=0.0.0.0` in `.env.example` for local containers or reverse-proxy use
- `MCPGATEWAY_UI_ENABLED=true` in `.env.example` to make the Admin UI visible during
  local development
- `MCPGATEWAY_ADMIN_API_ENABLED=true` in `.env.example` for local admin workflows
- `DATABASE_URL=sqlite:///./mcp.db` as the simple default storage backend
- `AUTH_REQUIRED=true` as the secure default for authenticated access

When the user wants production-safe behavior, favor the underlying code defaults and
explicitly set only the exceptions they actually need.

## Database and cache choices

| Choice | Best for | Notes |
| --- | --- | --- |
| SQLite | Quick local development | Lowest setup cost; keep it for single-node or disposable environments. |
| PostgreSQL | Production and multi-user use | Recommended when durability, concurrency, or operational tooling matter. |
| Redis | Shared cache and coordination | Optional for simple runs; useful for multi-instance or distributed behavior. |

## Safe startup diagnostics

Read-only or low-risk checks to use before changing anything:

- `mcpgateway --validate-config .env`
- `mcpgateway --config-schema schema.json`
- `mcpgateway --support-bundle`
- `python scripts/contextforge_env_audit.py .env --example-file .env.example`

The audit script is the safest way to compare env-file keys without printing secret
values.

## Local runtime lanes

- `make install-dev` — install the checkout with dev dependencies
- `make check-env` — run the repository env validation target
- `make check-env-dev` — run the dev-tolerant `.env` validation target
- `make dev` — live-reload development server on port `8000`
- `make serve` — production-style Gunicorn + Uvicorn on port `4444`
- `mcpgateway` — packaged entry point for runtime startup from PyPI or a checkout
- `mcpgateway-server` / `python -m mcpgateway` — direct server startup path

## Related references

- Package identity: [`../../../references/package-overview.md`](../../../references/package-overview.md)
- Entry points: [`../../../references/cli-entrypoints.md`](../../../references/cli-entrypoints.md)
- Deployment choices: [`deployment-recipes.md`](deployment-recipes.md)
