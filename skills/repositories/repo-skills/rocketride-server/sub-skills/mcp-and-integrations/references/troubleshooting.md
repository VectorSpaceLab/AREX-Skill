# MCP and integration troubleshooting

Start by classifying the failing edge:

- MCP assistant → `rocketride-mcp` → RocketRide engine WebSocket (`ws://…:5565`).
- n8n → RocketRide HTTP gateway (`http://…:5567/webhook`).
- RocketRide → n8n webhook/API (`http://…:5678/webhook/...` and `/api/v1/...`).

Most failures are wrong protocol/port, wrong credential type, or the wrong
meaning of `localhost` from inside a client/container.

## MCP failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Missing required environment variable: ROCKETRIDE_URI` | MCP server env lacks engine URI. | Set `ROCKETRIDE_URI` to the RocketRide engine WebSocket, e.g. `ws://localhost:5565` or `wss://…`. |
| `Missing required environment variable: ROCKETRIDE_AUTH or ROCKETRIDE_APIKEY` | Neither accepted MCP auth variable is present. | Set `ROCKETRIDE_AUTH` or `ROCKETRIDE_APIKEY`. If both are set, `ROCKETRIDE_AUTH` takes precedence. |
| MCP server starts but cannot connect to RocketRide | Engine not running, URI uses HTTP gateway instead of WebSocket, or auth invalid. | Check that the URI is `ws://`/`wss://` for MCP. Route engine startup and connection checks to the runtime/SDK sub-skills. |
| Running `rocketride-mcp --help` fails or appears to start a server | The entry point is a server command, not a help-aware CLI. | Use `python scripts/mcp_config_smoke.py` for safe config validation instead of invoking the entry point for help. |
| Assistant cannot find `rocketride-mcp` | The MCP client process PATH does not include the Python environment where the package is installed. | Use an absolute command path in the MCP client config or launch the client from an environment where `rocketride-mcp` is on PATH. Do not hardcode private paths in reusable skill content. |
| MCP tool list is empty | No running tasks for that auth key, pipeline stopped, or engine returned no task list. | Start the target pipeline through the proper SDK/IDE/runtime path, then refresh tools. The built-in `RocketRide_Document_Processor` may still appear. |
| Tool call says `filepath is required` | Assistant did not supply the required `filepath` argument. | Ask the assistant/tool caller to pass `{ "filepath": "..." }`. |
| Tool call says `Invalid filepath` or `Filepath must point to a file` | Path cannot be resolved or is not a regular file from the MCP server process. | Use a local path visible to `rocketride-mcp`; check container/remote workspace boundaries and `file://` URI decoding. |
| `Tool "…" not found` | Tool name is not a current running task and not the built-in document processor. | Refresh tool list, restart the pipeline, or use the exact dynamic tool name. |
| Convenience document processor fails to start | Engine unreachable or bundled parser pipeline/node support is unavailable in the runtime. | Treat it as an engine/node runtime issue; the MCP server only starts the bundled `webhook → parse → response` pipeline on demand. |
| SSE endpoint returns 401 | `MCP_API_KEY` is set and request lacks `Authorization: Bearer <token>`. | Add the bearer token or unset `MCP_API_KEY` for an unauthenticated test environment. |
| SSE `/health` is degraded | SSE process is up but cannot reach the RocketRide engine. | Re-check `ROCKETRIDE_URI`/auth and engine reachability. `/health` does not prove pipelines are running. |

## Auth name confusion

| Context | Credential/auth to use | Do not substitute |
| --- | --- | --- |
| `rocketride-mcp` WebSocket client | `ROCKETRIDE_AUTH` or `ROCKETRIDE_APIKEY` | n8n public API key; pipeline `pk_…` public key. |
| n8n RocketRide action node → RocketRide HTTP gateway | Pipeline public authorization key (`pk_…`) as Bearer token | MCP `ROCKETRIDE_AUTH`; n8n public API key. |
| RocketRide `tool_n8n` listing/polling/async | n8n public API key, often `${ROCKETRIDE_N8N_KEY}` | RocketRide engine auth; pipeline `pk_…` key. |
| RocketRide Trigger secret | Shared webhook secret in the incoming `Authorization` header | n8n public API key, unless you intentionally use the same value and accept the risk. |

