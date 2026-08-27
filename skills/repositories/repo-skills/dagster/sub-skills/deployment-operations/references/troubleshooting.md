# Deployment Troubleshooting

Use this guide when Dagster OSS behaves differently in a deployed service than in local development. Separate instance, service, code-location, and infrastructure failures before changing configuration.

## Fast Triage

1. Identify the failing process: webserver, daemon, code-location server, run worker, database/storage, or orchestrator.
2. Confirm every process uses the intended `DAGSTER_HOME` and reads the same `dagster.yaml`.
3. Run the bundled checker on the intended instance directory:

   ```bash
   python scripts/check_dagster_instance_config.py --dagster-home <path>
   ```

4. Run only non-mutating command checks first:

   ```bash
   dagster --help
   dagster-webserver --help
   dagster-daemon run --help
   ```

5. Inspect logs from the specific failing process before changing global config.

## Install or Import Errors

Symptoms include `ModuleNotFoundError`, import-time crashes, code locations that never load, or services that pass `--help` but fail on workspace load.

Likely causes:

- The webserver/daemon image has Dagster but the code-location image lacks project dependencies.
- The code-location image has project code but not optional Dagster integration packages such as Docker, Kubernetes, Postgres, MySQL, AWS, GCP, or Celery libraries.
- The working directory or package/module target differs between local CLI and deployed workspace config.
- Native system dependencies required by user code are absent from the image.
- Environment variables required at import time are missing.

Safe approach:

- Validate the same target locally with definitions validation or an import-only check before redeploying.
- Compare package lists across webserver, daemon, and code-location images.
- Move external-system calls out of module import time where possible.
- Prefer environment-variable placeholders in config and ensure the runtime environment supplies them.

## Optional Dependency Gaps

Dagster core does not install every deployment integration by default. If `dagster.yaml` references a class from an integration package, the process reading that file must have the package installed.

Common examples:

- `dagster_postgres` for Postgres instance storage.
- `dagster_mysql` for MySQL instance storage.
- `dagster_docker` for Docker run launchers/executors.
- `dagster_k8s` for Kubernetes launchers/executors.
- `dagster_aws` for ECS, S3 compute logs, or AWS-backed resources.
- `dagster_celery` or related packages for Celery execution.

If the webserver starts but the daemon fails, check optional packages in the daemon environment too. If runs fail only after launch, check the run worker image.

## Config, CLI, and API Misuse

Common mistakes:

- Setting `DAGSTER_HOME` for one shell/service but not another.
- Putting `dagster.yaml` in the project directory while services read a different instance directory.
- Expecting schedules/sensors to run with only `dagster-webserver`; they require the daemon.
- Expecting queued runs to launch without `dagster-daemon run`.
- Confusing run launcher behavior with executor behavior: launchers create run workers; executors run steps inside workers.
- Using local filesystem outputs with cross-container retries from failure; retried workers need access to previous outputs.
- Changing `workspace.yaml` for the webserver but forgetting the daemon uses it too.

Before editing deployment files, write down the intended values for: instance directory, workspace target, storage backend, run coordinator, run launcher, executor, image tag, and secret source.

## Schedules or Sensors Not Firing

Diagnosis checklist:

- Is exactly one daemon process running for the instance?
- Does the UI show recent daemon heartbeats?
- Do webserver and daemon share the same `DAGSTER_HOME` and instance database?
- Are the schedules/sensors enabled in the same instance the daemon uses?
- Can the daemon load the workspace/code locations?
- Are tick errors visible in daemon logs or UI tick history?
- Are run queue limits, tag limits, or pools preventing launched runs from starting?

A common failure is enabling a schedule in a webserver connected to one local instance while the daemon points at another instance directory. Align `DAGSTER_HOME` and storage first.

## Code-Location Deployment Failures

Symptoms include unloaded locations, reload failures, timeout errors, gRPC connection failures, or a blank/partial deployment in the UI.

Triage:

1. Inspect code-location server logs, not only webserver logs.
2. Confirm the target module/file/package and attribute exist in the deployed image.
3. Confirm required environment variables are present in the code-location process.
4. Confirm the image contains all project and optional integration dependencies.
5. Confirm network connectivity from webserver and daemon to the code-location server.
6. Confirm image tags are not stale and workspace entries point at the intended host/port.
7. For slow imports, reduce import work first; then consider `code_servers.local_startup_timeout`.

