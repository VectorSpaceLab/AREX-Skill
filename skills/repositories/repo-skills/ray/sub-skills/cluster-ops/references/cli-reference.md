# Ray CLI Reference for Cluster Operations

This reference distills the Ray CLI surface used for cluster administration, Jobs, dashboard access, state inspection, logs, and debugging. It is self-contained operational guidance; use `ray --help` or `scripts/ray_cli_doctor.py` to verify the installed CLI before relying on a command in a specific environment.

## Safety Classes

| Class | Commands | Default behavior for agents |
| --- | --- | --- |
| Help-only | `ray --help`, `ray <command> --help`, `ray job --help`, `ray list --help`, `ray summary --help`, `ray logs --help` | Safe to run; no cluster mutation expected. |
| Read-only cluster queries | `ray status`, `ray list`, `ray get`, `ray summary`, `ray logs`, `ray job status`, `ray job logs`, `ray job list`, `ray memory`, `ray timeline` | Connect to a cluster or dashboard; ask/confirm address when ambiguous. May be expensive on busy clusters. |
| Local process mutation | `ray start`, `ray stop`, `ray kill-actor`, `ray stack` | Can start/stop/kill/process-inspect local Ray workers; require explicit user authorization. `ray stack` may require `py-spy` and `sudo`. |
| Cluster lifecycle or SSH mutation | `ray up`, `ray down`, `ray attach`, `ray exec`, `ray submit`, `ray rsync-up`, `ray rsync-down`, `ray dashboard` | Uses cluster YAML/SSH/port forwarding or changes remote state; require explicit target and authorization. |
| Application mutation | `ray job submit`, `ray job stop`, `ray job delete` | Submits, cancels, or deletes job state; require dashboard address and user authorization. |
| Reference-only launchers | `ray symmetric-run` | Starts Ray across nodes and waits for nodes; document or inspect help unless the user explicitly requests a multi-node launch. |
| Route to Serve | `ray serve ...` | Use `../serve-deployments/SKILL.md` for Serve deploy/run/status/config specifics. |

## Core Command Map

| Command | Purpose | Key options or notes |
| --- | --- | --- |
| `ray start` | Start Ray processes manually on the local machine. | Important options include `--head`, `--address`, `--port`, `--include-dashboard`, `--dashboard-host`, `--dashboard-port`, `--object-store-memory`, `--num-cpus`, `--num-gpus`, `--resources`, worker port ranges, temp dir, object spilling directory, metrics export port, and resource isolation options. Mutating. |
| `ray stop` | Stop local Ray processes. | Mutating; `--force` is stronger and can cause unexpected worker exits. |
| `ray status` | Print cluster/autoscaler status and resource usage. | `--address` can override the Ray bootstrap address. Use this before deeper state queries. |
| `ray job` | Submit, stop, delete, list, get logs, or query status for Jobs. | Subcommands are `submit`, `status`, `logs`, `stop`, `list`, and `delete`; Jobs use the dashboard/API server address. |
| `ray list` | List State API resources. | Resources include `actors`, `jobs`, `placement-groups`, `nodes`, `workers`, `tasks`, `objects`, `runtime-envs`, and `cluster-events`; supports `--format`, `--filter`, `--limit`, `--detail`, `--timeout`, and `--address`. |
| `ray get` | Get one State API resource by ID. | Does not support every resource type; typically use after `ray list`. |
| `ray summary` | Summarize task, actor, or object state. | Prefer before broad `ray list` on large clusters. |
| `ray logs` | Fetch cluster, actor, task, worker, or job logs. | Useful forms include `ray logs raylet.out --tail 100`, `ray logs actor --id <actor_id>`, `ray logs task --id <task_id> --err`, and `ray logs job --id <job_id>`. |
| `ray dashboard` | Port-forward a Ray cluster's dashboard to a local port using a cluster YAML. | Long-running/connection-changing; common default local and remote port is `8265`. |
| `ray memory` | Print object reference and object store memory summary. | Read-only, but connects to GCS and can be verbose; use for object-reference leaks. |
| `ray timeline` | Write a Chrome tracing timeline JSON in the Ray temp directory. | Connects to the cluster and writes a file; useful for performance debugging. |
| `ray stack` | Dump stack traces of local Python workers. | Requires `py-spy` or `ray[default]`, often `sudo`; local process inspection. |
| `ray up/down/attach/exec/submit` | VM cluster launcher operations using cluster YAML. | Mutating or interactive; confirm config, cloud target, SSH behavior, and credentials first. |
| `ray symmetric-run` | Multi-node launch helper for symmetric jobs. | Reference-only by default because it starts processes and waits for nodes. |

