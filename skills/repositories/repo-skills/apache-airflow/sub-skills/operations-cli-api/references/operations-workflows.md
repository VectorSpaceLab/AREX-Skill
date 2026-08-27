<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operations Workflows

Use these playbooks for local installation, configuration checks, database operations, component startup, Dag testing, backfills, and safe maintenance.

## Install Airflow Reproducibly

Airflow is both a library and an application. Installing without constraints can produce an unusable dependency set. Prefer supported Python versions and version-matched constraints.

```bash
AIRFLOW_VERSION=3.3.0
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

`uv pip install` can be used with the same constraint URL in a virtual environment. For provider extras, install them with the same Airflow version and constraints, for example `apache-airflow[celery,postgres]==${AIRFLOW_VERSION}`. Only `pip` and `uv` follow the supported installation workflow; tools such as Poetry or pip-tools need converted constraints and are not the standard path.

Airflow 3.3 verified package facts for this skill:

- `apache-airflow` 3.3.0
- `apache-airflow-core` 3.3.0
- `apache-airflow-task-sdk` 1.3.0
- `apache-airflow-ctl` 0.1.5
- `apache-airflow-providers-standard` 1.15.0

## Install airflowctl

`airflowctl` can be installed as a user tool or in an environment:

```bash
pipx install "apache-airflow-ctl==0.1.5"
# or
uv tool install "apache-airflow-ctl==0.1.5"
# or in an environment
pip install "apache-airflow-ctl==0.1.5"
```

For quick checks, `uvx apache-airflow-ctl --help` or `pipx run` can run the tool without a permanent install.

## Local Standalone Workflow

Use `airflow standalone` for disposable local exploration.

```bash
export AIRFLOW_HOME="$HOME/airflow"
airflow standalone
```

What it does:

1. Creates `$AIRFLOW_HOME` and `airflow.cfg` if missing.
2. Initializes/migrates the metadata DB.
3. Creates a user for local login.
4. Starts the API server, scheduler, Dag processor, and triggerer.

Airflow 3 simple-auth passwords may be stored in `$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated`. If the terminal does not show the password, inspect that file locally rather than assuming a default password.

Use standalone for quick starts only. For production-like debugging, run components separately.

## Component Startup Workflow

```bash
export AIRFLOW_HOME="$HOME/airflow"
airflow db migrate
airflow db check
airflow api-server --port 8080
airflow scheduler
airflow dag-processor
airflow triggerer
```

Component roles:

| Component | Command | Operational Role |
| --- | --- | --- |
| API Server | `airflow api-server` | Serves UI, public REST/Core API, and Execution API by default. |
| Scheduler | `airflow scheduler` | Creates Dag runs, schedules task instances, enqueues work through the executor, and generates worker workload tokens. |
| Dag Processor | `airflow dag-processor` | Parses Dag files in separate processes and stores serialized Dags for scheduler/API use. Runs user Dag import code. |
| Triggerer | `airflow triggerer` | Runs async triggers for deferrable tasks. Runs user trigger code and uses internal Execution API paths. |
| Worker | Executor-specific | Executes tasks through Task SDK runtime and communicates through the Execution API rather than direct metadata DB access. |

`airflow api-server` uses `uvicorn` by default. `gunicorn` mode requires the `apache-airflow-core[gunicorn]` extra, Unix support, and `[api] server_type = gunicorn` or `AIRFLOW__API__SERVER_TYPE=gunicorn`.

## Database Workflow

Local/dev setup:

```bash
airflow db migrate
airflow db check
airflow db check-migrations
```

Production notes:

- SQLite is suitable for tests and local exploration, not production.
- Use PostgreSQL or MySQL for production metadata DBs.
- Create an empty database and grant Airflow permissions to create/alter tables before running `airflow db migrate`.
- `airflow db migrate` is safe to run repeatedly; it applies outstanding migrations.
- Legacy `airflow db upgrade` guidance is outdated for Airflow 3.

Dangerous/local-only commands:

| Command | Risk |
| --- | --- |
| `airflow db reset` | Burns down and rebuilds metadata DB; use only for disposable local environments. |
| `airflow db downgrade` | Schema downgrade can be destructive or incompatible; validate and back up first. |
| `airflow db shell` | Direct DB access can bypass Airflow validation; read-only inspection only unless you know the recovery plan. |

Metadata cleanup:

```bash
airflow db clean --clean-before-timestamp "2026-01-01T00:00:00+00:00" --dry-run
airflow db clean --clean-before-timestamp "2026-01-01T00:00:00+00:00" --yes --error-on-cleanup-failure
```

For large DBs, consider `--skip-archive`, table selection, Dag filters, and batch sizes to reduce lock duration. Back up before deletion.

Task state store cleanup:

```bash
airflow state-store cleanup-task-state-store --dry-run
airflow state-store cleanup-task-state-store
```

This cleans expired `MetastoreBackend` task state store rows only. Asset store rows and custom state-store backends are skipped by this command.

## Dag Parsing and Local Test Workflow

Use this when a user asks why a Dag is missing, failing to parse, or `airflow dags test` fails.

```bash
airflow config get-value core dags_folder
airflow dags list-import-errors --output json
airflow dags report --output json
airflow dags test <dag_id> -f <path-to-dag-file>
airflow tasks test <dag_id> <task_id> <logical-date-or-run-id>
```

Airflow 3 file-specific testing:

- Use `airflow dags test <dag_id> -f <path-to-dag-file>`.
- Do not use old Airflow 2 `--subdir` guidance.
- If `-f` still fails, check Python import errors, missing provider packages, `AIRFLOW_HOME`, `dags_folder`, top-level Dag code, and parse timeouts.

Dag parse debugging checklist:

1. Confirm the active `AIRFLOW_HOME` and `AIRFLOW_CONFIG`.
2. Confirm `core.dags_folder` or Dag bundle configuration.
3. Run `airflow dags list-import-errors --output json`.
4. Run `airflow dags report --output json` for DagBag load details.
5. Ensure required provider packages and task dependencies are installed in the same environment.
6. Reduce heavy top-level code in Dag files; Dag parsing runs repeatedly.
7. Tune `[dag_processor] min_file_process_interval`, `[dag_processor] parsing_processes`, `[dag_processor] dag_file_processor_timeout`, and `[core] dagbag_import_timeout` only after confirming code/import issues.

## Backfill Workflow

Use backfill when you intentionally need historical Dag runs over a date interval.

```bash
airflow backfill create \
  --dag-id <dag_id> \
  --from-date 2026-01-01 \
  --to-date 2026-01-07 \
  --max-active-runs 2
