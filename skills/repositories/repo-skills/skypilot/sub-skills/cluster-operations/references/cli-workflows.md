# Cluster CLI Workflows

This reference distills SkyPilot's interactive cluster CLI behavior for future agents. It focuses on commands that operate normal clusters and cluster-local jobs, not managed jobs or SkyServe services.

## Command Map

| Goal | Primary command | Notes |
| --- | --- | --- |
| Validate a launch plan | `sky launch --dryrun ...` | Parses the entrypoint and shows optimizer planning without provisioning cloud resources. |
| Create or reuse a cluster | `sky launch -c <cluster> <entrypoint>` | Reuses an existing named cluster shown by `sky status`; otherwise provisions a cluster. |
| Run on an existing cluster | `sky exec <cluster> <entrypoint>` | Faster iteration path; skips provisioning, setup, and file-mount syncing. |
| Inspect clusters | `sky status [--refresh] [-o json] [cluster]` | Use `--refresh` when cloud state may have changed outside SkyPilot or autostop is involved. |
| Inspect cluster-local jobs | `sky queue [-o json] <cluster>` | Shows pending/running/finished jobs for interactive clusters, not managed jobs. |
| Tail logs | `sky logs <cluster> [job-id] --tail <n>` | Omit job id for latest job; use `--no-follow` for bounded diagnostics. |
| Check job result | `sky logs <cluster> <job-id> --status` | Returns a status code instead of streaming logs. |
| Cancel cluster job | `sky cancel <cluster> <job-id>` | Use `--all` only after confirming all current-user cluster jobs should stop. |
| Estimate historical cost | `sky cost-report --days <n> [-o json]` | Cost is based on local cluster history and resource pricing estimates. |
| Stop restartably | `sky stop <cluster>` | Stops compute and preserves attached disks where supported; disks may still incur cost. |
| Restart stopped cluster | `sky start <cluster> [-i <minutes>]` | Restarts same cloud/region/zone; no optimizer failover for stopped clusters. |
| Schedule cleanup | `sky autostop <cluster> -i <minutes>` | Last setting wins; `--down` changes from restartable stop to destructive teardown. |
| Destroy cluster | `sky down <cluster>` | Deletes associated resources and attached disk data. Confirm first. |

## Launch Pattern

Prefer this sequence for new interactive work:

```bash
sky launch --dryrun -c <cluster> <task.yaml>
sky launch -c <cluster> <task.yaml> --idle-minutes-to-autostop 30
sky status -o json <cluster>
sky queue -o json <cluster>
sky logs <cluster> --tail 200 --no-follow
```

Launch behavior to remember:

- `ENTRYPOINT` can be a YAML task file or a bash command. YAML gives repeatable resources, workdir, setup, and run sections; direct commands are useful for small one-offs.
- `-c/--cluster` either reuses that named cluster or provisions a new one. If the user wants one persistent dev cluster, always name it.
- `--workdir` overrides YAML `workdir` and syncs that local directory before run commands. Both `setup` and `run` execute under the remote workdir.
- `--dryrun` avoids cloud launch and should be the default recommendation for unvalidated tasks.
- `--detach-run` returns after job submission instead of streaming logs; pair it with `sky queue` and `sky logs`.
- `--retry-until-up` is appropriate for unavailable capacity when the user accepts indefinite retry attempts.
- `--no-setup` skips setup on relaunch and is only safe when dependencies are already present.
- `--fast` may skip provisioning/setup when an existing cluster is already available; avoid it when validating changed setup or resources.

## Optimizer-Friendly Resources

SkyPilot is designed to choose cloud, region, zone, and instance type from resource constraints. Prefer constraints such as:

```bash
sky launch --dryrun -c <cluster> <task.yaml> --gpus A100:1 --cpus 8+ --memory 32+
```

Use manual pins only when the user has a concrete requirement:

- `--infra aws`, `--infra aws/us-east-1`, `--infra k8s/my-context`, or `--infra ssh/my-nodes` pins infrastructure. This is useful for account, data-sovereignty, Kubernetes, Slurm, SSH, or quota reasons, but it reduces optimizer flexibility.
- `--instance-type` pins a specific VM shape. Prefer `--gpus`, `--cpus`, and `--memory` unless the user needs that exact shape.
- `--region` and `--zone` are legacy-style pins surfaced through the CLI; prefer `--infra` for compact cloud/region/zone intent.
- `--use-spot` may reduce cost but changes availability and stop/recovery expectations; for resilient long-running workloads, route to managed jobs.
- `--ports` opens endpoint ports on the cluster. Inspect with `sky status <cluster> --endpoints` or `sky status <cluster> --endpoint <port>`.

