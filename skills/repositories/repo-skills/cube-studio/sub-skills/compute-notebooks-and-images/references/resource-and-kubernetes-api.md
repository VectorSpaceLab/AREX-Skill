# Resource and Kubernetes API guide

This sub-skill covers the CubeStudio runtime objects that decide where notebooks and debug containers run, how GPU strings are validated, and how monitoring pages summarize live resources.

## Core objects

| Object | What it controls |
| --- | --- |
| `Project` / `Project_User` | Resource group membership, org-scoped access, cluster choice, and shared volume mounts. |
| `Notebook` | Notebook / IDE placement, image choice, mounts, resource requests, and lifecycle actions. |
| `Docker` | Online image debug / commit / push workflow. |
| `Repository` | Registry host, registry credentials, and image pull secret name. |
| `Images` | Curated image catalog entries and their image family labels. |
| `Total Resource` views | Live CPU / memory / GPU summaries, pod links, and Grafana links. |

## Project, org, and cluster routing

`Project` records are the user-facing resource-group container. The important expansion keys are:

- `cluster`: target cluster name
- `org`: resource-group label used for node selection and resource views
- `volume_mount`: shared mount list that gets merged into new pods
- `SERVICE_EXTERNAL_IP`: notebook / service proxy address in edge or split-network setups

Important behavior:

- `Project.node_selector` merges `expand.node_selector` with `org=...` and removes duplicates.
- `Project.org` defaults to `public`.
- `Project.volume_mount` auto-adds `kubeflow-user-workspace(pvc):/mnt` when the workspace mount is missing.
- `Project_User.role` is one of `creator`, `dev`, or `ops`.
- `Project_User.org` controls which resource group a user can see or use.

## GPU string contract

`resource_gpu` is the authoritative GPU request string for notebooks and online debug containers.

Accepted shape:

- `0`
- `1`
- `2(V100)`
- `2（V100）`

Rules enforced by the backend parser:

- quantity must be a non-negative integer
- a model name is optional and may be wrapped in ASCII or Chinese parentheses
- the model name is uppercased
- commas inside the model name are rejected
- the parser returns `nvidia.com/gpu` as the resource key unless a custom resource name is supplied by code

## Selector switching

`MyappModelBase.get_default_node_selector(node_selector, resource_gpu, model_type)` performs the notebook / training selector switch.

| GPU request | Selector result |
| --- | --- |
| `0` | Convert GPU labels back to CPU labels, then append `cpu=true` and the model-type label. |
| `>=1` | Convert CPU labels to GPU labels, then append `gpu=true` and the model-type label. |
| missing `org` | Append `org=public`. |

Example for notebooks:

- input base selector: `cpu=true;notebook=true`
- input GPU string: `2(V100)`
- output selector: `gpu=true;notebook=true;org=public`
- pod-level extras from the Kubernetes helper: `gpu-type=V100`, `gpu=true` label, and `nvidia.com/gpu=2` request / limit

## Kubernetes helper behavior

`myapp.utils.py.py_k8s.K8s` normalizes selector strings and resource requests before creating the pod.

Key points:

- `make_pod()` parses semicolon-separated node selectors into a Kubernetes nodeSelector map.
- `make_pod()` adds `gpu-type=<MODEL>` when the GPU string contains a model.
- `make_pod()` sets `gpu=true` on the pod label and prefers existing GPU nodes when a GPU is requested.
- `make_pod()` uses `nvidia.com/gpu` requests / limits for integer GPU counts.
- `make_pod()` sets `NVIDIA_VISIBLE_DEVICES=none` when the GPU count is zero.
- `get_node_selector(node_selector)` is the lower-level parser for semicolon, newline, or tab separated selectors and can expand `org=a,b` into node affinity for other workflows.

## Monitoring and live resource views

CubeStudio uses Prometheus and Grafana links to summarize live pod and node usage.

Useful signals:

- `GRAFANA_TASK_PATH` → per-pod runtime usage
- `GRAFANA_CLUSTER_PATH` → cluster load summary
- `GRAFANA_NODE_PATH` → per-node load summary
- `GRAFANA_GPU_PATH` → GPU dashboard
- `py_prometheus.Prometheus` → CPU, memory, and GPU query helpers
- `Total_Resource` views → resource-group and namespace aggregation, with K8s dashboard links

GPU monitoring caveat:

- the bundled GPU metrics and dashboards are NVIDIA-oriented (`nvidia.com/gpu`, `dcgm-exporter`, and the NVIDIA device plugin)
- vendor accelerators may still be schedulable through labels or custom resources, but this sub-skill does not claim vendor-specific metric coverage

## Practical reading order

1. Read `notebook-workflows.md` for notebook lifecycle and URLs.
2. Read `image-catalog.md` for registry and image family choices.
3. Use `scripts/parse_resource_gpu.py` to sanity-check GPU strings and selector effects.
