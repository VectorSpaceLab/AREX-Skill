# Deployment Troubleshooting

Use this guide to triage Langflow install, startup, configuration, database, Docker, credential, logging, storage, and multi-worker failures.

## Fast Triage

1. Confirm the command and environment:

```bash
uv run langflow --help
uv run langflow run --env-file .env --log-level info
python scripts/check_env_vars.py --env-file .env --context local
```

2. Check server health:

```bash
curl -fsS http://localhost:7860/health
```

3. Check logs:

```bash
docker compose logs -f langflow
# or for local installs, inspect the configured LANGFLOW_LOG_FILE path
```

4. Separate failures into install/import, config parsing, database, auth/credentials, network/proxy, storage/files, optional dependency, or worker queue categories.

## Install and Import Failures

Symptoms:

- `langflow: command not found`.
- `No module named langflow`.
- CLI import fails before help text appears.
- Provider or model execution imports fail.

Fixes:

- Run inside the intended environment: `uv run langflow --help`.
- Install or upgrade the package: `uv pip install -U langflow`.
- If running from source, use `make init` then `make run_cli`.
- If current CLI import path complains about `openai`, install the missing optional dependency in that environment or use a Langflow distribution/image that includes it.
- Do not assume PyTorch/transformer model execution is available unless those packages and hardware backends were intentionally installed.
- For provider components, install the relevant optional package or bundle and set required provider credentials.

## CLI and `.env` Misuse

Symptoms:

- Port/host does not match `.env`.
- Boolean setting appears ignored.
- `.env` changes do not take effect.
- CLI superuser creation is unavailable.

Causes and fixes:

- CLI flags override `.env`: remove flags such as `--port`, `--host`, or `--no-remove-api-keys` if `.env` should control the value.
- Restart Langflow after changing `.env`; running processes do not automatically reload all settings.
- Boolean values should be plain `true`/`false`, `True`/`False`, `1`/`0`, `yes`/`no`, or use CLI positive/negative flags.
- Use `--env-file path/to/.env` when the file is not in the working directory Langflow expects.
- If `langflow superuser` is disabled, check `LANGFLOW_ENABLE_SUPERUSER_CLI`; production deployments may intentionally disable it.

## Database URL and Migration Problems

Symptoms:

- Startup fails with SQLAlchemy URL errors.
- SQLite file cannot be opened.
- Compose Langflow cannot connect to PostgreSQL.
- Migrations fail or warn about destructive changes.
- Existing flows disappear after changing configuration.

Fixes:

- Validate with:

```bash
python scripts/check_env_vars.py --env-file .env --context docker-compose
```

- For SQLite, use an absolute URL such as `sqlite:////var/lib/langflow/langflow.db`; create the parent directory first.
- For Compose PostgreSQL, use the database service name in the URL, for example `postgres`, not `localhost`.
- Verify username, password, database name, port, and network reachability from the Langflow container.
- Preserve both the database and `LANGFLOW_SECRET_KEY` when moving deployments if encrypted credentials/API keys must keep working.
- Run `langflow migration` before `langflow migration --fix`; apply fix mode only after backup.
- If flows appear missing, verify that the same database URL and config directory/volume are attached as before.

## Docker and Compose Failures

Symptoms:

- Browser cannot reach Langflow though the container is running.
- Container exits immediately.
- PostgreSQL starts but Langflow fails.
- Data disappears after `docker compose down` or image upgrade.
- Custom image starts but bundled flows/components are not loaded.

Fixes:

- Set `LANGFLOW_HOST=0.0.0.0` inside containers and publish `7860:7860`.
- Check `docker compose ps` and `docker compose logs -f langflow postgres`.
- Use `depends_on` for startup ordering, but still allow for PostgreSQL readiness delays; inspect retry logs before restarting repeatedly.
- Use persistent volumes for `/app/langflow` and PostgreSQL data. Avoid `docker compose down -v` unless deleting data is intended.
- Pin image tags for reproducible deployments; do not rely on `latest` for production rollouts.
- For bundled flows, set `LANGFLOW_LOAD_FLOWS_PATH` to the in-image directory and confirm the JSON files exist in the image.
- For custom components, set `LANGFLOW_COMPONENTS_PATH` to the in-container path and ensure dependencies are installed in the image.

## Authentication and API-key Failures

Symptoms:

- API calls return `401` or `403`.
- Visual editor auto-logs in unexpectedly.
- API keys disappear or are invalid after restart.
- All users appear to have superuser access.

Fixes:

- For shared deployments, set `LANGFLOW_AUTO_LOGIN=False`, configure a strong `LANGFLOW_SECRET_KEY`, and create a superuser.
- Keep `LANGFLOW_SECRET_KEY` stable across restarts and image upgrades.
- Avoid `LANGFLOW_REMOVE_API_KEYS=True` unless intentionally stripping keys/tokens from saved flows.
- Create or rotate API keys through a superuser account or the CLI command in a trusted environment.
- If exposing Langflow publicly with `LANGFLOW_AUTO_LOGIN=True`, add a reverse-proxy or network-layer access control; auto-login grants broad visual-editor access.

