# Ray Cluster Operations Troubleshooting

Start with non-mutating checks, record the address and cluster target, and escalate from help output to read-only cluster queries before running lifecycle commands.

## First Safe Checks

Run the bundled helper commands from the `cluster-ops` sub-skill directory:

```bash
python scripts/ray_cli_doctor.py
python scripts/ray_cli_doctor.py --command job
ray --help
ray job --help
ray list --help
ray status --help
```

If these fail, fix the local Ray installation before debugging the remote cluster.

## CLI Command Missing or Import Fails

Symptoms:

- `ray: command not found`
- `No such command 'job'`, `No such command 'list'`, or `No such command 'logs'`
- Import errors when invoking state, dashboard, or job commands

Likely causes and actions:

| Cause | Action |
| --- | --- |
| Ray is not installed in the active Python environment. | Ask the user which environment should own the CLI; install the appropriate narrow extra for the workflow. |
| Minimal Ray install lacks dashboard/state dependencies. | For cluster operations, prefer `ray[default]` rather than `ray[all]`. |
| Wrong Python environment first on `PATH`. | Compare `python -c "import ray; print(ray.__version__)"` with `ray --version`; ask user before changing environments. |
| Version mismatch between client and cluster. | Capture local `ray --version` and cluster version warnings from CLI output; avoid mutating commands until compatibility is understood. |

Recommended extras remain narrow by workflow: `ray[default]` for cluster/admin/jobs/state, and sibling-specific extras only when needed by Data, Train, Tune, Serve, or RLlib work.

## Dashboard or Jobs Address Cannot Connect

Symptoms:

- `ray job status` or `ray job logs` cannot connect
- Connection refused to `127.0.0.1:8265`
- Jobs CLI points at a different address than expected
- Dashboard page is unavailable

Checklist:

1. Confirm the address is an HTTP dashboard/API URL, not `ray://...` and not a GCS/bootstrap address.
2. Inspect the value of `RAY_API_SERVER_ADDRESS` and any explicit `--address` flag.
3. For local clusters, confirm the dashboard was included and the chosen host/port match the command output from `ray start --head`.
4. For VM clusters, confirm the `ray dashboard <cluster.yaml>` port-forward target and whether local port `8265` is already in use.
5. For Kubernetes, confirm the port-forward, namespace, service/pod name, and local port.
6. If auth or gateway headers are required, validate `RAY_JOB_HEADERS` is valid JSON.
7. Re-run a small read-only command such as `ray job list` once the endpoint is reachable.

Avoid exposing the dashboard on `0.0.0.0` unless the user explicitly accepts the network/security implications.

## `ray status` Cannot Find a Cluster

Symptoms:

- `ray status` errors about no cluster or bootstrap address
- The command works on a head node but not on a client machine

Actions:

- Try `ray status --help` first to confirm CLI availability.
- Ask where the command is running: head node, worker node, local laptop, container, or CI.
- If querying from outside the cluster, use dashboard-backed State API commands with the dashboard/API URL where applicable, or run status on the head node.
- If a local cluster is intended but not running, ask before starting one with `ray start --head`.

## Runtime Environment Upload or Import Fails

Symptoms:

- Job starts but fails before user code imports
- Logs mention runtime-env setup failure, missing module, unavailable package, upload failure, or timeout
- `working_dir` files are missing inside the job

Checklist:

1. Confirm the submitted command includes `--working-dir` or a runtime-env `working_dir` when using local source files on a remote cluster.
2. Verify the entrypoint path is relative to the uploaded working directory.
3. Keep runtime-env packages mutually compatible: top-level `pip`, `conda`, and `uv` are mutually exclusive.
4. If using `container` or `image_uri`, confirm only compatible runtime-env fields are present.
5. Trim large directories and exclude caches, datasets, build output, virtual environments, and credentials.
6. Increase `config.setup_timeout_seconds` only after confirming package installation legitimately needs more time.
7. Inspect `ray job logs <submission_id>`, `ray list runtime-envs`, `ray logs raylet.out --tail 200`, and dashboard runtime-env events if available.

For dependency-heavy applications, prefer a prebuilt cluster image/container or remote package artifact over repeatedly uploading large local environments.

