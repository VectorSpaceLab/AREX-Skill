---
name: deployment-operations
description: "Use when a coding agent needs to configure or troubleshoot Dagster
  OSS production operations: DAGSTER_HOME, dagster.yaml, instance storage,
  webserver and daemon services, run launchers/coordinators/executors, retries,
  run monitoring, Docker/Kubernetes/ECS deployment shape, or code-location
  deployment failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment Operations

Use this sub-skill for Dagster OSS deployment and operations work after the user has working Dagster definitions and wants persistent services, durable instance state, queued or remote run execution, schedule/sensor automation, monitoring, retries, or infrastructure-specific deployment guidance.

## Route First

- Use this sub-skill for `DAGSTER_HOME`, `dagster.yaml`, `dagster-webserver`, `dagster-daemon`, instance storage, run queue/concurrency, retries/timeouts, run monitoring, and run launcher operations.
- Use this sub-skill for Docker, Kubernetes, and ECS deployment checklists at the concept/configuration level, including image, workspace, service, and secret concerns.
- Route local command usage, `dagster dev`, definitions validation, and one-off asset/job execution to `../cli-local-development/SKILL.md` if that sub-skill exists.
- Route schedule/sensor definition authoring to `../automation-schedules-sensors/SKILL.md` if that sub-skill exists; use this sub-skill when the issue is daemon/runtime operation.
- Route resource/run config authoring and environment-variable config schemas to `../configuration-resources/SKILL.md` if that sub-skill exists.
- Do not cover Dagster Plus account setup, Dagster Cloud CLI deployment, UI TypeScript internals, or Helm template maintenance here.

## Start Here

1. Confirm the target is Dagster OSS and identify the deployment shape: local service, Docker Compose, Kubernetes, ECS, or custom process supervisor.
2. Establish one shared `DAGSTER_HOME` for the webserver, daemon, and run workers; verify that `dagster.yaml` lives there and is readable by every service.
3. Run `python scripts/check_dagster_instance_config.py --dagster-home <path>` from this sub-skill to check for a safe baseline without starting services.
4. Decide whether the instance needs durable external storage. SQLite is acceptable for local/single-node evaluation; production multi-service deployments usually need shared database-backed storage and shared compute logs.
5. Confirm the long-running services are represented: one or more webservers, exactly one daemon process, and one code-location server per code location.
6. Configure execution flow deliberately: run coordinator queues/submits runs, daemon dequeues if queued, run launcher starts the run worker, and the job executor controls per-step execution inside the worker.

## References

- [Deployment workflows](references/workflows.md) for service topology, `dagster.yaml` patterns, run queue/concurrency, retries, monitoring, daemon/webserver operations, and Docker/Kubernetes/ECS deployment checklists.
- [Troubleshooting](references/troubleshooting.md) for import/install issues, optional dependency gaps, config misuse, daemon heartbeat failures, storage mismatches, code-location failures, image pull failures, stuck runs, and concurrency deadlocks.
- [Instance config checker](scripts/check_dagster_instance_config.py) for a safe `DAGSTER_HOME` and `dagster.yaml` inspection helper that does not start services or contact infrastructure.

## Safety Notes

- Do not start or restart production services, run migrations, wipe storage, edit secrets, push images, or apply cluster/ECS changes without explicit user approval.
- Treat `dagster instance migrate`, direct database cleanup, Kubernetes/ECS deploy commands, and Docker Compose `up/down` as mutating operations.
- Keep secrets in environment variables or platform secret stores; do not write credentials directly into public `dagster.yaml`, workspace files, Dockerfiles, manifests, or generated skill content.
