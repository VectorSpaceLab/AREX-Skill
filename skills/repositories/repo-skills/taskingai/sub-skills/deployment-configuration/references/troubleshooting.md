# TaskingAI deployment troubleshooting

Use this reference for deployment and environment failures. First classify whether the symptom is a topology/configuration problem. If the health and routing layer is correct but the failure is about TaskingAI object behavior, provider/model semantics, or plugin bundle execution payloads, route to the sibling owner named in the final column.

## Triage order

1. Identify the public entry point: protocol, hostname, port, and reverse proxy.
2. Identify which service is failing: console/frontend, nginx, backend web, backend API, inference, plugin, Postgres, Redis, or object storage.
3. Check service health separately from functional calls. Health success does not prove provider credentials, S3 upload, or plugin execution.
4. Compare runtime env values with the deployment shape. Most reachability issues come from using host URLs inside containers or Compose DNS names outside Docker.
5. Check version alignment before assuming a config variable is ignored.
6. Only after deployment checks pass, route into backend API, inference-provider, or plugin-bundle semantics.

## Symptom matrix

| Symptom | Likely causes | Recovery steps | Route if deployment checks pass |
| --- | --- | --- | --- |
| Console does not open at the expected URL. | Nginx not running, host port not published, port conflict, wrong `HOST_URL` shared with user, frontend container missing, firewall/proxy issue. | Confirm the external URL and host port; inspect proxy/container status; check port binding; verify `/` routes to the console service; update `HOST_URL` to match the URL users actually open. | Deep console React internals are out of scope. |
| Console loads but API calls fail, show 404/502/connection errors, or login cannot reach the server. | Nginx route mismatch for `/api/v1/`; `backend-web` unhealthy; backend cannot reach DB/Redis; wrong public base URL in frontend/browser context. | Check `/api/v1/` proxy separately from `/`; inspect `backend-web` health; validate `POSTGRES_URL`, `REDIS_URL`, and secrets; confirm nginx routes `/api/v1/` to the web-purpose backend. | `../backend-api/` for web/auth/API object behavior. |
| SDK or direct API calls to `/v1/` fail but console web routes work. | Nginx route mismatch for `/v1/`; `backend-api` unhealthy; API-purpose backend missing required env; DB/Redis unavailable. | Check `/v1/health_check` via the public proxy and inside the service network if allowed; inspect API-purpose backend env; verify DB/Redis URLs and service health. | `../backend-api/` for request/response semantics. |
| Backend API/web cannot reach inference. | `TASKINGAI_INFERENCE_URL` points to `localhost` from inside a container; Compose DNS name used from a host process; wrong port; URL includes `/v1`; inference service unhealthy; custom network DNS mismatch. | Determine the backend network namespace. For Compose backend containers, use an origin like `http://backend-inference:8000`. For host-run backend, use a host-reachable inference origin. Test `GET <origin>/v1/health_check` from the backend namespace when command execution is allowed. Remove any extra `/v1` suffix from the configured origin. | `../inference-providers/` if health works but provider/model calls fail. |
| Backend API/web cannot reach plugin. | `TASKINGAI_PLUGIN_URL` points to `localhost` from inside a container; Compose DNS name used from a host process; wrong port; URL includes `/v1`; plugin service unhealthy; custom network DNS mismatch. | Determine the backend network namespace. For Compose backend containers, use an origin like `http://backend-plugin:8000`. For host-run backend, use a host-reachable plugin origin. Test `GET <origin>/v1/health_check` from the backend namespace when command execution is allowed. Remove any extra `/v1` suffix from the configured origin. | `../plugin-bundles/` if health works but bundle/plugin calls fail. |
| Inference health check passes but provider calls fail. | Missing provider API key, invalid provider credential, blocked outbound network, proxy needed, provider URL blocked, model schema mismatch. | Do not treat this as a deployment-stack failure unless the user only asked for provider connectivity. Confirm network/proxy/env presence, then hand off provider-specific debugging. | `../inference-providers/`. |
| Plugin health check passes but plugin execution fails. | Missing bundle credentials, storage misconfiguration, blocked outbound network, local/S3 path issue, bundle-specific payload problem. | First audit object storage and public URL settings in this sub-skill. If storage is valid, hand off bundle execution details. | `../plugin-bundles/`. |
| Generated files/images return broken URLs in browser. | `HOST_URL` not public, wrong protocol/port, missing reverse-proxy route, local volume not shared, S3 public domain missing or private, icon/image prefix env mismatch. | Confirm returned URL origin matches the browser-accessible deployment URL; check nginx image/icon routes; audit `OBJECT_STORAGE_TYPE`; for S3, check public-domain and bucket policy; for local, check shared writable volume. | `../plugin-bundles/` for bundle-specific output behavior. |
| Provider icons or plugin icons are missing. | Nginx icon paths not proxied to inference/plugin; image/icon prefix env variable mismatch for the running image tag; inference/plugin unhealthy. | Verify `/images/providers/icons/` routes to inference and `/images/plugins/bundles/icons/` routes to plugin; set the prefix variable expected by the running image tag; keep image tags and env examples aligned. | `../inference-providers/` or `../plugin-bundles/` for catalog contents. |
| `OBJECT_STORAGE_TYPE=s3` selected but uploads fail or service starts with missing env errors. | Missing `S3_ACCESS_KEY_ID`, `S3_ACCESS_KEY_SECRET`, `S3_ENDPOINT`, bucket name, public domain, or plugin `S3_IMAGE_BUCKET_NAME` fallback; invalid credentials; bucket not public; temporary path unwritable. | Run the S3 audit in [configuration](configuration.md). Set all required variables consistently for backend and plugin services. Ensure `PATH_TO_VOLUME` is still writable for temporary files. Do not exercise plugin/API flows until the missing variables are fixed. | `../plugin-bundles/` only after storage connectivity and URLs are valid. |
| `OBJECT_STORAGE_TYPE=local` selected but files disappear after restart. | `PATH_TO_VOLUME` is inside an ephemeral container filesystem or not backed by a persistent volume; services do not share the same volume. | Mount persistent storage at the configured path; use a shared volume for backend and plugin services that create/serve generated files; restart services after env/volume changes. | `../plugin-bundles/` for bundle-specific file generation. |
| Backend cannot connect to Postgres. | Wrong `POSTGRES_URL`, credentials mismatch with database env, database not healthy, pgvector image not running, host/container DNS confusion. | Validate URL host from backend namespace (`db` in the source Compose network, host/IP in standalone mode); align database username/password/db name; check database health and logs; preserve volumes during upgrades. | `../backend-api/` if database is reachable but application migrations/object behavior fail. |
| Backend cannot connect to Redis. | Wrong `REDIS_URL`, Redis password mismatch, Redis not healthy, DB index mismatch, host/container DNS confusion. | Align Redis command password and backend URL; use `cache` host in the source Compose network or a host-reachable address in standalone mode; check Redis health. | `../backend-api/` if cache is reachable but application behavior fails. |
| Services restart repeatedly at startup. | Missing required env, unsupported `OBJECT_STORAGE_TYPE`, invalid integer env such as port/max connections, database/cache unavailable, port already in use for standalone services. | Inspect first startup exception; validate required env from [configuration](configuration.md); fix unsupported storage type; confirm dependencies are healthy; avoid changing many variables at once. | Sibling sub-skills only after services are stable. |
| Health checks fail even though logs look normal. | Health route path/port mismatch, service still starting, container lacks `curl` or health command support in custom image, wrong exposed internal port. | Confirm the service listens on the expected internal port; test the health path from inside the service network if allowed; align health-check command with the image; allow enough startup time for DB/cache-dependent services. | Sibling sub-skills only if health works. |
| Health checks pass but console/API behavior is from an old version. | Stale images, partial pull/upgrade, mixed image tags, old containers still running, reverse proxy pointed at old project/network. | Check actual running image tags; pull/update all related TaskingAI service images together; recreate containers; ensure the proxy points to the intended project/network; preserve data volumes unless intentionally migrating. | `../backend-api/`, `../inference-providers/`, or `../plugin-bundles/` for versioned behavior details. |
| Login with default admin credentials fails on an existing deployment. | Database already initialized with different credentials, env changed after first setup, wrong backend-web instance, JWT/session secret rotation. | Treat defaults as initial-bootstrap values, not guaranteed persistent credentials. Confirm the web backend and database state; use the deployment's admin recovery process if available; avoid deleting database volumes unless data loss is acceptable and authorized. | `../backend-api/` for auth object/API behavior. |
| After secret rotation, stored provider/plugin credentials stop working. | `AES_ENCRYPTION_KEY` changed after credentials were encrypted; backend/inference/plugin do not share the same encryption key. | Restore the prior key if encrypted data must remain readable, or re-enter credentials after a planned rotation. Keep the key identical across TaskingAI services in the same deployment. | `../inference-providers/` or `../plugin-bundles/` for credential validation semantics. |
| Compose command fails before services start. | Docker daemon unavailable, image pull/network failure, invalid env file syntax, missing reverse-proxy config, port conflict, insufficient disk/permissions. | Fix host-level Docker access; retry image pulls when network is available; validate env file syntax; choose a free host port; ensure mounted directories are writable. | Not a TaskingAI application semantics issue. |

