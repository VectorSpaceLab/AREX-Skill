# Production Schedulers

## Flow-script CLI groups

- `step-functions`: `create`, `delete`, `trigger`, `terminate`, `list-runs`.
- `argo-workflows`: `create`, `delete`, `trigger`, `terminate`, `suspend`, `unsuspend`, `status`, `list-workflow-templates`.
- `airflow`: `create`.
- `batch`: `list`, `kill`, `step`.
- `kubernetes`: `list`, `kill`, `step`.

Treat `create`, `delete`, `trigger`, `terminate`, `kill`, and service `list/status` commands as service-affecting unless the user explicitly asks and configuration is verified. Airflow `create` compiles a DAG; still check output location and dependencies.

## Deployer bridge

`Deployer(flow_file, ...)` injects provider methods for available deployer implementations. Use it when Python code should manage deployments, but keep provider credentials and service checks in this sub-skill. `TriggeredRun` can wait for a scheduler-triggered run to become visible, but the run object may not exist until the start task begins.

## Configuration prerequisites

Provider workflows commonly need configured datastore roots, metadata service URLs, IAM roles, Kubernetes namespace/service account, Argo/Events settings, or Airflow Kubernetes settings. Verify configuration before generating commands.
