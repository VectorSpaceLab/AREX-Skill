<!-- SPDX-License-Identifier: Apache-2.0 -->

# Configuration and API Reference

Use this reference to reason about Airflow configuration, environment variables, public API authentication, `airflowctl` remote credentials, and the boundary between public REST API and internal Execution API.

## Configuration Sources

Airflow reads configuration from `airflow.cfg`, environment variables, command-backed values, secret-backed values, provider defaults, and command-line flags. For operations tasks, inspect effective configuration before changing behavior.

Important environment variables:

| Variable | Meaning |
| --- | --- |
| `AIRFLOW_HOME` | Root directory for Airflow content such as `airflow.cfg`, Dags, logs, generated standalone auth files, and local state. Set before first run when you want a non-default home. |
| `AIRFLOW_CONFIG` | Path to a specific `airflow.cfg`. |
| `AIRFLOW__{SECTION}__{KEY}` | Overrides a config key, such as `AIRFLOW__CORE__DAGS_FOLDER` or `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`. |
| `AIRFLOW__{SECTION}__{KEY}_CMD` | Runs a command and uses its output for supported sensitive config values. |
| `AIRFLOW__{SECTION}__{KEY}_SECRET` | Reads a supported sensitive config value from the configured secrets backend. |
| `AIRFLOW_CONN_{CONN_ID}` | Defines a connection URI through the environment. |
| `AIRFLOW_VAR_{KEY}` | Defines a variable through the environment. |
| `AIRFLOW_CLI_TOKEN` | Token used by `airflowctl` when credentials are not loaded from login/keyring. |
| `AIRFLOW_CLI_ENVIRONMENT` | Named `airflowctl` environment to use by default. |
| `AIRFLOW_CLI_API_RETRIES` | Number of remote API retries used by `airflowctl`. |
| `AIRFLOW_CLI_API_RETRY_WAIT_MIN` / `AIRFLOW_CLI_API_RETRY_WAIT_MAX` | Retry backoff bounds for `airflowctl`. |

Use these safe inspection commands:

```bash
airflow config get-value core dags_folder
airflow config list --include-sources --include-env-vars --hide-sensitive
airflow info --output json --anonymize
airflowctl auth list-envs --output json
```

Do not paste unmasked `sql_alchemy_conn`, Fernet keys, JWT signing keys, connection passwords, or tokens into generated files, public logs, issues, or PRs.

## Configuration Values That Commonly Affect Operations

| Area | Config Keys | Why They Matter |
| --- | --- | --- |
| Airflow home/config | `AIRFLOW_HOME`, `AIRFLOW_CONFIG` | Most local confusion starts from using a different home/config than expected. |
| Dags location | `[core] dags_folder`, Dag bundles | Determines what the Dag processor parses and what local `airflow dags test` can find. |
| Metadata DB | `[database] sql_alchemy_conn` | SQLite is fine for tests/local exploration, not production. PostgreSQL/MySQL are production choices. |
| API URL | `[api] base_url`, `[core] execution_api_server_url` | Must match reverse proxy/path-prefix layout so UI/client and workers can reach the correct endpoints. |
| API server type | `[api] server_type` | `uvicorn` is default; `gunicorn` requires the `apache-airflow-core[gunicorn]` extra and Unix. |
| JWT signing | `[api_auth] jwt_secret`, `[api_auth] jwt_private_key_path`, `[api_auth] trusted_jwks_url`, `[api_auth] jwt_algorithm` | Must be consistent where tokens are generated/validated; auto-generated per-process secrets break multi-component auth. |
| Public API token timing | `[api_auth] jwt_expiration_time`, `[api_auth] jwt_cli_expiration_time`, `[api_auth] jwt_leeway` | Controls UI/API token lifetime, CLI token lifetime, and clock-skew tolerance. |
| Execution API token timing | `[execution_api] jwt_expiration_time`, `[execution_api] jwt_audience`, `[scheduler] task_queued_timeout` | Controls worker task token validity and queue timeout behavior. |
| Dag parsing | `[dag_processor] refresh_interval`, `[dag_processor] min_file_process_interval`, `[dag_processor] parsing_processes`, `[core] dagbag_import_timeout` | Affects how quickly new/changed Dags appear and whether import-heavy files time out. |
| Scheduler | `[scheduler] task_queued_timeout`, scheduler loop limits, pool settings | Affects queued task failures and scheduling throughput. |
| State store cleanup | `[state_store] default_retention_days`, `[state_store] state_cleanup_batch_size` | Controls task state store retention cleanup behavior. |

## Public REST API

The Airflow public API is the stable external HTTP surface. In Airflow 3, generated public API paths are under `/api/v2`, with auth endpoints for login/logout/token flows provided by the configured auth manager.

Common resource families include:

- `/api/v2/dags` and nested Dag run/task instance/task endpoints.
- `/api/v2/backfills`.
- `/api/v2/assets` and queued events.
- `/api/v2/connections`.
- `/api/v2/variables`.
- `/api/v2/pools`.
- `/api/v2/providers`.
- `/api/v2/jobs`.
- `/api/v2/plugins`.
- `/api/v2/config`.
- `/api/v2/monitor/health`.
- `/api/v2/version`.