Do not mask import-time user-code failures by increasing timeouts unless logs show the process is genuinely progressing.

## Run Queue and Concurrency Stalls

Symptoms include runs stuck in QUEUED or concurrency pools that never free.

Checklist:

- `QueuedRunCoordinator` is configured if queueing is expected.
- `dagster-daemon run` is alive, heartbeating, and able to read the instance database.
- `concurrency.runs.max_concurrent_runs` is not lower than the intended capacity.
- Tag limits or pools are not saturated by long-running or abandoned runs.
- `run_monitoring.free_slots_after_run_end_seconds` is set when op concurrency slots can be abandoned by cancelled/failed runs.
- Daemon logs do not show database connectivity, import, or permission errors.

Direct database cleanup should be a last resort and requires explicit user approval.

## Stuck STARTING, STARTED, or CANCELING Runs

- STARTING usually points to a run worker that never started: image pull failure, launcher misconfiguration, service account/IAM/RBAC issue, missing environment, or timeout too short.
- STARTED but no progress can indicate a crashed/hung worker, user-code deadlock, lost logs, or external dependency hang.
- CANCELING can indicate the launcher could not terminate the worker or the worker did not report completion.

Use `run_monitoring` with `start_timeout_seconds`, `cancel_timeout_seconds`, and `max_runtime_seconds` to bound these states. Run worker crash recovery requires a launcher/executor combination that supports worker health checks and resumes.

## Docker Failures

Common causes:

- Container-local SQLite or compute logs used where multiple containers need shared state.
- Webserver and daemon containers mount different instance directories.
- User-code container lacks dependencies present in the webserver container.
- Docker run launcher lacks socket access, network access, image name, or environment configuration.
- Secrets are only present in an interactive shell, not in service containers.

Use help-only checks and image inspection before `docker compose up`, `docker compose push`, or context changes. Those operations can mutate local or remote infrastructure.

## Kubernetes Failures

Common causes:

- `ImagePullBackOff` from missing image-pull secret, wrong image name/tag, private registry auth failure, or registry/network outage.
- `CrashLoopBackOff` from import errors, missing environment variables, bad command/args, or missing optional packages.
- Run pods never start because of service account, RBAC, namespace, resource quota, node selector, or volume issues.
- Code-location service is not reachable from the webserver or daemon namespace.
- Compute logs or outputs use pod-local storage but retries/readers run in different pods.

Start with pod events and logs for the exact failing pod. Keep secrets in Kubernetes Secrets or external secret mechanisms, not in checked-in YAML.

## ECS Failures

Common causes:

- ECR image not pushed or task definition points at an old tag.
- Task role or execution role lacks permissions for logs, secrets, storage, or starting run tasks.
- Security groups/subnets prevent webserver, daemon, and code-location services from communicating.
- Load balancer health check points at the wrong port/path.
- Run launcher task configuration differs from the image/environment used by long-lived services.

Separate build/push errors, service scheduling errors, task startup errors, and user-code import errors. Each has different logs and owners.

## Compute Logs Missing

If the UI shows no raw compute logs:

- Check the `compute_logs` manager in `dagster.yaml`.
- Confirm the run worker can write to the configured location.
- Confirm the webserver can read from the configured location.
- For containers/pods/tasks, avoid worker-local paths unless the log location is mounted/shared or backed by object storage.
- Confirm optional packages for cloud log managers are installed in writer and reader processes.

## Storage and Migration Issues

Storage problems often appear as startup failures, missing runs/ticks, daemon heartbeat gaps, or inconsistent UI state.

Safe checks:

- Confirm the storage backend and credentials in `dagster.yaml`.
- Confirm every service reaches the same database.
- Confirm optional database packages are installed.
- Confirm the database schema matches the Dagster version before running migrations.

`dagster instance migrate` mutates the instance database. Ask for explicit approval, verify backups, and prefer staging validation before production.

## Difficult Synthetic Usability Cases

Use these as verification prompts for this sub-skill:

- Diagnose schedules not firing when the webserver and daemon use different `DAGSTER_HOME` values and the daemon cannot see the enabled schedule state or durable storage.
- Convert a local `dagster dev` workflow into a Docker/Kubernetes deployment checklist, explicitly flagging secrets, image tags, shared instance storage, daemon singleton behavior, image pull failures, and code-location reachability.