## Safe Help Patterns

Use these commands to discover installed behavior without mutating cluster state:

```bash
ray --help
ray start --help
ray status --help
ray job --help
ray job submit --help
ray list --help
ray summary --help
ray logs --help
python scripts/ray_cli_doctor.py --command job
```

If `ray --help` works but `ray list --help`, `ray job --help`, or `ray logs --help` fails, the install may be too minimal or missing dashboard/state dependencies; `ray[default]` is the usual extra for cluster operations.

## Local Cluster Start/Stop Patterns

Only run these after explicit user authorization:

```bash
ray start --head --dashboard-host=127.0.0.1 --dashboard-port=8265
ray status --address=<bootstrap-address-or-auto>
ray stop
```

For constrained local development, consider setting resource visibility at start time:

```bash
ray start --head --num-cpus=4 --num-gpus=0 --object-store-memory=<bytes>
```

For a head node that should primarily coordinate rather than run user tasks, start it with no schedulable CPUs:

```bash
ray start --head --num-cpus=0
```

Do not guess memory, CPU, GPU, worker port, dashboard host, or object spilling settings for a production cluster. Ask the user for the platform, resource budget, network exposure, and persistence requirements.

## Dashboard and Address Patterns

Ray has multiple address concepts:

- Dashboard/API server address: HTTP URL, commonly `http://127.0.0.1:8265`; used by Jobs CLI/API and many dashboard-backed observability workflows.
- Ray bootstrap address: GCS/bootstrap address used by some cluster CLI commands and `ray.init(address=...)` flows.
- Ray Client URI: commonly `ray://<host>:10001`; for client drivers, not the Jobs REST API.

Common dashboard flows:

```bash
export RAY_API_SERVER_ADDRESS="http://127.0.0.1:8265"
ray job list
ray job status <submission_id>
ray list nodes --address "$RAY_API_SERVER_ADDRESS"
```

For VM clusters launched from a cluster YAML, `ray dashboard cluster.yaml` port-forwards the remote dashboard to a local port. For Kubernetes, users commonly port-forward the dashboard service/pod to a local `8265` endpoint or use an ingress that exposes the dashboard over HTTP. Do not create cloud/Kubernetes credentials, services, or ingress objects without explicit user instructions.

## Jobs CLI Patterns

Typical lifecycle:

```bash
export RAY_API_SERVER_ADDRESS="http://127.0.0.1:8265"
ray job submit --working-dir ./app -- python script.py --arg value
ray job submit --no-wait --working-dir ./app -- python long_running.py
ray job status <submission_id>
ray job logs <submission_id>
ray job stop <submission_id>
```

Notes:

- The `--` separator is significant: Ray job options go before `--`; entrypoint command and its arguments go after it.
- For remote clusters, use `--working-dir` or a runtime environment so the cluster can access the application files.
- `ray job submit` streams stdout/stderr by default until the job exits; `--no-wait` returns after submission.
- `RAY_JOB_HEADERS` can provide JSON request headers when the dashboard/API endpoint requires them.

## State and Logs Workflow

Start broad, then narrow:

```bash
ray status
ray summary tasks
ray summary actors
ray list tasks --limit 20 --filter "state=RUNNING"
ray list actors --format table --limit 20
ray get actors <actor_id>
ray logs actor --id <actor_id> --tail 200
ray logs task --id <task_id> --err
ray logs raylet.out --tail 200
```

State API snapshots can be stale and may return partial or truncated data when multiple components are queried or the result set is too large. Use `--limit`, `--filter`, `--timeout`, and `--format json|yaml|table` to keep output bounded and machine-readable.

## OOM and Object Memory Workflow

Use read-only commands first:

```bash
ray status
ray summary tasks
ray summary actors
ray list nodes --format table
ray list workers --detail --limit 50
ray memory --stats-only
ray logs raylet.out --tail 300
```

Look for worker exit messages such as `UNEXPECTED_SYSTEM_EXIT`, `SYSTEM_ERROR`, Ray OOM-kill summaries, object store pressure, and repeated task/actor retries. If the issue is high parallelism or oversubscribed memory, route code-level fixes to `../core-runtime/SKILL.md` for task/actor resource annotations such as CPU and memory requests.

## Symmetric Run Is Reference-Only

`ray symmetric-run` is useful for tightly coordinated multi-node launches, but it starts Ray processes and waits for nodes. Treat it as documentation/help-only unless the user explicitly asks for it and provides node count, network assumptions, and failure-handling expectations:

```bash
ray symmetric-run --help
```