## Exec Iteration Pattern

Use `sky exec` after the first launch when the cluster exists and only run-time code or command arguments changed:

```bash
sky exec <cluster> --workdir . python train.py --debug
sky queue -o json <cluster>
sky logs <cluster> --tail 200 --no-follow
```

Important `exec` semantics:

- `sky exec` runs through the cluster job queue and requires resources to fit on the existing cluster.
- It syncs `workdir` if YAML `workdir` or `--workdir` is set.
- It skips provisioning, setup commands, and file-mount syncing. If setup dependencies, image, file mounts, resource shape, disk size, or cluster infrastructure changed, use `sky launch -c <cluster> <task.yaml>` instead.
- It is non-interactive and has no pseudo-terminal. For `htop`, `gpustat -i`, shells, editors, or live terminal UI, use SSH into the named cluster rather than `sky exec`.

## Status, Queue, And Logs

Use JSON output for automation and table output for humans:

```bash
sky status --refresh -o json <cluster>
sky queue --skip-finished -o json <cluster>
sky cost-report --days 7 -o json
```

Status fields include cluster name, launch age, resources, region, zone, hourly price, status, autostop, and last command. Common statuses:

- `INIT`: provisioning/setup is ongoing or the cluster is abnormal; rerun `sky launch -c <cluster> ...` to retry or recover.
- `UP`: provisioning and runtime setup succeeded.
- `STOPPED`: compute is stopped but persistent disks remain; restart with `sky start <cluster>`.

Logs patterns:

- `sky logs <cluster>` tails the latest cluster-local job.
- `sky logs <cluster> <job-id> --tail 200 --no-follow` captures recent logs without blocking.
- `sky logs <cluster> <job-id> --status` is best for scripts that need success/failure status.
- `sky logs <cluster> --provision` streams provisioning logs when launch failed before a job id exists.
- `sky logs <cluster> --sync-down <job-id>` downloads logs under the user's normal SkyPilot logs directory; use it when tailing is insufficient.

## Lifecycle And Cleanup

Choose cleanup based on data-retention needs:

| Need | Command | Safety note |
| --- | --- | --- |
| Restart later with disk state | `sky stop <cluster>` | Compute billing stops, disks remain and may still bill. Not supported for all resources, especially most spot clusters. |
| Restart a stopped/INIT cluster | `sky start <cluster>` | Starts same prior cloud/region/zone; add `-i <minutes>` for autostop on restart. |
| Auto-stop when idle | `sky autostop <cluster> -i 30` | Idleness means no pending/running cluster jobs. Last setting wins. |
| Cancel autostop | `sky autostop <cluster> --cancel` | Use when keeping a cluster up intentionally. |
| Auto-delete when idle | `sky autostop <cluster> -i 30 --down` | Destructive and non-restartable; confirm disk/data expectations. |
| Delete now | `sky down <cluster>` | Deletes all associated resources and attached disk data. |
| Flush cached uploads first | `sky stop/down <cluster> --graceful` | Cancels current jobs and waits for MOUNT_CACHED uploads before stopping/terminating. |

Avoid `--all`, `--all-users`, `--purge`, and `--yes` unless the user explicitly confirms scope. `--purge` is an advanced repair flag: it changes SkyPilot's cluster table even if cloud cleanup failed, so the user must separately ensure no cloud resources are leaked.

## Interactive Debug Case

For a request like “debug my training script on one GPU, check logs, then clean up,” suggest:

```bash
sky launch --dryrun -c debug-train task.yaml --gpus A100:1
sky launch -c debug-train task.yaml --gpus A100:1 --idle-minutes-to-autostop 30
sky exec debug-train --workdir . python train.py --debug
sky queue -o json debug-train
sky logs debug-train --tail 200 --no-follow
sky autostop debug-train -i 30
# when disk state is no longer needed:
sky down debug-train
```

If setup or resource requirements change after the first run, replace the `sky exec` line with `sky launch -c debug-train task.yaml ...` so SkyPilot can rerun setup and reconcile resources.
