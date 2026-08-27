# ContextForge troubleshooting

Use this page for fast operator triage before drilling into the runtime-configuration sub-skill.

## Fast checks

1. Confirm you are using the right entry point.
   - `mcpgateway` is the operator-facing wrapper.
   - `mcpgateway-server` is the direct server entry and may not show a useful help screen.
   - `cforge` is for deployment/build flows, not runtime help.
2. Confirm the secrets are real.
   - Both `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` must be present and strong.
   - Use `init-secrets` or `init-secrets --patch-env .env` to repair placeholders.
3. Confirm the environment matches the deployment lane.
   - Local dev commonly uses `make dev` on port `8000`.
   - Production-style startup typically uses `make serve`, `mcpgateway`, or `python -m mcpgateway` on port `4444`.
4. Confirm the management flags are what you expect.
   - `MCPGATEWAY_UI_ENABLED`
   - `MCPGATEWAY_ADMIN_API_ENABLED`
   - `AUTH_REQUIRED`

## Common symptoms

- `SecurityConfigurationError` during startup
  - Usually means a required secret is missing, placeholder, too short, or low entropy.
- Admin UI or admin API not visible
  - Check whether the feature flags are disabled in `.env` or still using code defaults.
- `mcpgateway-server --help` appears to hang
  - That entry point is a server launcher, not a help-oriented inspection probe.
- Compose or Helm starts with secret-related failures
  - Ensure you are injecting real values through an env file, Compose secret, or Kubernetes Secret.
- Need a read-only diagnostic bundle
  - Prefer `mcpgateway --validate-config`, `mcpgateway --config-schema`, or `mcpgateway --support-bundle`.

## Deeper detail

- Runtime config, database/cache choices, and deployment recipes: [`../sub-skills/runtime-configuration/SKILL.md`](../sub-skills/runtime-configuration/SKILL.md)