```

Before creating a backfill:

- Confirm the Dag parses and appears in `airflow dags list`.
- Confirm the intended data interval and timezone semantics.
- Confirm task idempotency; Airflow is not a streaming engine, and reruns should not duplicate external side effects.
- Use dry-run options when available for the specific command path.

## Remote Operations with airflowctl

Setup:

```bash
airflowctl auth login \
  --username <username> \
  --password <password> \
  --api-url <api-url> \
  --env <env-name>
export AIRFLOW_CLI_ENVIRONMENT=<env-name>
```

Daily checks:

```bash
airflowctl version --remote
airflowctl dags list --output json
airflowctl jobs list --output json
airflowctl pools list --output json
airflowctl variables list --output json
airflowctl connections list --output json
```

Mutation safety:

1. Run a read/list command against the selected environment first.
2. Use JSON/YAML input files checked into the automation repository for import commands.
3. Avoid passing secrets on the command line when an environment or secret manager can supply them.
4. Preserve the target `--env`/`AIRFLOW_CLI_ENVIRONMENT` in scripts to avoid accidental production changes.

## Stable REST API Workflow

Use the REST API for non-shell automation.

```bash
ENDPOINT_URL="http://localhost:8080"
TOKEN="<jwt>"

curl -sS "${ENDPOINT_URL}/api/v2/monitor/health" \
  -H "Authorization: Bearer ${TOKEN}"

curl -sS "${ENDPOINT_URL}/api/v2/dags?limit=100" \
  -H "Authorization: Bearer ${TOKEN}"
```

Prefer the API when:

- A CI/CD system or external service needs to trigger, pause, list, or inspect resources.
- You need pagination and typed request payloads.
- The automation should not have metadata DB credentials or local Airflow configuration.

Avoid using the Execution API directly. It is for Airflow internals and workers.

## Health and State Checks

Useful checks:

```bash
airflow db check
airflow db check-migrations
airflow jobs check --job-type SchedulerJob --allow-multiple
airflow dags list-import-errors --output json
curl -sS http://localhost:8080/api/v2/monitor/health
```

When the scheduler appears stuck:

- Confirm the scheduler process is alive and heartbeating.
- Confirm the metadata DB is reachable and migrations are complete.
- Confirm the Dag processor is parsing files and import errors are absent.
- Confirm pools/concurrency limits are not blocking task scheduling.
- Remember scheduled Dags run after the data interval closes; daily schedules often appear one period late by design.

When Dags do not appear:

- Check the Dag processor, not only the scheduler.
- Confirm file location and `dags_folder`/bundle settings.
- Check import errors and parsing timeouts.
- Avoid heavy top-level network/database work in Dag files.

## Production Boundary Reminder

This sub-skill explains core components and operational commands. For production deployment details such as Docker image customization, Helm chart values, Kubernetes executor topology, Celery workers, logs, secrets, PGBouncer, ingress, and rolling upgrades, route to `../deployment-helm-docker/`.
