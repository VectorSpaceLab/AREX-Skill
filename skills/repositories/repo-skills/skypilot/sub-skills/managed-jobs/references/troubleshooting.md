# Managed Jobs Troubleshooting

Use this reference to decide which `sky jobs` command to run next and when to route to another sub-skill.

## First Response Checklist

1. Identify the job by numeric ID from `sky jobs queue`; prefer job ID over name for terminal jobs or reused names.
2. Read user logs with `sky jobs logs <job-id> --no-follow`.
3. Read controller logs with `sky jobs logs --controller <job-id> --no-follow` for provisioning, resource search, recovery, and cleanup.
4. Use `sky jobs queue -a` or focused status filters to compare current status with the expected lifecycle.
5. Separate application failures from infrastructure failures before changing YAML.

## Status-Based Diagnosis

| Status | Meaning | Next action |
| --- | --- | --- |
| `PENDING` | Job is waiting for scheduler capacity, controller capacity, or resources. | Use `sky jobs queue --refresh`; inspect controller logs if it stays pending unexpectedly. |
| `STARTING` | SkyPilot is provisioning and launching the worker cluster. | Use controller logs for resource, credential, setup, or image failures. |
| `RUNNING` | User workload is running. | Use user logs and task-specific logs for pipelines/job groups. |
| `RECOVERING` | Worker cluster is being replaced after preemption or infrastructure failure. | Check controller logs for preemption and resource search; verify checkpointing if progress restarts. |
| `FAILED` | User `run` failed and recovery did not apply or retries ended. | Inspect user logs; consider `job_recovery.max_restarts_on_errors` only for transient app errors. |
| `FAILED_SETUP` | `setup` failed. | Inspect user logs; fix package install, env/secrets, workdir, or image assumptions. |
| `FAILED_PRECHECKS` | Prechecks failed before launch. | Route credentials/provider/resource validation to infrastructure-storage; route YAML schema to task-yaml. |
| `FAILED_NO_RESOURCE` | Resource search could not satisfy the request. | Consider broader `any_of`, different infra/region/GPU, or on-demand fallback; route provider capacity triage to infrastructure-storage. |
| `FAILED_CONTROLLER` | Controller process failed unexpectedly. | Inspect controller logs and API server health; route request/server mechanics to sdk-api-server. |
| `CANCELLING` | Cancellation requested but cleanup is still running. | Wait and refresh; inspect controller logs if stuck. |

## Preemption Versus User Failure

Preemption/infrastructure signals:

- Queue status enters `RECOVERING`.
- Controller logs mention preemption, cluster status loss, resource failover, or recovery attempts.
- User logs may stop abruptly without a clean application traceback.

User failure signals:

- User logs show Python exceptions, shell command failures, failed tests, missing files, or bad arguments.
- Queue status becomes `FAILED` or `FAILED_SETUP`.
- Recovery only happens for user failures when `resources.job_recovery.max_restarts_on_errors` or `recover_on_exit_codes` is configured.

If preemption recovery works but the job loses progress, add checkpoint save/load to persistent storage. SkyPilot restarts the job; the application must resume from checkpoint.

## Controller Logs Versus User Logs

Use user logs for:

- `setup` and `run` output.
- Application stack traces.
- Progress bars and checkpoint messages.
- Pipeline or job-group task output.

Use controller logs for:

- Optimizer/resource selection and provisioning.
- Cloud credentials and precheck failures.
- Spot preemption and recovery attempts.
- Cleanup and controller errors.
- Provisioning rich-status messages when user logs are not ready.

Typical commands:

```bash
sky jobs logs <job-id> --no-follow
sky jobs logs --controller <job-id> --no-follow
sky jobs logs <job-id> <task-name> --no-follow
sky jobs logs --sync-down <job-id>
```

## Job ID And Name Confusion

- `sky jobs logs -n <name>` is convenient for an active job, but job names can be reused and name lookup is less reliable for terminal jobs.
- When a job is cancelled or terminal, get the ID from `sky jobs queue -a` and use `sky jobs logs <job-id> --no-follow`.
- Pipelines and job groups have one outer job ID plus per-task IDs/names. Use `sky jobs logs <job-id> <task-id-or-name>` for one task.
- Pool-submitted jobs may also have worker-cluster job IDs internally; use the managed job ID shown by `sky jobs queue` for user-facing operations.

