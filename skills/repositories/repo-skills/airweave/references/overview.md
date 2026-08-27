# Airweave overview

Airweave is an open-source context retrieval platform: it syncs data from many source systems, transforms and embeds that data, stores it in vector search backends, and serves search and agent-facing retrieval APIs.

## Repository shape

- `backend/` - FastAPI service, async SQLAlchemy, PostgreSQL metadata, sync orchestration, source registry, search endpoints, connect/session APIs.
- `frontend/` - React 18 + TypeScript dashboard for search, collections, org context, billing/admin, and source management.
- `connect/` - Embeddable Connect widget for iframe/session flows and OAuth / source-connection UX.
- `mcp/` - Node.js MCP search server exposing search tools over stdio and Streamable HTTP.
- `monke/` - Connector E2E framework that creates real external data, triggers syncs, and verifies results in Airweave.
- `examples/` - Small end-to-end examples and webhook demos.
- `docker/`, `vespa/`, `start.sh` - Local stack and deployment helpers.

## Data flow

1. Sources and connector configs are registered.
2. Source connectors extract and transform entities.
3. Embeddings are generated and indexed.
4. Vector search serves collections and search tiers.
5. Agent-facing surfaces consume the same backend primitives through the API, widget, MCP, or Monke.

## Key package facts

- Backend package: `airweave`, Python 3.13, Poetry-managed.
- Frontend package: Vite / React dashboard.
- Connect package: dedicated widget application.
- MCP package: `airweave-mcp-search`, Node 20+.
- Monke uses Python configs and real connector accounts, with Composio or direct-auth credential resolution.

## Good entry points

- `scripts/check_env.py` for repo sanity and file-system checks
- `sub-skills/local-development/SKILL.md` for local stack orchestration
- `sub-skills/backend-api/SKILL.md` for search and API workflows
- `sub-skills/source-connectors/SKILL.md` for connector implementation details
- `sub-skills/frontend-dashboard/SKILL.md` for dashboard behavior
- `sub-skills/connect-widget/SKILL.md` for iframe/session flows
- `sub-skills/mcp-search/SKILL.md` for MCP transport and tools
- `sub-skills/monke-e2e/SKILL.md` for connector E2E discovery

## Common commands

```bash
# Quick repo sanity check
python skills/disco/airweave/scripts/check_env.py --repo-root /path/to/airweave

# Local stack
bash skills/disco/airweave/sub-skills/local-development/scripts/local-stack.sh --repo-root /path/to/airweave status

# MCP smoke helper
bash skills/disco/airweave/sub-skills/mcp-search/scripts/mcp-smoke.sh --help

# Monke discovery helper
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh --help
```
