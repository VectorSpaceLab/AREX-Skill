# Kubernetes operations for CubeStudio

This reference distills CubeStudio's Kubernetes deployment materials into a safe operator playbook. It names conventional manifest files and components so an operator can stage, inventory, and review them before applying anything.

## Preconditions to confirm

CubeStudio's production path assumes a prepared Kubernetes cluster and host baseline:

- Kubernetes version in the 1.25-1.31 range is documented, with 1.28 recommended in deployment notes.
- Docker or containerd runtime is already installed and sized for large image storage.
- Shared storage such as NFS/Ceph is mounted consistently on nodes, conventionally under `/data/k8s/`; single-node trials may use hostPath PVCs.
- Control-plane node resources are large enough for the platform control services; workload nodes must match intended CPU/GPU/NPU/RDMA use.
- GPU or vendor accelerator drivers and node plugins are operator-managed prerequisites when those workloads are enabled.
- Operators have reviewed registry access, image pull secrets, storage classes/PVs, ingress IP/domain, and rollback plan.

Read-only inventory first:

```bash
python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-install/kubernetes
```

## Namespace and secret model

The namespace bootstrap script creates or expects these namespaces:

| Namespace | Typical role |
| --- | --- |
| `infra` | CubeStudio backend, frontend, worker, scheduler, watch, MySQL, Redis, and control-plane config. |
| `kubeflow` | MinIO and Kubeflow training operator pieces. |
| `istio-system` | Istio control plane and ingress gateway. |
| `pipeline` | Argo workflow and user pipeline workloads. |
| `automl` | Hyperparameter search workloads. |
| `jupyter` | Notebook and online build pods. |
| `service` | Internal services and inference services. |
| `monitoring` | Prometheus, Grafana, exporters, ServiceMonitors, DCGM. |
| `logging` | Reserved for logging integrations. |
| `kube-system` | Kubernetes dashboard, metrics, device plugins, and system components. |
| `aihub` | AIHub/application workloads. |

`create_ns_secret.sh` also recreates a `hubsecret` Docker registry secret in each namespace and disables Istio sidecar injection on namespaces by default, then removes the disabled label from `service`. It is cluster-mutating and should not be run without replacing placeholder credentials and confirming namespace policy.

## Node labels are part of scheduling

The one-node start path labels a target node with many scheduling flags:

```text
train=true cpu=true notebook=true service=true org=public istio=true kubeflow=true
kubeflow-dashboard=true mysql=true redis=true monitoring=true logging=true
```

CubeStudio manifests use labels such as `kubeflow-dashboard=true` for control-plane pods, and monitoring/GPU manifests use labels such as `monitoring=true`, `gpu=true`, or `vgpu=true`. If pods remain pending with node affinity errors, inspect node labels before editing deployments.

## Component roles

| Component | Role in CubeStudio | Common dependencies |
| --- | --- | --- |
| Kubernetes Dashboard | Web UI for cluster resources. | `kube-system`, dashboard manifests, metrics scraper. |
| MySQL | Platform metadata database. | PV/PVC, service, configmap, deployment, backend `MYSQL_SERVICE`. |
| Redis | Cache, Celery broker/result backend, Socket.IO queue. | Redis manifest/service, backend/worker/scheduler env. |
| Prometheus Operator / Prometheus | Metrics storage and ServiceMonitor CRDs. | CRDs before Prometheus custom resources, RBAC, PV/PVC. |
| Grafana | Monitoring dashboards for nodes, pods, GPU, services. | ConfigMaps for dashboards/datasources, PVC. |
| Node exporter / kube-state-metrics / ServiceMonitors | Metrics scraping. | Prometheus operator CRDs and labels. |
| DCGM exporter | NVIDIA GPU metrics. | GPU nodes and DCGM image; monitoring namespace. |
| NVIDIA device plugin | Exposes NVIDIA GPU resources to Kubernetes. | GPU driver/node compatibility; node label selectors. |
| Volcano | Batch/distributed job scheduling. | Volcano CRDs established before workloads. |
| Istio | Ingress, VirtualService/Gateway routing, service telemetry. | Istio CRDs before gateway/virtual manifests. |
| Argo Workflows | Pipeline workflow execution. | MinIO storage, pipeline runner RBAC, Argo CRDs/controller. |
| Kubeflow training operator | TFJob/PyTorchJob/MPIJob/MXNet/XGBoost/Paddle distributed training. | Kubeflow RBAC and train-operator kustomize overlay. |
| CubeStudio backend/frontend/worker/scheduler/watch | Platform web app, API, Celery workers, scheduled tasks, Kubernetes watchers. | ConfigMaps, Redis/MySQL, kubeconfig ConfigMap, PVCs, image pull secret, service account. |

## Safe ordering model

The repository's start scripts encode this broad order. Operators should adapt it deliberately rather than executing it as-is:

1. Host prep and kubeconfig staging: host-mutating scripts initialize nodes, copy kubeconfig, and may download kubectl. In offline environments, remove downloads and stage binaries separately.
2. Node labels: apply scheduling labels only after confirming the target node and cluster role.
3. Namespaces and image pull secrets: create namespaces and correct registry secrets before starting pods.
4. Cluster RBAC: create CubeStudio service accounts and cluster roles only after reviewing their broad permissions.
5. Kubernetes Dashboard: optional cluster resource UI.
6. MySQL and Redis: create storage, services, configmaps, and deployments before CubeStudio backend pods.
7. Prometheus stack:
   - apply operator CRDs first;
   - apply operator RBAC and deployment;
   - wait for CRDs such as `podmonitors.monitoring.coreos.com` and `prometheuses.monitoring.coreos.com`;
   - then apply node-exporter, Grafana PVC/config/service/deployment, Prometheus rules/RBAC/service/main resource, and ServiceMonitors.
