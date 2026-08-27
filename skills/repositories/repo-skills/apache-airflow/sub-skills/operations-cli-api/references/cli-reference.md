<!-- SPDX-License-Identifier: Apache-2.0 -->

# CLI Reference

This reference distills Airflow 3.3 command-line behavior verified from installed package facts, parser source, generated CLI docs, and live parser inspection. Use it to choose a safe command path without reopening the source repository.

## CLI Surfaces

| Surface | Runs Where | Talks To | Best For | Avoid For |
| --- | --- | --- | --- | --- |
| `airflow` | Airflow environment/host | Local config, metadata DB, local API client, components | Component startup, DB migration/checks, local Dag parsing/test, local config/provider inspection | Remote-only clients without the Airflow runtime/config |
| `airflowctl` | Operator workstation or automation environment | Airflow public API server | Remote Dags, Dag runs, pools, variables, connections, jobs, xcom, assets, auth | Starting Airflow services or direct metadata DB migration |
| Stable REST API | Any HTTP-capable client | Airflow public API server under `/api/v2` plus auth endpoints | Durable integrations, typed payloads, pagination, language-neutral automation | Internal task execution APIs or operations needing local files/config |

`airflow` remains necessary for local service and database operations. Many state-changing operational commands in Airflow 3 are API-backed or deprecated toward `airflowctl`, so prefer `airflowctl` for remote automation when the API server is available.

## Verified Command Groups

Live parser inspection for the target package set reported these top-level groups.

### `airflow`

Core groups verified: `api-server`, `assets`, `backfill`, `config`, `connections`, `dag-processor`, `dags`, `db`, `info`, `jobs`, `plugins`, `pools`, `providers`, `scheduler`, `standalone`, `state-store`, `tasks`, `triggerer`, `variables`, `version`.

Additional parser-visible groups may appear when optional/provider command packages are installed, such as `cheat-sheet`, `db-manager`, `kerberos`, `partitions`, or `teams`. Treat provider-contributed CLI groups as installation-dependent; confirm with `airflow --help` or the bundled `scripts/inspect_airflow_cli.py` helper.

High-value local commands:

| Command | Use |
| --- | --- |
| `airflow version` | Confirm installed Airflow version. |
| `airflow info --output json` | Inspect runtime, config paths, executor, DB, providers, and environment summary. Use `--anonymize` before sharing. |
| `airflow config list` | Render effective configuration, optionally including descriptions, sources, env vars, and defaults. |
| `airflow config get-value <section> <option>` | Read one effective configuration value. |
| `airflow config lint` | Find Airflow 2-to-3 configuration migration issues. |
| `airflow db migrate` | Apply metadata DB migrations. Replaces old `airflow db upgrade` guidance. |
| `airflow db check` | Verify metadata DB reachability. |
| `airflow db check-migrations` | Wait/check for migrations to finish before components start. |
| `airflow db clean --dry-run` | Preview metadata cleanup before deleting rows. |
| `airflow state-store cleanup-task-state-store --dry-run` | Preview expired task state store cleanup. |
| `airflow standalone` | Initialize a disposable local environment, create a user, and start all components. |
| `airflow api-server` | Start Core and Execution API apps together by default. |
| `airflow scheduler` | Start the scheduler service. |
| `airflow dag-processor` | Start the Dag file processor that parses Dag files. |
| `airflow triggerer` | Start the triggerer for deferrable tasks. |
| `airflow dags list --output json` | List serialized/local Dags in machine-readable form. |
| `airflow dags list-import-errors --output json` | Inspect Dag import errors. |
| `airflow dags test <dag_id> -f <path>` | Execute one DagRun from a specific file in Airflow 3. |
| `airflow tasks test <dag_id> <task_id> [logical-date-or-run-id]` | Run one task instance locally for debugging. |
| `airflow backfill create --dag-id <dag_id> --from-date <date> --to-date <date>` | Create a backfill request. |
| `airflow jobs check` | Check component job heartbeats. |
| `airflow providers list --output json` | Inspect installed provider packages. |

### `airflowctl`

Core groups verified: `assets`, `auth`, `backfill`, `config`, `connections`, `dagrun`, `dags`, `jobs`, `plugins`, `pools`, `providers`, `variables`, `version`, `xcom`.

High-value remote commands:

| Command | Use |
| --- | --- |
| `airflowctl auth login --api-url <url> --env <name> ...` | Create/persist a named remote CLI environment. |
| `airflowctl auth list-envs --output json` | Confirm configured environments. |
| `airflowctl auth token --api-url <url> ...` | Generate/print a CLI JWT token when appropriate for automation. |
| `airflowctl version --remote --env <name>` | Compare local `airflowctl` and remote Airflow version. |
| `airflowctl dags list --output json` | List Dags through the API server. |
| `airflowctl dags pause <dag_id>` / `airflowctl dags unpause <dag_id>` | Change Dag pause state remotely. |
| `airflowctl dagrun ...` | Manage Dag runs through generated public API operations. |
| `airflowctl pools list --output json` | Inspect pools remotely. |
| `airflowctl variables import <file>` / `airflowctl variables ...` | Manage variables remotely. |
| `airflowctl connections import <file>` / `airflowctl connections ...` | Manage connections remotely. |
| `airflowctl config lint` | Lint config migration issues without requiring local Airflow service startup. |

