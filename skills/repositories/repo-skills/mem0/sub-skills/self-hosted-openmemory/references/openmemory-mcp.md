# OpenMemory API, UI, and MCP

OpenMemory is Mem0’s self-hosted memory platform with an API, UI, and local MCP server. Use it when the task is about user-controlled local memory infrastructure rather than hosted Mem0 Platform or an in-process SDK-only `Memory()` object.

## Stack Shape

Typical OpenMemory development/deployment includes:

- API service: FastAPI app under `openmemory/api`.
- UI service: Next.js app under `openmemory/ui`.
- Vector store: Qdrant by default in the OpenMemory Compose stack.
- MCP server: exposed by the API for agent/editor clients.
- Database/migrations: SQL app state through Alembic and the API models.

## Start and Verify

For the full stack, use the project’s OpenMemory Compose workflow from a maintained checkout or deployment script. Future agents using this skill should not assume the source checkout exists; use these steps as an operational shape:

1. Prepare required API/UI environment variables.
2. Start Qdrant, API, and UI services.
3. Verify API health and UI availability.
4. Verify MCP endpoint/tool listing from the intended client.
5. Add a tiny memory only after the user confirms the target environment and scope.

The bundled checklist helper is read-only:

```bash
python scripts/render_docker_env_check.py --target openmemory
```

## MCP Client Routing

OpenMemory MCP is different from hosted `https://mcp.mem0.ai`:

- Hosted MCP belongs with the integration/plugin route when using Mem0 Platform.
- OpenMemory MCP belongs here when the user runs local OpenMemory services.
- Client config must point at the local API/MCP URL and use the local auth mode required by that deployment.

Before editing any client config, inspect existing MCP server entries for duplicate `mem0` names. If an agent already has a hosted Mem0 MCP entry and the user asks for local OpenMemory, use a distinct server name or replace intentionally.

## API Responsibilities

OpenMemory API routes cover:

- Apps/configuration and permissions.
- Memory CRUD/search through API routers.
- Stats and dashboard-supporting data.
- Backup/export-style operations when enabled by deployment.
- MCP tool exposure through the API server.

## Backup and Export Safety

Backup/export scripts are deployment-specific and may read live memories or write files containing sensitive user data. Treat them as privileged operations:

- Confirm destination, retention policy, and data sensitivity.
- Redact or protect exported memory contents.
- Avoid copying production data into prompts or logs.
- Do not run backup/restore scripts as a generic smoke test.

## Common OpenMemory Failure Modes

| Symptom | Likely cause | Recovery path |
| --- | --- | --- |
| MCP client shows no tools | API not running, wrong MCP URL, auth missing, or client configured for hosted MCP instead of local API | Verify API logs/health, URL, auth header/env, and duplicate server names. |
| UI loads but memory calls fail | API URL mismatch, CORS/origin issue, backend env missing, or vector DB unavailable | Check API env, UI API base URL, Qdrant service, and browser/server logs. |
| Memory search empty | Wrong user/app scope, empty Qdrant collection, ingestion not completed, or filters too narrow | Check target entity scope and perform a small confirmed add/search only in non-production scope. |
| MCP writes unexpected project memories | Client identity/project scoping not configured | Review plugin/MCP config and OpenMemory app permissions before further writes. |

## When to Route Elsewhere

- Hosted Mem0 Platform MCP or editor plugin setup: `../integrations-plugins/SKILL.md`.
- Python/TypeScript in-process memory API usage: `../sdk-memory/SKILL.md`.
- Provider selection for OSS memory objects: `../provider-configuration/SKILL.md`.
- Terminal `mem0` CLI commands against Platform: `../cli-memory/SKILL.md`.
