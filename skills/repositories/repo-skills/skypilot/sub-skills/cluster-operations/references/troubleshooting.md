# Cluster Operations Troubleshooting

Use this guide for interactive SkyPilot cluster and cluster-local job failures. For provider credentials, disabled clouds, storage, Kubernetes, Slurm, or SSH node pools, route to the infrastructure-storage sub-skill after collecting the cluster command, status, and relevant logs.

## Quick Triage Loop

Start with read-only or bounded commands:

```bash
sky status --refresh -o json <cluster>
sky queue -o json <cluster>
sky logs <cluster> --tail 200 --no-follow
sky logs <cluster> --provision --tail 200 --no-follow
```

Then classify the failure:

- Launch never reached a job id: inspect `sky logs <cluster> --provision`, `sky status --refresh <cluster>`, and the dry-run plan.
- Job started but failed: inspect `sky queue <cluster>` and `sky logs <cluster> <job-id> --tail 200 --no-follow`.
- Status table looks stale: rerun with `--refresh`, especially after autostop, manual cloud-console changes, or spot interruptions.
- Commands need parsing or automation: use `-o json` for `status`, `queue`, and `cost-report` instead of scraping tables.

## API Server Or Request Errors

SkyPilot CLI commands talk through the SkyPilot client/server layer. If the user sees request failures, connection errors, or server-not-running messages:

- Run `sky api status` to see whether the local or configured API server is reachable.
- Restart a local API server only if the user intends local control: `sky api stop` then `sky api start`.
- If a remote API endpoint is configured, avoid changing it blindly; route remote login, dashboard, and API compatibility issues to the sdk-api-server sub-skill.
- Re-run the original cluster command with `--dryrun` where possible to separate task parsing/optimizer errors from API/server transport errors.

## Resource Unavailable Or Optimizer Failures

Symptoms include no feasible resources, quota/capacity failures, unsupported accelerator names, or repeated provisioning failures.

- Prefer widening constraints before pinning more: remove exact `--instance-type`, exact region/zone, or narrow `--infra` pins if the user does not require them.
- Keep useful constraints: `--gpus`, `--cpus`, `--memory`, `--disk-size`, `--ports`, and `--use-spot` express workload needs while letting SkyPilot search.
- Use `sky launch --dryrun ...` to see whether the optimizer can find candidates without provisioning.
- Use `--retry-until-up` only when the user accepts indefinite retry attempts for transient capacity shortages.
- If clouds are disabled, credentials are missing, or Kubernetes/SSH contexts are wrong, route to infrastructure-storage.
- For long-running spot workloads that must recover from preemption, route to managed-jobs rather than building a fragile interactive cluster loop.

## Stale Workdir Or Setup Changes

A common debugging trap is using `sky exec` after changing something it intentionally skips.

| Changed item | Use | Why |
| --- | --- | --- |
| Python script, command args, or files under `workdir` | `sky exec <cluster> --workdir . ...` | `exec` syncs workdir and runs through the cluster queue. |
| YAML `run` only | `sky exec <cluster> task.yaml` | Run commands are executed without reprovisioning. |
| `setup`, `file_mounts`, Docker image, disk, resources, ports, infrastructure, or dependency install | `sky launch -c <cluster> task.yaml` | `exec` skips setup and file-mount syncing, and cannot reshape the cluster. |
| Need a clean environment | `sky down <cluster>` then relaunch | Destructive; confirm disk/data loss first. |

If remote code still looks stale, confirm the YAML or CLI `workdir` path, whether `.gitignore`/sync behavior excluded needed files, and whether the command is running under the expected workdir.

## Logs Confusion

- No job id yet: use `sky logs <cluster> --provision` for provisioning/runtime setup logs.
- Need latest job: `sky logs <cluster>` defaults to the latest job on that cluster.
- Need a specific job: get id from `sky queue <cluster>` and run `sky logs <cluster> <job-id>`.
- Need nonblocking output: add `--no-follow --tail 200`.
- Need all logs locally: add `--sync-down`; for distributed jobs, SkyPilot downloads one log per worker.
- Need status in scripts: use `sky logs <cluster> <job-id> --status` rather than grepping log text.
- Need lifecycle hook logs: use `sky logs <cluster> --hook <event>`; omit event only when auto-selection is acceptable.

## Status Output Confusion

- `INIT` means provisioning/runtime setup is in progress or abnormal. If the previous launch failed, rerun `sky launch -c <cluster> ...` after reviewing provisioning logs.
- `UP` means the cluster is live and runtime setup succeeded.
- `STOPPED` means compute is stopped and attached storage may persist. Use `sky start <cluster>` to restart.
- The autostop column shows idle minutes. A value like `1m (down)` means the cluster will be autodowned, not merely stopped.
- Use `sky status --ip <cluster>` only for one cluster; use `sky status <cluster> --endpoints` or `--endpoint <port>` for exposed ports.
- Use `--all-users` only when the user has a multi-user/admin reason to inspect clusters not owned by the current identity.

## Autostop, Stop, And Down Semantics

- `sky autostop <cluster> -i <minutes>` stops after no pending/running jobs for that duration. Setting it later restarts the idle timer; the last setting wins.
- `sky autostop <cluster> --cancel` cancels active auto-stop/down settings.
- `sky autostop <cluster> -i <minutes> --down` schedules destructive teardown. Confirm data retention.
- `sky stop <cluster>` preserves attached disks where supported and can be restarted with `sky start <cluster>`, but disk charges may continue.
- `sky down <cluster>` deletes associated resources and attached disk data. Treat it as destructive.
- `--graceful` on stop/down cancels jobs and waits for MOUNT_CACHED uploads; use it when cached outputs matter.
- Stopping is not supported for all resources. Most spot clusters cannot be stopped; the user may need `sky down` or a managed job strategy.

## Manual Cloud Selection Anti-Pattern

If a user says “launch on AWS us-east-1 p4d” without explaining why, ask whether they need that exact infrastructure. Better default guidance:

```bash
sky launch --dryrun -c <cluster> <task.yaml> --gpus A100:8
```

Only keep pins when they represent real constraints: data locality, private networking, approved cloud account, Kubernetes context, SSH pool, quota, compliance, or exact image/instance dependencies.

## Cluster Owner Mismatch

SkyPilot can reject operations when the cluster was launched by a different identity.

- Do not work around ownership with `--all-users`, `--purge`, or cloud-console deletion unless the user is an authorized admin and understands the consequences.
- Use `sky status --all-users` only to confirm the mismatch in a shared environment.
- Ask the owning user to operate the cluster, or have an admin perform an explicit cleanup plan.
- If stale local state is suspected after confirmed cloud cleanup, treat `--purge` as last-resort repair and warn that the user must ensure no leaked cloud resources remain.

## Cost Report Caveats

`sky cost-report` reads local SkyPilot cluster history and estimates cost from recorded resources and durations. Costs can be inaccurate if clusters were manually changed in cloud consoles, autostopped externally, preempted, or if pricing metadata is stale. Use it for local estimates and cleanup prioritization, not billing reconciliation.
