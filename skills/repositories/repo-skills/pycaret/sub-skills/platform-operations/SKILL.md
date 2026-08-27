---
name: platform-operations
description: "Operate PyCaret's self-hosted platform deployment, configuration,
  storage, queues, workers, backups, and runtime health checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Platform Operations

Use this sub-skill when the task is about running or operating the PyCaret
Control Plane rather than changing engine code or web source. It covers local
single-process installs, Docker Compose deployments, production-shaped
Postgres/Redis/MinIO deployments, secrets persistence, object storage,
backup/restore, migrations, worker queues, optional GPU workers, and platform
health checks.

## Route first

1. Identify the install shape:
   - single-process `pycaret-server` process,
   - compact Docker Compose (`api` + `web`, SQLite/local artifacts),
   - production-shaped Compose (`api` + `worker` + Postgres + Redis + MinIO),
   - Kubernetes/Helm or cloud/Terraform target.
2. Load the matching reference:
   - [deployment modes](references/deployment-modes.md) for services, ports, and start/stop commands.
   - [configuration and secrets](references/configuration-and-secrets.md) for `PYCARET_*` settings and Fernet/JWT handling.
   - [backup, restore, and upgrade](references/backup-restore-and-upgrade.md) before touching state, migrations, or images.
   - [GPU workers and queues](references/gpu-workers-and-queues.md) for `default`, `cpu-heavy`, `gpu`, and `inference` worker routing.
   - [troubleshooting](references/troubleshooting.md) when a platform surface is stuck or unhealthy.
3. Prefer bundled, non-secret checks before destructive actions:
   - `python scripts/ops_doctor.py`
   - `bash scripts/check_container_secret_key.sh --data-dir ./data`
4. State clearly when a surface is documented as a future or stub target. Do
   not present Helm or Terraform as production-complete without verifying the
   actual chart/module templates in the user's distribution.

## Common commands

```bash
# Bootstrap and run a direct server install.
pycaret-server init --data-dir ./data
pycaret-server migrate
pycaret-server serve --host 0.0.0.0 --port 8020
pycaret-server doctor

# Compact Docker Compose from a source distribution.
docker compose up --build
docker compose logs -f api
docker compose down          # preserves named volumes
docker compose down --volumes # wipes data volumes

# Production-shaped Compose from a source distribution.
docker compose -f infra/docker/docker-compose.prod.yml up --build

# Redis worker process.
PYCARET_RUNS_BACKEND=redis pycaret-server worker --queues default,cpu-heavy --worker-id worker-1
```

## Boundaries

Route elsewhere for:

- Engine experiment/task API, model lists, `RunConfig`, and `pycaret` library use → `engine-workflows`.
- Editing React/Vite source, routes, or components → `web-ui`.
- Contributor Python style, package tests, release notes, and code changes → `repo-development`.

Keep operations guidance self-contained. Do not rely on a local checkout path,
private environment prefix, or secret value. Never print JWT secrets, Fernet
keys, storage credentials, SMTP passwords, or connection passwords.
