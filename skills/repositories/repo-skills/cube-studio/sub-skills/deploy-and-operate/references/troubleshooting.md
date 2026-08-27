# CubeStudio deployment troubleshooting

Use this reference to triage deployment symptoms without jumping directly to destructive scripts. Prefer read-only inventory, logs, describe output, and config diff review before applying, deleting, rebuilding, or resetting anything.

## Universal triage sequence

1. Identify mode: local Docker Compose, production Kubernetes, offline/private registry, Rancher/KubeSphere-managed cluster, or post-upgrade regression.
2. Inventory static state:
   ```bash
   python scripts/cube_studio_manifest_inventory.py /path/to/cube-studio-or-manifests
   ```
3. Compare the inventory with the intended environment: namespaces, images, pull secrets, PVCs, CRDs, node labels, overlay files, and service exposure.
4. Separate app boot failures from infrastructure failures:
   - app boot: entrypoint, DB migration, Redis, config/project overlays, Celery, frontend proxy;
   - infrastructure: namespace/secret, image pull, PVC pending, node affinity, missing CRD, ingress gateway, device plugin, DNS/registry.
5. Only after a specific failing surface is known should an operator run mutating commands.

## Local Docker Compose symptoms

| Symptom | Likely checks | Notes |
| --- | --- | --- |
| `myapp` never starts | MySQL healthcheck, Redis service, `MYSQL_SERVICE`, `REDIS_HOST`, published port conflicts, bind mounts for entrypoint/config/project. | Compose waits for MySQL health before backend. A DB volume with stale or incompatible data can block first boot. |
| Backend starts then exits during entrypoint | DB migration output, `myapp fab create-admin`, `myapp init`, permissions on `/data/k8s/kubeflow`, static symlink targets, `STAGE` value. | Entrypoint is mutating and reruns migration/admin/init on every boot. |
| Login page redirects or frontend cannot reach backend | Nginx config, frontend container on port `80`, backend service reachability, mounted static frontend directories, cookie/proxy host, first-login URL. | Frontend is served by Nginx and proxies `/` to backend in production-style config. |
| UI missing routes/static assets | `myapp/static/appbuilder/frontend` mount, frontend image/tag, Nginx root paths, whether frontend build artifacts exist. | Do not run `npm install/build` during static triage; route source/frontend build customization to `backend-and-configuration`. |
| Local code changes not visible | Confirm source bind mount into `/home/myapp/myapp/`, `STAGE=dev`, and that the process is running `python myapp/run.py`, not gunicorn/prod. | Backend dev mode supports code bind mount and hot/debug workflows. |
| Local Kubernetes integration fails | Check mounted `kubeconfig` directory and file named like `dev-kubeconfig`; check `ENVIRONMENT=DEV` maps to `dev` cluster config. | Local compose can connect to an existing dev cluster only if kubeconfig and config overlay agree. |

## Config overlay mistakes

CubeStudio's root package files `myapp/config.py` and `myapp/project.py` may be empty placeholders in a checkout. Runtime config normally comes from `install/docker/config.py` and `project.py` for compose, or the Kubernetes cube overlay config files for production.

Common mistakes:

- Editing the placeholder files instead of mounted overlay files.
- Updating `config.py` but not recreating the Kubernetes ConfigMap or rolling pods.
- Updating `project.py` in the wrong location; the mounted overlay owns auth/login, token login, auto-registration, and first-login workspace bootstrap.
- Mismatched `ENVIRONMENT` and `CLUSTERS` key; e.g., `ENVIRONMENT=DEV` expects a `dev` cluster entry.
- Registry fields changed in kustomization but not in runtime `config.py`, so platform-created notebooks/jobs/services still use old image names.
- `SERVICE_EXTERNAL_IP`, `SERVICE_DOMAIN`, dashboard/Grafana paths, or ingress host values still point to example values.
- Image pull secret name differs from `HUBSECRET` / `hubsecret` in namespaces used by workloads.

Route application-specific auth hooks, FAB registration, Celery internals, and model/view code changes to `backend-and-configuration`.

## Kubernetes scheduling and dependency failures

| Symptom | Likely cause | Triage direction |
| --- | --- | --- |
| Pods pending with node affinity errors | Required node labels missing (`kubeflow-dashboard=true`, `mysql=true`, `redis=true`, `monitoring=true`, `gpu=true`, etc.). | Inspect pod events and node labels; update label plan only with operator approval. |
| Pods pending with PVC unbound | PV/PVC/storage class missing or hostPath path unsuitable. | Inspect PVC status; create/adjust storage before redeploying pods. |
| `no matches for kind` or custom resource rejected | CRD missing or not established. | Apply/wait CRDs before custom resources; sequence Prometheus/Istio/Volcano/Argo/Kubeflow resources. |
| ConfigMap/Secret mount errors | ConfigMap or `hubsecret` not present in the pod namespace. | Confirm namespace, ConfigMap generator output, and secret names. |
| ImagePullBackOff | Public registry unreachable, private registry auth missing, image name/tag not rewritten, runtime registry trust missing. | Use manifest inventory and registry rewrite map; inspect namespace secret and node runtime trust. |
| Backend readiness/liveness probe fails | Entrypoint stuck, DB/Redis unavailable, migration failed, config overlay wrong, backend path `/health` not served. | Check backend logs and upstream MySQL/Redis/PVC state before changing probe settings. |
| Frontend reachable but API fails | Nginx proxy to `kubeflow-dashboard.infra`, backend service endpoints, Istio/gateway routing, host headers. | Distinguish in-cluster service DNS from external ingress. |
| Celery worker/scheduler errors | Redis/MySQL env, mounted config, task imports, `check_celery.py` readiness, queue state. | Deployment owns service/env; task internals route to `backend-and-configuration`. |
| Watch pod restarts | Supervisor/watch processes, kubeconfig ConfigMap, RBAC, API connectivity, scheduled liveness restart around hour 03. | Check mounted kubeconfig and cluster permissions. |

