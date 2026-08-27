# `prefect.yaml` Deployment Configuration

`prefect.yaml` stores deployment metadata, deployment-specific schedules and work-pool routing, and lifecycle steps that prepare code for execution. Treat it as a version-controlled deployment manifest; validate it before running `prefect deploy`.

## Minimal Shape

The generated default template has this shape:

```yaml
prefect-version: null
name: null

build: null
push: null
pull: null

deployments:
  - name: null
    version: null
    tags: []
    description: null
    schedule: {}
    concurrency_limit: null
    flow_name: null
    entrypoint: null
    parameters: {}
    work_pool:
      name: null
      work_queue_name: null
      job_variables: {}
```

Practical minimal deployment:

```yaml
name: analytics
pull: null

deployments:
  - name: daily-etl
    entrypoint: flows.py:daily_etl
    parameters:
      limit: 100
    work_pool:
      name: process-pool
      work_queue_name: default
```

Notes:

- `deployments` is a list. Use `prefect deploy --all` to deploy every entry.
- `entrypoint` is `path/to/file.py:function_name` or an importable module path where supported by the deployment API.
- `work_pool.name` must match the pool polled by a worker. `work_pool.work_queue_name` must match the queue polled by that worker if queues are used.
- The CLI model ignores unknown top-level and deployment fields in normal operation, but unknown keys usually indicate typos. Use the bundled validator with `--strict-unknown` when reviewing production manifests.

## Top-Level Fields

| Field | Purpose | Notes |
|---|---|---|
| `prefect-version` | Metadata for the Prefect version that generated or owns the file. | Bookkeeping; not a runtime lock. |
| `name` | Project name metadata. | Not the deployment name. |
| `build` | Steps run before pushing/deploying artifacts. | Often Docker image build steps. |
| `push` | Steps that publish code/artifacts. | Used for remote storage or image pushes. |
| `pull` | Steps the runtime uses to retrieve code. | Important for worker-based deployments where code is not baked into the image. |
| `deployments` | Deployment definitions. | List of deployment mappings. |

`build`, `push`, and `pull` can be `null`, a list of step mappings, or a mapping accepted by Prefect's permissive model. The normal step style is:

```yaml
pull:
  - prefect.deployments.steps.git_clone:
      id: clone-repo
      repository: https://github.com/org/repo.git
      branch: main
  - prefect.deployments.steps.set_working_directory:
      directory: "{{ clone-repo.directory }}"
```

Step notes:

- `id` lets later steps reference outputs with `{{ step-id.key }}`.
- `requires` can auto-install a missing step package at deploy/runtime; use it intentionally because it mutates the current environment.
- Provider-specific storage or Docker steps may require integration packages and credentials. Keep those decisions explicit.

## Deployment Fields

Common fields accepted by the deployment model:

| Field | Purpose |
|---|---|
| `name` | Deployment name. Refer to the deployed object as `<flow-name>/<deployment-name>`. |
| `version`, `version_type` | Deployment version metadata. |
| `tags` | Organizational tags; not worker routing. |
| `description` | Deployment description. |
| `entrypoint` | Flow function location. File form is `path/to/file.py:flow_func`. |
| `flow_name` | Flow name selector when needed for disambiguation. |
| `parameters` | Default parameter mapping for flow runs. |
| `enforce_parameter_schema` | Whether run parameters must match the flow signature. |
| `schedule` | Legacy single schedule. Prefer `schedules` for new files. |
| `schedules` | List of schedule entries. |
| `paused` | Whether schedules are paused. |
| `concurrency_limit` | Integer or object with `limit`, `collision_strategy`, `grace_period_seconds`. |
| `build`, `push`, `pull` | Per-deployment action overrides. |
| `work_pool` | Work-pool routing and job variables. |
| `triggers` | Deployment triggers, provided as raw mappings for later validation after template rendering. |
| `sla` | Experimental SLA configuration, currently Cloud-oriented and subject to change. |

## Schedules

Prefer the `schedules` list. Each raw schedule must specify exactly one of `cron`, `interval`, or `rrule`.

Cron example:

```yaml
deployments:
  - name: daily-etl
    entrypoint: flows.py:daily_etl
    schedules:
      - cron: "0 6 * * *"
        timezone: America/New_York
        active: true
        slug: east-coast-morning
```

Interval example:

```yaml
deployments:
  - name: every-ten-minutes
    entrypoint: flows.py:poll
    schedules:
      - interval: 600
        anchor_date: "2026-01-01T00:00:00Z"
        timezone: UTC
```

Multiple schedules with parameters:

```yaml
deployments:
  - name: regional-reports
    entrypoint: flows.py:send_report
    schedules:
      - cron: "0 8 * * *"
        slug: chicago
        timezone: America/Chicago
        parameters:
          region: central
      - cron: "0 8 * * *"
        slug: new-york
        timezone: America/New_York
        parameters:
          region: east
```

Schedule migration notes:

