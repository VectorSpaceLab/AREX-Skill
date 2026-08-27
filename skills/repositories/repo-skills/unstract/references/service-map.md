# Service Map

This file maps the runtime services that make up Unstract. It is the quickest way to understand what starts where, which ports matter, and which sub-skill owns the operational guidance.

## Runtime Services

| Service | Default port | Main entrypoint | Responsibility | Owning sub-skill |
| --- | --- | --- | --- | --- |
| Frontend | `3000` dev / `80` prod | `frontend/generate-runtime-config.sh`, Vite | React SPA, route shell, runtime config | `frontend` |
| Backend | `8000` | `backend/entrypoint.sh` | Django/DRF API, hosted MCP server, workflow APIs | `backend-platform` |
| Platform service | `3001` | `platform-service/entrypoint.sh` | Flask API for SDK / tool integration | `platform-deployment` |
| Runner | `5002` | `runner/entrypoint.sh` | Tool-container orchestration and execution support | `platform-deployment` |
| x2text service | `3004` | `x2text-service/run.py` | Text extraction bridge for document conversion tools | `platform-deployment` / `sdk-and-tools` |
| Tool sidecar | no HTTP port | `tool-sidecar/entrypoint.sh` | Log processing and streaming sidecar | `platform-deployment` |
| Celery workers | per worker (`8080`–`8089`) | `workers/run-worker.sh` | Async task processing for API, workflow, callback, and support queues | `workers` |
| PG-queue consumer | `8090` when enabled | `python -m pg_queue_consumer` | Postgres-backed queue consumer | `workers` |
| PG-queue reaper | `8086` when enabled | `python -m pg_queue_reaper` | Leader-elected recovery loop | `workers` |

## Supporting Infrastructure

| Dependency | Why it matters |
| --- | --- |
| PostgreSQL | Backend metadata, workflow state, execution rows, and some worker queues |
| Redis | Cache, session, result, and log-streaming support |
| RabbitMQ | Celery transport for the non-PG worker fleet |
| MinIO / object storage | File execution, test fixtures, and some integration flows |
| Docker / Docker Compose | Full-stack platform bootstrap and service isolation |

## Startup Relationships

- `run-platform.sh` is the top-level bootstrap script for the community stack.
- `backend/entrypoint.sh` starts Django with Gunicorn and can optionally run migrations first.
- `platform-service/entrypoint.sh`, `runner/entrypoint.sh`, and `x2text-service/run.py` are service-local launchers for the non-Django services.
- `tool-sidecar/entrypoint.sh` keeps SIGTERM handling in the shell so log processing can finish cleanly.
- `workers/run-worker.sh` multiplexes Celery workers, PG-queue workers, health ports, and log tails from one CLI.

## What To Read With This Map

- Use `installation-and-env.md` for the specific environment variables and install commands required by a chosen service.
- Use `troubleshooting.md` for startup failures, missing services, route auth issues, and path-ordering problems.
- Use the relevant sub-skill `SKILL.md` for the workflow itself.
