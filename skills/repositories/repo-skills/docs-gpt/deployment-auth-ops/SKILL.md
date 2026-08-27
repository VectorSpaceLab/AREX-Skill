---
name: deployment-auth-ops
description: "Use for DocsGPT deployment and operations, settings,
  Postgres/Redis/Celery, OIDC/SCIM/RBAC, admin, observability, and model
  providers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deployment, auth, and ops skill

Use this subskill for settings, local stack bring-up, Docker/Compose, Postgres/Redis, OIDC/SCIM, RBAC, teams, admin workflows, observability, and model/provider configuration.

## Primary surfaces

- App settings: `application/core/settings.py` and `docs/content/Deploying/DocsGPT-Settings.mdx`.
- Postgres lifecycle: `scripts/db/init_postgres.py`, `scripts/db/backfill.py`, `docs/content/Deploying/Postgres-Migration.mdx`.
- Auth: `application/api/oidc/`, `application/api/scim/`, `docs/content/Deploying/OIDC-SSO.mdx`, `docs/content/Deploying/Access-Control.mdx`.
- Admin/teams: `/api/admin`, `/api/teams`, `/api/resource_shares`, `/api/user/me`.
- Deployment manifests: `deployment/docker-compose*.yaml` and Kubernetes manifests under `deployment/`.
- Observability: `docs/content/Deploying/Observability.mdx`.
- Model catalog: `application/core/models/` and `docs/content/Models/*`.

## Environment rules that matter

- Postgres is the canonical user-data store.
- Redis is used for Celery, cache/session/event state, OIDC handoff/refresh state, revocations, and other coordination.
- MongoDB is not required unless the vector store is `mongodb` or you are running the one-shot legacy backfill.
- `AUTO_CREATE_DB` and `AUTO_MIGRATE` default to true for development convenience; production should usually run migrations explicitly.
- `AUTH_TYPE=None` is a no-auth local mode only. Do not enable `LOCAL_MODE_ADMIN=true` on a networked deployment.

## ASGI vs Flask

- Prefer `uvicorn application.asgi:asgi_app --host 0.0.0.0 --port 7091 --reload` for local development and any verification that depends on ASGI-mounted routes.
- Use `flask run` only when you intentionally want the WSGI app and do not need `/mcp` or `/api/messages/<id>/events` reconnect behavior.

## OIDC / SCIM / RBAC essentials

- `AUTH_TYPE=oidc` delegates sign-in to an external IdP using authorization code + PKCE.
- Group allowlists and admin group mappings are re-checked on login and silent renewal.
- SCIM user provisioning is optional but requires `SCIM_ENABLED=true` and `SCIM_TOKEN`.
- Global admin and team roles are different planes. A team admin is not a global admin.
- The `scripts/grant_admin.py` helper is the canonical bootstrap path for the first admin in OIDC deployments.

## Config and startup checks

Use these before touching deployment logic:

```bash
python skills/disco/docs-gpt/scripts/check_local_config.py --repo . --check-services
python - <<'PY'
from application.core.settings import settings
print(settings.AUTH_TYPE, settings.VECTOR_STORE, settings.POSTGRES_URI)
PY
```

If settings import itself fails, inspect the environment and dependency state before changing application code.

## What to inspect in source

- `application/app.py`
- `application/asgi.py`
- `application/core/settings.py`
- `application/api/admin/routes.py`
- `application/api/oidc/routes.py`
- `application/api/scim/routes.py`
- `application/api/user/teams/routes.py`
- `application/api/user/me/routes.py`
- `application/seed/commands.py`

## Safe checks

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/admin
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /scim/v2
python -m pytest tests/api/test_admin_dashboard.py tests/api/test_rbac_endpoints.py tests/integration/test_scim.py
```

If a change touches database bootstrap, run the explicit init script rather than relying on app auto-bootstrap in the final verification path.

## Useful references

- `../references/repo-map.md`
- `../references/dev-environment.md`
- `../references/verification-matrix.md`
- `docs/content/Deploying/Development-Environment.mdx`
- `docs/content/Deploying/DocsGPT-Settings.mdx`
- `docs/content/Deploying/Access-Control.mdx`
- `docs/content/Deploying/OIDC-SSO.mdx`
- `docs/content/Deploying/Postgres-Migration.mdx`
- `docs/content/Deploying/Observability.mdx`
