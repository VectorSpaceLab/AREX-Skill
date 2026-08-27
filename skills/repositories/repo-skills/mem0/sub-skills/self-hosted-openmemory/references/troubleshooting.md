# Self-hosted and OpenMemory Troubleshooting

## Upgrade Returns 401 Everywhere

Likely causes:

- Auth is enabled by default in the current self-hosted server.
- Deployment upgraded from a pre-auth or legacy shared-key setup.
- No admin user/API key has been created yet.
- Clients are still sending the old header or no key.

Recovery:

1. For fresh/team deployments, run the dashboard setup wizard or `make bootstrap` equivalent to create an admin and first API key.
2. For zero-client-change upgrades, set a strong `ADMIN_API_KEY` only if legacy compatibility is required.
3. For local development only, `AUTH_DISABLED=true` can bypass auth; never recommend it for production.
4. Verify clients send the self-hosted API key header expected by the server, not hosted Platform `Authorization: Token ...` unless that deployment explicitly supports it.

## Missing `JWT_SECRET`

Symptoms:

- Auth endpoints return `500`.
- Dashboard setup/login cannot complete.
- Server logs mention JWT/signing secret errors.

Recovery:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in the server env file as `JWT_SECRET`, then recreate/restart the API container so env changes are applied.

## Port Conflicts

Symptoms:

- Dashboard/API container exits immediately.
- Browser cannot reach port `3000` or `8888`.

Recovery:

- Check which process owns the port with platform tools such as `lsof` or `ss`.
- Stop the conflicting process or remap Compose host ports.
- Confirm internal service URLs still point to container ports, not remapped host ports.

## Provider 401 or Upstream Failures

Symptoms:

- Memory writes/searches fail after auth succeeds.
- Logs mention upstream provider key, model, or quota failures.
- Dashboard configuration page shows wrong provider state.

Recovery:

- Verify provider env variables match the configured LLM/embedder.
- If using runtime dashboard configuration, remember it layers over env defaults and persists to the app database.
- Test a provider credential outside production memory scope only when the user approves.
- Do not paste provider keys or full upstream responses into logs/prompts.

## Migration or Database Failures

Symptoms:

- Alembic migration fails on startup.
- Tables already exist after a restore.
- Postgres refuses to read old data directory.

Recovery:

- Read migration logs and identify whether this is a fresh install, upgrade, or restore.
- For PostgreSQL major-version changes, export from old container and import into a fresh new volume; do not point the new server at an old data directory.
- Avoid `docker compose down -v` until a verified backup exists and the user explicitly approves data loss.

## OpenMemory MCP Shows No Tools

Likely causes:

- OpenMemory API service is not running.
- Client points at hosted MCP instead of local OpenMemory MCP, or vice versa.
- Auth token/env var missing from client config.
- Duplicate MCP server names shadow each other.
- API started but Qdrant/database dependency is unavailable.

Recovery:

1. Check API health/logs and dependency container status.
2. Inspect client MCP config for URL, headers/token env, and duplicate `mem0` entries.
3. Use a distinct server name if hosted Mem0 and local OpenMemory are both installed intentionally.
4. Restart the client after config changes.

## Unsafe Operations Checklist

Ask for explicit confirmation before:

- Deleting all memories or deleting an entity with cascade behavior.
- Resetting admin passwords.
- Pruning request logs.
- Wiping Docker volumes.
- Restoring backups over live data.
- Running hook installers or scripts that rewrite user agent/editor config.

## Diagnostic Order

1. Classify deployment: hosted Platform, self-hosted server, or OpenMemory.
2. Identify auth mode and base URL.
3. Validate env/config without printing secret values.
4. Check container/service health and logs.
5. Confirm route/header/payload shape.
6. Run live add/search only in a safe non-production entity after approval.
