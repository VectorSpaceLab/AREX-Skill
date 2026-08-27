---
name: managed-jobs
description: "Launch and debug SkyPilot managed jobs, recovery, queues, logs,
  cancellation, job groups, and pools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Managed Jobs

Use this sub-skill when the user needs SkyPilot `sky jobs` workflows: production or long-running batch/training jobs, managed spot recovery, job queues/logs/cancel, job groups, job pools, or job recovery tuning.

## Route First

- Use `references/jobs-workflows.md` for launch patterns, queue/log/cancel commands, SDK equivalents, managed pipelines, spot recovery, job groups, and pools.
- Use `references/troubleshooting.md` when a job is stuck, failed, preempted, cancelled, missing logs, confused by job IDs/names, blocked by pools, or running cloud-bound native tests.
- Use `scripts/jobs_command_builder.py --help` to print safe commands for launch, queue, logs, cancel, and pool operations without executing cloud actions.

## Boundaries

- Route detailed YAML schema, `resources`, `file_mounts`, `volumes`, `envs`, and `secrets` syntax to `../task-yaml/SKILL.md`.
- Route provider credentials, unavailable GPUs, Kubernetes context, storage bucket, volume, Slurm, or SSH infrastructure failures to `../infrastructure-storage/SKILL.md`.
- Route SkyServe service deployment and replica operations to `../serving/SKILL.md`; pools here are only managed-job pools.
- Route API server login/version/request mechanics and SDK request lifecycle details to `../sdk-api-server/SKILL.md`.

## Fast Patterns

- Launch from YAML: `sky jobs launch -n <job-name> <task.yaml> -y`.
- Launch a command: `sky jobs launch -n <job-name> --infra <infra> --cpus 2+ "python train.py" -y`.
- Submit and return immediately: add `-d` / `--detach-run`, then inspect with `sky jobs queue` and `sky jobs logs <job-id>`.
- Debug failures: run `sky jobs queue -a`, then `sky jobs logs <job-id> --no-follow` for user logs and `sky jobs logs --controller <job-id> --no-follow` for provisioning/recovery logs.
- Cancel safely: prefer `sky jobs cancel <job-id> -y`; use `sky jobs cancel -n <name> -y` only when the name identifies the active job unambiguously.

## Verification Notes

- Help-only commands such as `sky jobs --help`, `sky jobs launch --help`, and `python sub-skills/managed-jobs/scripts/jobs_command_builder.py --help` are safe local checks.
- Real `sky jobs launch`, pool creation, recovery, and smoke tests require configured cloud/Kubernetes resources and should be treated as cloud-bound unless the user explicitly authorizes them.