## Secrets and Provider Credentials

Symptoms:

- Flow runs fail with missing `OPENAI_API_KEY` or similar provider variables.
- Credentials work locally but not in Docker.
- Logs or flow JSON show secrets.

Fixes:

- Inject provider keys through environment variables, a secrets manager, or Langflow global variables; do not bake them into Docker images.
- In Compose, pass required provider variables to the Langflow service, not only to your shell.
- Keep `LANGFLOW_FALLBACK_TO_ENV_VAR` behavior in mind when flows expect variables from the process environment.
- Avoid committing `.env` files containing real credentials.
- Use `LANGFLOW_REMOVE_API_KEYS=True` only when you intentionally want saved flows stripped of key/token values.

## Network and Reverse Proxy Issues

Symptoms:

- `/health` works locally but the public URL fails.
- Uploads fail behind a proxy.
- Streaming, build logs, or playground updates stall.
- Redirect loops or mixed HTTP/HTTPS behavior.

Fixes:

- Confirm proxy routes to internal `host:7860` and preserves the intended path prefixes.
- Match proxy body-size limits to `LANGFLOW_MAX_FILE_SIZE_UPLOAD`.
- Disable proxy buffering or configure streaming-friendly behavior for SSE/WebSocket-like responses.
- Terminate TLS consistently at the proxy, or configure direct `LANGFLOW_SSL_CERT_FILE` and `LANGFLOW_SSL_KEY_FILE` if Langflow terminates TLS itself.
- Check DNS, firewall, container networks, and security groups before changing Langflow settings.

## Logs, Observability, and Metrics

Symptoms:

- No logs are visible in container logs.
- Log collector cannot find files.
- JSON logs are malformed for the collector.
- Metrics endpoint is unreachable.

Fixes:

- For containers, prefer stdout/container logging with `LANGFLOW_LOG_ENV=container` and inspect `docker logs` or the orchestrator log stream.
- If file scraping is required, set `LANGFLOW_LOG_FILE` inside the watched directory and mount that directory.
- Use `LANGFLOW_LOG_LEVEL=debug` only temporarily.
- If enabling Prometheus metrics, verify the Prometheus port/path is exposed only where intended and does not conflict with the app port.
- In production stacks with Prometheus/Grafana/Flower, validate service labels, networks, and credentials independently from Langflow startup.

## File Storage and Upload Failures

Symptoms:

- Uploaded files vanish after restart.
- File-system tool can access too much or too little.
- Large uploads fail before reaching Langflow.
- Permission errors writing logs, storage, or monitor data.

Fixes:

- Persist and back up `LANGFLOW_CONFIG_DIR`.
- Set `LANGFLOW_FS_TOOL_BASE_DIR` to a constrained writable directory; avoid broad host mounts.
- Align `LANGFLOW_MAX_FILE_SIZE_UPLOAD` with reverse-proxy body-size limits.
- Ensure container user permissions allow writing to mounted volumes.
- For object storage, test bucket credentials and network access with a minimal operation before running full flows.

## Multi-worker and Redis Queue Problems

Symptoms:

- Startup refuses multiple workers with the default queue.
- Builds hang or cancel unexpectedly.
- Cancel requests only affect some workers.
- Managed Redis with TLS/auth fails.

Fixes:

- Set `LANGFLOW_JOB_QUEUE_TYPE=redis` on every worker.
- Prefer `LANGFLOW_REDIS_QUEUE_URL` for managed Redis, TLS, or password authentication.
- Use a Redis queue DB separate from cache DB.
- Increase `LANGFLOW_REDIS_QUEUE_STARTUP_GRACE_S` for slow cold starts.
- Tune polling watchdog thresholds only after confirming real abandoned-build behavior.

## Migration from SQLite to Compose PostgreSQL

If the user asks to move from local SQLite to Compose PostgreSQL without losing flows/API keys, require a backup-first plan:

1. Export flows and copy the SQLite database plus `LANGFLOW_CONFIG_DIR`.
2. Preserve `LANGFLOW_SECRET_KEY` if encrypted data or API keys must survive.
3. Start PostgreSQL with a persistent volume.
4. Point `LANGFLOW_DATABASE_URL` to the Compose service hostname.
5. Run migration preview and then fix mode only after backup.
6. Verify login, flow list, API key creation, and a simple no-credential flow run.
7. Keep the SQLite backup until the PostgreSQL deployment has passed acceptance checks.

## Custom Flow Image Validation

If the user asks to package a flow image and validate env/volume settings:

1. Validate flow JSON before building.
2. Ensure the Dockerfile copies flows into the exact `LANGFLOW_LOAD_FLOWS_PATH` directory.
3. Decide whether `LANGFLOW_LOAD_FLOWS_OVERWRITE_ON_NAME_MATCH` should protect UI edits or make image flows authoritative.
4. Keep provider keys out of the image; pass them at runtime.
5. Mount `LANGFLOW_CONFIG_DIR` if the container should preserve edits, generated secrets, logs, and file storage.
6. Run a disposable container first, check `/health`, confirm flows load, and inspect logs for skipped or duplicate flow names.
