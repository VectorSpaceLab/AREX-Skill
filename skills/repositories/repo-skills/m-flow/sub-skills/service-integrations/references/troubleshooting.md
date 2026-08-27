# Troubleshooting

## Fast checks

Use the bundled status checker first:

```bash
python scripts/service_status_check.py
```

Then confirm the specific service endpoint:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:3000
```

## Common issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Startup warns about default secrets | `MFLOW_ENV` is not a development value, or JWT/token secrets are missing | Set `FASTAPI_USERS_JWT_SECRET`, `FASTAPI_USERS_RESET_PASSWORD_TOKEN_SECRET`, and `FASTAPI_USERS_VERIFICATION_TOKEN_SECRET`; keep `MFLOW_ENV=local` only for development |
| Routes return 401 even though `REQUIRE_AUTHENTICATION=false` | Backend access control is still enabled | `ENABLE_BACKEND_ACCESS_CONTROL=true` also forces authentication; either log in or disable both flags for anonymous local dev |
| `mflow -ui` fails or frontend cannot build | Node.js / pnpm / frontend assets are missing | Install Node, run `pnpm install` in `m_flow-frontend`, or use Docker Compose with the `ui` profile |
| IDE cannot discover MCP tools | Wrong transport, wrong port, or wrong config shape | Use `stdio` for local CLI/IDE, `sse` for Docker at `http://localhost:8001/sse`, and `http` only for streamable HTTP clients |
| MCP remote mode cannot run `learn(...episode_ids=...)` | The remote client does not implement that path | Omit `episode_ids` or use direct mode instead |
| `memorize` appears to finish but the result is unclear | The tool is async and task-tracked | Use `wait=True` or call `memorize_status(task_id=...)` |
| Playground stays offline | Missing `FACE_API_KEY`, companion service, or camera access | Start `fanjing-face-recognition`, set the shared key, and keep the face service on the host on macOS/Windows |
| Cloud sync returns 409 | A sync is already running or the backend is unavailable | Check `/api/v1/sync/status` and wait for the current run to finish |
| Compose startup fails on port binding | Another service already owns the port | Check `8000`, `8001`, `3000`, `5001`, `5432`, `7474`, `7687`, `3002`, `6379`, and `5540` |
| Docker host cannot reach the face service | `localhost` inside Docker does not point to the host | The backend rewrites localhost to `host.docker.internal` when needed; keep the face service URL on localhost and let the container translate it |

## Service-specific signals

### Auth and settings

- `GET /api/v1/settings` should return LLM, vector DB, and embedding configuration.
- `POST /api/v1/settings` should accept a partial JSON payload; empty sections should be omitted.
- If auth cookies seem ignored, confirm the cookie name from `AUTH_TOKEN_COOKIE_NAME` and that the frontend is using the same backend origin.

### MCP

- `memorize` and `save_interaction` create background tasks; `memorize_status(task_id)` is the source of truth for completion.
- If the MCP server is in API mode, remember that the backend endpoint path changes but the tool names do not.

### Playground

- `FACE_API_KEY` must match in both services.
- Linux Docker mode can keep both services in containers.
- macOS/Windows usually need the face-recognition service on the host for camera access.

### UI

- `NEXT_PUBLIC_API_URL` must point to the backend that the browser can reach.
- If the UI opens but the graph stays blank, verify the backend health endpoint first, then the frontend network calls.

## What not to do

- Do not use service scripts to start or stop processes from this sub-skill's helper script.
- Do not run automated playground installers as a default runtime command; the setup is reference-only because it clones an external face-recognition service and downloads model files.