## Cancellation Problems

If cancellation does not behave as expected:

- Confirm the selector is valid: exactly one of job IDs, `--name`, `--pool`, `--all`, or `--all-users`.
- Use `sky jobs cancel <job-id> -y` for precise cancellation.
- Use `--graceful --graceful-timeout <seconds>` for workloads that need to flush checkpoints or buffered data.
- If the job remains `CANCELLING`, check controller logs for cleanup delays or cloud deletion failures.
- For pool jobs, `sky jobs cancel --pool <pool-name> -y` cancels jobs in the pool; it does not delete the pool workers themselves.

## Spot Recovery And Fallback

Common issue: “My spot job recovered but restarted from scratch.”

- Expected unless the application checkpoints and resumes.
- Add a persistent checkpoint location via `volumes` on Kubernetes or `file_mounts` bucket mounts.
- Ensure the training command has an explicit `--resume` or equivalent.
- Log the checkpoint path and run ID so post-recovery logs can prove resume behavior.

Common issue: “Spot capacity is unavailable.”

- Use `resources.any_of` with spot and non-spot entries for fallback.
- Broaden region/zone/infra constraints where possible.
- Use `sky jobs queue --refresh` and controller logs to distinguish waiting for capacity from invalid credentials.

Common issue: “User-code transient errors should retry.”

- Configure `resources.job_recovery.max_restarts_on_errors`.
- Add `recover_on_exit_codes` for known transient codes such as framework-specific NCCL timeout exits.
- Do not add exit code `137` to `recover_on_exit_codes`.

## Job Group Troubleshooting

- If YAML is not recognized as a job group, ensure the first document has `execution: parallel` and later documents are named tasks.
- If parsing fails, check every task has a unique `name`.
- If `primary_tasks` fails, ensure every listed primary task exists and names match exactly.
- If auxiliary tasks terminate too early or late, tune `termination_delay` as a string such as `30s` or a dict with `default` and per-task entries.
- If service discovery fails, confirm the workload is on Kubernetes. Hostnames use `{task_name}-{node_index}.{job_group_name}` and `SKYPILOT_JOBGROUP_NAME`.
- If logs are too noisy, use `sky jobs logs <job-id> <task-name> --no-follow`.

## Pool Troubleshooting

- If `sky jobs launch --num-jobs` fails, add `--pool <pool-name>`; `--num-jobs` only works with pools.
- If jobs submitted to a pool do not see new setup/file mounts/storage mounts, update the pool with `sky jobs pool apply`; submitted job setup and mounts may be ignored for pool jobs.
- If `pool down` warns about nonterminal jobs, cancel or let those jobs finish before deleting workers.
- Use `sky jobs pool logs --controller <pool-name> --no-follow` for pool control-plane issues and `sky jobs pool logs <pool-name> <worker-id> --no-follow` for worker logs.
- If pool YAML is rejected, route pool field syntax to task-yaml.

## Native Tests And Examples

Managed-job smoke tests, recovery tests, storage tests, and pool/job-group launches are not safe local checks by default because they may create cloud resources, need credentials, use GPUs/TPUs, or require Kubernetes.

Safe evidence-style checks are limited to help output, SDK signature/import inspection, YAML parser unit tests, and the bundled command builder. If the user explicitly authorizes cloud/Kubernetes execution, record the chosen provider, expected cost/risk, cleanup command, and skip conditions before running native managed-job tests.

## Escalation Routes

- YAML parse/schema/resource-field problems: `../../task-yaml/SKILL.md`.
- Credentials, cloud availability, Kubernetes context, storage bucket/volume problems: `../../infrastructure-storage/SKILL.md`.
- API server login, remote server version, request ID polling, dashboard access: `../../sdk-api-server/SKILL.md`.
- Serving replicas, service update/rollback/readiness: `../../serving/SKILL.md`.