Most `airflowctl` list/get/create/delete/update/trigger/add/edit operations support `--output` and default to JSON output. `airflowctl` commands generally accept an auth environment and token via environment, stored keyring/file credentials, or explicit flags.

## Output Formats

Both CLIs use the same rendered data formats for many commands:

- `table` — human-readable table. This is the default for many `airflow` commands.
- `json` — machine-readable JSON. This is the default for many generated `airflowctl` commands.
- `yaml` — YAML output for scripts or review.
- `plain` — plain table suitable for shell tools.

Prefer `--output json` for automation and `jq`, especially for `dags`, `tasks states-for-dag-run`, `providers`, `pools`, `variables`, `connections`, `jobs`, and remote `airflowctl` operations. Use `--hide-sensitive` or default masking flags when exporting or listing secrets.

## Safe Examples

### Inspect local runtime

```bash
airflow version
airflow info --output json --anonymize
airflow providers list --output json
airflow config get-value core dags_folder
airflow db check
```

### Start a disposable local environment

```bash
export AIRFLOW_HOME="$HOME/airflow"
airflow standalone
```

`airflow standalone` initializes the database, creates a user, and starts the API server, scheduler, Dag processor, and triggerer for local exploration. In Airflow 3, the generated simple-auth admin password may be written under `$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated` instead of displayed in terminal output.

### Start components separately

```bash
airflow db migrate
airflow api-server --port 8080
airflow scheduler
airflow dag-processor
airflow triggerer
```

Use separate processes when you need to isolate API, scheduler, Dag parsing, or triggerer failures. `airflow api-server` serves both Core API and Execution API by default; use `--apps core` or `--apps execution` only when intentionally separating them.

### Test a Dag file in Airflow 3

```bash
airflow dags list-import-errors --output json
airflow dags test example_bash_operator -f <path-to-dag-file>
```

Airflow 3 removed the old `--subdir` flag for this workflow. Use `-f`/`--file` on `airflow dags test` when testing a Dag from a specific file. If the file still does not load, debug Dag parsing/import errors before debugging scheduler state.

### Run a backfill

```bash
airflow backfill create \
  --dag-id example_bash_operator \
  --from-date 2015-01-01 \
  --to-date 2015-01-02
```

Use backfill commands for deliberate historical run creation. For regular scheduled execution, ensure the scheduler and Dag processor are healthy instead of using backfill as a scheduler substitute.

### Configure airflowctl

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

When no keyring is available, `AIRFLOW_CLI_TOKEN` or `--api-token` can be used, but avoid exposing tokens in shell history or logs.

## Parser Inspection Helper

Use the bundled helper to confirm installed command groups without relying on this source checkout:

```bash
python scripts/inspect_airflow_cli.py --check-imports --which both
python scripts/inspect_airflow_cli.py --which airflowctl
```

The helper imports installed modules only (`airflow.cli.cli_parser` and `airflowctl.ctl.cli_parser`), builds argparse parsers, and emits JSON with command groups, known top-level options, Python version, package versions when discoverable, and import status.

## Choosing CLI vs API for Automation

| Task | Preferred Path | Reason |
| --- | --- | --- |
| Start scheduler/API/Dag processor/triggerer locally | `airflow` | Components are local processes reading local config. |
| Apply metadata DB migrations | `airflow db migrate` | Migration uses local Airflow config and DB access. |
| Check remote Dag pause state | `airflowctl` or Stable REST API | Does not require local metadata DB access. |
| Trigger a remote Dag run from a CI job | Stable REST API or `airflowctl dags/dagrun` | Authenticated API path; avoids DB writes. |
| Bulk inspect pools/variables/connections | `airflowctl --output json` or REST API | API-backed, scriptable, remote-safe. |
| Parse and test a local Dag file | `airflow dags test ... -f` / `airflow tasks test` | Requires local file imports and installed dependencies. |
| Build a non-shell integration | Stable REST API | Stable HTTP contract and typed payloads. |
| Worker/task runtime data access | Execution API via Airflow internals only | Not a public client contract. |

## Deprecated or Migration-Sensitive CLI Notes

- Use `airflow db migrate`, not legacy `airflow db upgrade` guidance.
- Use `airflow dags test <dag_id> -f <path>`, not old `--subdir` guidance.
- Many local `airflow` state-mutating commands are deprecated toward equivalent `airflowctl` commands; when a warning says to use `airflowctl`, follow it for new automation.
- The `users` and `roles` commands are available only when the FAB auth manager/provider is enabled; do not assume they exist in a minimal Airflow 3 installation.
- Provider-level command groups can appear or disappear with installed providers; inspect live parsers rather than hard-coding every optional provider command.
