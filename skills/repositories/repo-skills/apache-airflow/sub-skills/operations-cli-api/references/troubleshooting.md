<!-- SPDX-License-Identifier: Apache-2.0 -->

# Troubleshooting

Use this guide to diagnose common Airflow operations failures without reopening source docs. Prefer read-only inspection first, then targeted fixes.

## First Triage Commands

```bash
airflow version
airflow info --output json --anonymize
airflow config list --include-sources --include-env-vars --hide-sensitive
airflow db check
airflow db check-migrations
airflow dags list-import-errors --output json
python scripts/inspect_airflow_cli.py --check-imports --which both
```

For remote/API issues:

```bash
airflowctl auth list-envs --output json
airflowctl version --remote --env <env-name>
curl -sS <api-url>/api/v2/monitor/health -H "Authorization: Bearer <token>"
```

## Installation Fails or Airflow Imports Break

Symptoms:

- `pip install apache-airflow` succeeds but `airflow version` fails.
- Dependency resolver chooses incompatible package versions.
- Providers import but operators/hooks fail at runtime.
- Python version is unsupported.

Likely causes:

- Airflow installed without version-matched constraints.
- Provider extras installed separately without the same constraints.
- Unsupported Python version or non-Linux production environment assumptions.
- Installing through tooling that does not preserve Airflow's constraints workflow.

Fix:

