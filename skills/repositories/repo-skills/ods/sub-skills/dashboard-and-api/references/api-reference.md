# ODS Dashboard API Reference

This reference distills the FastAPI backend used by the ODS dashboard. It is intended for future maintenance and debugging without depending on source docs being open.

## Service role and runtime shape

- Product service: `dashboard-api`.
- Default API port: `3002`.
- FastAPI application object: `main:app`.
- Production container: Python 3.11 slim image, `WORKDIR /app`, command `uvicorn main:app --host 0.0.0.0 --port ${DASHBOARD_API_PORT}`.
- Main container mounts in the installed ODS tree at `/ods` and data at `/data`; Python imports still come from the baked `/app` copy.
- Dashboard frontend uses the API as its single backend. In production the dashboard nginx container on port `3001` proxies `/api/*` to `dashboard-api:3002` and injects the Bearer API key.

Primary source modules:

| Module | Ownership |
| --- | --- |
| `main.py` | FastAPI app, router inclusion, CORS, core health/status/preflight/settings/storage/readiness routes, background service polling. |
| `security.py` | Bearer API key auth via `HTTPBearer(auto_error=False)` and `verify_api_key`. |
| `config.py` | Environment-derived install/data paths, service manifest loading, host-agent URL resolution, feature/persona/template/catalog config. |
| `models.py` | Pydantic response schemas for GPU, services, disk, model, bootstrap, status, and request payloads. |
| `helpers.py` | Service health, LLM metrics, disk/system metrics, uptime, async HTTP clients, cached service states. |
| `gpu.py` | Base GPU detection and metrics; detailed topology/history lives in `routers/gpu.py`. |
| `host_agent_client.py` | Typed host-agent request wrapper and exceptions (`AgentHTTPError`, `AgentUnavailable`, `AgentProtocolError`). |
| `session_signer.py` | HMAC-signed `ods-session` cookie issue/verify for admin sessions and magic-link redemption. |
| `settings.py` | `.env` parsing, field validation, allowed service apply plan, and host-agent availability checks. |

## Authentication and session model

### Bearer API key

Most dashboard-api routes require:

```http
Authorization: Bearer <DASHBOARD_API_KEY>
```

Important behavior:

- If `DASHBOARD_API_KEY` is set, protected endpoints compare the presented token with a constant-time UTF-8 byte comparison.
- If `DASHBOARD_API_KEY` is not set at dashboard-api startup, `security.py` generates a random key, writes it to `/data/dashboard-api-key.txt` with mode `0600`, and still requires Bearer auth.
- The dashboard nginx entrypoint reads `DASHBOARD_API_KEY` from its environment or `/data/dashboard-api-key.txt`, then substitutes that token into nginx `proxy_set_header Authorization "Bearer ..."` rules for proxied `/api/*` requests.
- `DASHBOARD_API_KEY` and `ODS_AGENT_KEY` are distinct. Dashboard API authentication and host-agent authentication should not be collapsed unless explicitly preserving backward compatibility.

### Session cookies and owner access

The dashboard also manages `ods-session` cookies for cookie-gated services:

| Route | Bearer? | Purpose |
| --- | --- | --- |
| `GET /api/auth/verify-session` | No | Validates the `ods-session` cookie for reverse-proxy `forward_auth`; the cookie is the credential. |
| `POST /api/auth/admin-session` | Yes | Trades the admin Bearer key for a signed `ods-session` cookie for the install owner. |
| `GET /auth/magic-link/{token}` and `GET /magic-link/{token}` | No | Redeem a magic-link token and set an `ods-session` cookie. |
| `GET/POST/DELETE /api/auth/magic-link/*` management routes | Yes | Generate, list, revoke, and QR-render invite links. |

`ODS_SESSION_SECRET` must be configured before session issuance. When it is missing, admin-session and magic-link issuance fail loudly instead of minting unverifiable cookies. `ODS_COOKIE_DOMAIN` scopes the cookie across device subdomains when the LAN proxy is configured; empty means host-only cookies.

### Public callback endpoints

Some endpoints are intentionally not Bearer-gated because an external system or reverse proxy must call them:

- `GET /health` for container health checks.
- `GET /api/auth/verify-session` for reverse-proxy session validation.
- `GET /api/oauth/callback` for OAuth provider redirects; security comes from a server-issued single-use `state` nonce.
- Magic-link redemption paths; security comes from the one-time token.
- ODS Talk endpoints validate the browser session in handler code rather than using the Bearer dependency.

