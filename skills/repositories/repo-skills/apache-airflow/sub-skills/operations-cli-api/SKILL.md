---
name: operations-cli-api
description: "Operate Apache Airflow locally and remotely through installation,
  configuration, CLI, airflowctl, REST API, component, metadata DB, and
  troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operations CLI and API

Use this sub-skill when the task is about running an Airflow environment, choosing between `airflow`, `airflowctl`, and HTTP APIs, inspecting or changing configuration, starting components, testing/backfilling Dags from the command line, or diagnosing metadata DB/API/server state.

## Route First

- For Dag authoring, decorators, task mapping, timetables, or Task SDK code, use `../authoring-task-sdk/` first and return here only for local run/test commands.
- For Helm, Docker image, Kubernetes, Celery, production deployment topology, or chart values, use `../deployment-helm-docker/` and return here only for core component semantics.
- For provider packages, custom providers, hooks, operators, provider CLI commands, or extension metadata, use `../providers-extensions/`.
- For the Go or Java SDKs, treat them as separate specialized skills; use this sub-skill only for Airflow service/API behavior they talk to.

## Core Decision Rules

1. Use the local `airflow` CLI when you are on an Airflow host, need local configuration/metadata DB access, or are starting/checking components such as `airflow scheduler`, `airflow dag-processor`, `airflow triggerer`, `airflow api-server`, `airflow db migrate`, `airflow dags test`, or `airflow tasks test`.
2. Use `airflowctl` when automating operations against a running remote API server: Dags, Dag runs, pools, variables, connections, assets, jobs, xcom, providers, and authentication.
3. Use the Stable REST API when a non-Python/non-shell client needs a durable HTTP contract, pagination, explicit request/response payloads, or integration with external automation.
4. Do not bypass Airflow by writing directly to the metadata DB unless an Airflow command explicitly exists for that operation; prefer CLI/API paths that enforce validation, auth, serialization, and audit behavior.

## References

- `references/cli-reference.md` — verified `airflow` and `airflowctl` command groups, output formats, parser inspection, and safe examples.
- `references/configuration-and-api.md` — `airflow.cfg`, environment variable precedence, REST API vs CLI, Execution API boundary, JWT/auth notes, and airflowctl environment handling.
- `references/operations-workflows.md` — install constraints, local standalone, DB migrate/check/reset, Dag test/backfill, and component health workflows.
- `references/troubleshooting.md` — common operations failures, Airflow 3 CLI migration traps, DB/auth/config/API/Dag parsing diagnosis.
- `scripts/inspect_airflow_cli.py` — safe installed-package parser helper for confirming CLI command groups and imports without depending on the source checkout.

## Fast Workflows

- Inspect installation: `airflow version`, `airflow info --output json`, `airflow providers list --output json`, and `python scripts/inspect_airflow_cli.py --check-imports --which both`.
- Configure local state: set `AIRFLOW_HOME` before first run, use `airflow config get-value <section> <option>`, and prefer `AIRFLOW__{SECTION}__{KEY}` for deployment overrides.
- Start locally: use `airflow standalone` for a disposable all-in-one environment; use separate `airflow api-server`, `airflow scheduler`, `airflow dag-processor`, and `airflow triggerer` commands when debugging components.
- Migrate/check metadata DB: use `airflow db migrate`, `airflow db check`, and `airflow db check-migrations`; avoid SQLite for production deployments.
- Test a Dag file in Airflow 3: use `airflow dags test <dag_id> -f <path-to-dag-file>` instead of the removed `--subdir` flag.

## Safety Notes

- Keep tokens, DB URLs, Fernet keys, and JWT signing keys out of pasted logs and generated files.
- In multi-component deployments, configure shared JWT signing material consistently for the API Server and Scheduler; mismatched or auto-generated per-process keys cause `403` and token validation failures.
- Treat the Execution API as internal Airflow-to-worker/component traffic, not as the public integration API for external clients.
- When using `airflowctl`, configure/login to the intended environment before mutating pools, variables, connections, Dag state, or Dag runs.
