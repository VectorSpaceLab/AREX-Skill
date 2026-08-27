# Deployment Notes

Read this when you need to start Cognee as a service, choose a Compose profile,
launch the UI, or reason about public ports and container networking.

## Compose profile map

The Compose file exposes a few independent service groups.

| Service | Profile | Purpose | Public ports |
| --- | --- | --- | --- |
| `cognee` | default | Main API/backend service. | `8000` and debugger `5678`. |
| `cognee-mcp` | `mcp` | MCP server for IDE / client integration. | Host `8001` maps to container `8000`; debugger `5679`. |
| `frontend` | `ui` | Next.js UI. | `3000`. |
| `neo4j` | `neo4j` | Optional graph database backend. | `7474`, `7687`. |
| `postgres` | `postgres` | Optional relational backend. | `5432`. |
| `redis` | `redis` | Optional cache / session backend. | `6379`. |

## Common launch patterns

### API backend

```bash
python -m cognee.api.client
```

Use `--agent-mode` if you want the agent-mode default port.

### Full local UI stack

```bash
cognee-cli -ui
```

This starts the browser UI, the API backend, and the MCP server together.
It is the quickest way to get a full local service stack without wiring the
pieces manually.

### Cloud or local service connection

| Command | Meaning |
| --- | --- |
| `cognee serve` | Connect to Cognee Cloud or a local instance. |
| `cognee serve --url http://localhost:8000` | Connect to a local backend directly. |
| `cognee serve --logout` | Disconnect and clear saved credentials. |
| `cognee push ...` | Upload a local dataset graph to a remote instance. |

### MCP server

| Transport | Typical use |
| --- | --- |
| `stdio` | Local client / shell integration. |
| `sse` | Streaming clients and most desktop MCP hosts. |
| `http` | Web deployments and explicit HTTP endpoints. |

## Frontend build notes

The frontend is a Next.js application. At a high level, the public workflow is:

```bash
npm install
npm run dev
npm run build && npm start
```

Notes:

- The Compose `ui` profile builds and runs the frontend container.
- The UI stack assumes a working Docker runtime; on macOS that usually means
  Docker Desktop or Colima, and on Linux it means a compatible Docker engine.
- If the UI needs to call a backend running on the host, use a host-reachable
  address rather than raw `localhost` inside the container.

## Service hardening checklist

### API server

- Set `CORS_ALLOWED_ORIGINS` for explicit browser origins.
- Use `UI_APP_URL` only as a fallback origin, not as a wildcard replacement.
- Keep `REQUIRE_AUTHENTICATION` aligned with `ENABLE_BACKEND_ACCESS_CONTROL`.
- Bind to `127.0.0.1` for local-only testing, or to a controlled interface for shared deployments.

### MCP server

- Use `MCP_CORS_ALLOW_ORIGINS` for browser-based MCP apps.
- Use `MCP_ALLOWED_HOSTS` only when you intentionally expose the HTTP transport beyond loopback.
- Leave DNS rebinding protection enabled unless you know why it must be disabled.
- Keep the transport choice aligned with the host environment: `stdio` for local pipes, `sse` or `http` for networked clients.

### Long-running services

- `cognee-cli -ui`, the API server, and the MCP server are long-running processes.
- Start them in separate terminals or container sessions if you need to inspect logs.
- Use background flags only when the command explicitly supports them.
- Expect `cognee-cli push` and `cognify` to take a while on large datasets.
