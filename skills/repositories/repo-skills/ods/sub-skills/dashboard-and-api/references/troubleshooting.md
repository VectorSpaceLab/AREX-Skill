# Dashboard And API Troubleshooting

Use this guide for ODS dashboard FastAPI/API/UI failures before reaching for full-stack reinstall or broad Docker changes.

## Fast triage

| Symptom | First checks |
| --- | --- |
| Browser dashboard loads but cards stay empty | Check `/api/status` through the same origin; if it is 401, solve Bearer injection; if 502/503, inspect dashboard-api and host-agent reachability. |
| Direct curl to a protected API is 401 | Add `Authorization: Bearer <DASHBOARD_API_KEY>`. Direct curl is not behind dashboard nginx. |
| Direct curl is 403 | A Bearer header was present but the token does not match the running dashboard-api process. Restart/recreate if the env/key file changed. |
| Host edits to dashboard-api appear ignored | You are probably hitting the baked `/app` code in the running container. Use native uvicorn with reload or rebuild/copy into the container. |
| Vite dev UI gets 401s | Vite proxies `/api` but does not perform the production nginx API-key substitution. Test API with an explicit Bearer header or use a dev-only header injection path. |
| Docker dashboard returns 502 after stopping dashboard-api | Stop both `dashboard` and `dashboard-api` and run Vite + native uvicorn, or restart the API container. Docker nginx proxies to service name `dashboard-api:3002`. |
| Host-agent-backed actions fail from native uvicorn | Set `ODS_AGENT_HOST=127.0.0.1` and confirm `ODS_AGENT_PORT`/`ODS_AGENT_KEY`. The container fallback host may not resolve on the host. |
| Owner/Hermes links ask for login repeatedly | Check `ODS_SESSION_SECRET`, `ODS_COOKIE_DOMAIN`, and `/api/auth/admin-session`; browser must receive a valid `ods-session` cookie. |
| Model load, template apply, Talk stream, or extension update times out | Check route-specific nginx timeouts and backend host-agent/model/service progress before shortening request budgets. |

## The baked container trap

Dashboard API source edits on the host do not automatically affect a running `ods-dashboard-api` container.

Why:

1. The dashboard-api image copies top-level Python modules, `performance_evidence.json`, and `routers/` into `/app` at build time.
2. uvicorn starts from `/app` and imports `main:app` from the baked copy.
3. The compose service also mounts the installed ODS tree at `/ods`, but that mount is used for reading config, scripts, manifests, and data context. It is not the Python import root.

Correct debug choices:

- **Preferred for edits:** stop both dashboard containers, run Vite on port `3001`, and run native uvicorn from the dashboard-api source tree on port `3002` with `--reload`.
- **Temporary proof:** copy a changed file into `/app` in the running container and restart dashboard-api. This proves a hot patch only; it is lost on rebuild.
- **Permanent ship:** rebuild the dashboard-api image so `/app` contains the changed source.

Do not rely on a compose `--reload` command that watches the mounted source while still importing from `/app`; reload will fire but re-import the same baked code.

## Native uvicorn + Vite checklist

1. Stop the two containers that own ports 3001/3002:

```bash
docker compose stop dashboard dashboard-api
```

2. Run Vite from the dashboard frontend directory:

```bash
npm install
npm run dev
```

3. Run uvicorn from the dashboard-api directory:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ODS_INSTALL_DIR=<ODS checkout>/ods \
ODS_DATA_DIR=<ODS checkout>/ods/data \
ODS_AGENT_HOST=127.0.0.1 \
ODS_AGENT_PORT=7710 \
DASHBOARD_API_KEY=<dashboard-api-key> \
ODS_AGENT_KEY=<host-agent-key> \
  uvicorn main:app --host 127.0.0.1 --port 3002 --reload
```

4. Open `http://localhost:3001`.

5. If browser API calls fail with 401, remember that production nginx injects the Bearer header but the default Vite proxy does not. Do not remove backend auth. Use explicit Bearer curl/API tests or a local-only proxy header override.

6. Restart production containers when finished:

```bash
docker compose start dashboard dashboard-api
```

## Bearer authentication failures

### 401: no credentials

Protected routes return 401 with `WWW-Authenticate: Bearer` when no Bearer token is supplied. This is expected for direct calls:

```bash
curl http://localhost:3002/api/status \
  -H "Authorization: Bearer <dashboard-api-key>"
```

If the dashboard UI sees 401s in production:

- confirm the dashboard nginx container has `DASHBOARD_API_KEY` or can read `/data/dashboard-api-key.txt`;
- confirm the key matches the dashboard-api process, not an old file after restart/recreate;
- inspect the generated nginx config inside the dashboard container for the `proxy_set_header Authorization` line;
- do not put the key in React source, localStorage, or committed config.

### 403: wrong token

A Bearer token was presented but did not match `DASHBOARD_API_KEY` loaded by the dashboard-api process. Common causes:

- `.env` changed but dashboard-api was not recreated/restarted;
- dashboard and dashboard-api containers read different key sources;
- a dev uvicorn process uses a different `DASHBOARD_API_KEY` than curl/UI tests.

### Generated key surprises

If `DASHBOARD_API_KEY` is empty at startup, dashboard-api generates a random key and writes it to `/data/dashboard-api-key.txt`. That is safe but can surprise development loops. Prefer setting a known local key for test/dev processes, and avoid logging the real production key.

## Session-cookie and magic-link failures