Use the Stable REST API when you need a durable HTTP contract, language-neutral automation, explicit pagination/limits, or integration from CI/CD systems and external tools.

### Public API Authentication

Public API requests use JWTs. A typical flow is:

```bash
ENDPOINT_URL="http://localhost:8080"
TOKEN="$(curl -sS -X POST "${ENDPOINT_URL}/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"<username>","password":"<password>"}' \
  | jq -r .access_token)"

curl -sS "${ENDPOINT_URL}/api/v2/dags" \
  -H "Authorization: Bearer ${TOKEN}"
```

Token extraction precedence for public API requests is `Authorization: Bearer <token>`, OAuth2 query parameter, then `_token` cookie. UI login stores a secure HTTP-only `_token` cookie. CLI token flows use a separate shorter CLI expiration setting.

Public REST API tokens include standard claims such as `jti`, `iss`, `aud`, `sub`, `iat`, `nbf`, and `exp`. Public API/UI tokens can be revoked; revoked `jti` values are tracked in the metadata DB until expiry cleanup.

### CORS and Pagination

- CORS is configured in `[api]` with `access_control_allow_headers`, `access_control_allow_methods`, and `access_control_allow_origins`.
- Because the API returns credentialed responses, configure exact allowed origins; wildcard `*` is rejected/broken for credentialed browser requests.
- The Stable REST API has a page size limit controlled by `[api] maximum_page_limit`.
- Put request payload size limits at the proxy layer for large payload endpoints such as variables.

## airflowctl Authentication and Environments

`airflowctl` is a remote CLI for the public API. It can store named environments and credentials.

Typical setup:

```bash
airflowctl auth login \
  --username <username> \
  --password <password> \
  --api-url http://localhost:8080 \
  --env local
export AIRFLOW_CLI_ENVIRONMENT=local
airflowctl version --remote
airflowctl dags list --output json
```

Alternative token setup:

```bash
export AIRFLOW_CLI_TOKEN=<token>
airflowctl auth login --api-url http://localhost:8080 --env local
```

Security notes:

- `airflowctl` uses public API security and stores tokens in keyring when available.
- If keyring is unavailable, it may use token flags or environment/file credentials; keep these out of shell history and logs.
- CLI JWT token lifetime defaults to the Airflow `[api_auth] jwt_cli_expiration_time` value, typically shorter than browser/API user tokens.
- Use `airflowctl auth list-envs --output json` and `AIRFLOW_CLI_ENVIRONMENT` to avoid accidentally mutating the wrong deployment.

## Execution API Boundary

The Execution API is internal Airflow traffic used by workers, task runtime, the Dag File Processor, and the Triggerer. It is not the public API for third-party automation.

Key distinctions:

| API | Intended Client | Auth/Token Type | Common Use |
| --- | --- | --- | --- |
| Public REST/Core API | UI, `airflowctl`, external clients, local CLI API-backed commands | User/CLI JWT tokens and cookies | Dags, Dag runs, pools, variables, connections, jobs, config, health, logs. |
| Execution API | Workers and internal components | Workload/execution-scoped JWT tokens tied to task instance identity | Task state transitions, heartbeats, runtime XCom/connection/variable/state access. |

Execution API token flow:

1. Scheduler generates a `workload`-scoped JWT for a task instance before dispatch.
2. Worker receives the workload JSON and calls the Execution API `/run` route with the workload token.
3. The server returns a fresh `execution` token in the `Refreshed-API-Token` response header.
4. Worker clients use `execution` tokens for subsequent heartbeats/runtime calls.
5. Execution tokens are refreshed when near expiry; workload tokens are not refreshed.

Execution API safety notes:

- Workload tokens can only start a queued/restarting task and are bounded by `[scheduler] task_queued_timeout`.
- Execution tokens have a short default lifetime and are scoped to a task instance UUID.
- Execution API tokens are not revoked like public REST API tokens; they expire naturally.
- Route enforcement checks token type and `ti:self` task identity, so a worker cannot use its token for another task instance.
- Dag File Processor and Triggerer may use in-process Execution API transport and software guards, but this is not a hard malicious-code isolation boundary. Treat deployment-level isolation as a separate production concern.

## API Server Layout

`airflow api-server` serves both Core/Public API and Execution API by default:

```bash
airflow api-server
# equivalent to all apps, commonly core + execution
```

It can be split intentionally:

```bash
airflow api-server --apps core
airflow api-server --apps execution
```

When deploying behind a path prefix or reverse proxy:

- Set `[api] base_url` so UI/static/API routes resolve correctly.
- Set `[core] execution_api_server_url` so workers can reach the Execution API.
- Keep JWT signing configuration consistent across API/Scheduler and relevant validators.

## Local CLI API Client Boundary

Airflow 3 local CLI commands may call the same typed client used by `airflowctl`, but the operational choice remains:

- Local `airflow` commands are appropriate when the process has the target Airflow installation, local configuration, and service context.
- `airflowctl` is the better default for remote API server operations and operator workstations.
- Stable REST API is the best interface for non-shell automation and long-lived integrations.

If an `airflow` command emits a deprecation warning suggesting an equivalent `airflowctl` command, use the `airflowctl` command in new automation.
