---
name: deployments-workers
description: "Create and manage Prefect deployments, schedules, serve processes,
  work pools, work queues, workers, runner APIs, Docker/image inputs, and
  prefect.yaml configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployments And Workers

Use this sub-skill when a task is about turning authored Prefect flows into remotely triggerable deployments, serving flows from a long-running process, configuring `prefect.yaml`, or routing runs through work pools, work queues, and workers.

## Start Here

1. Choose the deployment mode in [references/api-reference.md](references/api-reference.md): `flow.serve()` for static local processes, `flow.deploy()` / `prefect deploy` for work-pool deployments, or `run_deployment()` / `prefect deployment run` for triggering an existing deployment.
2. Check exact command flags in [references/cli-reference.md](references/cli-reference.md) before composing CLI commands; this Prefect version uses `prefect deploy init`, not top-level `prefect init --help`.
3. For project YAML, read [references/prefect-yaml.md](references/prefect-yaml.md) and run `python scripts/validate_prefect_yaml.py --file prefect.yaml` before deploying.
4. For failures where a deployment validates but never starts, read [references/troubleshooting.md](references/troubleshooting.md) and verify the API URL/profile, deployment name, work pool, work queue, and worker command all match.

## Use For

- `prefect deploy`, `prefect deploy init`, `prefect flow serve`, `prefect deployment run`, deployment schedules, deployment triggers, and runtime parameters.
- `prefect work-pool`, `prefect work-queue`, and `prefect worker start` commands for process, Docker, Kubernetes, and integration-provided worker types.
- `prefect.yaml` `build`, `push`, `pull`, `deployments`, `schedules`, `work_pool`, `job_variables`, and templated step-output fields.
- Python deployment APIs: `Flow.serve`, `Flow.deploy`, `prefect.deploy`, `RunnerDeployment.from_flow`, `RunnerDeployment.from_entrypoint`, and `run_deployment`.
- Docker image deployment inputs and job variables at the general Prefect layer; route provider-specific worker setup to integration-specific skills when available.

## Route Elsewhere

- General profile, server startup/status, Cloud login, dashboard, config, variables, and operational diagnostics: use `cli-server-operations`.
- Authoring `@flow` and `@task` code before deployment, local state behavior, task runners, retries, caching, and flow tests: use `flow-task-authoring`.
- Direct `get_client`, `PrefectClient`, settings/profile internals, schema models, and the `prefect-client` package split: use `api-client-settings`.
- Events/automations details, blocks, assets, and concurrency primitives beyond deployment trigger wiring: use `events-blocks-assets`.
- Maintainer-only source changes, repo test selection, generated artifacts, and internal runner refactors: use `repo-development`.

## Safe Validation

- Validate deployment YAML structure without contacting a Prefect API:

```bash
python scripts/validate_prefect_yaml.py --file prefect.yaml --check-entrypoints
```

- Build copyable commands from explicit inputs without running Prefect:

```bash
python scripts/deployment_command_builder.py deploy --entrypoint flows.py:etl --name etl-prod --pool process-pool --work-queue default --param limit=10
```

- Use `--help` on both bundled scripts for examples. They perform no network calls, do not start workers, and do not mutate Prefect server state.

## Safety Notes

- `prefect flow serve` and `prefect worker start` are long-running listeners; only run them when the user explicitly wants a service process.
- `prefect deployment run` creates server-side flow runs; use `--start-in`, `--start-at`, and `--watch-timeout` deliberately.
- `prefect deploy` and `flow.deploy()` require a reachable Prefect API and can create/update deployments, queues, and schedules.
- Docker image builds, pushes, and integration workers may require optional packages, credentials, network access, and external infrastructure; keep those provider-specific details outside this sub-skill unless the user asks at the general Prefect layer.
