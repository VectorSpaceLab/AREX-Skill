# Deployment Workflows

This reference covers Dagster OSS operational patterns for configuring an instance and running long-lived services. It is intentionally service-safe: commands are examples to adapt, not commands to run against production without user approval.

## OSS Service Topology

A production-style Dagster OSS deployment has three service categories:

- `dagster-webserver`: serves the UI and GraphQL API. Multiple replicas are possible if they share the same instance storage and workspace/code-location access.
- `dagster-daemon run`: runs schedules, sensors, queued-run dequeueing, run monitoring, and other daemon loops. Run exactly one daemon process for an instance.
- Code-location servers: load user definitions from Python files/modules/packages or workspace entries. Each code location has one server replica, but a deployment can have many code locations.

For every service, align:

- The same `DAGSTER_HOME` value.
- Compatible `dagster.yaml` content.
- The same package environment or image set for packages needed by the service.
- Shared access to configured instance storage and compute-log storage.
- A consistent workspace or code-location target.

If schedules or sensors are not firing, first suspect daemon absence, daemon heartbeat failure, or a different `DAGSTER_HOME` between the webserver and daemon.

## Instance Configuration Checklist

Dagster looks for `dagster.yaml` in `DAGSTER_HOME`. A practical review flow is:

1. Confirm `DAGSTER_HOME` is set for every service and points to a persistent directory or mounted volume.
2. Confirm `dagster.yaml` exists at `$DAGSTER_HOME/dagster.yaml` or pass the intended path to the checker script.
3. Confirm `storage` is appropriate for the deployment:
   - `sqlite` can work for local development and simple single-node evaluation.
   - `postgres` or `mysql` is the usual production choice for multi-service or containerized deployments and requires the matching optional package.
4. Confirm `compute_logs` are durable and visible to users who need raw stdout/stderr.
5. Confirm `scheduler` is not disabling daemon-backed scheduling unless that is intentional.
6. Confirm `run_coordinator`, `run_launcher`, `run_monitoring`, `run_retries`, and `concurrency` match the desired execution model.
7. Confirm secrets use environment indirection, for example `{env: SOME_SECRET_NAME}`, rather than literal credentials.

Minimal local persistent shape:

```yaml
storage:
  sqlite:
    base_dir: /var/lib/dagster/storage
compute_logs:
  module: dagster.core.storage.local_compute_log_manager
  class: LocalComputeLogManager
  config:
    base_dir: /var/lib/dagster/compute_logs
```

Queued production-style shape:

```yaml
run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
concurrency:
  runs:
    max_concurrent_runs: 15
run_monitoring:
  enabled: true
  start_timeout_seconds: 600
  cancel_timeout_seconds: 300
  max_runtime_seconds: 7200
run_retries:
  enabled: true
  max_retries: 3
  retry_on_asset_or_op_failure: false
```

Legacy deployments may use `run_queue` or `run_coordinator.config.max_concurrent_runs`; prefer the current `concurrency.runs.max_concurrent_runs` shape when adding new config unless the surrounding project clearly uses older config.

## Execution Flow Decisions

Dagster run execution flows through these layers:

1. Run submission from UI, CLI, schedule, or sensor.
2. Run coordinator decides whether to submit immediately or queue.
3. Daemon dequeues queued runs when `QueuedRunCoordinator` is configured.
4. Run launcher creates the run worker process/container/pod/task.
5. Executor inside the run worker executes ops/assets and controls step-level parallelism.

Choose components by asking what needs to scale:

- Use `DefaultRunCoordinator` when immediate submission and no instance-level queueing is acceptable.
- Use `QueuedRunCoordinator` when the deployment needs a daemon-managed queue, total run limits, tag/pool limits, or prioritization.
- Use `DefaultRunLauncher` for same-node process launches.
- Use Docker, Kubernetes, or ECS launchers when each run should execute in its own container, pod, or task. These require optional integration packages and platform-specific credentials/config.
- Tune executors in job/run config when per-step process/container behavior is the issue, not instance-level launch behavior.

## Daemon Operations

The daemon process is required for schedules, sensors, queued runs, run monitoring, and several automation loops.

Safe checks before changing runtime state:

```bash
dagster-daemon --help
dagster-daemon run --help
```

Operational checks to perform with the user’s approval or in a non-production environment:

- Inspect daemon logs for import errors, workspace load failures, database errors, or heartbeat failures.
- In the UI, inspect the Deployment/Daemons page for recent daemon heartbeats.
- Confirm the daemon and webserver share `DAGSTER_HOME`; differing instance directories make schedules/sensors appear enabled in one process but inactive in another.
- Confirm workspace/code-location targets are available to the daemon, not just to the webserver.

Do not run multiple daemon processes against the same instance unless Dagster documentation for a specific component explicitly supports that topology.

## Webserver Operations

`dagster-webserver` serves the UI and GraphQL API. It loads definitions from command-line targets or workspace files and uses the configured Dagster instance.