## Difficult case: backend cannot reach inference or plugin

Use this explicit diagnostic flow when a user reports errors such as connection refused, DNS resolution failure, timeout, or upstream 502 while backend operations call model/provider or plugin functionality.

1. Ask where the backend process runs:
   - Same Compose network as inference/plugin.
   - Host process outside Compose.
   - Custom orchestrator/network.
2. Read the configured origins:
   - `TASKINGAI_INFERENCE_URL`
   - `TASKINGAI_PLUGIN_URL`
3. Check for the two most common mismatches:
   - `localhost` inside a backend container: wrong, because it points to the backend container itself.
   - Compose service DNS from a host process: wrong, unless the host is joined to that Docker network or has equivalent DNS.
4. Confirm the value is an origin only. If it ends with `/v1` or `/v1/health_check`, replace it with the service origin.
5. Test health from the backend namespace when allowed:
   - inference: `<TASKINGAI_INFERENCE_URL>/v1/health_check`
   - plugin: `<TASKINGAI_PLUGIN_URL>/v1/health_check`
6. Recovery:
   - For source-like Compose backend containers, use `http://backend-inference:8000` and `http://backend-plugin:8000`.
   - For host-run backend processes, publish or otherwise expose the inference/plugin ports and use host-reachable URLs.
   - For custom orchestrators, use that platform's service DNS and port.