Session surfaces use a signed `ods-session` cookie, not the dashboard Bearer token.

| Failure | Likely cause | Fix |
| --- | --- | --- |
| `POST /api/auth/admin-session` returns 503 | `ODS_SESSION_SECRET` is missing or empty. | Set a 32+ byte random secret and restart dashboard-api. |
| `GET /api/auth/verify-session` returns 401 despite a cookie | Cookie is expired, malformed, signed with a different secret, or scoped to another host/domain. | Re-mint the session and check `ODS_COOKIE_DOMAIN`. |
| Subdomain services do not share login | Cookie domain is host-only or mismatched with the device LAN domain. | Set `ODS_COOKIE_DOMAIN` to the intended device domain when proxy/mDNS is configured. |
| Magic-link redemption fails | Token missing/expired/revoked or session signing not configured. | Generate a fresh link and check session secret. |
| OAuth callback rejected | `state` nonce missing, expired, replayed, malformed, or not issued by dashboard-api. | Restart the OAuth setup flow; do not bypass state validation. |

`verify-session` is intentionally public from a Bearer perspective because reverse proxies use it as `forward_auth`; the cookie is the credential. Do not add the Bearer dependency to that route unless the whole proxy flow is redesigned.

## Host-agent and DNS failures

Dashboard-api depends on the host agent for actions the container cannot safely perform directly: settings writes, service recreates, extension lifecycle, model lifecycle, Wi-Fi setup, updates, some remote-provider operations, Tailscale status, and selected diagnostics.

Check:

```bash
curl http://localhost:3002/api/host-agent/diagnostics \
  -H "Authorization: Bearer <dashboard-api-key>"
```

Common causes:

- **Native uvicorn:** default host resolution may use `host.docker.internal`; set `ODS_AGENT_HOST=127.0.0.1` when the agent listens on loopback.
- **Docker container:** dashboard-api prefers an explicit `ODS_AGENT_HOST`; otherwise it detects the container default gateway via `/proc/net/route`; only then does it fall back to `host.docker.internal`.
- **Custom Docker network:** `host.docker.internal:host-gateway` can resolve to the default bridge gateway, which may be unreachable from the custom ODS network. Gateway detection is there to avoid this class of failure.
- **Auth split:** `ODS_AGENT_KEY` is independent from `DASHBOARD_API_KEY` on newer installs. A valid dashboard Bearer key does not prove host-agent auth is configured.
- **Read-only mounts:** direct file writes from dashboard-api may fail by design; settings writes and compose/lifecycle changes should go through host-agent endpoints.

## Port conflicts

Default ports:

| Port | Owner |
| --- | --- |
| `3001` | dashboard UI nginx or Vite dev server. |
| `3002` | dashboard-api uvicorn container or native uvicorn. |
| `7710` | host agent. |
| `8080` | default local LLM/llama-server API in many ODS modes. |
| `5678` | n8n workflows. |
| `8880` | Kokoro TTS. |

If native Vite/uvicorn refuses to bind, stop the matching container. If Docker nginx 502s, make sure its upstream `dashboard-api` service exists or replace the nginx container with Vite for local dev.

## CORS and same-origin surprises

The FastAPI app allows common local dashboard origins (`localhost`/`127.0.0.1` on 3001 and 3000) and detected LAN dashboard origins. Production normally stays same-origin through nginx, so most browser auth problems are proxy/header/session issues rather than CORS.

If running a custom frontend host/port, set the allowed origins intentionally instead of broadening CORS in code for everyone.

## Route import script failures

The bundled route lister imports `main:app`. Importing dashboard-api executes module-level configuration:

- service manifests may be loaded from `ODS_EXTENSIONS_DIR`;
- host-agent defaults may be resolved;
- `security.py` needs a dashboard API key to avoid random-key generation;
- optional package dependencies from `requirements.txt` must be importable.

If route listing fails:

1. Install the dashboard-api requirements in a disposable environment.
2. Set safe inspection env values such as `DASHBOARD_API_KEY`, `ODS_INSTALL_DIR`, `ODS_DATA_DIR`, and `ODS_EXTENSIONS_DIR`.
3. Re-run:

```bash
python3 sub-skills/dashboard-and-api/scripts/list_dashboard_api_routes.py \
  --api-dir <ODS checkout>/ods/extensions/services/dashboard-api
```

The script is read-only; it does not start uvicorn, call host-agent endpoints, launch Docker, or write repo files.

## Focused validation after a fix

Choose the smallest check that covers the failure:

```bash
# Backend auth/session/routing.
cd <ODS checkout>/ods/extensions/services/dashboard-api
pytest tests/test_routers.py -q
pytest tests/test_auth_router.py -q
pytest tests/test_magic_link.py -q
pytest tests/test_oauth_passthrough.py -q
pytest tests/test_settings_env.py -q
pytest tests/test_host_agent_client.py -q

# Frontend consumer and production build.
cd <ODS checkout>/ods/extensions/services/dashboard
npm run test -- --run src/App.test.jsx
npm run test -- --run src/pages/Settings.test.jsx
npm run test -- --run src/pages/Extensions.test.jsx
npm run test -- --run src/pages/Models.test.jsx
npm run test -- --run src/pages/RemoteProvider.test.jsx
npm run test -- --run src/pages/ODSTalk.test.jsx
npm run build
```

Only run host-mutating endpoint calls, real extension operations, model downloads/loads, service restarts, updates, Wi-Fi changes, or full Docker lifecycle checks when the user explicitly accepts the side effects.