Common operational examples:

```bash
dagster-webserver --help
dagster-webserver -h 0.0.0.0 -p 3000 -w workspace.yaml
```

Use a process manager, container service, or orchestrator to run it in production. Verify:

- Host/port binding matches ingress/load-balancer expectations.
- Health checks target the webserver port.
- The webserver image/environment contains Dagster and code-location client dependencies.
- The webserver can reach code-location servers and instance storage.
- Multiple webserver replicas share the same instance storage and workspace/code-location configuration.

## Retries, Timeouts, and Monitoring

Use run retries for whole-run recovery after infrastructure failure or worker crashes. Use op/asset retries for step-level transient errors. Avoid unintentionally multiplying retries by enabling both without deciding whether run retries should retry asset/op failures.

Key settings:

```yaml
run_retries:
  enabled: true
  max_retries: 3
  retry_on_asset_or_op_failure: false
run_monitoring:
  enabled: true
  start_timeout_seconds: 600
  cancel_timeout_seconds: 300
  max_runtime_seconds: 7200
  free_slots_after_run_end_seconds: 300
```

Use `dagster/max_retries`, `dagster/retry_strategy`, `dagster/retry_on_asset_or_op_failure`, and `dagster/max_runtime` tags for per-job or per-run overrides where supported. `FROM_FAILURE` style retries require outputs to be accessible to the retried run; local filesystem outputs often fail in container/pod launchers unless the filesystem is shared.

## Concurrency and Run Queue

For total run limits in OSS, prefer:

```yaml
concurrency:
  runs:
    max_concurrent_runs: 15
```

For tag or pool limits, keep the policy close to the run coordinator/concurrency config and document which jobs set the corresponding tags or pools. If queued runs never dequeue:

- Confirm `QueuedRunCoordinator` is configured if expecting daemon-managed queue behavior.
- Confirm `dagster-daemon run` is alive and heartbeating.
- Confirm limits are not already saturated.
- Confirm failed/cancelled runs did not leave stale concurrency slots; configure `free_slots_after_run_end_seconds` for op concurrency pools that can be abandoned by crashes.

## Docker Deployment Checklist

Use Docker Compose or another container supervisor to run at least webserver, daemon, and code-location services. Checklist:

- Build separate images or stages for Dagster services and user code if that simplifies dependency isolation.
- Mount or inject the same `DAGSTER_HOME`/`dagster.yaml` into webserver and daemon containers.
- Use shared database-backed storage rather than container-local SQLite for multi-container production.
- Expose only the webserver port externally; keep code-location and database networks private where possible.
- If using a Docker run launcher/executor, verify Docker socket access, network names, image names, and environment variables are intentionally scoped.
- Prefer platform secrets or environment variables for credentials.

Safe native checks are help/build-plan checks; do not run `docker compose up`, push images, or alter Docker contexts without approval.

## Kubernetes Deployment Checklist

For Kubernetes, the important operational questions are independent of any specific Helm template:

- Which Deployment/StatefulSet runs the webserver?
- Which single Deployment runs the daemon?
- Which service(s) expose code-location servers?
- Which ConfigMap/Secret/mount provides `dagster.yaml`, workspace config, and secrets?
- Which image tag contains user definitions and optional integration packages?
- Which service account, RBAC, namespace, and image-pull secret does the run launcher need?
- Are compute logs and persistent storage accessible across pods?

If runs stay in STARTING, inspect run worker pod creation, image pull, service account/RBAC, environment variables, and run monitoring timeouts. If code locations fail to load, inspect code server pod logs separately from webserver logs.

## ECS Deployment Checklist

For ECS, map Dagster services to ECS services/tasks:

- Webserver task/service exposes the UI port through a load balancer.
- Daemon task/service runs one long-lived daemon replica.
- Code-location task/service exposes gRPC to webserver/daemon services.
- Run launcher starts per-run ECS tasks and needs IAM permissions, cluster/task definition configuration, subnets/security groups, and image access.
- ECR image build/push steps and ECS context changes are mutating infrastructure operations; confirm before running them.

When diagnosing ECS failures, separate image build/push failures, task placement failures, IAM permission failures, secret injection failures, and user-code import failures.

## Code-Location Deployment Diagnosis

Code-location failures are often not webserver bugs. Triage in this order:

1. Reproduce import/loading locally with the same Python environment or image.
2. Confirm `Definitions` discovery target and workspace entry are correct.
3. Check missing optional packages and native/system dependencies.
4. Check environment variables required by resources are present in the code-location process.
5. Check the code-location server can bind/listen and that webserver/daemon can reach it.
6. Check image tag drift: the webserver may be current while the code-location image is stale.
7. Check user code startup timeout; increase `code_servers.local_startup_timeout` only after fixing slow imports where possible.

A deployment is healthy only when both webserver and daemon can load the same intended code locations using the same instance configuration.