## State API Partial, Stale, or Truncated Results

Symptoms:

- `ray list` warns about partial results
- Output changes between calls
- Large result sets are truncated
- `--detail` is slow or times out

Expected behavior:

State APIs return snapshots, not transactional live views. A list call may query multiple components; if some components fail, the CLI can return partial output with a warning. Large outputs can also be truncated.

Actions:

```bash
ray summary tasks
ray summary actors
ray list tasks --limit 20 --filter "state=RUNNING" --timeout 60
ray list actors --format json --limit 50
ray get actors <actor_id>
```

Use `summary` first, reduce the scope with `--filter` and `--limit`, increase `--timeout` cautiously, and avoid assuming absence from one snapshot means the resource never existed.

## Logs Are Missing or Too Large

Actions:

- Use the most specific log target available: `job`, `actor`, `task`, `worker`, or cluster log file.
- Bound output with `--tail` and avoid following logs indefinitely unless the user requests it.
- For cluster-level issues, start with `ray logs raylet.out --tail 200` and `ray logs gcs_server.out --tail 200` when available.
- For application failures submitted through Jobs, start with `ray job logs <submission_id>` because it captures the entrypoint stdout/stderr.

Examples:

```bash
ray job logs <submission_id>
ray logs actor --id <actor_id> --tail 200
ray logs task --id <task_id> --err --tail 200
ray logs raylet.out --tail 200
```

## OOM and Unexpected Worker Exits

Symptoms:

- `Worker exit type: UNEXPECTED_SYSTEM_EXIT`
- `Worker exit type: SYSTEM_ERROR`
- Messages about workers killed due to node memory pressure
- Dashboard OOM-kill or unexpected system worker failure metrics increase
- Tasks or actors repeatedly retry after memory pressure

Read-only diagnosis sequence:

```bash
ray status
ray summary tasks
ray summary actors
ray list nodes --format table
ray list workers --detail --limit 50
ray memory --stats-only
ray logs raylet.out --tail 300
```

Interpretation:

- Ray's memory monitor can kill workers before the Linux OOM killer to keep the node stable; Ray logs details in `raylet.out`.
- Linux OOM kills use SIGKILL, so workers may disappear with generic unexpected-exit messages.
- Object store pressure is different from worker heap/RSS pressure. `ray memory` helps inspect object references; task/actor memory overuse often needs code-level resource requests or lower parallelism.
- Head nodes can OOM if they run user tasks and dashboard/GCS/system components. Starting a head node with `--num-cpus=0` can keep user tasks off the head node when that is appropriate.
- Resource isolation options such as `--enable-resource-isolation` and `--system-reserved-memory` affect start-time behavior and require platform support; do not change them on an existing cluster without an operations plan.

Route code changes such as adding task/actor memory requests, reducing parallelism, or fixing leaks to `../core-runtime/SKILL.md` after cluster-level evidence identifies the offending workload.

## Unsafe or High-Impact Commands

Require explicit user confirmation and a target review before running:

| Command | Risk |
| --- | --- |
| `ray stop`, especially `--force` | Stops local Ray processes and may surface as worker/system exits. |
| `ray start` | Starts local services, opens ports, allocates object store memory, and can expose dashboard depending on host options. |
| `ray up` / `ray down` | Creates, updates, or tears down remote cluster infrastructure. |
| `ray exec` / `ray submit` / `ray attach` | Runs commands or opens sessions on remote nodes. |
| `ray job submit` / `ray job stop` / `ray job delete` | Starts, cancels, or removes application job state. |
| `ray kill-actor` | Terminates application actors. |
| `ray stack` | Uses local process inspection tools and may require `sudo`. |
| `ray symmetric-run` | Starts Ray across multiple nodes and waits for cluster membership. |

Before running one, state the target, expected side effect, rollback/stop command, and what output will be captured.

## When to Ask the User

Ask a concise clarification when any of these are missing:

- Local versus remote cluster target.
- Dashboard/API URL or cluster YAML path.
- Permission to run mutating commands.
- Kubernetes namespace/context or VM/cloud credentials scope.
- Whether logs may contain secrets before saving or sharing them.
- Whether the goal is cluster diagnosis or code-level application repair.
