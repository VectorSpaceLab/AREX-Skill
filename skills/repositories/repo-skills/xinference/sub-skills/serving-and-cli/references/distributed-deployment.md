# Distributed deployment

This page focuses on service topology, host/port planning, and placement behavior for the CLI commands.

## Topology

- **Local**: one command starts the supervisor, worker, and API together.
- **Distributed**: one supervisor service plus one or more workers.

## Service roles

| Role | Command | What it does |
| --- | --- | --- |
| Local | `xinference-local` | Starts a local cluster and serves the API on `-p` |
| Supervisor | `xinference-supervisor` | Starts the cluster control plane and Web/API service |
| Worker | `xinference-worker` | Joins a cluster and executes model tasks |

## Port and host planning

- `-H`, `--host`: bind address for the service or worker process.
- `-p`, `--port`: service/Web UI endpoint.
- `--supervisor-port`: supervisor internal actor port.
- `--worker-port`: worker internal port.
- `--metrics-exporter-host`, `--metrics-exporter-port`: optional worker metrics exporter endpoint.
- Use `0.0.0.0` when you intentionally want remote access from another machine or container.

## Placement rules from the CLI

- `--n-worker`: number of worker machines to spread one model across.
- `--n-gpu`: GPUs per worker in distributed mode.
- `--worker-ip`: full registered worker address, not a bare host name.
- `--gpu-idx`: comma-separated GPU indexes on that worker.
- `--replica`: number of identical replicas.
- `replica_config` is more precise placement logic, but it is handled in the Python client route, not by the CLI.
- `replica` counts copies; `n-worker` counts worker machines; `n-gpu` counts GPUs per worker.
- When worker addresses are duplicated or unavailable, shrink the request or add more workers first.

## Docker notes

- GPU images need GPU access, port mapping, and `-H 0.0.0.0` when exposed from the container.
- Containerized launches may need larger shared memory for multi-GPU backends.
- Mount persistent model/cache locations if you want downloads to survive container restarts.
- Real model downloads may happen on first launch.

## Kubernetes notes

- Helm-based deployment can set worker count and GPUs per worker.
- Use a custom values file for more complex cluster topologies.
- KubeBlocks support is third-party and not maintained by Xinference.

## When placement goes wrong

- If a worker address is unknown, use the exact registered `IP:port`.
- If the worker count is too high, reduce `--n-worker` or add workers.
- If GPU placement conflicts, adjust `--gpu-idx` or rely on automatic allocation.
- If the command needs more backend-specific launch kwargs, route that work to `models-and-backends`.
