# Mars Backend Reference

## Purpose

Read this when the user asks about Ray, GPU/CUDA, Kubernetes, YARN, or external
cluster deployment. Treat these as optional backend routes unless the user has
provided the required services and package variants.

## Ray backend

Source-confirmed entry points:

```python
mars.new_session(address=None, session_id=None, backend='mars', default=True,
                 new=True, **kwargs)
mars.new_ray_session(address=None, session_id=None, backend='mars', default=True,
                     **new_cluster_kwargs)
mars.new_cluster_in_ray(**kwargs)
```

Common patterns:

```python
import mars

# Start a Mars runtime on an existing or auto-started Ray runtime.
session = mars.new_session(backend='ray')

# For larger Ray-side supervisor management.
session = mars.new_ray_session(backend='ray')
```

Prerequisites:
- A compatible `ray` installation, typically `ray>=1.8.0,<2.4.0` from Mars's Ray extra.
- Mars can auto-start a local Ray runtime, or you can point it at a Ray cluster address when connecting remotely.
- Python/package compatibility with Mars's Ray extra.

## GPU / CUDA route

Tensor and DataFrame GPU usage is optional and CUDA-specific:

```python
import mars.tensor as mt

a = mt.random.rand(10, 10, gpu=True)
result = a.sum().execute()

b = mt.random.rand(10, 10).to_gpu()
c = b.to_cpu()
```

Worker-side GPU selection:

```bash
mars-worker -H <worker_ip> -p <worker_port> -s <supervisor_ip>:<supervisor_port> --cuda-devices 0,1
```

Prerequisites:
- NVIDIA GPU, driver, and compatible CUDA package stack.
- CuPy for tensor GPU paths.
- cuDF for DataFrame GPU paths.
- Use `CUDA_VISIBLE_DEVICES` or worker `--cuda-devices` to constrain devices.

A CPU import or CPU local session smoke does not verify GPU execution.

## Kubernetes route

Source-confirmed API shape:

```python
from mars.deploy.kubernetes import new_cluster

cluster = new_cluster(
    kube_api_client=None,
    image=None,
    supervisor_num=1,
    supervisor_cpu=None,
    supervisor_mem=None,
    worker_num=1,
    worker_cpu=None,
    worker_mem=None,
    worker_spill_paths=None,
    worker_cache_mem=None,
    min_worker_num=None,
    web_num=1,
    web_cpu=None,
    web_mem=None,
    service_type=None,
    timeout=None,
    **kwargs,
)
```

Prerequisites:
- Real Kubernetes cluster access and a configured client.
- Kubernetes Python client package, typically `kubernetes>=10.0.0` from Mars's Kubernetes extra.
- Correct image choice and permissions to create namespace/service resources.
- Docker/registry credentials only if building or pushing images.

The repo's original image helper is intentionally not bundled as a runnable
script because it invokes Docker and can push images.

## YARN route

Source-confirmed API shape:

```python
from mars.deploy.yarn import new_cluster

cluster = new_cluster(
    environment=None,
    supervisor_num=1,
    supervisor_cpu=None,
    supervisor_mem=None,
    worker_num=1,
    worker_cpu=None,
    worker_mem=None,
    worker_spill_paths=None,
    worker_cache_mem=None,
    min_worker_num=None,
    timeout=None,
    log_config=None,
    skein_client=None,
    app_name=None,
    app_queue=None,
    **kwargs,
)
```

Prerequisites:
- Linux client support is required for Skein-based YARN deployment.
- Hadoop/YARN environment and Java.
- `skein` and any environment-packing tooling such as conda-pack or venv-pack.
- `JAVA_HOME` and `HADOOP_HOME` should point at real client installs, and Hadoop client tools must be on `PATH`.
- A packed environment, remote environment path, or explicit Python executable
  path that every YARN node can use.

## Backend verification policy

- CLI help is safe to verify.
- Real Ray, CUDA, Kubernetes, and YARN execution is optional and should be run
  only after prerequisites, hardware, services, credentials, and runtime budget
  are explicit.
- If the user asks for a backend task, do not claim it is verified from the CPU
  baseline alone.