```bash
AIRFLOW_VERSION=3.3.0
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

If a provider extra is needed, install it with the same Airflow version and constraint URL. Use a clean virtual environment when dependency state is uncertain.

## `AIRFLOW_HOME` or Config Confusion

Symptoms:

- CLI uses a different DB, Dags folder, or config than expected.
- `airflow standalone` created files in an unexpected location.
- `airflow dags list` and the UI disagree.

Checks:

```bash
echo "$AIRFLOW_HOME"
echo "$AIRFLOW_CONFIG"
airflow info --output json --anonymize
airflow config get-value core dags_folder
airflow config get-value database sql_alchemy_conn
```

Fix:

- Set `AIRFLOW_HOME` before first initialization when using a non-default home.
- Use `AIRFLOW_CONFIG` only when intentionally pointing at a custom config file.
- Prefer `AIRFLOW__{SECTION}__{KEY}` for deployment overrides and inspect effective values with `airflow config list --include-sources`.
- Ensure the API server, scheduler, Dag processor, triggerer, and workers receive the configuration they need for their role.

## Metadata DB Migration or Connectivity Errors

Symptoms:

- API server/scheduler exits on startup.
- `airflow db check` fails.
- Components report migrations are not complete.
- A fresh production DB has missing tables.

Checks:

```bash
airflow db check
airflow db check-migrations
airflow config get-value database sql_alchemy_conn
```

Fix:

- Run `airflow db migrate` for schema creation/upgrades.
- Use `airflow db migrate`, not old `airflow db upgrade` guidance.
- Ensure the DB user can create/alter tables during migration.
- Do not use SQLite in production; use PostgreSQL or MySQL.
- If a cleanup command failed mid-way, inspect archived tables created by `airflow db clean` and use `airflow db drop-archived` only after confirming they are safe to drop.

## Scheduler Is Not Parsing or Running Dags

Symptoms:

- Dag is missing from UI or `airflow dags list`.
- Scheduler appears alive but no new runs are created.
- `airflow dags test` fails before executing tasks.
- Task state changes unexpectedly.

Separate the concerns:

| Concern | Component/Command | What to Check |
| --- | --- | --- |
| File discovery/parsing | Dag processor, `airflow dags list-import-errors`, `airflow dags report` | Python import errors, file location, parsing timeouts, heavy top-level code. |
| Scheduling | Scheduler, `airflow jobs check`, pools/concurrency | Dag schedule semantics, paused Dag, pools, concurrency, queued timeouts. |
| Task execution | Worker/executor, task logs, `airflow tasks test` | Worker dependencies, runtime config, task heartbeat, external side effects. |

Debug workflow:

```bash
airflow config get-value core dags_folder
airflow dags list-import-errors --output json
airflow dags report --output json
airflow dags test <dag_id> -f <path-to-dag-file>
airflow tasks test <dag_id> <task_id> <logical-date-or-run-id>
airflow jobs check --job-type SchedulerJob --allow-multiple
```

Important Airflow 3 migration note: `airflow dags test` no longer uses the old `--subdir` flag. Use `-f <path-to-dag-file>` when testing a specific file.

If scheduled runs appear late, confirm the data interval semantics before treating it as failure. Cron/timedelta schedules run after the period they cover has ended.

## `airflow dags test` Fails After Using `--subdir`

This is a common Airflow 2-to-3 failure.

Symptoms:

- Command errors with unrecognized `--subdir`.
- Dag file is outside the configured `dags_folder`.
- User expects `--subdir` to point to one file.

Fix:

```bash
airflow dags test <dag_id> -f <path-to-dag-file>
```

Then check:

```bash
airflow dags list-import-errors --output json
airflow config get-value core dags_folder
```

If the Dag still cannot import, install missing provider/task dependencies in the same environment and remove expensive top-level imports/network calls from the Dag file.

## API Authentication or Token Errors

Symptoms:

- Public API returns `401` or `403`.
- UI works but curl/automation fails.
- CLI token expires unexpectedly.
- Multiple components reject each other's JWTs.

Checks:

```bash
airflow config get-value api_auth jwt_expiration_time
airflow config get-value api_auth jwt_cli_expiration_time
airflow config get-value api_auth jwt_secret
airflow config get-value api_auth jwt_private_key_path
airflowctl version --remote --env <env-name>
```

Avoid printing real secrets in shared logs. When collecting diagnostics, mask values.

Fix:

- Obtain a fresh token through the configured auth manager endpoint or `airflowctl auth login`.
- Send `Authorization: Bearer <token>` for public API calls.
- Confirm server clocks are synchronized; JWT validation checks time claims with limited leeway.
- Configure shared JWT signing material for components that generate/validate tokens. Auto-generated per-process secrets are not suitable for multi-component deployments.
- Check reverse proxy/path prefix settings: `[api] base_url` for UI/API clients and `[core] execution_api_server_url` for worker Execution API calls.

## airflowctl Remote API Errors

Symptoms:

- `airflowctl` talks to the wrong deployment.
- `airflowctl` reports missing/expired token.
- Keyring is unavailable.
- API URL was saved but token storage failed.
- Remote version check fails.

Checks:

```bash
airflowctl auth list-envs --output json
echo "$AIRFLOW_CLI_ENVIRONMENT"
airflowctl version --remote --env <env-name>
```

Fix:

- Re-run `airflowctl auth login --api-url <api-url> --env <env-name>` for the target environment.
- Set `AIRFLOW_CLI_ENVIRONMENT` explicitly in scripts.
- If keyring is unavailable, use `AIRFLOW_CLI_TOKEN` or `--api-token`, but protect the token from logs and shell history.
- Tune `AIRFLOW_CLI_API_RETRIES`, `AIRFLOW_CLI_API_RETRY_WAIT_MIN`, and `AIRFLOW_CLI_API_RETRY_WAIT_MAX` only after confirming URL/auth correctness.
- Use `airflowctl version --remote` before mutating remote Dags, variables, pools, or connections.

## Public REST API URL, CORS, or Proxy Errors

Symptoms:

- Browser UI fails API calls behind a prefix.
- Curl works locally but fails through proxy.
- CORS preflight fails.
- Workers cannot reach Execution API after URL prefix changes.

Checks:

```bash
airflow config get-value api base_url
airflow config get-value core execution_api_server_url
curl -i <api-url>/api/v2/monitor/health
```

Fix:

- Set `[api] base_url` to the externally visible API/UI URL, including path prefix when used.
- Set `[core] execution_api_server_url` to the route workers should use for Execution API calls.
- Configure exact CORS origins in `[api] access_control_allow_origins`; do not use `*` for credentialed API calls.
- Ensure proxy forwards `Authorization` headers and cookies.

## Execution API or Worker Token Errors

Symptoms:

- Worker fails to mark task running.
- Execution API returns `403` for task runtime calls.
- Long-queued tasks fail before starting.

Checks:

- Confirm Scheduler and API Server share JWT signing configuration.
- Confirm `[execution_api] jwt_audience` matches validators.
- Confirm `[scheduler] task_queued_timeout` is large enough for executor queue latency.
- Confirm worker can reach `[core] execution_api_server_url`.

Do not replace this with direct metadata DB access from workers. Workers should communicate through the Execution API, and tasks receive scoped tokens tied to their task instance identity.

## Optional Graphviz or Dag Image Failures

Symptoms:

- `airflow dags show --save output.png` fails.
- `airflow dags show --imgcat` fails or produces unreadable output.

Fix:

- Install Graphviz system binaries and Python dependencies required by the environment.
- Use DOT output or a simpler format when image rendering is unavailable.
- Do not treat Graphviz failures as Dag parsing failures unless `airflow dags list-import-errors` also reports import problems.

## Deprecated or Removed Airflow 2 CLI Flags

Common migration fixes:

| Old Guidance | Airflow 3 Path |
| --- | --- |
| `airflow dags test --subdir <path> <dag_id>` | `airflow dags test <dag_id> -f <path>` |
| `airflow db upgrade` | `airflow db migrate` |
| Local state-changing `airflow` commands with deprecation warning | Equivalent `airflowctl` command when operating through the API server. |
| Assuming `airflow users` always exists | Enable/use the relevant auth manager/provider, such as FAB, or use configured auth-manager workflows. |

## Choosing Between `airflow`, `airflowctl`, and REST API

If a user asks which interface to automate for pools, variables, and Dag runs:

- Choose `airflowctl` for operator scripts against a running Airflow API server when shell commands are acceptable.
- Choose the Stable REST API for application integrations, CI systems, or non-shell clients.
- Choose local `airflow` only when the script intentionally runs on an Airflow host with local config/metadata DB access or needs local Dag parsing/testing.
- Never choose direct DB writes for normal pool/variable/Dag run operations.

## Escalation Clues

Escalate from this sub-skill when:

- The failure depends on Helm chart values, Docker image build, Kubernetes ingress, executor pods, Celery workers, or production secrets management — use `../deployment-helm-docker/`.
- The failure is a Dag code/import/task design problem — use `../authoring-task-sdk/`.
- The failure is inside a specific provider hook/operator/auth manager/executor — use `../providers-extensions/`.
