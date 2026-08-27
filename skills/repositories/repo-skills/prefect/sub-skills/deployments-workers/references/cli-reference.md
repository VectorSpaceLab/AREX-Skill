# Deployment And Worker CLI Reference

This reference covers Prefect 3.6.24 deployment and worker commands verified from live CLI help. Commands that contact the API or start listeners require a configured Prefect server or Prefect Cloud workspace; profile/server setup is owned by the `cli-server-operations` sub-skill.

## Command Selection

| Goal | Prefer | Notes |
|---|---|---|
| Scaffold a project deployment file | `prefect deploy init` | The deploy app owns `init` in this version. Top-level `prefect init --help` is not valid here. |
| Create/update deployments from an entrypoint or `prefect.yaml` | `prefect deploy` | Reads `prefect.yaml` by default and can create queues/schedules. |
| Serve a flow from a long-running local process | `prefect flow serve` | Starts a runner process; do not use for one-shot deploy-only work. |
| Trigger an existing deployment | `prefect deployment run` | Creates a flow run; a matching worker or serve process must pick it up. |
| Create/update infrastructure routing | `prefect work-pool`, `prefect work-queue` | Work pool type determines the worker implementation and job variables. |
| Poll a work pool for runs | `prefect worker start` | Long-running process unless `--run-once` is used. |
| Manage deployment schedules after creation | `prefect deployment schedule ...` | Adds, replaces, pauses, resumes, or clears schedules. |

## `prefect deploy init`

Use `prefect deploy init` to create `prefect.yaml` from the default template or a recipe.

Important flags:

- `--name`: project name to place in `prefect.yaml` metadata.
- `--recipe`: recipe directory name to use for the generated deployment file.
- `--field` / `-f`: repeatable `key=value` inputs for a recipe, such as `--field image_name=my-image`.
- Session flags: `--profile`, `--prompt` / `--no-prompt`.

Examples:

```bash
prefect deploy init --name analytics
prefect deploy init --recipe docker --field image_name=registry.example.com/etl --field tag=prod
```

## `prefect deploy`

Use `prefect deploy [ENTRYPOINT]` to create or update deployments. `ENTRYPOINT` is optional when deploying selected entries from `prefect.yaml`; file entrypoints use `path/to/file.py:flow_func`.

Live-help-verified flags:

- Naming and metadata: `--name` / `-n`, `--description` / `-d`, `--version-type`, `--version`, `--tag` / `-t`.
- Concurrency: `--concurrency-limit`, `--collision-strategy`.
- Routing: `--pool` / `-p`, `--work-queue` / `-q`.
- Job variables: `--job-variable`, repeatable; accepts `key=value` or a JSON object string.
- Schedules: `--cron`, `--interval`, `--anchor-date`, `--rrule`, `--timezone`.
- Triggers: `--trigger`, repeatable; accepts a JSON string or path to a `.yaml` / `.json` file.
- Parameters: `--param`, repeatable `key=value` values parsed as JSON when possible; `--params` for a JSON mapping string.
- Schema enforcement: `--enforce-parameter-schema` / `--no-enforce-parameter-schema`.
- Selection: `--all` / `--no-all`, `--prefect-file`.
- Experimental Cloud-only SLA: `--sla`.
- Session flags: `--profile`, `--prompt` / `--no-prompt`.

Examples:

```bash
prefect deploy flows.py:daily_etl \
  --name daily-etl-prod \
  --pool process-pool \
  --work-queue default \
  --cron "0 6 * * *" \
  --timezone America/New_York \
  --param limit=100

prefect deploy --prefect-file deploy/prefect.yaml --all --no-prompt
```

Notes:

- Tags are organizational metadata; use `--work-queue` for worker routing.
- `--work-queue` creates the queue if it does not already exist for the selected work pool.
- `--param count=10` parses `10` as JSON number, while invalid JSON values remain strings.
- If both `--param` and `--params` are passed through the CLI configuration path, Prefect rejects the combination.

