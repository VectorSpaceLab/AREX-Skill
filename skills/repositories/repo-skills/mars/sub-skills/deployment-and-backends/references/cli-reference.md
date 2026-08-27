# Mars CLI Reference

## Purpose

Read this when the user asks about `mars-supervisor`, `mars-worker`, service
flags, or a safe way to verify entry points without starting a cluster.

## Verified console entry points

The package metadata exposes these console scripts:

- `mars-supervisor = mars.deploy.oscar.supervisor:main`
- `mars-worker = mars.deploy.oscar.worker:main`

The bundled helper `scripts/check_mars_cli.py` verifies their help paths through
module execution so it works even when console scripts are not on `PATH`. Run it
with the Python environment that has `pymars` installed, for example
`python scripts/check_mars_cli.py --json`; executing the file directly can use a
wrong system Python if the shebang resolves outside the Mars environment.

## Shared CLI flags

Both supervisor and worker support these options:

| Option | Meaning |
|---|---|
| `-h`, `--help` | Show help and exit. Do not confuse this with host binding. |
| `-e`, `--endpoint` | Explicit service endpoint. |
| `-H`, `--host` | Host name or bind address for the service. |
| `-p`, `--ports` | Port list; must match the process count when used. |
| `-c`, `--config` | Inline JSON service configuration. |
| `-f`, `--config-file` | Service configuration file. |
| `-s`, `--supervisors` | Supervisor endpoints, required for workers in fixed-cluster mode. |
| `--log-level` | Log level. |
| `--log-format` | Python logging format. |
| `--log-conf` | Logging config file, defaulting to `logging.conf` when present. |
| `--load-modules` | Extra modules to import into the service process. |
| `--use-uvloop` | `auto` by default; use `no` to disable uvloop. |

## Supervisor-specific flags

| Option | Meaning |
|---|---|
| `-w`, `--web-port` | Web UI service port. |
| `--n-process` | Number of supervisor processes; default is `1`. |

## Worker-specific flags

| Option | Meaning |
|---|---|
| `--n-cpu` | CPU cores to use; default is `auto`. |
| `--mem-bytes` | Worker memory in bytes; default is `auto`. |
| `--n-io-process` | Number of IO processes; default is `1`. |
| `--cuda-devices` | CUDA device list; default `auto` discovers visible devices. Empty string disables GPU use. |

## Safe help checks

Prefer these for verification:

```bash
mars-supervisor --help
mars-worker --help
```

or through the current Python interpreter:

```bash
python -m mars.deploy.oscar.supervisor --help
python -m mars.deploy.oscar.worker --help
```

Do not start long-running services just to answer a parser or flag question.

## Local cluster command shape

For a real local cluster, first choose endpoints and ports, then run supervisor
and worker processes separately. A typical shape is:

```bash
mars-supervisor -H 127.0.0.1 -p 7001 -w 7005
mars-worker -H 127.0.0.1 -p 7003 -s 127.0.0.1:7001
```

Use this as a command shape, not as a verification case, because it starts
long-running services.
