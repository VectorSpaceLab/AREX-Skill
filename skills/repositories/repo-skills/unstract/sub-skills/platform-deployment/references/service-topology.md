# Service Topology

This service family is the runtime shell around the Unstract platform. It is the right mental model when you need to start the stack, check ports, or understand how the non-backend services fit together.

## Core Services

| Service | Default port | Entry point | Purpose | Key dependencies |
| --- | --- | --- | --- | --- |
| Backend | `8000` | `backend/entrypoint.sh` | Django API and hosted MCP server | PostgreSQL, Redis, RabbitMQ |
| Platform service | `3001` | `platform-service/entrypoint.sh` | SDK-facing Flask API for platform helpers | PostgreSQL, Redis |
| Runner | `5002` | `runner/entrypoint.sh` | Tool-container orchestration and execution support | Docker, backend APIs |
| x2text service | `3004` | `x2text-service/run.py` | Bridge to text-extraction services | Platform API, execution data dir, PostgreSQL |
| Tool sidecar | no HTTP port | `tool-sidecar/entrypoint.sh` | Log processing and real-time streaming | Redis, tool container |
| Frontend | `3000` dev / `80` prod | `frontend/generate-runtime-config.sh` + Vite | Browser shell for the platform | Backend URL, runtime config |

## Bootstrap Flow

The top-level `run-platform.sh` script is the community bootstrap entry point. In practical terms it:

1. Checks for Git, Python, Docker, and a usable Compose command.
2. Creates or merges service `.env` files.
3. Wires the generated encryption / auth defaults into the backend and platform-service env files.
4. Pulls or builds the service images and then starts the compose stack.

That script is the fastest way to understand deployment intent, but do not treat it as a smoke test. It mutates env files and expects Docker to be healthy.

## Entry Point Notes

- `backend/entrypoint.sh` supports `--migrate` and `--dev`.
- `platform-service/entrypoint.sh` and `runner/entrypoint.sh` support `--dev` for reloading in local debugging.
- `tool-sidecar/entrypoint.sh` intentionally traps SIGTERM in the shell so log processing can finish gracefully.
- `x2text-service/run.py` is a plain Flask launcher that delegates to `app.config.create_app()`.

## When To Read This File

Read this file when a task involves:

- the compose/bootstrap path,
- which service owns a port,
- how the non-backend services are related,
- or why a service is launching but the platform still cannot function.