## CRD/component-specific issues

### Prometheus and Grafana

- Prometheus custom resources require Prometheus operator CRDs before `Prometheus`, `ServiceMonitor`, and `PodMonitor` objects.
- Grafana expects PVC/configmaps for config and dashboards before deployment.
- ServiceMonitor selection may depend on labels; if metrics are missing, inspect target labels and Prometheus scrape config.
- DCGM GPU dashboards require GPU exporter pods and compatible NVIDIA drivers/device plugin.

### Istio

- `VirtualService` and `Gateway` require Istio networking CRDs.
- External access depends on gateway service exposure, external IP/domain, DNS, and service routing.
- Namespace sidecar injection policy matters. The namespace bootstrap disables injection broadly and removes the disabled label from `service`; do not assume every namespace has sidecars.

### Argo and Kubeflow training operator

- Pipeline workflows rely on Argo controller/CRDs, MinIO or artifact storage, and pipeline runner RBAC.
- Distributed jobs rely on Kubeflow training operator CRDs/RBAC for TFJob, PyTorchJob, MPIJob, MXNet, XGBoost, Paddle, etc.
- Pipeline/job-template authoring and DAG errors route to `pipelines-and-job-templates`; deployment owns whether the CRDs/controllers exist.

### Volcano

- Volcano jobs require Volcano CRDs and controllers/scheduler/webhook.
- If batch/distributed jobs fail scheduling, distinguish Volcano availability from task resource requests and GPU/resource strings. Resource-string interpretation routes to compute/pipeline sub-skills.

### GPU plugin and vendor accelerators

- NVIDIA path uses device plugin plus DCGM exporter; nodes must have drivers and labels expected by manifests.
- GPU monitoring dashboards require metrics exporter pods to run on GPU nodes.
- Vendor accelerator support is a platform capability but actual device names, drivers, resource classes, and node labels are operator-specific. Do not claim hardware validation from static manifests.

## Offline/private-registry failures

| Symptom | Likely cause | Triage direction |
| --- | --- | --- |
| Pulls still hit public registry | Missed image literal in manifest, kustomization, config.py, seed catalog, job template, or runtime-created workload. | Run inventory; compare against registry rewrite map; inspect generated job/notebook/service images. |
| Pulls hit internal registry but fail auth | Missing/incorrect `hubsecret`, wrong namespace, wrong registry server string, expired credentials. | Recreate secret deliberately in all workload namespaces. |
| TLS/insecure registry errors | Runtime lacks registry CA or insecure registry config. | Fix Docker/containerd/RKE2/K3S registry trust with node-owner approval. |
| Offline example pipeline/service fails on `wget` | Built-in command still downloads public data/model. | Rewrite command to copy from offline workspace/PVC and verify data path. |
| Rancher server or agents fail after reboot | Disk pressure, time skew, certificate expiry, webhook/auth proxy issues, containerd image pull problems. | Use Rancher-specific recovery docs; do not reset nodes unless accepted. |
| DNS to mirrors/registries unreliable | CoreDNS host mapping missing, egress proxy down, iptables/DNAT mismatch, TLS/proxy mismatch. | Coordinate with network owners; avoid ad-hoc iptables edits. |

## Dangerous commands that usually indicate overreach

Pause and ask for operator approval before any of these appear in a plan:

- `kubectl delete -k`, `kubectl delete -f`, `kubectl delete ns`, or broad cleanup scripts.
- `uninstall.sh`, Rancher reset scripts, Docker reset scripts, or node cleanup.
- `kubectl label nodes --all` without a node-selection review.
- `kubectl patch svc` for ingress/external IP without IP ownership confirmation.
- `docker build`, `docker pull`, `docker push`, `docker save`, `docker load`, `docker login`.
- `wget`/`curl` installers, apt/yum/pip/npm/yarn installs, or frontend builds.
- Editing host iptables, CoreDNS, kubelet, Docker/containerd, or systemd settings.

## Hard-to-debug cases

### Case: backend reachable, platform-created workloads fail

Likely split-brain configuration: the control-plane deployment image was rewritten correctly, but runtime `config.py` still points `REPOSITORY_ORG`, `NOTEBOOK_IMAGES`, `NNI_IMAGES`, `INFERNENCE_IMAGES`, or `HUBSECRET` to public or stale values. Fix the mounted config overlay and roll the CubeStudio control pods; route notebook image choice details to `compute-notebooks-and-images` and inference defaults to `serving-aihub-and-llm`.

### Case: local compose succeeds, production fails immediately

Local compose does not prove Kubernetes prerequisites. Recheck namespaces/secrets, node labels, PVCs, CRDs, kubeconfig ConfigMap, Redis/MySQL service names, and ingress. Production `STAGE=prod` runs gunicorn and mounts config via ConfigMaps; local `STAGE=dev` runs the Python dev server with bind-mounted code.

### Case: first install partially succeeded, rerun gets worse

Start scripts include `delete`, `create`, and `apply` commands. Rerunning after partial failure can delete live resources, leave PVCs/data inconsistent, or recreate ConfigMaps/Secrets with old values. Inventory current state and build an idempotent repair plan instead of rerunning the whole script.
