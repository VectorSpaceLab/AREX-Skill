# Security and Operations

## Purpose

Read this before running or recommending any `xparl start`, `xparl connect`, or
`xparl stop` command. xparl is powerful because it can execute arbitrary Python
work on joined workers; that same feature is the primary security boundary.

## Trust model

- Only trusted users should submit client code to a cluster.
- Only trusted machines should join a cluster as workers.
- Only trusted code and trusted `distributed_files` should be sent to workers.
- Do not expose master, monitor, or log-server ports to the public internet or
  to a shared network where untrusted users can connect.

PARL/xparl intentionally uses Python serialization for remote classes and data.
Serialized Python objects can carry executable behavior. Treat xparl similarly
to giving the client the ability to run Python code on every worker machine,
including reading, creating, modifying, or deleting files that the worker process
can access.

## Port and network boundary

A running cluster can use several network services:

| Service | Typical source | Notes |
| --- | --- | --- |
| Master | `xparl start --port PORT` | Coordinates resources and receives client/worker connections. |
| Monitor | `--monitor_port`, defaulting near the master port | Exposes HTTP status for workers, clients, and jobs. |
| Worker log server | Random available port from `--log_server_port_range` | Exposes remote actor logs and log downloads. |

Operational guidance:

1. Prefer `localhost` for single-machine tests.
2. For multi-machine clusters, use a private subnet, VPN, or similarly trusted
   network boundary.
3. Choose explicit monitor and log-server port ranges that are not publicly
   reachable and do not conflict with other services.
4. Treat monitor and log URLs as sensitive operational surfaces because they
   reveal cluster/job state and logs.
5. Never ask untrusted users to run `xparl connect` into your master.

## Lifecycle checklist

Before start:

- Confirm the task genuinely needs distributed execution; many API/import checks
  should stay local.
- Decide CPU versus GPU cluster mode. Do not mix mode assumptions.
- Select free, private ports for master, monitor, and log servers.
- Bound local resource use with `--cpu_num` or explicit GPU IDs.
- Confirm all workers have compatible PARL and Python major/minor versions.
- Confirm no credentials or private material will be shipped through
  `distributed_files`.

During run:

- Call `parl.connect` before creating remote actors.
- Read remote logs through the log URL or monitor; local stdout does not show
  remote `print()` output.
- Watch for no-vacant-resource symptoms instead of spawning unbounded actors.
- Avoid long-running production work until a tiny trusted smoke actor succeeds.

Shutdown:

- Use `xparl stop` only when you intend to stop local xparl processes on that
  machine. It kills local `remote/start.py`, `remote/job.py`, `remote/monitor.py`,
  and `remote/log_server.py` style processes, not just a single port.
- Stop stale workers on the host where they run; do not assume stopping the
  master cleans up every failure mode after network partitions.
- On shared machines, inspect active processes and coordinate with other users
  before stopping anything.

## CPU and GPU resource modes

- CPU clusters run CPU actors by default. `xparl start` without `--cpu_num` can
  consume all CPUs on the local worker; set `--cpu_num` for bounded use.
- GPU clusters are started with `--gpu_cluster`; workers contribute GPUs with
  `--gpu 0,1,...`.
- Remote actors request GPUs with `@parl.remote_class(n_gpu=N)`.
- A CPU cluster rejects GPU actor requests. A GPU cluster can reject CPU actor
  requests. Treat mode mismatch as a configuration error, not a soft fallback.

## Version and dependency consistency

When a client connects, PARL checks that the client and master agree on PARL
version and Python major/minor version. If workers use a different environment,
remote imports and serialization can still fail. Align the cluster environment
before debugging application logic.

Common required runtime pieces include the `xparl` console entry point, Python
serialization support, ZeroMQ, gRPC/protobuf, Click, Requests, Flask-based log
and monitor services, and PARL itself. For backend-specific model code, use the
`core-framework` sub-skill to verify Paddle/Torch/Fluid imports before launching
remote actors.

## Logs and monitor behavior

- Remote actor stdout is not printed in the client terminal by default.
- xparl emits a log-monitor URL after `parl.connect`; use it to inspect actor
  output.
- The cluster monitor reports connected workers, clients, and jobs through an
  HTTP interface.
- A log-server health check can return HTTP 400 for `/get-log` without a
  `job_id`; in PARL's own checks, that response indicates the service is up.
- If monitor startup fails, choose an explicit free monitor port and verify that
  host policy allows local HTTP services.

## Safe operational boundaries for future agents

- The bundled `scripts/check_xparl_cli.py` is safe by default because it runs
  help text only.
- Do not hide `xparl start`, `connect`, or `stop` inside a diagnostic helper or
  notebook cell that looks read-only.
- Do not start a public multi-machine cluster as part of skill verification.
  Use a tiny localhost cluster only after explicit approval and cleanup planning.
