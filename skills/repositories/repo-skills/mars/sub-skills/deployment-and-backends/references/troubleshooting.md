# Deployment and Backend Troubleshooting

## CLI and service startup

### `-h` did not set the host

**Symptoms**
- The command prints help instead of binding to a host.

**Likely cause**
- `-h` is the help flag. Mars uses `-H` / `--host` for host binding.

**Recovery**
- Use `mars-supervisor -H <host> ...` or `mars-worker -H <host> ...`.

### Worker says supervisors are missing

**Symptoms**
- Worker startup fails because no supervisor endpoint was found.

**Likely cause**
- Fixed-cluster mode needs `-s` / `--supervisors` for workers unless endpoint
  discovery is available.

**Recovery**
- Start or identify the supervisor first.
- Pass `-s <supervisor_host>:<supervisor_port>` to each worker.

### Port or process count mismatch

**Symptoms**
- Startup errors around `--ports` or process count.

**Likely cause**
- The port list does not match the number of service processes.

**Recovery**
- Provide one port per process or let Mars choose ports automatically.

## Ray backend

### Ray imports fail or point to a placeholder

**Symptoms**
- `backend='ray'` fails before runtime starts, or optional Ray imports are not
  real packages.

**Likely cause**
- Ray is not installed, is the wrong version, or a local path shadows the real
  package.

**Recovery**
- Install the Ray dependency for the requested environment.
- Run from a neutral directory with isolated Python when diagnosing imports.
- Verify `import ray; print(ray.__version__)` before starting Mars on Ray.

## GPU / CUDA

### `gpu=True` fails at execution time

**Symptoms**
- CUDA, CuPy, cuDF, device allocation, or missing library errors.

**Likely causes**
- No compatible GPU runtime is installed.
- CuPy/cuDF wheel does not match the driver/CUDA stack.
- The worker did not expose the expected devices.

**Recovery**
- Verify the NVIDIA driver and a minimal CuPy or cuDF operation first.
- Use `CUDA_VISIBLE_DEVICES` or worker `--cuda-devices` intentionally.
- Do not call a CPU import check a GPU verification.

### Worker uses GPUs you did not intend

**Symptoms**
- A worker binds to visible GPUs unexpectedly.

**Likely cause**
- `--cuda-devices auto` is the default behavior.

**Recovery**
- Pass `--cuda-devices ""` to disable GPU use.
- Pass an explicit comma-separated device list to limit GPU use.

## Kubernetes

### Kubernetes cluster creation fails

**Symptoms**
- Errors mention kube config, namespace, RBAC, pods, services, image pull, or
  timeouts.

**Likely causes**
- No Kubernetes client configuration.
- Insufficient permissions.
- Wrong image or missing registry access.

**Recovery**
- Confirm `kubectl get nodes` outside Mars if a real cluster is expected.
- Verify the Kubernetes Python client import.
- Choose an image and permissions before calling `new_cluster`.

## YARN

### Non-Linux client

**Symptoms**
- YARN deployment fails before Mars can submit anything.

**Likely cause**
- Skein only supports Linux clients.

**Recovery**
- Use a Linux client or container/VM, then reinstall `skein` and retry.

### YARN cluster creation fails

**Symptoms**
- Errors mention Java, Hadoop, Skein, packed environments, or application queues.

**Likely causes**
- Missing `JAVA_HOME`, `HADOOP_HOME`, `skein`, or environment archive.

**Recovery**
- Verify Java/Hadoop/Skein tooling before calling `new_cluster`.
- Use a packed environment or a remote environment path that exists on YARN
  nodes.

## Docker image helper is not bundled

The original repo image helper performs Docker build and push actions. It is a
reference-only source artifact, not a safe runtime helper. If a user asks to
build an image, treat it as an explicit Docker task with registry, tag, and
permission decisions.
