# Runtime troubleshooting

This page focuses on the failures most often seen during install, startup, and first deployment.

## 1) Missing or weak secrets

Symptoms:

- `SecurityConfigurationError` at startup
- `init-secrets` appears to work, but the gateway still refuses to start
- `.env.example` values were copied into a real deployment without replacement

Checks:

- Confirm both `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` are present
- Confirm they are real, strong values rather than placeholders or defaults
- Use `init-secrets --patch-env .env` to repair an env file in place
- Use `python scripts/contextforge_env_audit.py .env --example-file .env.example` for a read-only audit

## 2) UI or admin API not visible

Symptoms:

- The Admin UI does not appear
- Admin routes return 404 or look disabled

Checks:

- `MCPGATEWAY_UI_ENABLED`
- `MCPGATEWAY_ADMIN_API_ENABLED`
- `AUTH_REQUIRED`
- Whether the deployment is using the secure code defaults or the dev-friendly `.env.example` overrides

## 3) Port confusion

Symptoms:

- The developer expects port `4444` but sees `8000`
- A `uvicorn` command exposes a different default than the packaged wrapper

Checks:

- `make dev` uses `8000`
- `make serve`, `mcpgateway`, and `python -m mcpgateway` commonly use `4444`
- `mcpgateway` injects its own app and host/port defaults when the user does not supply them

## 4) SQLite vs PostgreSQL vs Redis mismatch

Symptoms:

- A single-node local setup works, but the production target does not
- A deployment expects shared state or coordination that SQLite cannot provide well

Checks:

- Use SQLite for local experimentation only
- Use PostgreSQL for production or multi-user durability
- Use Redis when shared cache or coordination behavior is required

## 5) Basic auth appears disabled

Symptoms:

- `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` are set, but nothing changes

Checks:

- `API_ALLOW_BASIC_AUTH` must be enabled for API basic auth
- `DOCS_ALLOW_BASIC_AUTH` must be enabled for docs basic auth
- If both remain false, the basic-auth credentials are effectively unused

## 6) Container / Helm secret handling

Symptoms:

- Compose or Kubernetes startup fails because the gateway sees placeholders
- A values file or manifest still contains example credentials

Checks:

- Never commit real secrets into Compose files or Helm values
- Use env-file injection, Compose secrets, Kubernetes Secrets, or an external secret manager
- Prefer the bundled audit script before changing a deployment

## 7) Need a safe diagnostic bundle

Use one of these before changing the deployment:

- `mcpgateway --validate-config .env`
- `mcpgateway --config-schema schema.json`
- `mcpgateway --support-bundle`
- `python scripts/contextforge_env_audit.py .env --example-file .env.example`

## Related references

- Root troubleshooting overview: [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md)
- Runtime settings: [`configuration-and-runtime.md`](configuration-and-runtime.md)
- Deployment recipes: [`deployment-recipes.md`](deployment-recipes.md)