Do not add or remove auth dependencies mechanically. Check the route's threat model first.

## Core environment and ports

| Variable or port | Meaning |
| --- | --- |
| `DASHBOARD_API_PORT` / `3002` | API listen port inside and outside the container. |
| `DASHBOARD_PORT` / `3001` | Dashboard UI nginx/Vite port. |
| `BIND_ADDRESS` | Host bind address; default is loopback (`127.0.0.1`). |
| `ODS_INSTALL_DIR` | Installed ODS root from dashboard-api's perspective; container value is `/ods`. |
| `ODS_DATA_DIR` | Data directory from dashboard-api's perspective; container value is `/data`. |
| `ODS_EXTENSIONS_DIR` | Service manifest directory used to populate service health/sidebar/feature data. |
| `GPU_BACKEND`, `GPU_COUNT`, split-mode vars | Dashboard display and model/GPU status inputs; internals belong to `hardware-and-models`. |
| `OLLAMA_URL` / `LLM_URL` / `LLM_API_URL` | LLM backend URL used by setup chat/status probes. |
| `KOKORO_URL`, `N8N_URL`, `TOKEN_SPY_URL` | Service-specific dashboard API targets. |
| `ODS_AGENT_HOST`, `ODS_AGENT_PORT`, `ODS_AGENT_KEY` | Host-agent endpoint and authentication. Native uvicorn usually needs `ODS_AGENT_HOST=127.0.0.1`. |
| `ODS_SESSION_SECRET`, `ODS_COOKIE_DOMAIN` | Session cookie signing and cross-subdomain cookie scope. |

Host-agent-backed routes use `host_agent_client.request_json()` or local wrappers. They typically return 502/503-style errors when the agent is unreachable or the key/host is wrong.

## Route group map

Use the bundled route-list script to get the exact route set for a checkout. The following map is the expected ownership model.

| Owner module | Main routes | Notes |
| --- | --- | --- |
| `main.py` | `/health`, `/gpu`, `/services`, `/disk`, `/model`, `/bootstrap`, `/status`, `/api/status`, `/api/readiness`, `/api/model-readiness`, `/api/preflight/*`, `/api/service-tokens`, `/api/external-links`, `/api/storage`, `/api/settings/*`, `/api/host-agent/diagnostics` | Core status/settings/preflight layer. Settings save/apply uses the host agent to write `.env` and recreate eligible services. |
| `routers/workflows.py` | `/api/workflows`, `/api/workflows/categories`, `/api/workflows/n8n/status`, enable/disable/delete/executions | n8n workflow catalog and lifecycle. Validate workflow ids; do not route general extension semantics here. |
| `routers/features.py` | `/api/features`, `/api/features/{feature_id}/enable` | Hardware-aware feature discovery from manifests and service/GPU status. |
| `routers/setup.py` | `/api/setup/status`, persona routes, `/api/setup/complete`, `/api/setup/test`, `/api/chat`, Wi-Fi setup/status routes | First-run setup and diagnostics. Wi-Fi operations proxy through the host agent. |
| `routers/updates.py` | `/api/version`, `/api/releases/manifest`, `/api/update/dry-run`, `/api/update/status`, `POST /api/update` | Release/update status and host-agent managed update actions. |
| `routers/agents.py` | `/api/agents/metrics`, `/api/agents/metrics.html`, `/api/agents/cluster`, `/api/agents/throughput` | Agent metrics and htmx fragment; HTML output must escape untrusted values. |
| `routers/privacy.py` | `/api/privacy-shield/status`, `/api/privacy-shield/toggle`, `/api/privacy-shield/stats` | Privacy Shield control and stats. Toggle can start/stop containers. |
| `routers/extensions.py` | `/api/extensions/catalog`, detail/progress/logs/install/update/rollback/enable/disable/uninstall/data purge, `/api/storage/orphaned` | Dashboard extension portal. Manifest semantics and compose security belong to `services-and-extensions`; API mutation flow belongs here. |
| `routers/gpu.py` | `/api/gpu/detailed`, `/api/gpu/topology`, `/api/gpu/amd-runtime`, `/api/gpu/history` | Dashboard-facing GPU detail/history. Backend detection internals belong to `hardware-and-models`. |
| `routers/resources.py` | `/api/services/resources`, `/api/services/{service_id}/restart` | Resource cards and service restart calls; restart is host-mutating. |
| `routers/models.py`, `model_state.py`, `model_routes.py` | `/api/models`, Hugging Face search/details/import/avatar, download/load/benchmark/delete/status/cancel, `/api/models/state`, `/api/models/routes/{probe_id}` | Dashboard model library and lifecycle. Model catalog/runtime internals belong to `hardware-and-models`. |
| `routers/remote_provider_status.py` | `/api/remote-provider/status`, peer model routes, plan/probe/apply | Remote GPU/provider dashboard flow. Be careful with secret redaction and URL validation. |
| `routers/templates.py` | `/api/templates`, preview, apply | Service-template selection and install preview/apply. Apply can start several services. |
| `routers/auth.py` | `/api/auth/verify-session`, `/api/auth/admin-session` | Cookie session validation and admin session minting. |
| `routers/magic_link.py` | owner-card status, generate, QR, list, revoke, redemption paths | LAN owner/invite flow; token and session secrecy are critical. |
| `routers/oauth_passthrough.py` | `/api/oauth/init`, `/api/oauth/callback`, `/api/oauth/pending`, `/api/oauth/providers` | Agent-driven OAuth callback capture. Init/pending/providers require Bearer; callback relies on nonce state. |
| `routers/talk.py` | `/api/talk/status`, session, message, stream, attachment, audio-message, speak | ODS Talk chat/voice/vision bridge. Uses session cookies and long-running/streaming responses. |
| `routers/tailscale.py` | `/api/tailscale/status` | Host-agent proxied Tailscale status. |
| `routers/usage.py` | `/api/usage/readiness`, `/api/usage/report` | Token-spy/local runtime usage reporting and remediation actions. |
| `routers/voice.py` | `/api/voice/status` | Voice service readiness. |
| `routers/node.py` | `/api/node/capabilities` | Node/device capability summary. |

