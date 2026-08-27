---
name: self-hosted-openmemory
description: "Deploy, configure, and troubleshoot self-hosted Mem0 server,
  dashboard, auth, API keys, REST endpoints, Docker Compose services, OpenMemory
  API/UI/MCP, migrations, backups, and operational safety."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# self-hosted-openmemory

Use this sub-skill when a task mentions self-hosted Mem0, the Mem0 REST server, Docker Compose, dashboard login, API keys, request logs, Postgres/pgvector, Neo4j, OpenMemory, local MCP hosting, migrations, `.env` setup, `make bootstrap`, auth upgrades, backups, or operational troubleshooting.

## Route First

- Use this sub-skill for server deployment, dashboard/admin setup, API key issuance, auth defaults, REST routes, OpenMemory API/UI/MCP, Docker services, migrations, and operations.
- Use [Server Deployment](references/server-deployment.md) for `server/` style setup, dashboard/auth, bootstrap, request logs, migrations, and operations.
- Use [OpenMemory MCP](references/openmemory-mcp.md) for OpenMemory stack, Qdrant-backed local memory app, API/UI layout, and MCP client integration.
- Use [REST API and Auth](references/rest-api-and-auth.md) for endpoint families, auth modes, API keys, CORS, request logs, and client configuration.
- Use [Troubleshooting](references/troubleshooting.md) for 401s after upgrade, missing secrets, port conflicts, provider failures, migrations, MCP tool visibility, and destructive recovery paths.

## Sibling Boundaries

- Route direct Python/TypeScript SDK CRUD/search, `MemoryClient`, `Memory`, async clients, filters, exports, and feedback to `../sdk-memory/SKILL.md`.
- Route OSS provider/vector/embedder/LLM/reranker configuration for in-process `Memory()` to `../provider-configuration/SKILL.md`.
- Route terminal `mem0 init/add/search/list` workflows to `../cli-memory/SKILL.md`.
- Route hosted MCP/plugin setup for Claude, Cursor, Codex, OpenCode, Antigravity, OpenClaw, Pi Agent, and Vercel AI SDK to `../integrations-plugins/SKILL.md`.

## Fast Decision Tree

1. Need a hosted-free local service with dashboard and API keys? Use the Mem0 self-hosted server path and start with `server/.env` validation, then `make bootstrap` or browser setup.
2. Need local memory app plus MCP server for user-controlled memories? Use OpenMemory and verify API, UI, and Qdrant containers before client wiring.
3. Seeing `401` after an upgrade? Decide between legacy `ADMIN_API_KEY`, recommended dashboard-created per-user keys, or `AUTH_DISABLED=true` for local development only.
4. Need to reset passwords, prune request logs, wipe volumes, or export backups? Treat those as privileged or destructive operations and confirm target environment first.
5. Need in-process Python/Node memory only, without server containers? Route to `sdk-memory` and `provider-configuration` instead.

## Bundled Scripts

- `python scripts/check_self_host_env.py --help` checks `.env`-style files for required self-hosted settings without printing secret values.
- `python scripts/render_docker_env_check.py --help` prints a safe checklist for server/OpenMemory Docker Compose readiness and upgrade risks.

## Working Rules

- Never invent, print, commit, or echo real provider keys, `JWT_SECRET`, admin passwords, API keys, refresh tokens, or database passwords.
- Never run destructive commands such as volume resets, password resets, cascade deletes, or backup restores without explicit user confirmation.
- Prefer read-only checks first: env-file validation, port availability, container status, logs, and migration state.
- Keep local development bypasses separate from production guidance; `AUTH_DISABLED=true` is local-only.
- Do not tell future agents to run original repo scripts from a source checkout. Use the bundled references and validators here.