- If both `schedule` and `schedules` are present and `schedule` is truthy, Prefect raises a validation error asking you to use only `schedules`.
- An empty or null `schedule` is allowed for no schedule, but `schedules: []` is clearer for new files.
- `replaces` can rename an existing schedule slug without creating an orphaned schedule.
- Two schedules cannot target the same `replaces` slug.
- Cron time zones should be IANA names such as `America/New_York`; DST-observing zones follow cron's wall-clock behavior.

## Work Pool Routing

Work-pool deployment config lives under `work_pool`:

```yaml
deployments:
  - name: daily-etl
    entrypoint: flows.py:daily_etl
    work_pool:
      name: process-pool
      work_queue_name: default
      job_variables:
        env:
          EXECUTION_ENVIRONMENT: production
          LOG_LEVEL: INFO
```

Routing checklist:

- Deployment `work_pool.name` must equal `prefect worker start --pool ...`.
- Deployment `work_pool.work_queue_name` must equal one of the worker's repeatable `--work-queue ...` values when queue filtering is used.
- If `work_queue_name` is omitted, the worker must be polling the pool without queue filters or must include the queue Prefect assigns.
- Tags do not route work to workers.
- Paused pools/queues, saturated concurrency limits, or a worker with the wrong type can make a valid deployment never start.

## Job Variables

`job_variables` override infrastructure variables exposed by a work pool base job template. They can set environment variables, image names, resource limits, commands, or other worker-type-specific values.

Deployment default example:

```yaml
deployments:
  - name: api-sync
    entrypoint: flows.py:sync_api
    work_pool:
      name: docker-pool
      job_variables:
        image: registry.example.com/api-sync:2026-06-01
        env:
          EXECUTION_ENVIRONMENT: production
```

Runtime override example:

```bash
prefect deployment run api-sync-flow/api-sync --job-variable image='"registry.example.com/api-sync:hotfix"'
```

Notes:

- CLI `--job-variable` values are interpreted as JSON for `deployment run`, so quote strings deliberately.
- `prefect deploy --job-variable` accepts `key=value` or a JSON object string.
- Prefer templated image values such as `{{ build-image.image }}` when a build step produces an image, so build output and deployment config do not drift.

## Parameters

`parameters` in YAML are deployment defaults. `prefect deployment run --param` or `--params` can override them per run.

```yaml
deployments:
  - name: daily-etl
    entrypoint: flows.py:daily_etl
    parameters:
      limit: 500
      dry_run: false
```

Parameter notes:

- Keep parameter types JSON-serializable.
- Leave `enforce_parameter_schema` enabled unless there is a compatibility reason to accept extra parameters.
- A string that looks like JSON may be parsed as JSON by the CLI, especially with `--param` and `--job-variable`.

## Triggers

Deployment `triggers` entries connect events/automations to deployment runs. They are kept as raw mappings in the deploy CLI model because template rendering happens before strict trigger validation.

```yaml
deployments:
  - name: react-to-upstream
    entrypoint: flows.py:react
    triggers:
      - enabled: true
        match:
          prefect.resource.id: prefect.flow-run.*
        expect:
          - prefect.flow-run.Completed
        parameters:
          upstream_id: "{{ event.resource.id }}"
```

Route deep automation/event troubleshooting to the `events-blocks-assets` sub-skill; this sub-skill owns only deployment-side trigger placement.

## Docker And Image Inputs

There are two general patterns:

1. **Bake code into an image**: build/push an image and point job variables or Python `flow.deploy(image=...)` at it.
2. **Pull code at runtime**: use `pull` steps or `flow.from_source(...).deploy(...)` so a worker retrieves code before execution.

Safety notes:

- Docker builds and pushes can be slow, require credentials, and mutate local Docker state.
- Passing an image string to Python deployment APIs may suppress build/push progress. Use a `DockerImage` object when progress output matters.
- Integration-specific Docker/Kubernetes/ECS/ACI/Cloud Run details should be routed to integration skills when available.

## Validation Workflow

1. Run the bundled lint helper:

```bash
python ../scripts/validate_prefect_yaml.py --file prefect.yaml --check-entrypoints --strict-unknown
```

2. Inspect generated commands before execution:

```bash
python ../scripts/deployment_command_builder.py deploy --entrypoint flows.py:daily_etl --name daily-etl --pool process-pool --cron "0 6 * * *"
```

3. Use `prefect deploy --prefect-file prefect.yaml --all --no-prompt` only after the API/profile and work-pool plan are correct.

## Common YAML Mistakes

- `deployments` is a mapping instead of a list.
- A deployment has neither `entrypoint` nor a CLI-supplied entrypoint.
- File entrypoint lacks `:` or points to a missing local file.
- `schedules` is a mapping instead of a list.
- A raw schedule sets both `cron` and `interval`, or sets none of `cron`, `interval`, `rrule`.
- `schedule` and `schedules` are both set.
- `work_pool` is a string instead of a mapping with `name`.
- `job_variables` is a list or scalar instead of a mapping.
- `parameters` is not a mapping.
- `work_queue_name` in YAML does not match the worker's `--work-queue` flag.
