# Platform Stack Configuration

## Environment precedence

The repository uses three related default files:

- `autogpt_platform/.env.default` for shared/platform values.
- `autogpt_platform/backend/.env.default` for backend services.
- `autogpt_platform/frontend/.env.default` for Next.js and auth values.

Copy each default to a local `.env` only when it is absent. Docker Compose loads
`env_file` values into containers; explicit Compose `environment` values and the
shell can override them. Next.js reads `.env`, not `.env.default`, when running
outside Docker.

Never commit a local `.env`, API key, OAuth secret, database password, or
production data export.

## Service and development commands

From `autogpt_platform/`:

| Command | Purpose | Side effect |
| --- | --- | --- |
| `make init-env` | Create missing env files | Writes only missing files |
| `make start-core` | Start Postgres, Redis, RabbitMQ | Starts containers |
| `make stop-core` | Stop core services | Stops containers, keeps data |
| `make logs-core` | Follow core logs | Read-only |
| `make migrate` | Deploy Prisma migrations and generate artifacts | Mutates selected DB |
| `make run-backend` | Run backend locally | Long-lived process |
| `make run-frontend` | Run Next.js locally | Long-lived process |
| `make test-data` | Create backend test data | Writes DB records |
| `make load-store-agents` | Load store fixtures | Writes DB records |

## Local AutoPilot transport

For a self-hosted OpenAI-compatible endpoint, configure the backend `.env` with
at least:

```bash
CHAT_USE_LOCAL=true
CHAT_BASE_URL=http://host-or-lan-address:11434/v1
CHAT_API_KEY=non-empty-local-value
CHAT_FAST_STANDARD_MODEL=<bare-model-name>
```

From inside containers, `127.0.0.1` points to the container. Use a reachable
host/LAN address or an explicitly configured `host.docker.internal` route.
Local transport does not automatically reuse `OPENAI_API_KEY` as
`CHAT_API_KEY`. The local chat path uses the fast OpenAI-compatible transport;
extended-thinking SDK behavior is not available on that path.

Set a context window of at least 24k, preferably 32k, on the local model
server when its default is smaller than AutoPilot's system prompt and tool
schemas. The server's actual context window, not a frontend setting, controls
compaction.

## Port and profile assumptions

The documented defaults are frontend 3000, WebSocket 8001, and REST/execution
API 8006. `docker compose --profile local up deps_backend -d` is the lightweight
profile for host-run frontend/backend development. Always inspect the active
Compose file and environment before changing a client base URL.
