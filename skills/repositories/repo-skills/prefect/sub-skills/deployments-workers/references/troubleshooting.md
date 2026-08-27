# Deployment And Worker Troubleshooting

Use this guide when a Prefect deployment command, Python deployment API call, `prefect.yaml` manifest, worker, schedule, or deployment run does not behave as expected. Prefer local validation and inspection before running commands that mutate the Prefect API.

## Quick Triage

1. Validate local YAML without contacting the API:

```bash
python ../scripts/validate_prefect_yaml.py --file prefect.yaml --check-entrypoints --strict-unknown
```

2. Inspect the command you plan to run without executing it:

```bash
python ../scripts/deployment_command_builder.py deploy --entrypoint flows.py:daily_etl --name daily-etl --pool process-pool --work-queue default
```

3. Verify the active Prefect profile/API with the CLI-server operations skill before creating or triggering deployments.
4. Confirm deployment routing: deployment `work_pool_name`, deployment `work_queue_name`, worker `--pool`, and worker `--work-queue` must align.
5. If a command starts a listener (`prefect flow serve` or `prefect worker start`), run it only when a long-running service process is intended.

## Schema Validation Problems

Symptoms:

- `prefect deploy` rejects `prefect.yaml`.
- A deployment entry is ignored or selected incorrectly.
- Schedules or work-pool settings appear missing after deployment.

Checks:

- `deployments` must be a list of mappings, not a single mapping.
- Each deployment should have a `name` and either an `entrypoint` in YAML or an entrypoint supplied on the CLI.
- `parameters`, `job_variables`, and `work_pool` must be mappings.
- `schedules` must be a list. Each raw schedule should set exactly one of `cron`, `interval`, or `rrule`.
- Do not set both a truthy singular `schedule` and `schedules` on the same deployment.
- Use `--strict-unknown` in the bundled validator when reviewing production manifests for misspelled keys.

Fix pattern:

```yaml
deployments:
  - name: daily-etl
    entrypoint: flows.py:daily_etl
    schedules:
      - cron: "0 6 * * *"
        timezone: UTC
    work_pool:
      name: process-pool
      work_queue_name: default
      job_variables: {}
```

## Missing Or Bad Entrypoints

Symptoms:

- `prefect deploy` cannot load a flow.
- A worker starts a run but cannot import the flow function.
- `validate_prefect_yaml.py --check-entrypoints` reports a missing file or malformed entrypoint.

Checks:

- File entrypoints should look like `path/to/file.py:flow_function`.
- The file path is resolved relative to the current working directory or the manifest directory during local validation.
- A module-path entrypoint must be importable in the runtime environment; local file existence checks cannot prove that.
- Remote-code deployments need `pull` steps, `flow.from_source(...)`, or code baked into the image so the worker can access the flow code.
- If a deployment author and worker do not share a filesystem, avoid local-only paths unless using a process pool on that same host.

Fix pattern:

```yaml
pull:
  - prefect.deployments.steps.git_clone:
      id: clone-repo
      repository: https://github.com/org/project.git
      branch: main
  - prefect.deployments.steps.set_working_directory:
      directory: "{{ clone-repo.directory }}"
```

## Server Or API Unavailable

Symptoms:

- Deployment creation fails with connection errors.
- `run_deployment()` cannot read the deployment.
- Worker polling logs repeated API failures.

Checks:

- Confirm the active profile and `PREFECT_API_URL` with `prefect config view`.
- Start or select a Prefect server/Cloud workspace before creating deployments, schedules, workers, or runs.
- Verify credentials for Cloud workspaces and avoid mixing local-server and Cloud profiles.
- Remember that the bundled scripts do not contact the API; passing them only proves local command/YAML shape.

Fix pattern:

- Use the CLI-server operations skill for profile, server startup, Cloud login, and API health checks.
- Retry deployment commands only after profile/API status is known.

## Worker Not Picking Up Runs

Symptoms:

- `prefect deployment run` creates a run that stays scheduled or pending.
- The deployment exists and the schedule creates runs, but nothing executes.
- Worker logs show polling but no matching runs.

Checks:

- Confirm a worker or serve process is actually running.
- Inspect the deployment and compare `work_pool_name` and `work_queue_name` with the worker command.
- Confirm the work pool and queue are not paused.
- Confirm deployment-level, pool-level, queue-level, or worker `--limit` concurrency is not saturated.
- Confirm the worker type matches the work pool type, for example `process` worker for a process pool.
- For served flows, ensure the `flow.serve()` process is still alive; no separate worker will pick those runs up.

Safe bounded worker smoke command:

```bash
prefect worker start --pool process-pool --work-queue default --run-once --limit 1 --install-policy never
```

## Work Pool Or Queue Mismatch

Symptoms:

- Worker is online but does not receive the deployment's runs.
- Queue-specific workers ignore default-queue deployments.
- A deployment is routed to an unexpected infrastructure template.

Checks:

- YAML route: `deployments[].work_pool.name` and `deployments[].work_pool.work_queue_name`.
- Python route: `work_pool_name=...` and `work_queue_name=...`.
- CLI route: `prefect deploy --pool ... --work-queue ...`.
- Worker route: `prefect worker start --pool ... --work-queue ...`.
- Tags do not route deployments to workers.

Fix pattern:

```bash
prefect work-pool inspect process-pool --output json
prefect work-queue inspect default --pool process-pool --output json
prefect deployment inspect daily-etl/daily-etl-prod --output json
```

## Schedule Timezone Surprises

Symptoms:

- Runs appear at the wrong local time.
- Daylight saving time changes shift expectations.
- Multiple schedules fire with different parameter sets unexpectedly.

Checks:

- Use explicit IANA time zones such as `UTC` or `America/New_York`.
- Cron schedules follow wall-clock behavior in the configured timezone.
- Interval schedules are easier to reason about with an `anchor_date`.
- Do not mix `schedule` and `schedules`; prefer `schedules` for new manifests.
- Schedule-specific `parameters` override deployment defaults for runs created by that schedule.

Fix pattern:

```yaml
schedules:
  - cron: "0 8 * * *"
    timezone: America/New_York
    active: true
    parameters:
      region: east
```

## Parameter JSON Parsing

Symptoms:

- A CLI parameter arrives as a number or boolean instead of a string.
- `--params` and `--param` conflict.
- Deployment run parameter validation fails.

Checks:

- `prefect deploy --param` and `prefect deployment run --param` parse values as JSON when possible.
- Use JSON quoting for strings that must remain strings, for example `--param code='"001"'`.
- Prefer `--params '{"limit": 100}'` for complex mappings.
- Do not combine `--param` and `--params` for the same command path.
- Keep YAML `parameters` JSON-serializable and leave `enforce_parameter_schema` enabled unless compatibility requires otherwise.

Fix examples:

```bash
prefect deployment run daily-etl/daily-etl-prod --param limit=100
prefect deployment run daily-etl/daily-etl-prod --param code='"001"'
prefect deployment run daily-etl/daily-etl-prod --params '{"limit": 100, "dry_run": true}'
```

## Job Variables Problems

Symptoms:

- Worker infrastructure starts with the wrong image, environment, command, or resource settings.
- `--job-variable` values have unexpected types.
- Job variables appear to have no effect.

Checks:

- Inspect the work pool base job template to confirm variable names that can be overridden.
- `job_variables` must be a mapping in YAML and Python.
- Runtime `prefect deployment run --job-variable` overrides apply only to that flow run.
- CLI job-variable values may be JSON-parsed; quote strings deliberately.
- Worker-type-specific keys vary by integration. Route provider details to integration-specific skills when needed.

Fix examples:

```yaml
work_pool:
  name: docker-pool
  job_variables:
    image: registry.example.com/project/flow:prod
    env:
      EXECUTION_ENVIRONMENT: production
```

```bash
prefect deployment run api-sync/api-sync-prod --job-variable image='"registry.example.com/project/flow:hotfix"'
```

## Docker Optional Dependencies

Symptoms:

- `flow.deploy(image=...)` or Docker recipe deployment fails before reaching the API.
- Image build/push works locally but workers cannot pull the image.
- Worker type installation prompts unexpectedly.

Checks:

- Docker builds and pushes may require Docker daemon access, registry credentials, and network access.
- Passing an image string can use default Docker behavior; use Prefect's Docker image helpers only when you need customized build settings.
- `prefect worker start --install-policy prompt` may ask to install optional packages. Use `--install-policy never` for deterministic checks.
- For Kubernetes, ECS, ACI, Cloud Run, and other provider-specific workers, confirm the integration package and credentials separately.

Fix pattern:

- Prebuild and push images in CI when possible.
- Set deployment `job_variables.image` or Python `image=...` to a pullable immutable tag.
- Keep provider-specific setup in the relevant integration skill.

## Long-Running Service Safety

Commands and APIs that keep running:

- `prefect flow serve ...`
- `flow.serve(...)`
- `prefect.serve(...)`
- `prefect worker start ...` without `--run-once`

Safety checklist:

- Ask before starting service processes in an interactive coding session.
- Prefer command construction and `--help` checks before running listeners.
- Use `--run-once` for bounded worker smoke tests.
- Use a supervisor, container, system service, or deployment platform for production listeners.
- Record shutdown behavior, especially `pause_on_shutdown` for served flows and schedule continuity.

## When To Escalate Elsewhere

- Profile, server startup, Cloud login, dashboard, and config diagnostics: use `cli-server-operations`.
- Flow/task authoring errors before deployment: use `flow-task-authoring`.
- Direct API client internals and settings internals: use `api-client-settings`.
- Event trigger semantics beyond deployment-side placement: use `events-blocks-assets`.
- Provider-specific worker infrastructure: integration-specific skills when available.
