# Platform troubleshooting

Start with non-secret diagnostics:

```bash
pycaret-server doctor
python scripts/ops_doctor.py
bash scripts/check_container_secret_key.sh --data-dir ./data
curl -f http://localhost:8020/healthz
```

Do not paste secret values into logs, tickets, prompts, or terminal captures.

## Docker daemon and build failures

| Signal | Likely cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop/Engine is stopped or inaccessible | Start Docker, wait until it is healthy, retry `docker compose up`. |
| Build hangs during Python dependency install | Slow network or low Docker memory | Increase Docker memory to at least 6 GB for builds; retry. |
| `no space left on device` during build | Docker image/cache volume full | Run `docker system df`, then prune unused images/containers only when safe. |
| `/bin/sh^M: bad interpreter` | Windows CRLF line endings on scripts | Re-check out with LF line endings or normalize scripts before building. |

## Port conflicts

| Signal | Fix |
|---|---|
| `bind: address already in use` on API port `8020` | `PYCARET_API_PORT=8030 docker compose up` or stop the process using the port. |
| `bind: address already in use` on UI port `3020` | `PYCARET_WEB_PORT=3030 docker compose up` or stop the process using the port. |
| UI loads but API calls hit the wrong service | Confirm nginx/proxy routes `/api` to the API service and browser origin matches `PYCARET_CORS_ORIGINS`. |

## Database failures

| Signal | Likely cause | Fix |
|---|---|---|
| `pycaret-server doctor` reports `database FAIL` | Wrong `PYCARET_DATABASE_URL`, DB down, missing driver, or network blocked | Check URL backend and host; install `pycaret-server[postgres]` for Postgres; verify DB accepts `SELECT 1`. |
| Non-SQLite production startup fails on empty DB | Explicit migrations were not run | Run `pycaret-server migrate --revision head` before starting the API. |
| SQLite reset needed during dev | Local schema/data can be discarded | `pycaret-server migrate --reset-dev`; this refuses non-SQLite URLs. |
| Restore creates inconsistent rows/artifacts | DB and object store backups came from different windows | Restore matching DB/object snapshots; then migrate and smoke test. |

## Redis and worker failures

| Signal | Likely cause | Fix |
|---|---|---|
| `redis SKIP` in doctor | `PYCARET_RUNS_BACKEND=inprocess` | Healthy for single-process mode. |
| `redis FAIL` in doctor | `PYCARET_RUNS_BACKEND=redis` but Redis is unreachable | Check `PYCARET_REDIS_URL`, network, Redis health, and credentials if any. |
| `pycaret-server worker` exits with Redis unreachable | Worker refuses to start without Redis | Start/fix Redis, then restart the worker. |
| Jobs stay `queued` | No worker listening on that queue, wrong queue list, or worker cannot claim resources | Check `/api/v1/admin/queues`, worker command, and logs. |
| `gpu` jobs are repeatedly requeued | CPU-only worker is listening on `gpu` or CUDA devices are hidden | Start a GPU-visible worker; set `CUDA_VISIBLE_DEVICES` correctly; remove CPU-only workers from `gpu`. |

## Storage failures

| Signal | Likely cause | Fix |
|---|---|---|
| `unknown PYCARET_STORAGE_BACKEND` | Typo or unsupported value | Use `local`, `s3`, or `minio`. |
| S3 driver errors about missing bucket | `PYCARET_STORAGE_BUCKET` is unset | Set bucket and ensure it exists or run the MinIO bootstrap. |
| `boto3 is not installed` | S3/MinIO backend selected without optional dependency | Install `pycaret-server[s3]` in the API and worker environments. |
| Artifact download/prediction cannot fetch object | DB row points at missing local file/S3 key, wrong bucket, or credentials changed | Check URI scheme, bucket, object existence, and storage credentials. Restore matching artifacts from backup if missing. |
| Local artifact check fails | Directory missing or permission denied | Create the artifact directory with API/worker write permissions; ensure the container volume is mounted. |

## Secrets and key rotation

| Signal | Likely cause | Fix |
|---|---|---|
| Decrypt error mentioning `PYCARET_SECRETS_KEY` | Fernet key changed, was lost, or was ephemeral across restart | Restore the previous key or re-enter affected secrets. Use `check_container_secret_key.sh` to validate presence/format. |
| Secrets worked before `docker compose down --volumes` and now fail | The data volume containing DB/artifacts/key was wiped | Restore the volume backup or re-bootstrap and re-enter secrets. |
| Multiple API replicas disagree on secrets | Different `PYCARET_SECRETS_KEY` values | Inject one shared key through the orchestrator secret store. |
| Need JWT rotation | Existing sessions will be invalidated | Rotate during maintenance; shorten refresh-token TTL beforehand if needed. |

Do not log Fernet keys, JWT secrets, DB passwords, storage access keys, SMTP
passwords, LLM keys, or datasource credentials.

## Notebook backend

| Signal | Likely cause | Fix |
|---|---|---|
| Notebook iframe shows backend unavailable | `PYCARET_NOTEBOOK_BACKEND=local` | This is expected in local placeholder mode. Switch to `docker` only where Docker is available. |
| Docker notebook open fails | Docker daemon unavailable, image pull failed, or network misconfigured | Start Docker, pre-pull the notebook image, set `PYCARET_NOTEBOOK_NETWORK`, and inspect `docker ps`/container logs. |
| Notebook container starts but cannot see data/API | Missing volume or network access | Configure notebook data directory/network and verify the container can reach required endpoints. |

## Web/API proxy and CORS

| Signal | Likely cause | Fix |
|---|---|---|
| UI loads but `/api` calls return 404 | API not healthy yet or nginx proxy target is wrong | Wait for API health; check web container config and API logs. |
| Browser CORS errors | Origin not in `PYCARET_CORS_ORIGINS` | Set a JSON-array origin list matching the exact browser scheme/host/port. |
| Deep links 404 in UI container | SPA fallback/proxy config not active | Confirm nginx serves `index.html` for unmatched UI paths. |

## Backup/restore pitfalls

- Always preserve the Fernet key with the DB containing encrypted rows.
- API backup/restore endpoints are useful for local/small deployments but do not
  replace native S3/MinIO object-store mirroring in production-shaped installs.
- After restore, run migrations, doctor, and an authenticated UI/API smoke test.