8. GPU monitoring/plugin: apply NVIDIA device plugin and DCGM exporter only on clusters with compatible GPU nodes or when explicitly staging them for future use.
9. Volcano: apply Volcano manifests and wait for `jobs.batch.volcano.sh` CRD establishment before Volcano workloads.
10. Istio: apply Istio CRDs first, wait for networking CRDs, then install control plane, gateway, and virtual routing manifests.
11. Argo: create MinIO PV/PVC, pipeline runner RBAC, and Argo Workflow controller/resources.
12. Kubeflow training operator: apply service account/RBAC and the standalone train-operator kustomize overlay.
13. Kubeconfig ConfigMaps: create `kubernetes-config` in namespaces where CubeStudio workloads need cluster access, including `infra`, `pipeline`, and `automl` in the source sequence.
14. CubeStudio PVCs: create PVC/PV manifests for `infra`, `jupyter`, `automl`, `pipeline`, and `service` before deployments that mount them.
15. CubeStudio overlays: set config/project/entrypoint overlays, image names/tags, service external IPs, and then apply the cube kustomize overlay.
16. Ingress exposure: expose via Istio gateway/virtual service or the KubeSphere path's service patch only after the gateway is ready and IP/domain ownership is confirmed.

## CRD and PVC ordering rules

- Apply a CRD before any custom resource of that kind. Examples: Prometheus `ServiceMonitor`/`PodMonitor`/`Prometheus`, Istio `VirtualService`/`Gateway`, Volcano `Job`, Argo Workflow, Kubeflow training jobs.
- Use CRD establishment waits where available before dependent resources. A manifest inventory can show CRD kinds, but it cannot prove API server establishment.
- Create namespace-scoped PVCs and storage classes before pods that mount them. Pending PVCs will block MySQL, Grafana, Prometheus, MinIO, and CubeStudio data volumes.
- Create ConfigMaps and Secrets before Deployments that mount them; otherwise pods may crash or remain pending.
- Recreate or roll pods after changing mounted ConfigMap contents if the deployment does not pick changes up automatically.

## CubeStudio control-plane overlay

The cube overlay builds a `kubeflow-dashboard-config` ConfigMap from:

- `config/config.py`
- `config/project.py`
- `config/entrypoint.sh`

It also builds a `deploy-config` ConfigMap with values such as:

- `STAGE=prod`
- `REDIS_HOST=redis-master.infra`
- `REDIS_PORT=6379`
- `REDIS_PASSWORD=admin`
- `MYSQL_SERVICE=mysql+pymysql://root:admin@mysql-service.infra:3306/kubeflow?charset=utf8`
- `ENVIRONMENT=DEV`

The base manifests deploy:

| Workload | Runtime behavior |
| --- | --- |
| `kubeflow-dashboard` | Backend web/API container, privileged, mounts config, kubeconfig, and `infra-kubeflow` PVC; health probes `/health`. |
| `kubeflow-dashboard-frontend` | Nginx frontend proxying to backend and serving static/frontend files. |
| `kubeflow-dashboard-worker` | Celery worker using Redis/MySQL env and mounted config/kubeconfig/PVC. |
| `kubeflow-dashboard-schedule` | Celery beat scheduler; has a readiness probe that runs a Celery check helper. |
| `kubeflow-watch` | Supervisor-based watchers for platform Kubernetes state. |

The service account is cluster-wide and powerful (`create`, `delete`, `patch`, `update`, `get`, `list`, `watch` on all API groups/resources). Review this trust boundary for each target cluster.

## KubeSphere variant

The KubeSphere-oriented script follows the same broad platform order, but differs in monitoring installation and ingress exposure:

- It applies Grafana and Prometheus adapter resources rather than the full Prometheus operator sequence in the same way as the single-node script.
- It patches `istio-ingressgateway` external IPs after applying cube overlays.
- It still mutates namespaces, secrets, labels, PVCs, CRDs, RBAC, and deployments.

Treat it as a deployment recipe to adapt, not a portable safe command.

## Read-only versus mutating actions

Read-only or static:

- Run the bundled manifest inventory helper.
- Parse YAML/kustomization files.
- Use `bash -n` on shell scripts.
- Review image names, namespaces, PVC names, ConfigMap keys, and command lines.

Mutating and approval-required:

- `kubectl apply`, `create`, `delete`, `patch`, `label`, `wait` against a real cluster.
- Editing host files, kubelet config, Docker/containerd registries, iptables, CoreDNS, or storage mounts.
- Running install/uninstall/reset scripts.
- Image pulls, pushes, saves, loads, and builds.

## Operator handoff checklist

Before execution, provide:

- cluster identity and kubeconfig source;
- target namespaces and registry secret values;
- storage/PVC plan and whether hostPath is acceptable;
- node label plan;
- image registry rewrite plan;
- CRD dependency order;
- overlay diff for `config.py`, `project.py`, `entrypoint.sh`, kustomization image names/tags, and service exposure;
- rollback plan for ConfigMaps, deployments, PVCs, and ingress;
- explicit list of commands that will mutate the cluster or hosts.