## Response and schema ownership

- Pydantic response models in `models.py` cover stable core shapes such as `GPUInfo`, `ServiceStatus`, `DiskUsage`, `ModelInfo`, `BootstrapStatus`, `FullStatus`, and preflight request payloads.
- Many router endpoints intentionally return plain dictionaries because they aggregate host-agent responses, service manifests, or optional runtime probes. For those, tests should assert key fields, status behavior, auth gates, and redaction rather than overfitting every optional field.
- Settings endpoints intentionally return secret fields with blank public values. Never send stored secrets back to the browser. Saving form values preserves existing secrets when blanks are submitted unless a supported clear action is requested.
- Host-agent exception classes should map to meaningful API responses: host-agent unreachable is a user-actionable 503, protocol errors are server-side issues, and upstream host-agent HTTP errors should preserve useful detail without leaking secrets.

## Change recipes

### Add a protected API route

1. Pick the owning router from the route group map. Create a new router only when no existing group owns the capability.
2. Add `api_key: str = Depends(verify_api_key)` or `dependencies=[Depends(verify_api_key)]` unless the route is deliberately public/cookie/nonce protected.
3. If the route touches the host, filesystem, Docker, Wi-Fi, model lifecycle, settings, updates, or extensions, route mutating actions through the host agent when the dashboard-api container has read-only mounts.
4. Add tests for no-auth rejection, success with Bearer header, input validation, and host-agent failure mapping.
5. Update the frontend consumer only after the response contract is stable enough for focused tests.

### Add or change a frontend-backed route

1. Confirm the frontend page/hook/component endpoint in `references/frontend-workflows.md`.
2. Preserve production nginx Bearer injection assumptions. Direct browser `fetch('/api/...')` usually carries no explicit Authorization header because nginx injects it.
3. If a dev-only proxy/header is needed, keep it local or clearly scoped; do not weaken backend auth.
4. Add or update Vitest coverage for the hook/page behavior and pytest coverage for the backend route.

### Diagnose API route drift

Run the bundled lister against the dashboard-api source tree:

```bash
python3 sub-skills/dashboard-and-api/scripts/list_dashboard_api_routes.py \
  --api-dir <ODS checkout>/ods/extensions/services/dashboard-api --json
```

Check route ownership, method/path collisions, unexpected public routes, and endpoints that moved between modules.
