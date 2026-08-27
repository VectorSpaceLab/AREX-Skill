# Troubleshooting

Start with read-only evidence. Do not run restart, reset, seed, image-pull, or
profile-changing commands until the user approves the side effects.

## Baseline collection

For development:

```bash
scripts/check-runtime-health.sh --project-dir . --dev
```

For production:

```bash
scripts/check-runtime-health.sh --project-dir . --prod
```

Then, if the user accepts bounded log output:

```bash
docker compose logs --tail=100 api worker web sandbox-provisioner
```

For production, add `-f docker-compose.prod.yml` to Compose commands.

## Symptom table

| Symptom | Likely cause | Safe checks | Next action gate |
| --- | --- | --- | --- |
| Compose reports missing `.env` | Development config file absent. | Confirm file existence only; do not print it. | Ask before running init helper or creating config from template. |
| Compose reports `SANDBOX_PROVISIONER_TOKEN` is required | Token blank or absent. | Report variable name only. | Generate/store a strong token after approval. |
| Production Compose refuses to create services | Required `.env.prod` secrets are blank. | Check required variable names; do not echo values. | User must supply strong persisted secrets. |
| Image pull or build fails | Network, DNS, registry, proxy, or mirror issue. | Capture failing image name and error. | Ask before using mirror helper, setting proxies, or pulling large images. |
| API health endpoint fails | API not running, dependency unhealthy, migration/startup failure, wrong port/proxy. | `docker compose ps`, API logs, Postgres/Redis/MinIO health status. | Restart/rebuild only after identifying failed dependency or approved retry. |
| Web UI unreachable in development | `web-dev` not running, Vite build error, port conflict, API dependency unhealthy. | `docker compose ps web api`, `docker compose logs --tail=100 web api`. | Rebuild/restart only after approval. |
| Production `/api/system/health` is 502/404 | Nginx cannot proxy to API, API unhealthy, wrong path, or custom proxy mismatch. | `docker compose ps web api`, web logs, API logs, direct container health status. | Change proxy/CORS/TLS config only after deployment owner approval. |
| Browser CORS errors | Production cross-origin frontend lacks explicit `YUXI_CORS_ORIGINS`. | Confirm deployment shape: same-origin or cross-origin. | Set exact origins and restart API/worker when approved. |
| SSE/chat stream stalls | Worker not running, Redis unhealthy, proxy buffering/timeouts, run queue blocked. | API/worker logs, Redis health, web proxy config, run endpoint status. | Route to `agent-runtime` after base services are healthy. |
| Lite mode has no knowledge/graph/evaluation routes | Expected `LITE_MODE=true` behavior. | Check Lite env and started service set. | Use full Compose stack if those capabilities are required. |
| Milvus unhealthy | etcd/MinIO dependency issue, volume state, startup delay. | `docker compose ps milvus etcd minio`, Milvus healthcheck/logs. | Restart Milvus/API only with approval. |
| Neo4j auth fails after changing env | Existing volume still has old credentials. | Check logs for auth messages; do not reveal passwords. | Rotate credentials inside Neo4j or recreate volume only with explicit approval. |
| Public images broken in production | Wrong `MINIO_PUBLIC_URL`, missing public bucket object, or direct 9000 URL retained. | Check browser path uses `/minio/public/...`; check web proxy logs. | Do not expose MinIO API publicly; fix proxy/domain config. |
| Sandbox health fails | Missing token, Docker socket unavailable, sandbox image missing, bad network prefix, backend mismatch. | `docker compose ps sandbox-provisioner`, sandbox logs, loopback `/health` in dev. | Pull sandbox image or change backend/network only after approval. |
| OCR engine unavailable | Optional service not started, GPU missing, bad service URL, cloud token absent, provider disabled. | Check selected engine and health UI/API when authenticated; check optional service status. | Start `--profile all` or add cloud token only when user requests that engine. |
| Model-provider call fails | Provider disabled, missing env key, wrong Base URL/model ID, network/provider outage. | UI provider status, variable name presence, logs without secrets. | Run real connectivity tests only when explicitly enabled with credentials. |
| Seed helper fails with initialized DB | Users already exist. | Read error summary only. | Do not force seed; use existing admin flow or disposable reset with approval. |

## Side-effectful commands and safer alternatives

| Command | Why guarded | Safer first step |
| --- | --- | --- |
| `./scripts/init.sh` / PowerShell variant | Writes `.env`, prompts for secrets, pulls images. | Read required variable list; ask user to provide or approve initialization. |
| `scripts/pull_image.*` | Pulls, retags, and removes image tags using mirror assumptions. | Identify the exact failing image and registry error. |
| `make reset` | Deletes Docker volumes and seeds a fresh database. | Collect logs and health statuses; only reset disposable dev stacks. |
| `make seed` | Writes demo departments/users and prints demo credentials. | Use first-admin setup in UI or explicit dev-only seeding. |
| `docker compose down` | Stops services. | Prefer read-only `ps`, `logs`, and health endpoints first. |
| `docker compose up --build` | Starts/rebuilds containers and may pull images. | Ask before changing runtime state. |

## Evidence to capture before routing elsewhere

- Deployment flavor: development, Lite, production, or optional OCR profile.
- Compose file and service names involved.
- Health status of API, worker, web, sandbox-provisioner, Postgres, Redis,
  MinIO, and any selected Milvus/Neo4j/OCR services.
- Whether the failing workflow needs external credentials, model provider
  network calls, GPU OCR, Langfuse, or web search.
- Bounded logs for the directly failing service, with secrets redacted.
- Exact public endpoint checked: `/api/system/health`, web root, or other route.

Once the deployment substrate is healthy, route workflow-specific problems to
the appropriate sub-skill instead of continuing to restart services.
