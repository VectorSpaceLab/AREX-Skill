---
name: api-cli-services
description: "Operates Cognee through the CLI, FastAPI app, Docker Compose
  profiles, MCP server, UI launch, cloud/local connection, and dataset push/sync
  surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee API, CLI, and Service Router

Use this sub-skill when the request is about service-facing Cognee entry points:
CLI flags and subcommands, the FastAPI server, Docker Compose profiles, MCP transports,
cloud/local connection helpers, UI launch, and dataset push/sync operations.

## Route here for

- `cognee-cli` global flags and service-oriented subcommands.
- `python -m cognee.api.client` and the public FastAPI router surface.
- `cognee serve`, `cognee serve --logout`, `cognee push`, and related connection flows.
- `cognee-mcp` transports, tools, resources, and API/cloud connection modes.
- `cognee-cli -ui`, Docker Compose profiles, and frontend launch notes.
- Safe help/output checks that do not start listeners or mutate data.

## Route away

- Backend/provider selection, storage/database matrices, and environment tuning: [configuration-backends](../configuration-backends/SKILL.md).
- Deep SDK workflow semantics beyond service routing and connectivity.
- Frontend internals beyond build and launch guidance.

## Read first

1. [references/cli-reference.md](references/cli-reference.md)
2. [references/services-mcp.md](references/services-mcp.md)
3. [references/deployment.md](references/deployment.md)
4. [references/troubleshooting.md](references/troubleshooting.md)

## Safe helpers

- [scripts/check_cli_surface.py](scripts/check_cli_surface.py) — verifies the installed `cognee-cli` help surface.
- [scripts/check_mcp_surface.py](scripts/check_mcp_surface.py) — checks the MCP entry point and reports a missing `mcp` package clearly.

## Working rules

- Prefer public entry points such as `cognee-cli`, `python -m cognee.api.client`, `cognee serve`, `cognee push`, and `cognee-mcp`.
- Treat `cognee serve --logout` as the CLI disconnect path; the SDK exposes `cognee.disconnect(clear_saved=True)`.
- Keep service commands non-destructive unless the user explicitly asked for a change.
- Use the troubleshooting reference for auth, CORS, transport, bundle, container, and port issues.
- Use the configuration sub-skill for provider and backend matrix questions.
