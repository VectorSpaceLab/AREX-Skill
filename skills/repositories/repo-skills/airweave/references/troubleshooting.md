# Airweave troubleshooting

This page is the cross-cutting map. Use the sub-skill troubleshooting docs for surface-specific detail.

## 1. Repo sanity and helper discovery

If the skill tree looks incomplete or a helper cannot find the repo root:
- Run `scripts/check_env.py --repo-root /path/to/airweave`
- Confirm the generated sub-skill directories exist
- Use an explicit repo root instead of relying on the current working directory

## 2. Local stack and services

Common failures:
- Docker or Podman daemon not running
- Port conflicts on 8001, 8080, 8081, 8082, 5432, 6379, 7233, 8233, 8071
- Missing or invalid `.env` values
- Vespa schema or embedder dimension mismatch

Go to `sub-skills/local-development/references/troubleshooting.md` for startup, health, and recovery commands.

## 3. Backend import and environment validation

If backend imports or settings fail:
- Check the backend Python environment is active and matches the repo's Python 3.13 expectation
- Ensure required secrets satisfy length validation, especially `STATE_SECRET` and `SVIX_JWT_SECRET`
- Confirm `backend/pyproject.toml` dependencies are installed

Go to `sub-skills/backend-api/references/troubleshooting.md` for API and stream failures.

## 4. Dashboard auth and org context

If the dashboard shows stale org data or auth problems:
- Verify the auth context is ready before API calls
- Check `X-Organization-ID` handling and cached org switching behavior
- Revisit the auth-disabled dev mode versus Auth0 mode split

Go to `sub-skills/frontend-dashboard/references/troubleshooting.md`.

## 5. Connect widget session or OAuth issues

If the widget cannot mount, loses token state, or fails OAuth recovery:
- Check the parent/child postMessage contract
- Confirm the session token and origin checks
- Make sure OAuth callback state is preserved until verification completes

Go to `sub-skills/connect-widget/references/troubleshooting.md`.

## 6. MCP transport or auth issues

If the MCP server does not start or tools are missing:
- Check `AIRWEAVE_API_KEY` and `AIRWEAVE_COLLECTION`
- Confirm stdio versus HTTP mode is chosen correctly
- Verify the `/mcp` transport and tool names against the current package

Go to `sub-skills/mcp-search/references/auth-and-troubleshooting.md`.

## 7. Source connector or Monke failures

If a connector or Monke test behaves unexpectedly:
- Use `sub-skills/source-connectors/references/...` for registry, auth, and browse-tree issues
- Use `sub-skills/monke-e2e/references/...` for connector discovery, config validation, or credential resolution
- Remember that Monke runs real external systems and should not be treated as a mock-only harness

## 8. When in doubt

- Search issues first with `backend-api` if the surface is search or source connections.
- Use `source-connectors` if the task mentions `@source(...)`, connector config, browse-tree, ACLs, or federated search.
- Use `mcp-search` if the task mentions MCP tools, stdio, Streamable HTTP, or `/mcp`.
- Use `monke-e2e` if the task mentions connector discovery, changed connectors, or real external test accounts.