## `prefect flow serve`

Use `prefect flow serve --name NAME ENTRYPOINT` to create a deployment and immediately serve it from the current process. This is for static infrastructure where a long-running Python process watches for scheduled work.

Important flags:

- Required: `ENTRYPOINT`, `--name` / `-n`.
- Metadata: `--description` / `-d`, `--version` / `-v`, `--tag` / `-t`.
- Schedules: `--cron`, `--interval`, `--anchor-date`, `--rrule`, `--timezone`.
- Shutdown behavior: `--pause-on-shutdown` / `--no-pause-on-shutdown`; default is `True`.
- Limits: `--limit` for this served flow instance, `--global-limit` across served flow instances associated with the same deployment.
- Session flags: `--profile`, `--prompt` / `--no-prompt`.

Example:

```bash
prefect flow serve flows.py:hourly_report --name hourly-report --cron "0 * * * *" --timezone UTC
```

Safety:

- This command stays running; run it in a supervisor, terminal multiplexer, container, or service manager when production reliability matters.
- If `--no-pause-on-shutdown` is used, schedules continue creating runs even after the local listener exits, so another listener must be available.

## `prefect deployment run`

Use `prefect deployment run FLOW_NAME/DEPLOYMENT_NAME` or `--id DEPLOYMENT_ID` to create a flow run for an existing deployment. It will not execute until a matching worker or serve process picks it up.

Important flags:

- Target: `NAME` in `<FLOW_NAME>/<DEPLOYMENT_NAME>` form, or `--id`.
- Job variables: `--job-variable`, repeatable `key=value`, interpreted as JSON.
- Parameters: `--param` / `-p`, repeatable `key=value`, interpreted as JSON; `--params` mapping string or `-` for stdin.
- Timing: `--start-in`, `--start-at`.
- Tags/name: `--tag`, `--flow-run-name`.
- Watching: `--watch` / `--no-watch`, `--watch-interval`, `--watch-timeout`.
- Session flags: `--profile`, `--prompt` / `--no-prompt`.

Examples:

```bash
prefect deployment run analytics-flow/daily-etl --param limit=100 --tag manual
prefect deployment run analytics-flow/daily-etl --start-in "2 hours"
prefect deployment run --id 00000000-0000-0000-0000-000000000000 --params '{"limit": 100}' --watch --watch-timeout 300
```

## `prefect deployment schedule`

Use schedule subcommands to manage schedules on an existing deployment.

Common subcommands:

- `prefect deployment schedule create NAME`: add a schedule, or replace existing schedules with `--replace`.
- `prefect deployment schedule ls DEPLOYMENT-NAME`: list schedules, optionally `--output json`.
- `prefect deployment schedule pause DEPLOYMENT_NAME SCHEDULE_ID` or `--all`: pause schedules.
- `prefect deployment schedule resume DEPLOYMENT_NAME SCHEDULE_ID` or `--all`: resume schedules.
- `prefect deployment schedule clear DEPLOYMENT-NAME`: remove all schedules, with `--accept-yes` / `-y` for noninteractive confirmation.

`create` flags:

- Schedule selectors: `--interval`, `--rrule`, `--cron`.
- Schedule options: `--anchor-date`, `--day_or` / `--no-day_or`, `--timezone`, `--active` / `--no-active`.
- Replacement: `--replace` / `--no-replace`.
- Prompting: `--accept-yes` / `-y`.

Examples:

```bash
prefect deployment schedule create analytics-flow/daily-etl --cron "0 9 * * *" --timezone America/New_York
prefect deployment schedule create analytics-flow/daily-etl --interval 1800 --replace --accept-yes
prefect deployment schedule ls analytics-flow/daily-etl --output json
```

## Work Pools

`prefect work-pool` manages infrastructure templates and routing destinations.

Selected commands:

- `create NAME`: create or update a work pool.
- `update NAME`: update a base job template, concurrency limit, or description.
- `inspect NAME`: inspect details; supports `--output json`.
- `ls`: list pools.
- `pause NAME` / `resume NAME`: stop or resume scheduling work from a pool.
- `preview NAME`: preview scheduled work across queues; supports `--hours` and `--output json`.
- `set-concurrency-limit NAME CONCURRENCY-LIMIT` and `clear-concurrency-limit NAME`.
- `get-default-base-job-template --type TYPE --file PATH`: write or print the default job template for a worker type.
- `provision-infra` / `provision-infrastructure`: provision supported infrastructure types; may require credentials and external services.

`create` flags:

- Required: `NAME`.
- Template/type: `--type` / `-t`, `--base-job-template`.
- State/default: `--paused` / `--no-paused`, `--set-as-default` / `--no-set-as-default`.
- Provisioning: `--provision-infrastructure`, `--provision-infra`, and negative aliases.
- Replacement: `--overwrite` / `--no-overwrite`.

Examples:

```bash
prefect work-pool create process-pool --type process --set-as-default
prefect work-pool inspect process-pool --output json
prefect work-pool get-default-base-job-template --type process --file process-base-job-template.json
```

## Work Queues

`prefect work-queue` manages queue-level filtering, priority, and concurrency within a work pool.

Selected commands:

- `create NAME`: create a queue.
- `inspect NAME`: inspect by queue name or ID; supports `--pool` and `--output json`.
- `ls`: list queues.
- `pause NAME` / `resume NAME`: pause or resume queue dispatch.
- `preview NAME`: preview queue runs; supports `--pool`, `--hours`, and `--output json`.
- `read-runs NAME`: get runs in a queue.
- `set-concurrency-limit NAME LIMIT` and `clear-concurrency-limit NAME`.
- `slots NAME`: show slot utilization.
- `delete NAME`: delete by ID.

`create` flags:

- Required: `NAME`.
- Pool: `--pool` / `-p`.
- Concurrency: `--limit` / `-l`.
- Priority: `--priority` / `-q`.

Example:

```bash
prefect work-queue create default --pool process-pool --limit 5 --priority 1
prefect work-queue inspect default --pool process-pool --output json
```

## Workers

Use `prefect worker start` to poll a work pool for scheduled flow runs and submit them to the work pool's infrastructure.

Important flags:

- Identity/routing: `--name` / `-n`, `--pool` / `-p`, `--work-queue` / `-q` repeatable, `--type` / `-t`.
- Polling/execution: `--prefetch-seconds`, `--run-once` / `--no-run-once`, `--limit` / `-l`.
- Health and setup: `--with-healthcheck` / `--no-with-healthcheck`, `--install-policy` with choices `always`, `if-not-present`, `never`, `prompt`.
- Pool creation: `--base-job-template`, `--create-pool-if-not-found` / `--no-create-pool-if-not-found`.
- Session flags: `--profile`, `--prompt` / `--no-prompt`.

Examples:

```bash
prefect worker start --pool process-pool --work-queue default --name local-process-worker
prefect worker start --pool process-pool --run-once --limit 1 --install-policy never
```

Safety:

- `worker start` is normally long-running. Use `--run-once` for bounded polling during smoke checks.
- If the worker type package is optional, `--install-policy prompt` may ask to install it. Use `--install-policy never` in locked-down environments and install required integration packages explicitly.
- A worker only receives runs from the exact work pool and, when specified, work queue names it polls.

## Troubleshooting Command Flow

When a deployment does not run:

1. Confirm the deployment exists: `prefect deployment inspect FLOW/DEPLOYMENT --output json`.
2. Confirm schedules: `prefect deployment schedule ls FLOW/DEPLOYMENT --output json`.
3. Confirm the run was created: `prefect deployment run FLOW/DEPLOYMENT --watch --watch-timeout 60`.
4. Confirm routing: inspect the deployment's `work_pool_name` and `work_queue_name`.
5. Confirm the worker command polls the same `--pool` and `--work-queue`.
6. Confirm the pool/queue is not paused and concurrency limits are not saturated.
