---
name: control-plane-api
description: "Use PyCaret's FastAPI Control Plane backend: CLI, configuration,
  auth, workspaces, experiments, runs/trials, data sources, deployments,
  storage, LLM advisories, schedules, webhooks, and API tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# control-plane-api

Use this sub-skill when the task is about the PyCaret Control Plane backend:
`pycaret-server`, FastAPI route behavior, TestClient/API usage, bootstrap and
auth, workspaces/projects/experiments, run and trial lifecycles, data sources
and catalog connections, artifact storage, pipeline promotion, registry and
deployment serving, monitoring/drift/schedules/webhooks, backup/restore, or
LLM advisory endpoints.

The behavior in this skill is distilled for PyCaret 4.0 / `pycaret-server`
`0.1.0a0`. It is intended to be usable without reopening the source checkout.

## Route first

- Engine algorithm/task recipes, task classes, typed result dataclasses, model
  lists, or notebook-only workflows → `engine-workflows`.
- React/Vite components, TypeScript API client, UI route wiring, or frontend
  tests → `web-ui`.
- Docker Compose, Helm, Kubernetes, production port/proxy layout, cloud
  infrastructure, host backups, or operator runbooks → `platform-operations`.
- Contributor policy, migrations as a code change, release notes, CI, or
  monorepo maintenance conventions → `repo-development`.

## Read the bundled references

1. [API reference](references/api-reference.md) for route families, auth,
   request/response shapes, and the domain model.
2. [CLI and configuration](references/cli-and-config.md) for `pycaret-server`
   commands, `PYCARET_*` settings, and isolated TestClient fixtures.
3. [Run lifecycle](references/run-lifecycle.md) for `dispatch_run`, Run/Trial/Job
   semantics, plan behavior, artifact storage, promotion, and serving.
4. [LLM advisories](references/llm-advisories.md) for provider settings,
   `LLMRouter`, the six advisory endpoints, and the no-side-effect rule.
5. [Troubleshooting](references/troubleshooting.md) for predictable bootstrap,
   auth, SQLite/migration, secret-key, data-source, storage, run, WebSocket,
   deployment, LLM, schedule/webhook, and GPU-queue failures.

## Safe smoke scripts

These scripts create temporary SQLite databases and artifact directories. They
never touch the caller's default `pycaret.db` or `./artifacts` unless you modify
them.

```bash
python scripts/server_smoke.py --help
python scripts/server_smoke.py --json

python scripts/run_lifecycle_smoke.py --help
python scripts/run_lifecycle_smoke.py --plan setup --timeout-s 60 --json
python scripts/run_lifecycle_smoke.py --plan create --model-id lr --timeout-s 180 --json
```

If running from a source checkout with `uv`, prefix the command in the usual
way, for example:

```bash
uv run --package pycaret-server python scripts/run_lifecycle_smoke.py --plan setup
```

## Common backend entry points

```bash
pycaret-server version
pycaret-server init --data-dir ./data
pycaret-server migrate
pycaret-server serve --host 127.0.0.1 --port 8020
pycaret-server doctor
pycaret-server worker --queues default,gpu --worker-id worker-1
```

Important HTTP entry points:

- App metadata: `GET /`, `GET /healthz`, `GET /docs`, `GET /openapi.json`.
- First run: `GET /api/v1/setup/status`, `POST /api/v1/setup/bootstrap`.
- Auth: bearer JWT in `Authorization: Bearer <access_token>` or programmatic
  key in `X-PyCaret-Key`.
- Submit runs: `POST /api/v1/experiments/{experiment_id}/runs` with a
  `RunCreate` body. Poll `GET /api/v1/runs/{run_id}` or block with
  `POST /api/v1/runs/{run_id}/wait?timeout_s=...`.
- Live run events: `GET /api/v1/runs/{run_id}/events` or WebSocket
  `/api/v1/runs/{run_id}/events/ws?token=<access_token>`.
- Serve a deployed pipeline: `POST /api/v1/deployments/{endpoint_slug}/predict`
  with `{"rows": [{...}]}`.

## Non-negotiables

- LLM calls are advisory only. They may create an `LLMConsultation` audit row
  and return `suggested_config_json`, `suggested_action`, `reasoning_summary`,
  and `risk_flags`; they must not directly execute runs, deploy, delete, or
  mutate production state.
- Preserve the Run/Trial split: a Run is the user action; Trials are candidate
  pipelines; Jobs are queueable worker units.
- Use temp-dir-backed SQLite for tests and smoke checks. Do not rely on a
  private environment prefix or absolute checkout path in examples.
- Treat `PYCARET_SECRETS_KEY` as persistent state. If it changes, encrypted LLM
  keys, connection passwords, webhooks, and other secrets may become unreadable.
- Deployment endpoints are version-pinned. A deployment should point at one
  exact pipeline/model version; create a new version or explicitly roll back
  rather than mutating completed artifacts.
