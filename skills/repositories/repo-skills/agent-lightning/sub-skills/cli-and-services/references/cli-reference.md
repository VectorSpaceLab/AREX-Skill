# CLI reference

## Purpose

Use this for help-confirmed `agl` commands and flags. The public docs warn that CLI reference can lag; prefer live `--help` in the target environment.

## `agl`

Verified help shape:

```text
usage: agl [-h] {vllm,store,prometheus,agentops}

Agent Lightning CLI entry point.

Available subcommands:
  vllm      Run the vLLM CLI with Agent Lightning instrumentation.
  store     Run a LightningStore server.
  prometheusServe Prometheus metrics from the multiprocess registry.
  agentops  Start the AgentOps server manager.
```

The dispatcher imports subcommand modules lazily. A subcommand can appear in top-level help but still fail if its optional module/dependency is absent.

## `agl store`

Verified help:

```text
usage: agl store [-h] [--host HOST] [--port PORT] [--cors-origin CORS_ORIGINS]
                 [--log-level {DEBUG,INFO,WARNING,ERROR}]
                 [--tracker {prometheus,console} [{prometheus,console} ...]]
                 [--n-workers N_WORKERS] [--backend {memory,mongo}]
                 [--mongo-uri MONGO_URI]
```

Options:

| Flag | Meaning |
| --- | --- |
| `--host` | Host to bind. Default is service-oriented (`0.0.0.0`). Use `127.0.0.1` for local-only tests. |
| `--port` | Store server port, default `4747`. |
| `--cors-origin` | Repeatable allowed CORS origin; `*` allows all origins. |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, or `ERROR`. |
| `--tracker` | Enable metrics tracking: `prometheus`, `console`, or both. |
| `--n-workers` | Worker count for server launch mode; values >1 use multiprocess launch for zero-copy stores. |
| `--backend` | `memory` or optional `mongo`. |
| `--mongo-uri` | Mongo URI used only with `--backend mongo`. |

Local-only example:

```bash
agl store --host 127.0.0.1 --port 4747 --log-level DEBUG
```

Connect from Python:

```python
store = agl.LightningStoreClient("http://127.0.0.1:4747")
```

## `agl prometheus`

Verified help:

```text
usage: agl prometheus [-h] [--host HOST] [--port PORT]
                      [--metrics-path METRICS_PATH]
                      [--log-level {DEBUG,INFO,WARNING,ERROR}] [--access-log]
```

Options:

| Flag | Meaning |
| --- | --- |
| `--host` | Host to bind metrics server. |
| `--port` | Port for metrics server, default `4748`. |
| `--metrics-path` | Endpoint path; must start with `/` and must not be root. Default `/v1/prometheus`. |
| `--log-level` | Logging level. |
| `--access-log` | Enable uvicorn access logs. |

Before starting the server, set `PROMETHEUS_MULTIPROC_DIR` to an existing or creatable directory:

```bash
export PROMETHEUS_MULTIPROC_DIR="$(mktemp -d)"
agl prometheus --host 127.0.0.1 --port 4748
```

## `agl vllm`

`agl vllm` imports vLLM and then runs vLLM's CLI with Agent Lightning instrumentation. Use it only in an environment where vLLM and compatible torch/CUDA dependencies are installed.

Typical failure in a CPU/base environment:

```text
ModuleNotFoundError: No module named 'vllm'
```

That is not a core package failure unless the user's task requires vLLM.

## `agl agentops`

The top-level dispatcher lists `agentops`. Because this subcommand is imported lazily, verify it in the target environment with:

```bash
agl agentops --help
```

If it fails with a missing module, treat the subcommand as unavailable for that installation and use `AgentOpsTracer` from Python instead when trace instrumentation is the real goal.

## Help-first verification commands

```bash
agl --help
agl store --help
agl prometheus --help
```

Avoid starting long-running services during simple validation; use `--help` first.