7. If health succeeds but the operation still fails, route to provider or plugin semantics rather than continuing deployment debugging.

## Difficult case: `OBJECT_STORAGE_TYPE=s3` with missing variables

Use this explicit validation when a user selects S3 storage or reports upload/file URL failures after switching to S3.

1. Confirm `OBJECT_STORAGE_TYPE=s3` is set for every service expected to create or serve generated files.
2. Required S3 access fields:
   - `S3_ACCESS_KEY_ID`
   - `S3_ACCESS_KEY_SECRET`
   - `S3_ENDPOINT`
3. Required bucket fields:
   - `S3_BUCKET_NAME` for backend/Compose compatibility.
   - `S3_IMAGE_BUCKET_NAME` for plugin image outputs, or a confirmed plugin fallback to `S3_BUCKET_NAME`.
4. Required URL/public-access field:
   - `S3_BUCKET_PUBLIC_DOMAIN`, because returned file URLs must be public-reachable by clients.
5. Required local temporary field:
   - `PATH_TO_VOLUME` must point to a writable temporary location even in S3 mode.
6. If any value is absent or empty, report a configuration validation failure before attempting runtime tests. Example:

```text
OBJECT_STORAGE_TYPE=s3 is selected, but the deployment is missing S3_ENDPOINT and S3_BUCKET_PUBLIC_DOMAIN. Set the S3 endpoint, bucket, credentials, public domain, and writable PATH_TO_VOLUME for backend/plugin services before retrying uploads.
```

7. If all values exist but uploads still fail, check credentials, bucket policy/public access, endpoint compatibility, and network egress. Plugin bundle execution details belong to `../plugin-bundles/` after storage is proven valid.

## Health-check expectations

| Service role | Health path or command | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Backend API/Web | `GET /v1/health_check` on the service port | Service process is up enough to answer health. | Correct DB migrations, valid API payloads, or successful provider/plugin calls. |
| Inference | `GET /v1/health_check` on the service port | Inference service process is up. | Provider API keys, external provider reachability, or model execution. |
| Plugin | `GET /v1/health_check` on the service port | Plugin service process is up. | Bundle credentials, S3 upload, generated file public access, or plugin payload validity. |
| Postgres | `pg_isready` in the database container/process context | Database process accepts readiness check. | Correct app schema or credentials from backend's point of view. |
| Redis | Authenticated `PING` | Redis process and password auth work. | Application cache behavior. |

## Safe recovery practices

- Change one layer at a time: public URL/proxy, service URL, storage mode, database/cache, then provider/plugin credentials.
- Preserve database and object-storage volumes during upgrades unless the user explicitly accepts data loss.
- Never publish the source example secrets or default admin password in an exposed deployment.
- Keep image tags, env examples, and route assumptions from one compatible release set.
- When logs mention request validation, missing env, or unsupported storage type, fix configuration before retrying functional API calls.
- When logs mention provider or bundle validation after all deployment checks pass, route to the appropriate semantic sub-skill.

## Native-test and skip guidance

A full self-host stack test is useful but optional. It is safe to skip when Docker, network image pulls, open ports, disk, S3 credentials, or provider credentials are not available or not approved. For deployment-level verification without full startup, use static checks:

- Required env variables are present for the selected service roles.
- Inter-service URLs match the runtime network namespace.
- `OBJECT_STORAGE_TYPE` is exactly `local` or `s3`.
- S3 mode has all required S3 variables and a writable temporary path.
- Local mode has a writable persistent volume and public `HOST_URL`.
- Image tags and env variable names are not mixed across incompatible releases.

If the user authorizes native startup, expected deployment-level success is healthy backend, inference, plugin, database, and cache services plus a reachable console at the configured public URL. Do not require provider execution or plugin bundle execution for this sub-skill's deployment verification.
