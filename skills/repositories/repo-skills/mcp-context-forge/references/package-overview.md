# ContextForge package overview

ContextForge is published as `mcp-contextforge-gateway` version `1.0.7`.
It requires Python `>=3.12,<3.14` and installs a FastAPI gateway that federates MCP, A2A, REST, and gRPC backends.
The gateway centralizes tools, prompts, resources, servers, gateways, admin API/UI, cpex plugin framework integration, and observability surfaces.

## Install paths

- PyPI: `pip install mcp-contextforge-gateway`
- Editable checkout: `pip install -e .`
- Ephemeral run: `uvx --from mcp-contextforge-gateway mcpgateway --help`

## Optional extras

- `.[postgres]` for PostgreSQL client support
- `.[redis]` for Redis parsing support
- `.[observability]` for OpenTelemetry export packages
- `.[aiosqlite]` or `.[asyncpg]` when a specific database driver is needed

## Primary runtime entry points

- `mcpgateway` — uvicorn wrapper for `mcpgateway.main:app`
- `mcpgateway-server` — direct `python -m mcpgateway` server entry
- `cforge` — builder/deployment CLI
- `init-secrets` — secret generation CLI

## Where to go next

- CLI usage and special flags: [`cli-entrypoints.md`](cli-entrypoints.md)
- Install/run/configuration guidance: [`../sub-skills/runtime-configuration/SKILL.md`](../sub-skills/runtime-configuration/SKILL.md)
