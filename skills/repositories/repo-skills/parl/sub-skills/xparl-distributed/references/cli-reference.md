# xparl CLI Reference

## Purpose

Read this when a task needs to inspect, start, connect to, monitor, or shut down
PARL's `xparl` distributed runtime. Commands in this reference are distilled for
future use; they do not require opening PARL source files.

## Safe help-only check

Before planning a cluster command, check that the installed CLI exposes the
expected commands and options without starting services:

```bash
python scripts/check_xparl_cli.py
```

The bundled checker runs only `--help` forms by default. It does not start,
connect, stop, or query live clusters.

## Command overview

| Command | Mutates processes? | Use it for | Important safety note |
| --- | --- | --- | --- |
| `xparl --help` | No | Confirm CLI entry point and subcommands. | Safe diagnostic. |
| `xparl start --port PORT ...` | Yes | Start a master node and optionally a local worker plus monitor/log services. | Opens ports and launches subprocesses; use only on trusted networks. |
| `xparl connect --address HOST:PORT ...` | Yes | Start a worker node that contributes this machine's CPU or GPU resources. | A joined worker can execute submitted code; never join untrusted clusters. |
| `xparl status` | Reads live state | Show active clusters and monitor addresses detected on this machine. | May contact local cluster processes; avoid as a default smoke check. |
| `xparl stop` | Yes | Stop local xparl master, worker, job, monitor, and log-server processes. | Broad local cleanup; inspect before using on shared machines. |

The `xparl` console entry point is `xparl=parl.remote.scripts:main` in PARL's
package metadata.

## Local CPU cluster pattern

Use this only on a trusted local machine or private test host. Pick ports that
are free on that host and not reachable from untrusted networks.

```bash
# Start a localhost CPU cluster with a bounded local worker and explicit ports.
xparl start --port 6006 --cpu_num 2 --monitor_port 6106 --log_server_port_range 6200-6299

# In user code, connect before creating any @parl.remote_class object.
# parl.connect("localhost:6006")

# Inspect status when needed.
xparl status

# Shut down local xparl processes when finished.
xparl stop
```

By default a CPU worker uses all CPUs on the worker machine. Prefer `--cpu_num`
for notebooks, shared hosts, CI, or any bounded reproduction.

## Adding CPU workers

On another trusted machine that can reach the master:

```bash
xparl connect --address MASTER_IP:6006 --cpu_num 8 --log_server_port_range 6200-6299
```

`xparl connect` can be run after the master is already up. Workers exit
automatically after the master exits under normal conditions, but network
failures can leave stale local processes that require careful local cleanup.

## GPU cluster pattern

A GPU cluster is a different resource mode from a CPU cluster. In GPU mode,
remote actors should request GPUs with `@parl.remote_class(n_gpu=N)`. CPU-only
actor requests can be rejected by a GPU cluster, and GPU actor requests can be
rejected by a CPU cluster.

```bash
# Start a GPU-mode master.
xparl start --port 8002 --gpu_cluster --monitor_port 8102 --log_server_port_range 8200-8299

# Add trusted GPU workers. The list is passed to CUDA_VISIBLE_DEVICES on jobs.
xparl connect --address MASTER_IP:8002 --gpu 0,1,2,3 --log_server_port_range 8200-8299
```

If the master host itself should also contribute GPUs, provide `--gpu` to the
start command. If it should only coordinate workers, omit `--gpu`.

## `xparl start` options

| Option | Required | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--port PORT` | Yes | Master port. | Must be free; error says the localhost master address is already in use if occupied. |
| `--cpu_num N` | No | Number of local worker CPUs. | Must be `>= 0`. If omitted in CPU mode, all local CPUs are used. In GPU-cluster mode the local CPU count is forced to `0`. |
| `--gpu_cluster` | No | Start the master as GPU-cluster mode. | Use with GPU workers and `remote_class(n_gpu=N)`. |
| `--gpu 0,1,...` | No | Comma-separated local GPU IDs to contribute. | Ignored in CPU-cluster mode; useful with `--gpu_cluster` when the master host should also be a worker. |
| `--monitor_port PORT` | No | HTTP monitor port. | Defaults to `master_port + 100`; if unavailable, xparl chooses a free port. |
| `--log_server_port_range START-END` | No | Candidate HTTP log-server ports for local worker jobs. | Default `8000-9000`; format must be `start-end` and start must not exceed end. Avoid master and monitor ports. |
| `--debug` | No | Run in debugging mode with more runtime logs. | Can increase log volume; avoid for long production runs unless needed. |

## `xparl connect` options

| Option | Required | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--address HOST:PORT` | Yes | Master node address. | The worker validates that it can contact the master before launching. |
| `--cpu_num N` | No | Number of worker CPUs to contribute. | Must be `>= 0`; if omitted, all CPUs may be used. |
| `--gpu 0,1,...` | No | Comma-separated GPU IDs to contribute. | Use only for trusted GPU workers attached to GPU clusters. |
| `--log_server_port_range START-END` | No | Candidate HTTP log-server ports for worker jobs. | Default `8000-9000`; choose a private range that does not conflict with other services. |

## Monitor and log service behavior

- `xparl start` launches a monitor process and prints an HTTP monitor URL when
  startup succeeds.
- Each worker starts a log server on a random available port from
  `--log_server_port_range`; remote actor stdout is visible through the log
  service rather than the client terminal.
- `xparl status` detects local worker processes and reports monitor URLs for
  active clusters.
- If the monitor or log server fails to start, choose explicit free ports and
  check firewall or host policy before retrying.

## Bundling decision

The real `xparl start`, `connect`, and `stop` commands are intentionally
process-mutating. This skill bundles only a help-check helper instead of wrapping
cluster lifecycle commands, so future agents must make an explicit safety
decision before launching or stopping any cluster.
