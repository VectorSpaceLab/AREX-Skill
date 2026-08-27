---
name: deployment-runtime-and-operations
description: "Operate Bindu CLI, runtime deployment, source packaging, storage
  and scheduler backends, migrations, observability, tunneling, and
  repo-maintenance workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Deployment, Runtime, and Operations

Use this sub-skill for `bindu` CLI process control, local serve modes, boxd deployment, source packaging, storage/scheduler selection, observability, tunneling, migrations, and checkout maintenance.

## References and helper

- `references/cli-and-runtime.md` — `serve`, `deploy`, `logs`, `shell`, runtime-boxd, dry-run, and provider behavior.
- `references/storage-scheduler-observability.md` — memory/Postgres, memory/Redis, owner backfill, health/metrics, OTLP/Sentry.
- `references/source-packaging-and-secrets.md` — file inclusion/exclusion, `.binduignore`, secret dropping, tarball cap.
- `references/repo-maintenance.md` — repo commands, generated-code policy, contribution gotchas.
- `references/troubleshooting.md` — CLI/runtime/storage/telemetry/tunnel symptoms.
- `scripts/bindu_runtime_preflight.py` — safe local CLI, port, env-key-presence, and source-package preflight.

## Command map

| Need | Command |
|---|---|
| Start core for SDKs | `bindu serve --grpc` |
| Run a script that calls `bindufy()` | `bindu serve --script PATH` |
| Preview boxd deploy | `bindu deploy SCRIPT --runtime=boxd --dry-run` |
| Deploy to boxd | `bindu deploy SCRIPT --runtime=boxd` |
| Stream VM logs | `bindu logs AGENT` |
| Open VM shell | `bindu shell AGENT` |

## Safety

Start with `--dry-run` for deployments. Inject secrets with `--env KEY=VALUE`; do not ship `.env`, key, cert, or credential files. Use memory backends locally, Postgres/Redis for persistence/distribution, and live cloud/database actions only after the user approves the environment.