## n8n → RocketRide failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Credential test fails at `GET /version` | Base URL unreachable or wrong protocol/port. | Use the HTTP gateway base URL, usually `http://127.0.0.1:5567`, not `ws://localhost:5565`. |
| Credential test passes but node run gets 401/403 | Base URL works but pipeline public key is missing, expired, or for a different/stopped pipeline. | Copy the running pipeline's public authorization key (`pk_…`) and ensure that pipeline is still running. |
| `connection refused` with `localhost` | n8n resolved `localhost` to IPv6 `::1` or is running in a container. | On the same host use `http://127.0.0.1:<port>`; across Docker boundaries use `host.docker.internal` or a shared network service name. |
| n8n in Docker cannot call host RocketRide | `localhost` points inside the n8n container. | Use `http://host.docker.internal:5567/webhook` on Docker Desktop, Linux `host-gateway`, or put both services on one Docker network. |
| RocketRide Cloud pipeline cannot be called from n8n using a private URL | URL is not public from n8n's environment, or Cloud/private routing differs. | Use a public HTTPS gateway/interface URL or a tunnel; avoid private LAN/localhost URLs across Cloud boundaries. |
| Chat operation returns unexpected shape | Pipeline is not chat-enabled or response lanes are dynamic. | Use a chat/dropper-compatible source and inspect returned top-level keys plus `_rocketride` metadata rather than assuming `answers`. |
| Upload fails near 16 MB | n8n default payload cap. | Reduce files, split upload, or increase n8n's payload limit with explicit operational approval. |
| Self-signed HTTPS fails | TLS verification rejects the certificate. | Use trusted certificates or enable the node's insecure ignore/verify toggle only for local self-signed development. |

## RocketRide → n8n failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 404 from `/webhook/<path>` | n8n workflow is not activated/published, wrong path, or using a one-shot test URL outside editor listening mode. | Activate the workflow for production `/webhook/...`; use the displayed test URL only while n8n is waiting for a test execution. |
| n8n returns only `Workflow was started` | Workflow did not respond synchronously. | Add **Respond to Webhook** or configure the trigger to respond when the last node finishes. For long runs use async mode. |
| Async mode says API key required | Async polling needs n8n public API access. | Set `ROCKETRIDE_N8N_KEY` or explicit API key, or switch to sync result mode. |
| Agent cannot list workflows/executions | API key missing/invalid or n8n public API disabled/unreachable. | Provide n8n public API key (`X-N8N-API-KEY`) and correct Base URL; keep read-only mode on unless writes are needed. |
| Agent activation/deactivation blocked | `tool_n8n` read-only mode is enabled. | Leave read-only on by default; disable only if the user explicitly wants the agent to mutate workflow activation. |
| `localhost` from RocketRide cannot reach n8n | RocketRide is in a container, remote runtime, or Cloud. | Use `host.docker.internal`, a shared network hostname such as `http://n8n:5678`, or a public/tunnel URL. |
| n8n displays a webhook URL other systems cannot reach | n8n behind Docker/reverse proxy generated internal URLs. | Set n8n's `WEBHOOK_URL` environment variable to the externally reachable base URL. |
| Incoming RocketRide Trigger returns 401 | Secret mismatch or missing `Authorization` header. | Send the configured secret in `Authorization`; `Bearer <secret>` and raw secret forms are accepted. |
| Workflow fails but RocketRide only sees an error | n8n workflow error without centralized handling. | Add an n8n Error Trigger workflow and select it in workflow settings for alerting/dead-lettering. |

## Round-trip debugging

For `RocketRide A → n8n → RocketRide B → n8n → RocketRide A`, check each hop in
order:

1. Pipeline A reaches n8n webhook path with the intended mode (`sync`/`async`).
2. n8n workflow responds, or async polling can find the execution.
3. n8n HTTP Request uses pipeline B's HTTP gateway URL and public pipeline key.
4. Pipeline B response node emits the expected data.
5. n8n Respond to Webhook returns that data to pipeline A.
6. Pipeline A response node consumes the returned lane.

Avoid reusing the same webhook path for both directions unless you have loop
protection. A miswired round trip can recursively call itself.

## Safe local checks

- MCP config only: `python scripts/mcp_config_smoke.py --check-current-env`.
- MCP client JSON only: `python scripts/mcp_config_smoke.py --client-config ./mcp.json`.
- n8n credential reachability: use n8n's credential test for `GET /version`, but
  remember it does not validate a live pipeline `pk_…` key.
- Never use network-bound or credential-bound n8n/Cloud behavior as verified
  evidence unless you actually ran it in the user's target environment.
